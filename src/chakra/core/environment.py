import pathlib
import shutil

from .command import Command
from .platform import OpSystem

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
