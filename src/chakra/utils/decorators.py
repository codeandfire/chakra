import functools

from ..errors import ParseError

def parseerror(msg):

    def decorator(func):

        @functools.wraps(func)
        def wrapper():
            try:
                return func()
            except AssertionError:
                raise ParseError(msg)

        return wrapper

    return decorator
