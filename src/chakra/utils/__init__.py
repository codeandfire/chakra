# import the monkey-patched modules.

from .tempfile_patch import tempfile
from .tomllib_patch import tomllib

class NotSupportedError(Exception):
    pass
