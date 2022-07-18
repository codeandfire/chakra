import os
import sys
import tempfile
import unittest
from pathlib import Path

from chakra import Command, DevDeps, Environment


class TestCommand(unittest.TestCase):

    def test_echo(self):
        """Run an `echo` command."""

        result = Command('echo foo').run()
        assert result.returncode == 0
        assert result.stdout.decode('utf-8').strip() == 'foo'
        assert result.stderr.decode('utf-8').strip() == ''

    def test_error(self):
        """Run a command which gives an error."""

        result = Command('foo').run()
        assert result.returncode != 0
        assert result.stdout.decode('utf-8').strip() == ''
        assert result.stderr.decode('utf-8').strip() != ''

    def test_empty(self):
        """Run a command which is the empty string ``."""

        result = Command('').run()
        assert result.returncode == 0
        assert result.stdout.decode('utf-8').strip() == ''
        assert result.stderr.decode('utf-8').strip() == ''


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

            # pre-activation, none of the paths in `PYTHONPATH` (i.e. `sys.path`) should
            # have anything to do with the created environment.
            assert all([not Path(path).is_relative_to(env_path) for path in sys.path])

            env.activate()

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
            assert env.create_command == \
                Command('virtualenv .venv --download --activators python')

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
