import enum
import functools
import os

from .command import Command
from .._utils import NotSupportedError

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
