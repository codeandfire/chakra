"""Script to build Chakra from source (a barebones build).

Chakra can be bootstrapped by using an older version of Chakra to build a newer version.
To build Chakra from source (without a previous version), i.e. to create the first build
in the bootstrapping cycle, this script can be used. It installs Chakra's dependencies
using Pip and calls Chakra's build backend hooks.

Create a virtual environment, activate it, and run this script:

    $ virtualenv .venv
    $ source .venv/bin/activate
    $ python scripts/barebones_build.py

Pass `-e` or `--editable` to get an editable install:

    $ python scripts/barebones_build.py --editable
"""


import argparse
import subprocess
import sys

parser = argparse.ArgumentParser(description='Barebones build script.')
parser.add_argument(
    '-e', '--editable', action='store_true', help='install in editable mode')
args = parser.parse_args()

# (install and) load TOML parser.
if sys.version_info < (3, 11):
    subprocess.run(['pip', 'install', 'tomli'])
    import tomli as tomllib
else:
    import tomllib

# parse pyproject.toml to find dependencies.
with open('pyproject.toml', 'rb') as f:
    dependencies = tomllib.load(f)['project']['dependencies']

# install dependencies.
subprocess.run(['pip', 'install'] + dependencies)

# add the source code directory to path.
sys.path.append('src')

# invoke the build backend hooks.
from chakra import backend
if args.editable:
    wheel = backend.build_editable('.')
else:
    wheel = backend.build_wheel('.')

# install the built wheel.
subprocess.run(['pip', 'install', wheel])
