from copy import copy
import os
import subprocess
from .tempfile_patch import tempfile
from pathlib import Path


class Command(object):
    """A shell command."""

    def __init__(self, command, subcommand=None, positional_args=[], optional_args={},
                 flags=[], env_vars={}, description=''):
        self.command = command
        self.subcommand = subcommand
        self.positional_args = positional_args
        self.optional_args = optional_args
        self.flags = flags
        self.env_vars = env_vars
        self.description = description

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(command={self.command!r}, '
            f'subcommand={self.subcommand!r}, positional_args={self.positional_args!r}, '
            f'optional_args={self.optional_args!r}, flags={self.flags!r}, '
            f'env_vars={self.env_vars!r}, description={self.description!r})'
        )

    def __eq__(self, other):
        return repr(self) == repr(other)

    def run(self):
        for name, value in self.env_vars.items():
            os.environ[name] = value

        full_command = [self.command]
        if self.subcommand is not None:
            full_command += [self.subcommand]
        full_command += self.positional_args
        full_command += [
            item for key, value in self.optional_args.items() for item in (key, value)]
        full_command += self.flags

        return subprocess.run(full_command, check=True, capture_output=True, text=True)


class Hook(Command):
    """An executable script."""

    def __init__(self, script_path):
        self.script_path = script_path

        if self.script_path.suffix == '.ps1':
            self.interpreter = 'powershell'

            super().__init__(
                command=self.interpreter, optional_args={'-File': str(self.script_path)})

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

            super().__init__(
                command=self.interpreter, positional_args=[str(self.script_path)])

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(interpreter={self.interpreter!r}, '
            f'script_path={self.script_path!r})'
        )


class ParamCommand(object):
    """A parameterized shell command."""

    def __init__(self, *args, **kwargs):
        self._command = Command(*args, **kwargs)

    def run(self, **params):
        command = copy(self._command)

        command.positional_args = [
            arg.format(**params) for arg in command.positional_args]
        command.optional_args = {
            key: value.format(**params) for key, value in command.optional_args.items()}
        command.env_vars = {
            key: value.format(**params) for key, value in command.env_vars.items()}

        return command.run()


class DevDeps(object):
    """Development dependencies."""

    def __init__(self, **kwargs):
        self._deps = kwargs

    def __repr__(self):
        return f'{self.__class__.__name__}({self._deps!r})'

    def requirements_txt(self):
        temp_file = tempfile.NamedTemporaryFile()
        with open(temp_file.name, 'w') as f:
            f.write(
                '\n'.join([dep for dep_list in self._deps.values() for dep in dep_list]))
        return temp_file


class Environment(object):
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
        return f'{self.__class__.__name__}({self.path!r})'

    @property
    def create_command(self):
        if self.path.exists():
            raise RuntimeError(f'{self.path} already exists!')

        return Command('virtualenv', positional_args=[str(self.path)],
                       optional_args={'--activators': 'python'},
                       flags=['--download'])

    def activate(self):
        self.is_activated = True
        exec(open(self._activate_script).read(), {'__file__': str(self._activate_script)})
