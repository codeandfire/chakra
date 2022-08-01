from pathlib import Path
from tempfile_patch import tempfile
import textwrap
import unittest

from chakra.config import Config


class TestConfig(unittest.TestCase):

    def test(self):
        """Test a sample `pyproject.toml` configuration."""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / Path('pyproject.toml')

            with open(config_file, 'w') as f:
                f.write(textwrap.dedent("""
                    [project]
                    name = "foo"
                    version = "0.1.0"

                    [build-system]
                    requires = ["bar", "baz"]

                    [tool.setuptools.packages.find]
                    where = ["src"]

                    [tool.chakra]
                    env = "env"

                    [tool.chakra.dev-deps]
                    docs = ["sphinx"]
                    lint = ["mypy", "flake8"]

                    [tool.chakra.source]
                    packages = ["foo"]
                    """
                ))

            config = Config(config_file)

        metadata_text = config.metadata.text()
        assert len(metadata_text.strip().split('\n')) == 3

        assert config.env.path == Path('env')
        assert config.build_env.path == Path('.build-venv')

        assert config.dev_deps['docs'] == ['sphinx']
        assert config.dev_deps['lint'] == ['mypy', 'flake8']

        assert config.build_deps['build'] == ['bar', 'baz']
