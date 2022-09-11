import os
import subprocess
import sys
import unittest
from pathlib import Path

import virtualenv

from chakra.core import Command, Environment, Hook
from chakra._utils import tempfile


def make_directories(structure, at=Path('.')):
    """Create a directory structure.

    For documentation on how this works, please refer: tests/make_directories.md
    """

    if isinstance(structure, tuple):
        dir_name = structure[0]
        dir_path = at / Path(dir_name)
        dir_path.mkdir()
        make_directories(structure[1], at=dir_path)

    elif isinstance(structure, list):
        for s in structure:
            make_directories(s, at=at)

    # it must be a string, i.e. a file name.
    else:
        (at / Path(structure)).touch()


class TestCommand(unittest.TestCase):

    @unittest.skipIf(os.name == 'nt', 'on windows system')
    def test_echo(self):
        """Run an `echo` command."""

        result = Command(['echo', 'foo']).run()
        assert result.returncode == 0
        assert result.stdout == 'foo'
        assert result.stderr == ''

    @unittest.skipIf(os.name == 'nt', 'on windows system')
    def test_ls(self):
        """Run an `ls -lh` command."""

        result = Command(['ls', '-l', '-h']).run()

        assert result.returncode == 0

        # output of `ls -lh` will always have multiple lines.
        assert len(result.stdout.split(os.linesep)) > 1

        assert result.stderr == ''

    @unittest.skipIf(os.name == 'nt', 'on windows system')
    def test_mkdir(self):
        """Run a `mkdir` command against an existing directory."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            Path('foo').mkdir()

            # `mkdir` against an existing directory will always throw an error.
            result = Command(['mkdir', 'foo']).run()

        assert result.returncode != 0
        assert result.stdout == ''
        assert result.stderr != ''

    def test_python_c(self):
        """Run a `python -c` command."""

        result = Command(
            ['python', '-c', "print('Hello, world!')"]).run()
        assert result.returncode == 0
        assert result.stdout == 'Hello, world!'
        assert result.stderr == ''

    def test_pip(self):
        """Run the command `pip install foo bar baz --find-links file:///foo/bar`."""

        result = Command(
            ['pip', 'install', 'foo', 'bar', 'baz', '--find-links',
             Path('/foo/bar').as_uri()],
        ).run()

        assert result.returncode != 0
        assert 'Looking in links:' in result.stdout
        for line in result.stderr.split(os.linesep):
            assert line.startswith('WARNING') or line.startswith('ERROR')

    def test_python_m(self):
        """Run a `python -m` command."""

        result = Command(
            ['python', '-m', 'unittest', 'discover', '-h']).run()
        assert result.returncode == 0
        assert result.stdout.startswith('usage: python -m unittest discover')
        assert result.stderr == ''

    def test_invalid(self):
        """Run an invalid command, i.e. a command that does not exist."""

        result = Command(['foo']).run()
        assert result.returncode != 0
        assert result.stdout == ''
        assert result.stderr == 'command not found: foo'

    @unittest.skipIf(os.name == 'nt', 'on windows system')
    def test_env_vars_sh(self):
        """Verify that environment variables are accessible to the command."""

        command = Command(['/bin/sh', '-c', 'echo $FOO $BAR'],
                          env_vars={'FOO': 'bar', 'BAR': 'foo'})
        result = command.run()
        assert result.stdout == 'bar foo'

    @unittest.skipUnless(os.name == 'nt', 'on non-windows system')
    def test_env_vars_powershell(self):
        """Verify that environment variables are accessible to the command."""

        command = Command(['powershell', '-Command', 'echo $env:Foo $env:Bar'],
                          env_vars={'Foo': 'bar', 'Bar': 'foo'})
        result = command.run()
        assert result.stdout == 'bar\nfoo'


class TestHook(unittest.TestCase):

    def test_python(self):
        """Test a Python hook."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            with open('foo.py', 'w') as f:
                f.write("print('foo')")
            result = Hook(Path('foo.py')).run()

        assert result.stdout == 'foo'

    @unittest.skipIf(os.name == 'nt', 'on windows system')
    def test_bash(self):
        """Test a Bash hook."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            with open('foo', 'w') as f:
                f.write("#!/bin/bash\n\necho 'foo'")
            result = Hook(Path('foo')).run()

        assert result.stdout == 'foo'

    @unittest.skipIf(os.name == 'nt', 'on windows system')
    def test_bash_sh_extension(self):
        """Test a Bash hook with an `.sh` extension."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            with open('foo.sh', 'w') as f:
                f.write("#!/bin/bash\n\necho 'foo'")
            result = Hook(Path('foo.sh')).run()

        assert result.stdout == 'foo'

    @unittest.skipUnless(os.name == 'nt', 'on non-windows system')
    def test_powershell(self):
        """Test a Powershell hook."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            with open('foo.ps1', 'w') as f:
                f.write("echo 'foo'")
            result = Hook(Path('foo.ps1')).run()

        assert result.stdout == 'foo'

    def test_unsupported(self):
        """Test a hook with an unsupported extension."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            with open('foo.bat', 'w') as f:
                f.write('dir')

            with self.assertRaises(RuntimeError):
                Hook(Path('foo.bat')).run()


class TestEnvironment(unittest.TestCase):

    def test_create(self):
        """Test creation of an environment."""

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / Path('.venv')
            env = Environment(env_path)
            env.create()

            assert env_path.exists()
            assert env.activate_script.exists()
            assert env.python_executable.exists()
            assert env.site_packages.exists()
            assert env.pyvenv_cfg.exists()

    def test_activate(self):
        """Test if activation of an environment works.

        This test works by checking the value of `PATH` before and after activating the
        environment. After activating the environment, `PATH` should contain some
        directories that are relative to the directory of the environment.
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            # create an environment by directly accessing the `virtualenv` module's API.
            env_path = Path(temp_dir) / Path('.venv')
            virtualenv.cli_run([str(env_path)])

            env = Environment(env_path)

            env.create()
            assert not env.is_activated

            # pre-activation, none of the paths in `PATH` (i.e. `sys.path`) should
            # have anything to do with the created environment.
            assert all([not Path(path).is_relative_to(env_path) for path in sys.path])

            env.activate()
            assert env.is_activated

            # post-activation, at least one of the paths in `PATH` (i.e. `sys.path`)
            # should refer to the created environment.
            assert any([Path(path).is_relative_to(env_path) for path in sys.path])

    def test_setuptools_wheel_not_installed(self):
        """Test that `setuptools` and `wheel` are not installed in the environment.

        The packages `setuptools` and `wheel` are not required by Chakra; if required by
        other packages as build-time dependencies, they can be installed at that time. Not
        including these two packages may save some time while creating the environment.
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / Path('.venv')
            env = Environment(env_path)
            env.create()

            assert not env.has_installed('setuptools')
            assert not env.has_installed('wheel')

    def test_pip_installed(self):
        """Test that `pip` is installed in the environment."""

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / Path('.venv')
            env = Environment(env_path)
            env.create()

            assert env.has_installed('pip')

    def test_pip_latest_version(self):
        """The environment should come with the latest version of Pip."""

        version_cmd = Command(['pip', '--version'])
        upgrade_cmd = Command(['pip', 'install', '--upgrade', 'pip'])

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / Path('.venv')
            env = Environment(env_path)
            env.create()
            env.activate()

            version = version_cmd.run().stdout
            upgrade_cmd.run()
            new_version = version_cmd.run().stdout

        assert version == new_version

    def test_package_installs(self):
        """Test that package installs work in the environment."""

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / Path('.venv')
            env = Environment(env_path)
            env.create()
            env.activate()

            Command(
                ['pip', 'install', 'tabulate==0.8.4', 'build==0.4.0']
            ).run()

            assert env.has_installed('tabulate', '0.8.4')
            assert env.has_installed('build', '0.4.0')

    def test_package_imports(self):
        """Test that packages can be imported within the environment."""

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / Path('.venv')
            env = Environment(env_path)
            env.create()
            env.activate()

            Command(['pip', 'install', 'tabulate']).run()

            result = Command(['python', '-c', '"import tabulate"']).run()

        assert result.stdout == ''
        assert result.stderr == ''

    def test_console_scripts(self):
        """Test that console scripts work in the environment."""

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / Path('.venv')
            env = Environment(env_path)
            env.create()
            env.activate()

            Command(['pip', 'install', 'build']).run()

            result = Command(['pyproject-build', '-h']).run()

        assert result.stdout != ''
        assert result.stderr == ''
