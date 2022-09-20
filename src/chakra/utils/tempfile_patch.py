import os
import tempfile

__all__ = ['tempfile']

# (monkey-) patch for `TemporaryDirectory`.
# for cases when the current directory is changed to the temporary directory and not
# changed back to the original directory before closing the temporary directory.

class DirChangeTemporaryDirectory(tempfile.TemporaryDirectory):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __enter__(self):
        self.orig_dir = os.getcwd()
        return super().__enter__()

    def __exit__(self, exc_type, exc_value, exc_tb):
        if os.getcwd() != self.orig_dir:
            os.chdir(self.orig_dir)
        super().__exit__(exc_type, exc_value, exc_tb)

    def __fspath__(self):
        return self.name

tempfile.TemporaryDirectory = DirChangeTemporaryDirectory

# (monkey-) patch for `TemporaryFile` which implements a temporary file as a file inside a
# `TemporaryDirectory`.
# this is for cases in which the original `TemporaryFile` doesn't work.

class FileInsideTemporaryDirectory:

    def __init__(self, **kwargs):
        self._dir = tempfile.TemporaryDirectory()
        self.name = os.path.join(self._dir, 'temp')

    def __enter__(self):
        self._dir.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self._dir.__exit__(exc_type, exc_value, exc_tb)

tempfile.NamedTemporaryFile = FileInsideTemporaryDirectory
