try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from pathlib import Path

from .core import Environment, Metadata, Source


class Config(object):
    """Chakra-specific configuration from `pyproject.toml`."""

    def __init__(self, env_dir, dev_deps, source):
        self.env_dir = env_dir
        self.dev_deps = dev_deps
        self.source = source

    @classmethod
    def load(cls, pyproject_file='pyproject.toml'):
        with open(pyproject_file, 'rb') as f:
            config = tomllib.load(f)

        build_deps = config['build-system'].get('requires', [])

        config = config.get('tool', {}).get('chakra', {})

        env_dir = Path(config.get('env-dir', '.envs'))
        dev_deps = config.get('dev-deps', {})
        dev_deps['build'] = build_deps

        source_config = config['source']
        source = Source(source_config['packages'])

        for glob in source_config.get('include', []):
            source.include(glob)
        for glob in source_config.get('exclude', []):
            source.exclude(glob)

        return Config(env_dir, dev_deps, source)

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(env_dir={self.env_dir!r}, '
            f'dev_deps={self.dev_deps!r}, source={self.source!r})'
        )
