import glob
import os
import shutil
import subprocess
from pathlib import Path

from pyproject_metadata import StandardMetadata


class Command(object):
    """A shell command."""

    def __init__(self, tokens, env_vars={}, description=''):
        self.tokens = tokens
        self.env_vars = env_vars
        self.description = description

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(tokens={self.tokens!r}, '
            f'env_vars={self.env_vars!r}, description={self.description!r})'
        )

    def __eq__(self, other):
        return repr(self) == repr(other)

    def run(self):
        for name, value in self.env_vars.items():
            os.environ[name] = value
        return subprocess.run(self.tokens, check=True, capture_output=True, text=True)


class Hook(Command):
    """An executable script."""

    def __init__(self, script_path):
        self.script_path = script_path

        if self.script_path.suffix == '.ps1':
            self.interpreter = 'powershell'

            super().__init__([self.interpreter, '-File', str(self.script_path)])

        else:
            if self.script_path.suffix == '.py':
                self.interpreter = 'python'
            elif self.script_path.suffix == '' or self.script_path.suffix == '.sh':
                self.interpreter = 'bash'
            else:
                raise RuntimeError(
                    f"unsupported extension '{self.script_path.suffix}': "
                    "only Python ('.py' extension), Bash (no extension or '.sh' "
                    "extension) and Powershell ('.ps1' extension) scripts are supported."
                )

            super().__init__([self.interpreter, str(self.script_path)])

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(interpreter={self.interpreter!r}, '
            f'script_path={self.script_path!r})'
        )


class Environment(object):
    """A virtual environment."""

    def __init__(self, path):
        assert isinstance(path, Path), 'path must be a pathlib.Path object'
        self.path = path

        if os.name == 'posix':
            self._bin = self.path / Path('bin')
        else:
            self._bin = self.path / Path('Scripts')

        self._activate_script = self._bin / Path('activate_this.py')
        self.python_executable = self._bin / Path('python')

        self.is_activated = False

    def __repr__(self):
        return f'{self.__class__.__name__}({self.path!r})'

    @property
    def create_command(self):
        return Command(
            ['virtualenv', str(self.path), '--activators', 'python', '--download'])

    def activate(self):
        self.is_activated = True
        exec(open(self._activate_script).read(), {'__file__': str(self._activate_script)})

    def remove(self):
        shutil.rmtree(self.path)


class Metadata(object):
    """Project metadata from `pyproject.toml`.

    This is a very thin wrapper around `pyproject_metadata.StandardMetadata`.
    """

    def __init__(self, pyproject_config):
        self._metadata = StandardMetadata.from_pyproject(pyproject_config)

    def __repr__(self):
        return self._metadata.__repr__().replace(
            self._metadata.__class__.__name__, self.__class__.__name__)

    def __getattr__(self, attr):
        return getattr(self._metadata, attr)

    def text(self):
        return str(self._metadata.as_rfc822())


class Source(object):
    """Globs representing the distribution source."""

    def __init__(self, packages):
        self._globs = ['pyproject.toml']

        for package in packages:
            self._globs.append(f'src/{package}/**/*.py')
            self._globs.append(f'{package}/**/*.py')

        self._exclude_globs = []

    def __repr__(self):
        return \
            f'{self.__class__.__name__}({self._globs!r}, exclude={self._exclude_globs!r})'

    def __contains__(self, item):
        return (item in self._globs) and (item not in self._exclude_globs)

    def include(self, glob):
        self._globs.append(glob)

    def exclude(self, glob):
        self._exclude_globs.append(glob)

    def expand(self):
        files = []
        for pattern in self._globs:
            files.extend(glob.glob(pattern, recursive=True))

        exclude_files = []
        for pattern in self._exclude_globs:
            exclude_files.extend(glob.glob(pattern, recursive=True))

        files = [file for file in files if file not in exclude_files]
        return files
