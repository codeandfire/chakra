import os
import subprocess
import tempfile
from pathlib import Path


class Command:
    """A shell command."""

    def __init__(self, command, description=''):
        self._command = command
        self.description = description

    def __repr__(self):
        return (
            f'{self.__class__.__name__}({self._command!r}, '
            f'description={self.description!r})'
        )

    def __eq__(self, other):
        return self._command == other._command and self.description == other.description

    def run(self):
        return subprocess.run(self._command, shell=True, capture_output=True)


class DevDeps:
    """Development dependencies."""

    def __init__(self, **kwargs):
        self._deps = kwargs

    def __repr__(self):
        return f'{self.__class__.__name__}({self._deps!r})'

    def __getitem__(self, key):
        return self._deps[key]

    def requirements_txt(self):
        temp_file = tempfile.NamedTemporaryFile()
        with open(temp_file.name, 'w') as f:
            f.write(
                os.linesep.join(
                    [dep for dep_list in self._deps.values() for dep in dep_list]))
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

    def __repr__(self):
        return f'{self.__class__.__name__}({self.path})'

    @property
    def create_command(self):
        if self.path.exists():
            raise RuntimeError(f'{self.path} already exists!')
        return Command(f'virtualenv {self.path} --download --activators python')

    def activate(self):
        exec(open(self._activate_script).read(), {'__file__': str(self._activate_script)})
