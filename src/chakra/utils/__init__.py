# import the monkey-patched modules.

from .tempfile_patch import tempfile
from .tomllib_patch import tomllib
from .version import Version

class NotSupportedError(Exception):
    pass
