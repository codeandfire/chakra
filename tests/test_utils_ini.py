import unittest
import textwrap

from chakra.utils import ini

class Test(unittest.TestCase):

    # sample data.

    _data = {
        'foo_section': {'foo': 'bar', 'bar': 'baz', 'baz': 'foo'},
        'bar_section': {'bar': 'baz'},
    }
    _text = textwrap.dedent("""
        [foo_section]
        foo = bar
        bar = baz
        baz = foo

        [bar_section]
        bar = baz
    """).strip()


    def test_dumps(self):
        assert ini.dumps(self._data) == self._text

    def test_loads(self):
        assert ini.loads(self._text) == self._data

    def test_identity(self):
        # data converted to text and back should be the same and likewise for text
        assert ini.loads(ini.dumps(self._data)) == self._data
        assert ini.dumps(ini.loads(self._text)) == self._text

class TestBoundaryCases(unittest.TestCase):

    def test_empty(self):
        data = {}
        text = ''
        assert ini.dumps(data) == text
        assert ini.loads(text) == data

    def test_empty_sections(self):
        data = {'foo_section': {}, 'bar_section': {}}
        text = textwrap.dedent("""
            [foo_section]

            [bar_section]

        """).strip()
        assert ini.dumps(data) == text
        assert ini.loads(text) == data

    @unittest.skip('currently failing')
    def test_no_sections(self):
        data = {'foo': 'bar', 'bar': 'baz', 'baz': 'foo'}
        text = textwrap.dedent("""
            foo = bar
            bar = baz
            baz = foo
        """).strip()
        assert ini.dumps(data) == text
        assert ini.loads(text) == data

    def test_empty_values(self):
        data = {'foo_section': {'foo': '', 'bar': ''}}
        text = textwrap.dedent("""
            [foo_section]
            foo = 
            bar = 
        """).strip()
        assert ini.dumps(data) == text
        assert ini.loads(text) == data

    # TODO: A test for empty keys? But is that even valid INI?
