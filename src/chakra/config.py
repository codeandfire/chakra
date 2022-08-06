try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from pathlib import Path

from .core import Environment, Metadata, Source


class Config(object):
    """Configuration from `pyproject.toml`."""

    def __init__(self, metadata, env_dir, dev_deps, source):
        self.metadata = metadata
        self.env_dir = env_dir
        self.dev_deps = dev_deps
        self.source = source

    @classmethod
    def load(cls, pyproject_file='pyproject.toml'):
        with open(pyproject_file, 'rb') as f:
            config = tomllib.load(f)

        metadata = Metadata(config)

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

        return Config(metadata, env_dir, dev_deps, source)

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(metadata={self.metadata!r}, '
            f'env_dir={self.env_dir!r}, dev_deps={self.dev_deps!r})'
        )
