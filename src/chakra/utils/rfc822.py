__all__ = ['dumps', 'dump', 'loads', 'load']

# `dumps()` code below draws from code in the package `pyproject-metadata`.
# https://github.com/FFY00/python-pyproject-metadata/blob/main/pyproject_metadata/__init__.py#L52

def dumps(headers, body):
    text = []
    for name, entries in headers.items():
        for entry in entries:
            lines = entry.strip().split('\n')
            text.append(f'{name}: {lines[0]}')
            for line in lines[1:]:
                text.append(f'        {line}')
    text.append('')    # leave a line
    text.append(body)
    return '\n'.join(text)

def dump(headers, body, fp):
    return fp.write(dumps(headers, body))

def loads(text):
    text = text.split('\n')
    headers = {}
    last_added_key = None

    for idx, line in enumerate(text):
        if line == '':   # headers over
            break
        try:
            key, value = line.split(': ', maxsplit=1)
        except ValueError:
            # no colon indicates a continuation of the previous key-value pair
            value = line.strip()
            key = last_added_key
            try:
                headers[key][-1] += '\n' + value
            except KeyError:
                # the first (few) line(s) are "pretending" to be a continuation of a
                # "previous" key-value pair; just ignore them
                continue
        else:
            key, value = key.strip(), value.strip()
            if key in headers.keys():
                headers[key].append(value)
            else:
                headers[key] = [value]
            last_added_key = key

    body = text[idx+1:]
    body = '\n'.join(body)
    return (headers, body)

def load(fp):
    return loads(fp.read().strip())
