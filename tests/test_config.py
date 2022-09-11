from pathlib import Path
import textwrap
import unittest

from chakra.config import Config
from chakra._utils import tempfile
from chakra._utils import tomllib


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
                },
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            pyproject_file = Path(temp_dir) / Path('pyproject.toml')

            with open(pyproject_file, 'wb') as f:
                tomllib.dump(data, f)

            config = Config.load(pyproject_file)

        assert config.env_dir == Path('my-envs')

        assert config.dev_deps['docs'] == ['sphinx']
        assert config.dev_deps['lint'] == ['mypy', 'flake8']
        assert config.dev_deps['build'] == ['bar', 'baz']
