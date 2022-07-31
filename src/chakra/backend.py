def get_requires_for_build_sdist(config_settings=None):
    raise NotImplementedError

def build_sdist(sdist_directory, config_settings=None):
    raise NotImplementedError

def get_requires_for_build_wheel(config_settings=None):
    raise NotImplementedError

def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    raise NotImplementedError

def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    raise NotImplementedError

def get_requires_for_build_editable(config_settings=None):
    raise NotImplementedError

def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
    raise NotImplementedError

def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    raise NotImplementedError
