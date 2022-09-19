import enum
import functools
import os
import pathlib
import sys

from .command import Command
from ..errors import NotSupportedError
from ..utils import Version

class OpSystem(enum.Enum):
    WINDOWS = 'nt'
    LINUX = 'linux'
    MACOS = 'darwin'

    @classmethod
    @functools.cache
    def find(cls):
        # plat_os = platform OS, cand_os = candidate OS
        if os.name == 'posix':
            plat_os = Command(['uname', '-s']).run().stdout.lower()
        else:
            plat_os = os.name
        for cand_os in cls:
            if plat_os == cand_os.value:
                return cand_os
        raise NotSupportedError(f'unsupported operating system (or kernel) {plat_os!r}')

class Arch(enum.Enum):
    INTEL_AMD_32_BIT = ('x86', 'i386', 'i586', 'i686')
    INTEL_AMD_64_BIT = ('x86_64', 'amd64')
    ARM_64_BIT = ('arm64', 'aarch64')

    @classmethod
    @functools.cache
    def find(cls, opsys):
        # plat_ar = platform arch., cand_ar = candidate arch.
        if opsys == OpSystem.WINDOWS:
            plat_ar = os.environ['PROCESSOR_ARCHITECTURE'].lower()
        else:
            plat_ar = Command(['uname', '-m']).run().stdout
        for cand_ar in cls:
            if plat_ar in cand_ar.value:
                return cand_ar
        raise NotSupportedError(f'unsupported architecture {plat_ar!r}')

class Python(object):

    class Type(enum.Enum):
        PYTHON = 'cp'   # regular CPython
        PYPY = 'pp'

    def __init__(self, type_, ver):
        self.type_ = type_
        self.ver = ver

    def __repr__(self):
        return f'{self.__class__.__name__}(type_={self.type_!r}, ver={self.ver!r})'

    def __str__(self):
        return f'{self.type_.value}{self.ver}'.replace('.', '')

    def __eq__(self, other):
        return self.type_ == other.type_ and self.ver == other.ver

    @classmethod
    def parse(cls, pystr):
        for type_ in cls.Type:
            if pystr.startswith(type_.value):
                break
        else:
            raise NotSupportedError(f'unsupported python type {pystr}')
        ver = pystr[len(type_.value):]
        ver = ver[0] + '.' + ver[1:]
        try:
            ver = Version.parse(ver)
            assert ver.patch is None
        except AssertionError:
            raise ValueError(f'invalid python {pystr!r}')
        return cls(type_, ver)

def current_py():
    # TODO: manipulate sys.executable
    pass
