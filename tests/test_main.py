from io import StringIO
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import virtualenv

from chakra.__main__ import cli
from chakra._utils import tempfile

import simulator


@patch('sys.stdout', new_callable=StringIO)
class TestBuild(unittest.TestCase):

    @patch('sys.argv', ['chakra', 'build'])
    def test(self, _):
        """Test regular call. An sdist and wheel must be created."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            simulator.SamplePackage('foo').create()
            cli()

            assert (Path('.envs') / Path('build')).exists()
            assert Path('foo-0.1.0.tar.gz').exists()
            assert Path('foo-0.1.0-py3-none-any.whl').exists()

    @patch('sys.argv', ['chakra', 'build', '-e'])
    def test_editable_wheel(self, _):
        """Test call with the `-e` argument. An editable wheel must be created."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            simulator.SamplePackage('foo').create()
            cli()

            assert (Path('.envs') / Path('build')).exists()
            assert Path('foo-0.1.0-py3-none-any.whl').exists()

    @patch('sys.argv', ['chakra', 'build'])
    def test_env_exists(self, _):
        """Check that the environment is not regenerated if it already exists.

        This check is performed by recording the last modification time of the environment
        directory and ensuring that it does not change after invoking `chakra build`.
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            env_path = Path('.envs') / Path('build')
            virtualenv.cli_run([str(env_path)])  # create the environment
            mtime = env_path.stat().st_mtime_ns

            simulator.SamplePackage('foo').create()
            cli()

            new_mtime = env_path.stat().st_mtime_ns
            assert mtime == new_mtime

    @patch('sys.argv', ['chakra', 'build'])
    def test_build_deps(self, _):
        """Check that any build dependencies specified are installed."""

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            simulator.SamplePackage(
                'foo', build_requires=['tabulate', 'termcolor==1.1.0']).create()
            cli()

            env_path = Path('.envs') / Path('build')
            assert simulator.is_installed('tabulate', env_path)
            assert simulator.is_installed('termcolor', env_path, version='1.1.0')
