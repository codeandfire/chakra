import os
import pathlib
import subprocess
import sys
import unittest

import virtualenv

from chakra.core import Command, Environment, Hook, OpSystem
from chakra.errors import NotSupportedError
from chakra.utils import tempfile


class TestCommand(unittest.TestCase):

    @unittest.skipIf(OpSystem.find() == OpSystem.WINDOWS, 'on windows system')
    def test_echo(self):
        result = Command(['echo', 'foo']).run()
        assert result.returncode == 0
        assert result.stdout == 'foo'
        assert result.stderr == ''

    @unittest.skipIf(OpSystem.find() == OpSystem.WINDOWS, 'on windows system')
    def test_ls(self):
        result = Command(['ls', '-l', '-h']).run()
        assert result.returncode == 0
        # output of `ls -lh` will always have multiple lines.
        assert len(result.stdout.split(os.linesep)) > 1
        assert result.stderr == ''

    @unittest.skipIf(OpSystem.find() == OpSystem.WINDOWS, 'on windows system')
    def test_mkdir(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            pathlib.Path('foo').mkdir()

            # `mkdir` against an existing directory will always throw an error.
            result = Command(['mkdir', 'foo']).run()

        assert result.returncode != 0
        assert result.stdout == ''
        assert result.stderr != ''

    def test_python_c(self):
        result = Command(
            ['python', '-c', "print('Hello, world!')"]).run()
        assert result.returncode == 0
        assert result.stdout == 'Hello, world!'
        assert result.stderr == ''

    def test_pip(self):
        result = Command(
            ['pip', 'install', 'foo', 'bar', 'baz', '--find-links',
             pathlib.Path('/foo/bar').as_uri()],
        ).run()
        assert result.returncode != 0
        assert 'Looking in links:' in result.stdout
        for line in result.stderr.split(os.linesep):
            assert line.startswith('WARNING') or line.startswith('ERROR')

    def test_python_m(self):
        result = Command(
            ['python', '-m', 'unittest', 'discover', '-h']).run()
        assert result.returncode == 0
        assert result.stdout.startswith('usage: python -m unittest discover')
        assert result.stderr == ''

    def test_invalid(self):
        result = Command(['foo']).run()
        assert result.returncode != 0
        assert result.stdout == ''
        assert result.stderr == 'command not found: foo'

    @unittest.skipIf(OpSystem.find() == OpSystem.WINDOWS, 'on windows system')
    def test_env_vars_sh(self):
        command = Command(['/bin/sh', '-c', 'echo $FOO $BAR'],
                          env_vars={'FOO': 'bar', 'BAR': 'foo'})
        result = command.run()
        assert result.stdout == 'bar foo'

    @unittest.skipUnless(OpSystem.find() == OpSystem.WINDOWS, 'on non-windows system')
    def test_env_vars_powershell(self):
        command = Command(['powershell', '-Command', 'echo $env:Foo $env:Bar'],
                          env_vars={'Foo': 'bar', 'Bar': 'foo'})
        result = command.run()
        assert result.stdout == 'bar\nfoo'


class TestHook(unittest.TestCase):

    def test_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            with open('foo.py', 'w') as f:
                f.write("print('foo')")
            result = Hook(pathlib.Path('foo.py')).run()
        assert result.stdout == 'foo'

    @unittest.skipIf(OpSystem.find() == OpSystem.WINDOWS, 'on windows system')
    def test_bash(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            with open('foo', 'w') as f:
                f.write("#!/bin/bash\n\necho 'foo'")
            result = Hook(pathlib.Path('foo')).run()

        assert result.stdout == 'foo'

    @unittest.skipIf(OpSystem.find() == OpSystem.WINDOWS, 'on windows system')
    def test_bash_sh_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            with open('foo.sh', 'w') as f:
                f.write("#!/bin/bash\n\necho 'foo'")
            result = Hook(pathlib.Path('foo.sh')).run()
        assert result.stdout == 'foo'

    @unittest.skipUnless(OpSystem.find() == OpSystem.WINDOWS, 'on non-windows system')
    def test_powershell(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            with open('foo.ps1', 'w') as f:
                f.write("echo 'foo'")
            result = Hook(pathlib.Path('foo.ps1')).run()
        assert result.stdout == 'foo'

    def test_unsupported(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            with open('foo.bat', 'w') as f:
                f.write('dir')
            with self.assertRaises(NotSupportedError):
                Hook(pathlib.Path('foo.bat')).run()


class TestEnvironment(unittest.TestCase):

    def test_create(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = pathlib.Path(tmp) / '.venv'
            env = Environment(env_path)
            env.create()
            assert env_path.exists()
            assert env.activate_script.exists()
            assert env.python_executable.exists()
            assert env.site_packages.exists()
            assert env.pyvenv_cfg.exists()

    def test_activate(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = pathlib.Path(tmp) / '.venv'
            virtualenv.cli_run([str(env_path)])
            env = Environment(env_path)
            env.create()
            assert not env.is_activated
            # no path in `sys.path` should have anything to do with `env_path`
            assert all([not pathlib.Path(path).is_relative_to(env_path) for path in sys.path])

            env.activate()
            assert env.is_activated
            # at least one path in `sys.path` should be relative to `env_path`
            assert any([pathlib.Path(path).is_relative_to(env_path) for path in sys.path])

    def test_setuptools_wheel_not_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = pathlib.Path(tmp) / '.venv'
            env = Environment(env_path)
            env.create()
            assert not env.has_installed('setuptools')
            assert not env.has_installed('wheel')

    def test_pip_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = pathlib.Path(tmp) / '.venv'
            env = Environment(env_path)
            env.create()
            assert env.has_installed('pip')

    def test_pip_latest_version(self):
        version_cmd = Command(['pip', '--version'])
        upgrade_cmd = Command(['pip', 'install', '--upgrade', 'pip'])

        with tempfile.TemporaryDirectory() as tmp:
            env_path = pathlib.Path(tmp) / '.venv'
            env = Environment(env_path)
            env.create()
            env.activate()
            version = version_cmd.run().stdout
            upgrade_cmd.run()
            new_version = version_cmd.run().stdout

        assert version == new_version

    def test_package_installs(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = pathlib.Path(tmp) / '.venv'
            env = Environment(env_path)
            env.create()
            env.activate()
            Command(
                ['pip', 'install', 'tabulate==0.8.4', 'build==0.4.0']
            ).run()

            assert env.has_installed('tabulate', '0.8.4')
            assert env.has_installed('build', '0.4.0')

    def test_package_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = pathlib.Path(tmp) / '.venv'
            env = Environment(env_path)
            env.create()
            env.activate()
            Command(['pip', 'install', 'tabulate']).run()
            result = Command(['python', '-c', '"import tabulate"']).run()

        assert result.returncode == 0
        assert result.stdout == ''
        assert result.stderr == ''

    def test_console_scripts(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = pathlib.Path(tmp) / '.venv'
            env = Environment(env_path)
            env.create()
            env.activate()
            Command(['pip', 'install', 'build']).run()
            result = Command(['pyproject-build', '-h']).run()

        assert result.returncode == 0
        assert result.stdout != ''
        assert result.stderr == ''
