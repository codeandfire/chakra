from pathlib import Path
import textwrap
import unittest

import tomli_w
from chakra.config import Config, _write_ini, _write_rfc822

# load a patched version of `tempfile`.
from chakra._tempfile_patch import tempfile


class TestWriteRFC822(unittest.TestCase):
    """Tests for the helper function `_write_rfc822()`."""

    def test(self):
        """Test a sample message."""

        text = _write_rfc822(
            headers={
                'foo': ['bar', 'baz', 'foo\nbar'],
                'bar': ['baz\nfoo\nbar', 'foo', 'baz'],
                'baz': ['foo'],
            },
            body='foo bar baz')
        assert text == textwrap.dedent("""
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

            foo bar baz
        """).strip()


class TestWriteINI(unittest.TestCase):
    """Tests for the helper function `_write_ini()`."""

    def test(self):
        """Test with some sample data."""

        text = _write_ini({
            'foo': {'foo1': '1', 'foo2': '2', 'foo3': '3'},
            'bar': {'1': 'bar1', '2': 'bar2'},
            'baz': {},
        })
        assert text == textwrap.dedent("""
            [foo]
            foo1 = 1
            foo2 = 2
            foo3 = 3

            [bar]
            1 = bar1
            2 = bar2

            [baz]
        """).strip()


class TestMetadata(unittest.TestCase):
    pass


class TestConfig(unittest.TestCase):

    def test(self):
        """Test with a sample `pyproject.toml` configuration."""

        data = {
            'project': {'name': 'foo', 'version': '0.1.0'},
            'build-system': {'requires': ['bar', 'baz']},
            'tool': {
                'setuptools': {'packages': {'find': {'where': ['src']}}},
                'chakra': {
                    'env-dir': 'my-envs',
                    'dev-deps': {'docs': ['sphinx'], 'lint': ['mypy', 'flake8']},
                    'source': {'packages': ['foo']},
                },
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            pyproject_file = Path(temp_dir) / Path('pyproject.toml')

            with open(pyproject_file, 'wb') as f:
                tomli_w.dump(data, f)

            config = Config.load(pyproject_file)

        assert config.env_dir == Path('my-envs')

        assert config.dev_deps['docs'] == ['sphinx']
        assert config.dev_deps['lint'] == ['mypy', 'flake8']
        assert config.dev_deps['build'] == ['bar', 'baz']
