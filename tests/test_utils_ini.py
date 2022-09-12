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
        """Test conversion to INI formatted text."""

        assert ini.dumps(self._data) == self._text

    def test_loads(self):
        """Test conversion from INI formatted text back to data."""

        assert ini.loads(self._text) == self._data

    def test_identity(self):
        """Test whether identity holds.

        Essentially, a piece of data converted to INI formatted text and back to data
        should be exactly the same as the original data, and similarly for text
        converted to data and back to text.
        """

        assert ini.loads(ini.dumps(self._data)) == self._data
        assert ini.dumps(ini.loads(self._text)) == self._text


class TestBoundaryCases(unittest.TestCase):

    def test_empty(self):
        """No data."""

        data = {}
        text = ''

        assert ini.dumps(data) == text
        assert ini.loads(text) == data

    def test_empty_sections(self):
        """Data with empty sections."""

        data = {'foo_section': {}, 'bar_section': {}}
        text = textwrap.dedent("""
            [foo_section]

            [bar_section]

        """).strip()

        assert ini.dumps(data) == text
        assert ini.loads(text) == data

    @unittest.skip('currently failing')
    def test_no_sections(self):
        """Data with key-value pairs not under any section."""

        data = {'foo': 'bar', 'bar': 'baz', 'baz': 'foo'}
        text = textwrap.dedent("""
            foo = bar
            bar = baz
            baz = foo
        """).strip()

        assert ini.dumps(data) == text
        assert ini.loads(text) == data

    def test_empty_values(self):
        """Key-value pairs have empty strings as values."""

        data = {'foo_section': {'foo': '', 'bar': ''}}
        text = textwrap.dedent("""
            [foo_section]
            foo = 
            bar = 
        """).strip()

        assert ini.dumps(data) == text
        assert ini.loads(text) == data

    # TODO: A test for empty keys? But is that even valid INI?
