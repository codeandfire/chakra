import os
import subprocess
import tempfile
from pathlib import Path


class Command:
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


class DevDeps:
    """Development dependencies."""

    def __init__(self, docs=[], checks=[], tests=[]):
        self.docs = docs
        self.checks = checks
        self.tests = tests

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(docs={self.docs!r}, checks={self.checks!r}, '
            f'tests={self.tests!r}'
        )

    def requirements_txt(self):
        temp_file = tempfile.NamedTemporaryFile()
        with open(temp_file.name, 'w') as f:
            f.write(os.linesep.join(self.docs + self.checks + self.tests))
        return temp_file


class Environment:
    """A virtual environment."""

    def __init__(self, path):
        assert isinstance(path, Path), 'path must be a pathlib.Path object'
        self.path = path

        if os.name == 'posix':
            self._activate_script = self.path / Path('bin') / Path('activate_this.py')
        else:
            self._activate_script = self.path / Path('Scripts') / Path('activate_this.py')

        self.is_activated = False

    def __repr__(self):
        return f'{self.__class__.__name__}({self.path})'

    @property
    def create_command(self):
        if self.path.exists():
            raise RuntimeError(f'{self.path} already exists!')

        return Command(
            ['virtualenv', str(self.path), '--activators', 'python', '--download'])

    def activate(self):
        self.is_activated = True
        exec(open(self._activate_script).read(), {'__file__': str(self._activate_script)})
