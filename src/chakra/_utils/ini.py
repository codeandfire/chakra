"""Simple implementation of the INI configuration format.

This implementation is simply a thin wrapper around the standard library `configparser`
module.
"""


from configparser import ConfigParser
import io


__all__ = ['dumps', 'dump', 'loads', 'load']


def dumps(data):
    parser = ConfigParser(delimiters=('=',))
    parser.read_dict(data)

    # `ConfigParser` does not provide a method to write the INI formatted text to a
    # string, i.e. it can only be written to a file.
    # hence, we use an `io.StringIO` object as a workaround.

    with io.StringIO() as s:
        parser.write(s, space_around_delimiters=True)
        text = s.getvalue().strip()

    return text


def dump(data, fp):
    return fp.write(dumps(data))


def loads(text):
    parser = ConfigParser(delimiters=('=',))
    parser.read_string(text)

    data = {}
    for section in parser.sections():
        data[section] = dict(parser.items(section))

    return data


def load(fp):
    return loads(fp.read().strip())
