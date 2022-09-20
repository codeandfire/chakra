import unittest

from chakra.errors import ParseError
from chakra.utils import parseerror

class TestParseerror(unittest.TestCase):

    def test_success(self):

        @parseerror('this is never going to happen')
        def truthy_func():
            assert True
            return 'foo'

        assert truthy_func() == 'foo'    # no error should be raised

    def test_failure(self):

        @parseerror('this is always going to happen')
        def falsy_func():
            assert False

        with self.assertRaisesRegex(ParseError, r'^this is always going to happen$'):
            falsy_func()
