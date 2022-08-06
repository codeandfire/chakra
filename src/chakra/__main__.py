import argparse
from pathlib import Path
from .tempfile_patch import tempfile

from .backend import build_editable
from .config import Config
from .core import Command, Environment


def _requirements_txt(deps):
    """Write a `requirements.txt` with the given list of dependencies."""

    temp_file = tempfile.NamedTemporaryFile()
    with open(temp_file.name, 'w') as f:
        f.write('\n'.join(deps))
    return temp_file


def cli():
    parser = argparse.ArgumentParser('chakra', description='Chakra CLI.')
    subparsers = parser.add_subparsers(
        title='commands', dest='command', help='run workflows', required=True)

    build_parser = subparsers.add_parser(
        'build', description='Build an sdist and/or a wheel.')

    args = parser.parse_args()

    config = Config()

    env = Environment(config.env_dir / Path(args.command))

    if not env.path.exists():
        env.create()
        env.activate()

        deps = config.dev_deps[args.command]
        with _requirements_txt(deps) as req_txt:
            Command(['pip', 'install', '-r', req_txt.name]).run()
    else:
        env.activate()

    if args.command == 'build':
        build_editable(Path.cwd())
    else:
        pass


if __name__ == '__main__':
    cli()
