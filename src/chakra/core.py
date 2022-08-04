import glob
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from pyproject_metadata import StandardMetadata


def _subprocess_run(args, capture_output=False, env=None, **kwargs):
    """A simple wrapper around `subprocess.run()` with `shell=False` and `check=False`.

    This wrapper basically transforms any `FileNotFoundError` exception that may be raised
    due to the fact that the given command is not found, into a regular
    `subprocess.CompletedProcess` result.
    """

    try:
        return subprocess.run(
            args, shell=False, check=False, capture_output=capture_output, env=env,
            **kwargs)

    except FileNotFoundError as exc:

        # come up with an error message.
        # `exc.filename` contains the name of the command that was not found.
        err = f'command not found: {exc.filename}'

        if not capture_output:
            print(err, file=sys.stderr)
            stdout, stderr = None, None
        else:
            stdout, stderr = '', err

        # 127 is the exit code returned by the shell in the case of a command not found
        # error, on all platforms (Linux / Windows / MacOS).
        # hence the choice of this exit code.
        return subprocess.CompletedProcess(
            args=args, returncode=127, stdout=stdout, stderr=stderr)


class Command(object):
    """A shell command."""

    def __init__(self, tokens, env_vars={}):
        self.tokens = tokens
        self.env_vars = env_vars

    def __repr__(self):
        return \
            f'{self.__class__.__name__}(tokens={self.tokens!r}, env_vars={self.env_vars!r})'

    def __str__(self):
        return shlex.join(self.tokens)

    def __eq__(self, other):
        return self.tokens == other.tokens and self.env_vars == other.env_vars

    def run(self, capture_output=False):
        return _subprocess_run(
            self.tokens, capture_output=capture_output, env=self.env_vars, text=True)


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
        self.is_activated = False

    def __repr__(self):
        return \
            f'{self.__class__.__name__}({self.path!r}, is_activated={self.is_activated})'

    @property
    def _activate_script(self):
        if os.name == 'posix':
            return self.path / Path('bin') / Path('activate_this.py')
        else:
            return self.path / Path('Scripts') / Path('activate_this.py')

    @property
    def python_executable(self):
        if os.name == 'posix':
            return self.path / Path('bin') / Path('python')
        else:
            return self.path / Path('Scripts') / Path('python')

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
