import enum
import functools
import os
import pathlib
import shlex
import shutil
import subprocess
import sys

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


class OpSystem(enum.Enum):
    WINDOWS = 'nt'
    LINUX = 'linux'
    MACOS = 'darwin'

    @classmethod
    @functools.cache
    def find(cls):
        # plat_os = platform OS, cand_os = candidate OS
        if os.name == 'posix':
            plat_os = Command(['uname', '-s']).run().stdout.lower()
        else:
            plat_os = os.name
        for cand_os in cls:
            if plat_os == cand_os.value:
                return cand_os
        raise NotSupportedError(f'unsupported operating system (or kernel) {plat_os!r}')


class Arch(enum.Enum):
    INTEL_AMD_32_BIT = ('x86', 'i386', 'i586', 'i686')
    INTEL_AMD_64_BIT = ('x86_64', 'amd64')
    ARM_64_BIT = ('arm64', 'aarch64')

    @classmethod
    @functools.cache
    def find(cls, opsys):
        # plat_ar = platform arch., cand_ar = candidate arch.
        if opsys == OpSystem.WINDOWS:
            plat_ar = os.environ['PROCESSOR_ARCHITECTURE'].lower()
        else:
            plat_ar = Command(['uname', '-m']).run().stdout
        for cand_ar in cls:
            if plat_ar in cand_ar.value:
                return cand_ar
        raise NotSupportedError(f'unsupported architecture {plat_ar!r}')


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
                raise NotSupportedError(f'unsupported hook extension {self.script.suffix}')
            super().__init__([self.interpreter, str(self.script)])

    def __repr__(self):
        return f'{self.__class__.__name__}(interpreter={self.interpreter!r}, script={self.script!r})'


class Environment(object):
    """A virtual environment."""

    def __init__(self, path, python='python'):
        self.path = pathlib.Path(path)
        self.python = pathlib.Path(shutil.which(python)).resolve()
        self.is_activated = False

    def __repr__(self):
        return (
            f'{self.__class__.__name__}({self.path!r}, python={self.python!r}, '
            f'is_activated={self.is_activated})'
        )

    @property
    def activate_script(self):
        if OpSystem.find() == OpSystem.WINDOWS:
            return self.path / 'Scripts' / 'activate_this.py'
        else:
            return self.path / 'bin' / 'activate_this.py'

    @property
    def python_executable(self):
        if OpSystem.find() == OpSystem.WINDOWS:
            return self.path / 'Scripts' / self.python.name
        else:
            return self.path / 'bin' / self.python.name

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
