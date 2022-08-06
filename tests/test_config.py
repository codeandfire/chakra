from pathlib import Path
from tempfile_patch import tempfile
import textwrap
import unittest

from chakra.config import Config, _write_rfc822


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


class TestMetadata(unittest.TestCase):
    pass


class TestConfig(unittest.TestCase):

    def test(self):
        """Test a sample `pyproject.toml` configuration."""

        with tempfile.TemporaryDirectory() as temp_dir:
            pyproject_file = Path(temp_dir) / Path('pyproject.toml')

            with open(pyproject_file, 'w') as f:
                f.write(textwrap.dedent("""
                    [project]
                    name = "foo"
                    version = "0.1.0"

                    [build-system]
                    requires = ["bar", "baz"]

                    [tool.setuptools.packages.find]
                    where = ["src"]

                    [tool.chakra]
                    env-dir = "my-envs"

                    [tool.chakra.dev-deps]
                    docs = ["sphinx"]
                    lint = ["mypy", "flake8"]

                    [tool.chakra.source]
                    packages = ["foo"]
                    """
                ))

            config = Config.load(pyproject_file)

        metadata_text = config.metadata.text()
        assert len(metadata_text.strip().split('\n')) == 3

        assert config.env_dir == Path('my-envs')

        assert config.dev_deps['docs'] == ['sphinx']
        assert config.dev_deps['lint'] == ['mypy', 'flake8']
        assert config.dev_deps['build'] == ['bar', 'baz']
