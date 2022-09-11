from configparser import ConfigParser
import functools
import io
from pathlib import Path

from chakra._utils import ini
from chakra._utils import rfc822
from chakra._utils import tomllib

from chakra.core import Environment


@functools.cache
def _read_pyproject(file='pyproject.toml'):
    """Small function to read and parse a `pyproject.toml` file.

    The result of this function is cached by the `functools.cache` decorator above. This
    prevents repetitive parsing of the contents of `pyproject.toml` by the `.load()`
    methods of the various classes below.
    """

    with open(file, 'rb') as f:
        return tomllib.load(f)


class EntryPoints(object):
    """Entry points metadata."""

    def __init__(self, scripts={}, gui_scripts={}, **kwargs):
        self._entry_points = {'console_scripts': scripts, 'gui_scripts': gui_scripts}
        for key, value in kwargs.items():
            self._entry_points[key] = value

    @classmethod
    def load(self, file='pyproject.toml'):
        config = _read_pyproject(file)
        config = config.get('project', {})

        scripts = config.get('scripts', {})
        gui_scripts = config.get('gui-scripts', {})
        entry_points = config.get('entry-points', {})

        return EntryPoints(scripts, gui_scripts, **entry_points)

    def __repr__(self):
        return f'{self.__class__.__name__}({self._entry_points!r})'

    def write(self):
        return ini.dumps(self._entry_points)


class Metadata(object):
    """Core metadata."""

    def __init__(self, metadata_version, name, version, summary, description,
                 description_content_type, requires_python, license_, author,
                 author_email, maintainer, maintainer_email, keywords, classifier,
                 project_url, requires_dist, provides_extra):

        # the following loop is just a shorter way of writing the following:
        # self.metadata_version = metadata_version
        # self.name = name
        # self.version = version
        # ...
        # and so on for all the arguments.

        for key, value in locals().items():

            # the `self` argument should not be assigned as an attribute of itself!
            if key == 'self':
                continue

            # the `license_` argument should be converted into the attribute name
            # `license` without the underscore.
            elif key == 'license_':
                key = 'license'

            setattr(self, key, value)

    @classmethod
    def load(cls, file='pyproject.toml'):
        config = _read_pyproject(file)
        config = config.get('project', {})

        metadata_version = '2.1'

        name = config.get('name', None)
        version = config.get('version', None)
        summary = config.get('description', None)

        description = config.get('readme', {})
        try:
            description = Path(description)

        except TypeError:
            try:
                description = Path(description['file']).read_text()
            except KeyError:
                try:
                    description = description['text']
                except KeyError:
                    description = None
                    description_content_type = None
            description_content_type = description['content-type']

        else:
            if description.suffix == '.rst':
                description_content_type = 'text/x-rst'
            elif description.suffix == '.md':
                description_content_type = 'text/markdown'
            elif description.suffix == '':
                description_content_type = 'text/plain'

            description = description.read_text()

        requires_python = config.get('requires-python', None)

        license_ = config.get('license', {})
        try:
            license_ = Path(license_['file']).read_text()
        except KeyError:
            try:
                license_ = license_['text']
            except KeyError:
                license_ = None

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

        author, author_email = names_and_emails(config.get('authors', []))
        maintainer, maintainer_email = \
            names_and_emails(config.get('maintainers', []))

        keywords = ','.join(config.get('keywords', []))
        classifier = config.get('classifiers', [])

        project_url = config.get('urls', {})
        project_url = [f'{name}, {url}' for name, url in project_url.items()]

        requires_dist = config.get('dependencies', [])

        provides_extra = []

        for name, dependencies in config.get('optional-dependencies', {}).items():
            provides_extra.append(name)

            for dep in dependencies:
                if ';' not in dep:
                    dep_str = f"{dep} ; extra == '{name}'"
                else:
                    dep_str = f"{dep} and extra == '{name}'"
                requires_dist.append(dep)

        return Metadata(metadata_version, name, version, summary, description,
                        description_content_type, requires_python, license_, author,
                        author_email, maintainer, maintainer_email, keywords, classifier,
                        project_url, requires_dist, provides_extra)

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

        return rfc822.dumps(headers, body=self.description)


class Config(object):
    """Chakra-specific configuration from `pyproject.toml`."""

    def __init__(self, env_dir, dev_deps):
        self.env_dir = env_dir
        self.dev_deps = dev_deps

    @classmethod
    def load(cls, file='pyproject.toml'):
        config = _read_pyproject(file)

        build_deps = config['build-system'].get('requires', [])

        config = config.get('tool', {}).get('chakra', {})

        env_dir = Path(config.get('env-dir', '.envs'))
        dev_deps = config.get('dev-deps', {})
        dev_deps['build'] = build_deps

        return Config(env_dir, dev_deps)

    def __repr__(self):
        return f'{self.__class__.__name__}(env_dir={self.env_dir!r}, dev_deps={self.dev_deps!r})'
