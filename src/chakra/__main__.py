import argparse
from pathlib import Path

from .config import Config
from .core import Command
from .backend import build_editable


def cli():
    parser = argparse.ArgumentParser('chakra', description='Chakra CLI.')
    subparsers = parser.add_subparsers(
        title='commands', dest='command', help='run workflows', required=True)

    build_parser = subparsers.add_parser(
        'build', description='Build an sdist and/or a wheel.')

    args = parser.parse_args()

    config = Config()

    if args.command == 'build':
        config.build_env.create_command.run()
        config.build_env.activate()

        with config.build_deps.requirements_txt() as requirements_txt:
            Command(['pip', 'install', '-r', requirements_txt.name]).run()

        build_editable(Path.cwd())

        config.build_env.remove()

    else:
        pass


if __name__ == '__main__':
    cli()
