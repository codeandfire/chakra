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
            self.description = Path(self.description)

        except TypeError:
            try:
                self.description = Path(self.description['file']).read_text()
            except KeyError:
                try:
                    self.description = self.description['text']
                except KeyError:
                    self.description = None
                    self.description_content_type = None
            self.description_content_type = self.description['content-type']

        else:
            if self.description.suffix == '.rst':
                self.description_content_type = 'text/x-rst'
            elif self.description.suffix == '.md':
                self.description_content_type = 'text/markdown'
            elif self.description.suffix == '':
                self.description_content_type = 'text/plain'

            self.description = self.description.read_text()

        self.requires_python = config.get('requires-python', None)

        self.license = config.get('license', {})
        try:
            self.license = Path(self.license['file']).read_text()
        except KeyError:
            try:
                self.license = self.license['text']
            except KeyError:
                self.license = None

        def names_and_emails(persons):
            emails = [
                '{name} <{email}>'.format(name=person['name'], email=person['email'])
                for person in persons
                if 'name' in person.keys() and 'email' in person.keys()
            ]
            emails += [
                person['email']
                for person in persons
                if 'name' not in person.keys() and 'email' in person.keys()
            ]
            names = [
                person['name']
                for person in persons
                if 'name' in person.keys() and 'email' not in person.keys()
            ]
            return (','.join(names), ','.join(emails))

        self.author, self.author_email = names_and_emails(config.get('authors', []))
        self.maintainer, self.maintainer_email = \
            names_and_emails(config.get('maintainers', []))

        self.keywords = ','.join(config.get('keywords', []))
        self.classifier = config.get('classifiers', [])

        self.project_url = config.get('urls', {})
        self.project_url = [f'{name}, {url}' for name, url in self.project_url.items()]

        self.requires_dist = config.get('dependencies', [])

        self.provides_extra = []

        for name, dependencies in config.get('optional-dependencies', {}).items():
            self.provides_extra.append(name)

            for dep in dependencies:
                if ';' not in dep:
                    dep_str = f"{dep} ; extra == '{name}'"
                else:
                    dep_str = f"{dep} and extra == '{name}'"
                self.requires_dist.append(dep)

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(metadata_version={self.metadata_version!r}, '
            f'name={self.name!r}, version={self.version!r}, summary={self.summary!r}, '
            f'description={self.description!r}, '
            f'description_content_type={self.description_content_type!r}, '
            f'requires_python={self.requires_python!r}, license={self.license!r}, '
            f'author={self.author!r}, author_email={self.author_email!r}, '
            f'maintainer={self.maintainer!r}, maintainer_email={self.maintainer_email!r}, '
            f'keywords={self.keywords!r}, classifier={self.classifier!r}, '
            f'project_url={self.project_url!r}, requires_dist={self.requires_dist!r}, '
            f'provides_extra={self.provides_extra!r})'
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
