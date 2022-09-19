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
        assert rfc822.dumps(self._headers, self._body) == self._text

    def test_loads(self):
        assert rfc822.loads(self._text) == (self._headers, self._body)

    def test_identity(self):
        # data converted to text and back should be the same and likewise for text
        assert rfc822.loads(rfc822.dumps(self._headers, self._body)) == \
            (self._headers, self._body)
        assert rfc822.dumps(*rfc822.loads(self._text)) == self._text

class TestBoundaryCases(unittest.TestCase):

    def test_empty(self):
        headers, body = {}, ''
        text = '\n'
        assert rfc822.dumps(headers, body) == text
        assert rfc822.loads(text) == (headers, body)

    def test_empty_body(self):
        headers = {
            'foo': ['bar', 'baz', 'foo\nbar'],
            'baz': ['foo'],
        }
        body = ''
        # the `\n\n` is added outside the `textwrap.dedent()` argument so that it is not
        # removed by the `.strip()` method
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
        headers = {}
        body = 'foo bar\nbaz'
        text = '\nfoo bar\nbaz'
        assert rfc822.dumps(headers, body) == text
        assert rfc822.loads(text) == (headers, body)

    @unittest.skip('currently failing')
    def test_empty_values_case1(self):
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
        # value in the headers contains two or more consecutive newlines, it should be
        # collapsed down to a single newline.

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
        # note that this data does not uniquely produce the above text
        headers = {
            'foo': ['bar', 'baz', 'foo\n\nbar'],
            'bar': ['baz\nfoo\n\n\nbar', 'foo', 'baz'],
        }
        body = 'foo bar\nbaz'
        assert rfc822.loads(text) != (headers, body)   # parsing fails

    def test_colon_without_space(self):
        text = textwrap.dedent("""
            foo:bar
            foo:baz
            bar: baz
            bar:foo

            foo bar
            baz
        """).strip()
        # note that this data does not uniquely produce the above text
        headers = {'foo': ['bar', 'baz'], 'bar': ['baz', 'foo']}
        body = 'foo bar\nbaz'
        assert rfc822.loads(text) != (headers, body)   # parsing fails
