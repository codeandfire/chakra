from pathlib import Path

from .config import Config

def get_requires_for_build_sdist(config_settings=None):
    raise NotImplementedError

def build_sdist(sdist_directory, config_settings=None):
    config = Config()
    name = config.metadata.name
    version = str(config.metadata.version)
    Path(f'{name}-{version}.tar.gz').touch()

def get_requires_for_build_wheel(config_settings=None):
    raise NotImplementedError

def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    raise NotImplementedError

def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    config = Config()
    name = config.metadata.name
    version = str(config.metadata.version)
    Path(f'{name}-{version}-py3-none-any.whl').touch()

def get_requires_for_build_editable(config_settings=None):
    raise NotImplementedError

def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
    raise NotImplementedError

def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    config = Config()
    name = config.metadata.name
    version = str(config.metadata.version)
    Path(f'{name}-{version}-py3-none-any.whl').touch()
