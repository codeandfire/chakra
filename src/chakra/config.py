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

    def __init__(self, metadata_version, name, version, summary, description,
                 requires_python, license_, requires_dist):
        self.metadata_version = metadata_version
        self.name = name
        self.version = version
        self.summary = summary
        self.description = description
        self.requires_python = requires_python
        self.license = license_
        self.requires_dist = requires_dist

    @classmethod
    def load(cls, pyproject_file='pyproject.toml'):
        with open(pyproject_file, 'rb') as f:
            config = tomllib.load(f)

        config = config.get('project', {})

        metadata_version = '2.1'

        name = config.get('name', None)
        version = config.get('version', None)
        summary = config.get('description', None)

        description = config.get('readme', {})
        try:
            description = Path(description).read_text()
        except TypeError:
            try:
                description = Path(description['file']).read_text()
            except KeyError:
                try:
                    description = description['text']
                except KeyError:
                    description = None

        requires_python = config.get('requires-python', None)

        license_ = config.get('license', {})
        try:
            license_ = Path(license_['file']).read_text()
        except KeyError:
            try:
                license_ = license_['text']
            except KeyError:
                license_ = None

        requires_dist = config.get('dependencies', [])

        return Metadata(metadata_version, name, version, summary, description,
                        requires_python, license_, requires_dist)

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

    def __init__(self, config_file=Path('pyproject.toml')):
        with open(config_file, 'rb') as f:
            config = tomllib.load(f)

        self.metadata = Metadata.load()

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
