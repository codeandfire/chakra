from configparser import ConfigParser
import io

__all__ = ['dumps', 'dump', 'loads', 'load']

# this is a simple wrapper around the `ConfigParser` module

def dumps(data):
    parser = ConfigParser(delimiters=('=',))
    parser.read_dict(data)
    # `io.StringIO`: a workaround for `ConfigParser` not having a method to write to a string
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
