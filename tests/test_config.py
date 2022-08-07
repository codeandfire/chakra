from pathlib import Path
from tempfile_patch import tempfile
import textwrap
import unittest

from chakra.config import Config


class TestConfig(unittest.TestCase):

    def test(self):
        """Test with a sample `pyproject.toml` configuration."""

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

        assert config.env_dir == Path('my-envs')

        assert config.dev_deps['docs'] == ['sphinx']
        assert config.dev_deps['lint'] == ['mypy', 'flake8']
        assert config.dev_deps['build'] == ['bar', 'baz']
