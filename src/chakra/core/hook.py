from .command import Command
from ..utils import NotSupportedError

class Hook(Command):
    """An executable script."""

    def __init__(self, script):
        self.script = script
        if self.script.suffix == '.ps1':
            self.interpreter = 'powershell'
            super().__init__([self.interpreter, '-File', str(self.script)])
        else:
            if self.script.suffix == '.py':
                self.interpreter = 'python'
            elif self.script.suffix == '' or self.script.suffix == '.sh':
                self.interpreter = 'bash'
            else:
                raise NotSupportedError(f'unsupported hook extension {self.script.suffix}')
            super().__init__([self.interpreter, str(self.script)])

    def __repr__(self):
        return f'{self.__class__.__name__}(interpreter={self.interpreter!r}, script={self.script!r})'
