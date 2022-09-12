"""Simple implementation of the RFC 822 format.

The format consists of a series of headers (represented by a dictionary) and a body
(represented by a string).

The `dumps()` implementation below draws from code from the package `pyproject-metadata`.
Refer: https://github.com/FFY00/python-pyproject-metadata/blob/main/pyproject_metadata/__init__.py#L52
"""


__all__ = ['dumps', 'dump', 'loads', 'load']


def dumps(headers, body):
    text = []

    for name, entries in headers.items():

        for entry in entries:
            lines = entry.strip().split('\n')

            # remove any blank lines arising due to consecutive newlines.
            lines = [line for line in lines if line != '']

            try:
                text.append(f'{name}: {lines[0]}')
            except IndexError:
                # there aren't actually any values.
                continue

            for line in lines[1:]:
                text.append(f'        {line}')

    # leave a line.
    text.append('')

    text.append(body)

    return '\n'.join(text)


def dump(headers, body, fp):
    return fp.write(dumps(headers, body))


def loads(text):
    text = text.split('\n')
    headers = {}
    last_added_key = None

    for idx, line in enumerate(text):
        if line == '':
            # headers are over, we have reached the body.
            break

        try:
            key, value = line.split(': ')

        except ValueError:
            # no colon in the line indicates that this is a continuation of the previous
            # key-value pair.

            value = line.strip()
            key = last_added_key

            try:
                headers[key][-1] += '\n' + value

            except KeyError:
                # this is a case of the first line (or first few lines) "pretending" to be
                # a continuation of a "previous" key-value pair.
                # we will just ignore such lines.
                continue

        else:
            key, value = key.strip(), value.strip()

            if key in headers.keys():
                headers[key].append(value)
            else:
                headers[key] = [value]

            last_added_key = key

    # `idx` here will be the index at which the for loop above breaks.
    # it represents an index of a line in `text`; the index following `idx` will
    # correspond to the line where the body starts.

    body = text[idx+1:]
    body = '\n'.join(body)

    return (headers, body)


def load(fp):
    return loads(fp.read().strip())
