try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from pathlib import Path

from .core import DevDeps, Environment, Metadata, Source


class Config(object):
    """Configuration from `pyproject.toml`."""

    def __init__(self, config_file=Path('pyproject.toml')):
        with open(config_file, 'rb') as f:
            config = tomllib.load(f)

        self.metadata = Metadata(config)

        self.build_deps = DevDeps(build=config['build-system'].get('requires', []))

        config = config.get('tool', {}).get('chakra', {})

        self.env = Environment(Path(config.get('env', '.venv')))
        self.build_env = Environment(Path(config.get('build-env', '.build-venv')))
        self.dev_deps = DevDeps(**config.get('dev-deps', {}))

        source_config = config['source']
        self.source = Source(source_config['packages'])

        for glob in source_config.get('include', []):
            self.source.include(glob)
        for glob in source_config.get('exclude', []):
            self.source.exclude(glob)

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(metadata={self.metadata!r}, env={self.env!r}, '
            f'build_env={self.build_env!r}, dev_deps={self.dev_deps!r}, '
            f'build_deps={self.build_deps!r})'
        )
