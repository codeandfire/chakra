import os
import subprocess
import sys
from tempfile_patch import tempfile
import unittest
from pathlib import Path

import virtualenv

from chakra.core import Command, Environment, Hook


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

        result = Command(['echo', 'foo']).run(capture_output=True)
        assert result.returncode == 0
        assert result.stdout.strip() == 'foo'
        assert result.stderr.strip() == ''

    @unittest.skipIf(os.name == 'nt', 'on windows system')
    def test_ls(self):
        """Run an `ls -lh` command."""

        result = Command(['ls', '-l', '-h']).run(capture_output=True)

        assert result.returncode == 0

        # output of `ls -lh` will always have multiple lines.
        assert len(result.stdout.strip().split(os.linesep)) > 1

        assert result.stderr.strip() == ''

    @unittest.skipIf(os.name == 'nt', 'on windows system')
    def test_mkdir(self):
        """Run a `mkdir` command against an existing directory."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            Path('foo').mkdir()

            # `mkdir` against an existing directory will always throw an error.
            result = Command(['mkdir', 'foo']).run(capture_output=True)

        assert result.returncode != 0
        assert result.stdout.strip() == ''
        assert result.stderr.strip() != ''

    def test_python_c(self):
        """Run a `python -c` command."""

        result = Command(
            ['python', '-c', "print('Hello, world!')"]).run(capture_output=True)
        assert result.returncode == 0
        assert result.stdout.strip() == 'Hello, world!'
        assert result.stderr.strip() == ''

    def test_pip(self):
        """Run the command `pip install foo bar baz --find-links file:///foo/bar`."""

        result = Command(
            ['pip', 'install', 'foo', 'bar', 'baz', '--find-links',
             Path('/foo/bar').as_uri()],
        ).run(capture_output=True)

        assert result.returncode != 0
        assert 'Looking in links:' in result.stdout.strip()
        for line in result.stderr.strip().split(os.linesep):
            assert line.startswith('WARNING') or line.startswith('ERROR')

    def test_python_m(self):
        """Run a `python -m` command."""

        result = Command(
            ['python', '-m', 'unittest', 'discover', '-h']).run(capture_output=True)
        assert result.returncode == 0
        assert result.stdout.strip().startswith('usage: python -m unittest discover')
        assert result.stderr.strip() == ''

    def test_invalid(self):
        """Run an invalid command, i.e. a command that does not exist."""

        result = Command(['foo']).run(capture_output=True)
        assert result.returncode != 0
        assert result.stdout == ''
        assert result.stderr.strip() == 'command not found: foo'

    @unittest.skipIf(os.name == 'nt', 'on windows system')
    def test_env_vars_sh(self):
        """Verify that environment variables are accessible to the command."""

        command = Command(['/bin/sh', '-c', 'echo $FOO $BAR'],
                          env_vars={'FOO': 'bar', 'BAR': 'foo'})
        result = command.run(capture_output=True)
        assert result.stdout.strip() == 'bar foo'

    @unittest.skipUnless(os.name == 'nt', 'on non-windows system')
    def test_env_vars_powershell(self):
        """Verify that environment variables are accessible to the command."""

        command = Command(['powershell', '-Command', 'echo $env:Foo $env:Bar'],
                          env_vars={'Foo': 'bar', 'Bar': 'foo'})
        result = command.run(capture_output=True)
        assert result.stdout.strip() == 'bar\nfoo'


class TestHook(unittest.TestCase):

    def test_python(self):
        """Test a Python hook."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            with open('foo.py', 'w') as f:
                f.write("print('foo')")
            result = Hook(Path('foo.py')).run(capture_output=True)

        assert result.stdout.strip() == 'foo'

    @unittest.skipIf(os.name == 'nt', 'on windows system')
    def test_bash(self):
        """Test a Bash hook."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            with open('foo', 'w') as f:
                f.write("#!/bin/bash\n\necho 'foo'")
            result = Hook(Path('foo')).run(capture_output=True)

        assert result.stdout.strip() == 'foo'

    @unittest.skipIf(os.name == 'nt', 'on windows system')
    def test_bash_sh_extension(self):
        """Test a Bash hook with an `.sh` extension."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            with open('foo.sh', 'w') as f:
                f.write("#!/bin/bash\n\necho 'foo'")
            result = Hook(Path('foo.sh')).run(capture_output=True)

        assert result.stdout.strip() == 'foo'

    @unittest.skipUnless(os.name == 'nt', 'on non-windows system')
    def test_powershell(self):
        """Test a Powershell hook."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            with open('foo.ps1', 'w') as f:
                f.write("echo 'foo'")
            result = Hook(Path('foo.ps1')).run(capture_output=True)

        assert result.stdout.strip() == 'foo'

    def test_unsupported(self):
        """Test a hook with an unsupported extension."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            with open('foo.bat', 'w') as f:
                f.write('dir')

            with self.assertRaises(RuntimeError):
                Hook(Path('foo.bat')).run(capture_output=True)


class TestEnvironment(unittest.TestCase):

    def test_create(self):
        """Test creation of an environment."""

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / Path('.venv')
            env = Environment(env_path)
            env.create()

            assert env_path.exists()
            assert (env_path / Path('bin')).exists()
            assert (env_path / Path('lib')).exists()
            assert (env_path / Path('pyvenv.cfg')).exists()

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

    @unittest.expectedFailure
    def test_path_is_a_path(self):
        """The `path` parameter passed must be a `pathlib.Path` instance."""
        _ = Environment('.venv')

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


class TestCommandUnderEnvironment(unittest.TestCase):

    def test(self):
        """Test a command run under an environment."""

        command = Command(['pip', 'freeze'])

        result = command.run(capture_output=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / Path('.venv')
            env = Environment(Path(env_path))
            env.create_command.run(capture_output=True)
            env.activate()

            new_result = command.run(capture_output=True)

        assert result.stdout != new_result.stdout
