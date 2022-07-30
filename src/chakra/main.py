import argparse
from pathlib import Path

from pep517.wrappers import Pep517HookCaller

from .core import Command, Config


def cli():
    parser = argparse.ArgumentParser(description='Chakra CLI.')
    subparsers = parser.add_subparsers(title='commands', dest='command')

    build_parser = subparsers.add_parser('build', description='Build a wheel.')

    args = parser.parse_args()

    config = Config()

    if args.command == 'build':
        config.build_env.create_command.run()
        config.build_env.activate()

        hooks = Pep517HookCaller(
            Path.cwd(),
            build_backend=config.build_backend,
            backend_path=config.backend_path,
            python_executable=config.build_env.python_executable,
        )

        with config.build_deps.requirements_txt() as requirements_txt:
            Command(
                'pip', subcommand='install', optional_args={'-r': requirements_txt.name}
            ).run()

        hooks.build_editable(Path.cwd())

        config.build_env.remove()

    else:
        pass
