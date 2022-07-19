import os
import subprocess
import sys
import unittest
from pathlib import Path

from chakra import Command, DevDeps, Environment

# load a patched version of `tempfile`.
from tempfile_patch import tempfile


class TestCommand(unittest.TestCase):

    @unittest.skipIf(os.name == 'nt', 'on windows system')
    def test_echo(self):
        """Run an `echo` command."""

        result = Command('echo', positional_args=['foo']).run()
        assert result.returncode == 0
        assert result.stdout.strip() == 'foo'
        assert result.stderr.strip() == ''

    @unittest.skipIf(os.name == 'nt', 'on windows system')
    def test_ls(self):
        """Run an `ls -lh` command."""

        result = Command('ls', flags=['-l', '-h']).run()

        assert result.returncode == 0

        # output of `ls -lh` will always have multiple lines.
        assert len(result.stdout.strip().split(os.linesep)) > 1

        assert result.stderr.strip() == ''

    def test_mkdir(self):
        """Run a `mkdir` command against an existing directory."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            Path('foo').mkdir()

            # `mkdir` against an existing directory will always throw an error.
            with self.assertRaises(subprocess.CalledProcessError) as exc:
                Command('mkdir', positional_args=['foo']).run()

        exc = exc.exception
        assert exc.returncode != 0
        assert exc.stdout.strip() == ''
        assert exc.stderr.strip() != ''

    def test_python_c(self):
        """Run a `python -c` command."""

        result = Command('python', optional_args={'-c': "print('Hello, world!')"}).run()
        assert result.returncode == 0
        assert result.stdout.strip() == 'Hello, world!'
        assert result.stderr.strip() == ''

    def test_pip(self):
        """Run the command `pip install foo bar baz --find-links file:///foo/bar --progress-bar off --isolated --no-color`."""

        with self.assertRaises(subprocess.CalledProcessError) as exc:
            command = Command(
                'pip',
                subcommand='install',
                positional_args=['foo', 'bar', 'baz'],
                optional_args={
                    '--find-links': Path('/foo/bar').as_uri(),
                    '--progress-bar': 'off',
                },
                flags=['--isolated', '--no-color'],
            )
            command.run()

        exc = exc.exception
        assert exc.returncode != 0
        assert exc.stdout.strip().startswith('Looking in links:')
        for line in exc.stderr.strip().split(os.linesep):
            assert line.startswith('WARNING') or line.startswith('ERROR')

    # NOTE: this test is currently failing. Shows how we are not able to support `python
    # -m` commands yet.
    @unittest.skip('currently not working')
    def test_python_m(self):
        """Run a `python -m` command."""

        result = Command('python', optional_args={'-m': 'unittest discover -h'}).run()
        assert result.returncode == 0
        assert result.stdout.strip().startswith('usage: python -m unittest discover')
        assert result.stderr.strip() == ''

    def test_invalid(self):
        """Run an invalid command, i.e. a command that does not exist."""

        with self.assertRaises(FileNotFoundError):
            Command('foo').run()

    @unittest.skipIf(os.name == 'nt', 'on windows system')
    def test_env_vars_sh(self):
        """Verify that environment variables are accessible to the command."""

        command = Command('/bin/sh', optional_args={'-c': 'echo $FOO $BAR'},
                          env_vars={'FOO': 'bar', 'BAR': 'foo'})
        result = command.run()
        assert result.stdout.strip() == 'bar foo'

    @unittest.skipUnless(os.name == 'nt', 'on non-windows system')
    def test_env_vars_powershell(self):
        """Verify that environment variables are accessible to the command."""

        command = Command('pwsh', optional_args={'-Command': 'echo $env:Foo $env:Bar'},
                          env_vars={'Foo': 'bar', 'Bar': 'foo'})
        result = command.run()
        assert result.stdout.strip() == 'bar foo'


class TestDevDeps(unittest.TestCase):

    def test_sample(self):
        """A sample set of development dependencies."""

        dev_deps = DevDeps(
            docs=['sphinx'], checks=['mypy', 'flake8', 'black'], tests=['pytest'])

        with dev_deps.requirements_txt() as requirements_txt:
            with open(requirements_txt.name, 'r') as f:
                contents = [line.strip() for line in f.readlines()]

        assert contents == ['sphinx', 'mypy', 'flake8', 'black', 'pytest']

    def test_empty(self):
        """No development dependencies."""

        dev_deps = DevDeps()

        with dev_deps.requirements_txt() as requirements_txt:
            with open(requirements_txt.name, 'r') as f:
                assert f.read() == ''


class TestEnvironment(unittest.TestCase):

    def test_create_and_activate(self):
        """Test if creation and activation of an environment works.

        This test takes a little time because of the time spent in creating the
        environment.
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / Path('.venv')
            env = Environment(env_path)

            env.create_command.run()
            assert not env.is_activated

            # pre-activation, none of the paths in `PYTHONPATH` (i.e. `sys.path`) should
            # have anything to do with the created environment.
            assert all([not Path(path).is_relative_to(env_path) for path in sys.path])

            env.activate()
            assert env.is_activated

            # post-activation, at least one of the paths in `PYTHONPATH` (i.e. `sys.path`)
            # should refer to the created environment.
            assert any([Path(path).is_relative_to(env_path) for path in sys.path])

    def test_create_command(self):
        """Test the command used to create the environment.

        While the test above just tests if the environment is created (and activated),
        this test checks the actual command used for creating the environment, i.e. flags
        and arguments passed to the `virtualenv` command are also checked. Therefore this
        test is relevant.
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            # Why is a temporary directory, and cd'ing into it required here? Because the
            # presence of a .venv directory within the directory from which these tests
            # are being run can interfere with this test.

            env = Environment(Path('.venv'))
            assert env.create_command == Command('virtualenv', positional_args=['.venv'],
                                                 optional_args={'--activators': 'python'},
                                                 flags=['--download'])

    @unittest.expectedFailure
    def test_path_is_a_path(self):
        """The `path` parameter passed must be a `pathlib.Path` instance."""
        _ = Environment('.venv')

    def test_create_on_path_exists(self):
        """Trying to create an environment at an existing path."""

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / Path('.venv')
            env_path.mkdir()

            with self.assertRaises(RuntimeError):
                Environment(env_path).create_command.run()
