try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from pathlib import Path

from .core import Environment, Metadata, Source


class Config(object):
    """Configuration from `pyproject.toml`."""

    def __init__(self, config_file=Path('pyproject.toml')):
        with open(config_file, 'rb') as f:
            config = tomllib.load(f)

        self.metadata = Metadata(config)

        build_deps = config['build-system'].get('requires', [])

        config = config.get('tool', {}).get('chakra', {})

        self.env_dir = Path(config.get('env-dir', '.envs'))
        self.dev_deps = config.get('dev-deps', {})
        self.dev_deps['build'] = build_deps

        source_config = config['source']
        self.source = Source(source_config['packages'])

        for glob in source_config.get('include', []):
            self.source.include(glob)
        for glob in source_config.get('exclude', []):
            self.source.exclude(glob)

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(metadata={self.metadata!r}, '
            f'env_dir={self.env_dir!r}, dev_deps={self.dev_deps!r})'
        )
