import unittest
import textwrap

from chakra.utils import rfc822


class Test(unittest.TestCase):

    # sample data.

    _headers = {
        'foo': ['bar', 'baz', 'foo\nbar'],
        'bar': ['baz\nfoo\nbar', 'foo', 'baz'],
        'baz': ['foo'],
    }
    _body = 'foo bar\nbaz'

    _text = textwrap.dedent("""
        foo: bar
        foo: baz
        foo: foo
                bar
        bar: baz
                foo
                bar
        bar: foo
        bar: baz
        baz: foo

        foo bar
        baz
    """).strip()


    def test_dumps(self):
        """Test conversion to RFC 822 formatted text."""

        assert rfc822.dumps(self._headers, self._body) == self._text

    def test_loads(self):
        """Test conversion from RFC 822 formatted text back to data."""

        assert rfc822.loads(self._text) == (self._headers, self._body)

    def test_identity(self):
        """Test whether identity holds.

        Essentially, a piece of data converted to RFC 822 formatted text and back
        to data should be exactly the same as the original data, and similarly for text
        converted to data and back to text.
        """

        assert rfc822.loads(rfc822.dumps(self._headers, self._body)) == \
            (self._headers, self._body)
        assert rfc822.dumps(*rfc822.loads(self._text)) == self._text


class TestBoundaryCases(unittest.TestCase):

    def test_empty(self):
        """No data."""

        headers, body = {}, ''
        text = '\n'
        assert rfc822.dumps(headers, body) == text
        assert rfc822.loads(text) == (headers, body)

    def test_empty_body(self):
        """Headers but no body."""

        headers = {
            'foo': ['bar', 'baz', 'foo\nbar'],
            'baz': ['foo'],
        }
        body = ''

        # the `\n\n` is added outside the `textwrap.dedent()` argument so that it is not
        # removed by the `.strip()` method.
        text = textwrap.dedent("""
            foo: bar
            foo: baz
            foo: foo
                    bar
            baz: foo
        """).strip() + '\n\n'
        assert rfc822.dumps(headers, body) == text
        assert rfc822.loads(text) == (headers, body)

    def test_empty_headers(self):
        """Body but no headers."""

        headers = {}
        body = 'foo bar\nbaz'
        text = '\nfoo bar\nbaz'
        assert rfc822.dumps(headers, body) == text
        assert rfc822.loads(text) == (headers, body)

    @unittest.skip('currently failing')
    def test_empty_values_case1(self):
        """Empty lists as values."""

        headers = {'foo': [], 'bar': []}
        body = 'foo bar\nbaz'
        text = textwrap.dedent("""
            foo: 
            bar: 

            foo bar
            baz
        """).strip()
        assert rfc822.dumps(headers, body) == text

    @unittest.skip('currently failing')
    def test_empty_values_case2(self):
        """Empty strings as individual values."""

        headers = {
            'foo': ['bar', '', ''],
            'bar': ['', 'baz'],
        }
        body = 'foo bar\nbaz'
        text = textwrap.dedent("""
            foo: bar
            foo: 
            foo: 
            bar: 
            bar: baz

            foo bar
            baz
        """).strip()
        assert rfc822.dumps(headers, body) == text

    def test_two_newlines_in_value_case1(self):
        """A value in the headers contains two (or more) consecutive newlines.

        The expected behaviour is that any consecutive newlines in the headers should be
        collapsed down to a single newline.
        """

        headers = {
            'foo': ['bar', 'baz', 'foo\n\nbar'],
            'bar': ['baz\nfoo\n\n\nbar', 'foo', 'baz'],
        }
        body = 'foo bar\nbaz'
        text = textwrap.dedent("""
            foo: bar
            foo: baz
            foo: foo
                    bar
            bar: baz
                    foo
                    bar
            bar: foo
            bar: baz

            foo bar
            baz
        """).strip()
        assert rfc822.dumps(headers, body) == text

    def test_two_newlines_in_value_case2(self):
        """Two (or more) consecutive newlines in headers must cause parsing issues.

        This is somewhat a different test because it verifies that our implementation HAS
        (instead of does NOT have) a particular flaw.
        """

        text = textwrap.dedent("""
            foo: bar
            foo: baz
            foo: foo
                    
                    bar
            bar: baz
                    foo
                    
                    
                    baz
            bar: foo
            bar: baz

            foo bar
            baz
        """).strip()

        # the headers and body from which the above text could have possibly been
        # generated.
        headers = {
            'foo': ['bar', 'baz', 'foo\n\nbar'],
            'bar': ['baz\nfoo\n\n\nbar', 'foo', 'baz'],
        }
        body = 'foo bar\nbaz'
        assert rfc822.loads(text) != (headers, body)

    def test_colon_without_space(self):
        """Using a colon without a space following it must cause parsing issues.

        Again, this verifies that our implementation HAS a particular flaw.
        """

        text = textwrap.dedent("""
            foo:bar
            foo:baz
            bar: baz
            bar:foo

            foo bar
            baz
        """).strip()

        # the headers and body from which the above text could have possibly been
        # generated.
        headers = {'foo': ['bar', 'baz'], 'bar': ['baz', 'foo']}
        body = 'foo bar\nbaz'
        assert rfc822.loads(text) != (headers, body)
