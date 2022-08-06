try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from pathlib import Path

from .core import Environment, Source


def _write_rfc822(headers, body=None):
    """Write an RFC 822 message with headers and a body."""

    text = []

    for name, entries in headers.items():
        for entry in entries:
            lines = entry.strip().split('\n')
            text.append(f'{name}: {lines[0]}')
            for line in lines[1:]:
                text.append(f'        {line}')

    if body is not None:
        text.append(body)

    return '\n'.join(text)


class Metadata(object):
    """Core metadata."""

    def __init__(self, config_file=Path('pyproject.toml')):
        with open(config_file, 'rb') as f:
            config = tomllib.load(f)

        config = config.get('project', {})

        self.metadata_version = '2.1'

        self.name = config.get('name', None)
        self.version = config.get('version', None)
        self.summary = config.get('description', None)

        self.description = config.get('readme', {})
        try:
            self.description = Path(self.description).read_text()
        except TypeError:
            try:
                self.description = Path(self.description['file']).read_text()
            except KeyError:
                try:
                    self.description = self.description['text']
                except KeyError:
                    self.description = None

        self.requires_python = config.get('requires-python', None)

        self.license = config.get('license', {})
        try:
            self.license = Path(self.license['file']).read_text()
        except KeyError:
            try:
                self.license = self.license['text']
            except KeyError:
                self.license = None

        self.requires_dist = config.get('dependencies', [])

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(metadata_version={self.metadata_version!r}, '
            f'name={self.name!r}, version={self.version!r}, summary={self.summary!r}, '
            f'description={self.description!r}, requires_python={self.requires_python!r}, '
            f'license={self.license!r}, requires_dist={self.requires_dist!r})'
        )

    def write(self):
        headers = {}

        for attr, value in vars(self).items():
            if attr == 'description':
                # description won't go in the headers.
                continue

            if not isinstance(value, list):
                # wrap up single entries in a list.
                value = [value]

            headers[attr.replace('_', '-').title()] = value

        return _write_rfc822(headers, body=self.description)


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
