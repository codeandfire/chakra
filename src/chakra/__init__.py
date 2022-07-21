import shutil
from collections import namedtuple
import distutils
import os
import subprocess
from .tempfile_patch import tempfile
from pathlib import Path


class Command:
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


class DevDeps:
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


class BuildMatrix:
    """A build matrix."""

    def __init__(self, pythons=['py3'], platforms=['any'], abi_spec='none',
                 is_subset=False):
        self.pythons = pythons
        self.platforms = platforms
        self.abi_spec = abi_spec
        self.is_subset = is_subset

    def __iter__(self):
        builds = []

        Build = namedtuple('Build', fields=['python', 'platform', 'abi'])

        for python in self.pythons:
            for platform in self.platforms:
                abi = self.translate_abi_spec(self.abi_spec, python)
                python = shutil.which(python)

                builds.append(Build(python=python, platform=platform, abi=abi))

        return builds

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(pythons={self.pythons!r}, '
            f'platforms={self.platforms!r}, abi_spec={self.abi_spec!r}, '
            f'is_subset={self.is_subset!r})'
        )

    def __eq__(self, other):
        return repr(self) == repr(other)

    @staticmethod
    def translate_pytag(pytag):
        """Translate a PEP-425 Python tag to its corresponding executable."""

        implementation = pytag[:2]
        major_version = pytag[2]
        minor_version = pytag[3:]

        if implementation == 'py' or implementation == 'cp':
            implementation = 'python'
        elif implementation == 'pp':
            implementation = 'pypy'
        else:
            # not supported right now
            pass

        if minor_version == '':
            python = f'{implementation}{major_version}'
        else:
            python = f'{implementation}{major_version}.{minor_version}'

        return shutil.which(python)

    @staticmethod
    def translate_abi_spec(abi_spec, pytag):
        """Translate the ABI spec into an ABI tag for the given Python tag."""

        if abi_spec == 'none':
            abi_tag = 'none'
        elif abi_spec == 'stable':
            abi_tag = 'abi3'
        else:
            abi_tag = pytag
            if abi_spec['pydebug']:
                abi_tag += 'd'
            if abi_spec['pymalloc']:
                abi_tag += 'm'
            if abi_spec['wide-unicode']:
                abi_tag += 'u'

        return abi_tag

    def identify(self):
        """Identify the subset of builds that are possible on the current machine."""

        current_platform = distutils.util.get_platform()
        assert current_platform in self.platforms, (
            f'current platform {current_platform} does not match any platform in the '
            'build matrix!'
        )

        found_pythons = []

        for python in self.pythons:
            if self.translate_pytag(python) is not None:
                found_pythons.append(python)

        assert len(found_pythons) > 0, (
            'could not find a Python interpreter matching any of those specified in the '
            'build matrix!'
        )

        return BuildMatrix(
            platforms=[current_platform], pythons=found_pythons, abi_spec=self.abi_spec,
            is_subset=True,
        )
