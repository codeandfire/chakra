"""A patch for the `tempfile` module, specially `tempfile.TemporaryDirectory`."""

import os
import tempfile


class DirChangeTemporaryDirectory(tempfile.TemporaryDirectory):
    """A `TemporaryDirectory` which is robust against directory changes.

    In our tests, occasionally we have snippets like these:
    ```python
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        ...
    ```
    This leads to two problems. One: on Windows, this leads to all sorts of errors; see
    this issue https://github.com/python/cpython/issues/86962 for more details. Second: on
    Unix systems (Linux/Mac), there are other errors involving tests that take place
    *after* such tests, and continue to consider `temp_dir` as the current directory
    though it has been destroyed, and there are obscure `FileNotFoundError`s.

    The solution to both these problems is simply that: a) we must record the current
    directory at the time of entering the `with` block, and b) at the end of the `with`
    block, if we observe that the current directory has changed, we must change back to
    the original directory.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __enter__(self):
        self.orig_dir = os.getcwd()
        return super().__enter__()

    def __exit__(self, exc_type, exc_value, exc_tb):
        if os.getcwd() != self.orig_dir:
            os.chdir(self.orig_dir)
        super().__exit__(exc_type, exc_value, exc_tb)


# apply the patch.
tempfile.TemporaryDirectory = DirChangeTemporaryDirectory
