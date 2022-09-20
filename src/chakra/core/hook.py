import enum
import pathlib

from .command import Command
from .platform import OpSystem
from ..errors import NotSupportedError

class _HookType(enum.Enum):
    BASH = ('', '.sh')
    POWERSHELL = ('.ps1',)
    PYTHON = ('.py',)

    @classmethod
    def identify(cls, fpath):
        ext = fpath.suffix
        for type_ in cls:
            if ext in type_.value:
                return type_
        raise NotSupportedError(f'unsupported hook extension {ext}')

    @property
    def interpreter(self):
        if self == self.__class__.POWERSHELL:
            return ('powershell', '-File')
        else:
            return (self.name.lower(),)

    def is_compat(self, opsys):
        if self == self.__class__.PYTHON:
            return True
        else:
            if opsys == OpSystem.WINDOWS:
                if self == self.__class__.POWERSHELL:
                    return True
            else:
                if self == self.__class__.BASH:
                    return True
        return False

class Hook(Command):
    """An executable script."""

    def __init__(self, script):
        script = pathlib.Path(script)
        self._type = _HookType.identify(script)
        super().__init__(list(self._type.interpreter) + [str(script)])

    def is_compat(self, opsys):
        return self._type.is_compat(opsys)
