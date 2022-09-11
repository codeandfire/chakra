import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from ._utils import NotSupportedError

def _subprocess_run(args, capture_output=True, env=None):
    """A simple wrapper around `subprocess.run()`.

    * This sets `shell=False` and `check=False` by default.
    * Transforms `FileNotFoundError`s occuring due to a command not being found into a
      regular `subprocess.CompletedProcess` result, with an error message and an exit code
      of 127.
    * Strips leading/trailing whitespace from stdout and stderr, if it is captured.
    """

    try:
        result = subprocess.run(
            args, shell=False, check=False, text=True, capture_output=capture_output,
            env=env)
    except FileNotFoundError as exc:
        err = f'command not found: {exc.filename}'
        if not capture_output:
            print(err, file=sys.stderr)
            stdout, stderr = None, None
        else:
            stdout, stderr = '', err
        result = subprocess.CompletedProcess(
            args=args, returncode=127, stdout=stdout, stderr=stderr)
    else:
        if capture_output:
            result.stdout, result.stderr = result.stdout.strip(), result.stderr.strip()

    return result


class Command(object):
    """A shell command."""

    def __init__(self, tokens, env_vars={}):
        self.tokens = tokens
        self.env_vars = env_vars

    def __repr__(self):
        return f'{self.__class__.__name__}(tokens={self.tokens!r}, env_vars={self.env_vars!r})'

    def __str__(self):
        return shlex.join(self.tokens)

    def __eq__(self, other):
        return self.tokens == other.tokens and self.env_vars == other.env_vars

    def run(self, capture_output=True):
        env_vars = self.env_vars.copy()
        env_vars['PATH'] = os.environ['PATH']    # pass the current PATH
        return _subprocess_run(self.tokens, capture_output=capture_output, env=env_vars)


class Hook(Command):
    """An executable script."""

    def __init__(self, script):
        self.script = script
        if self.script.suffix == '.ps1':
            self.interpreter = 'powershell'
            super().__init__([self.interpreter, '-File', str(self.script)])
        else:
            if self.script.suffix == '.py':
                self.interpreter = 'python'
            elif self.script.suffix == '' or self.script.suffix == '.sh':
                self.interpreter = 'bash'
            else:
                self._unsupported_ext(self.script.suffix)
            super().__init__([self.interpreter, str(self.script)])

    @staticmethod
    def _unsupported_ext(ext):
        raise NotSupportedError(
            f"unsupported hook extension {ext}: only Python (.py), Bash (no extension or "
            ".sh), and Powershell (.ps1) scripts are supported")

    def __repr__(self):
        return f'{self.__class__.__name__}(interpreter={self.interpreter!r}, script={self.script!r})'


class Environment(object):
    """A virtual environment."""

    def __init__(self, path, python='python'):
        self.path = Path(path)
        self.python = Path(shutil.which(python)).resolve()
        self.is_activated = False

    def __repr__(self):
        return (
            f'{self.__class__.__name__}({self.path!r}, python={self.python!r}, '
            f'is_activated={self.is_activated})'
        )

    @property
    def activate_script(self):
        if os.name == 'posix':
            return self.path / 'bin' / 'activate_this.py'
        else:
            return self.path / 'Scripts' / 'activate_this.py'

    @property
    def python_executable(self):
        if os.name == 'posix':
            return self.path / 'bin' / self.python.name
        else:
            return self.path / 'Scripts' / self.python.name

    @property
    def site_packages(self):
        return self.path / 'lib' / self.python.name / 'site-packages'

    @property
    def pyvenv_cfg(self):
        return self.path / 'pyvenv.cfg'

    def create(self, **kwargs):
        # not using `virtualenv.cli_run([...])` here, since `virtualenv` turns out to be a
        # time-consuming import and impacts chakra's startup time.
        Command([
            'virtualenv', str(self.path),
            '--download',
            '--activators', 'python',
            '--no-setuptools',
            '--no-wheel',
            '--prompt', self.path.name,
            '--python', str(self.python),
        ]).run(**kwargs)

    def activate(self):
        self.is_activated = True
        exec(open(self.activate_script).read(), {'__file__': str(self.activate_script)})

    def has_installed(self, package, ver=None):
        if (self.site_packages / package).exists() or (self.site_packages / f'{package}.py').exists():
            if ver is None:
                dist_info = self.site_packages.glob(f'{package}-*.dist-info')
                dist_info = list(dist_info)
                if len(dist_info) == 1:
                    return True
            else:
                dist_info = self.site_packages / f'{package}-{ver}.dist-info'
                if dist_info.exists():
                    return True
        return False

    def remove(self):
        shutil.rmtree(self.path)
