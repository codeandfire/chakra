"""Patches for the `tempfile` module.

The Python standard library's `tempfile` module has some issues. A full list can be found
here: https://github.com/python/cpython/issues?q=is:open%20is:issue%20project:python/17

The patches applied here are sufficient for Chakra's source code and tests, until more
appropriate patches are applied upstream.
"""


import os
import tempfile


__all__ = ['tempfile']


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

    def __fspath__(self):
        return self.name


# apply the patch.
tempfile.TemporaryDirectory = DirChangeTemporaryDirectory


class FileInsideTemporaryDirectory:
    """An alternative to `tempfile.NamedTemporaryFile`.

    This class basically implements a workaround for `tempfile`'s `NamedTemporaryFile`
    functionality. It creates a `tempfile.TemporaryDirectory` and uses a file (named
    `temp`) within that directory as a named temporary file.

    The docs for `tempfile.NamedTemporaryFile`
    (https://docs.python.org/3/library/tempfile.html#tempfile.NamedTemporaryFile) mention
    that this class has a `file` attribute which is the underlying true file object.
    Therefore, we assume that we can use this `file` attribute to write to and read from
    the temporary file:
    ```
    >>> import tempfile
    >>> with tempfile.NamedTemporaryFile() as temp_file:
            file = temp_file.file
            file.write(bytes('foo'.encode('utf-8')))
            print(file.read().decode('utf-8'))
    ```
    However, this doesn't work. The output of `file.read()` is an empty string ''. One
    might assume that this is happening because the temporary file is opened in write-only
    or read-only mode; but this is not the case, the default mode is 'w+b' which allows
    reading and writing both.

    Writing to and reading from the `NamedTemporaryFile` object itself doesn't work
    either, i.e. `temp_file.write()` and `temp_file.read()` don't work.

    Another alternative that is indicated in the docs, and in a StackOverflow answer
    (https://stackoverflow.com/a/39984066), is to use the `name` attribute of the
    `NamedTemporaryFile` to get the name of the temporary file, and then open the file
    with this name. In other words:
    ```
    >>> import tempfile
    >>> with tempfile.NamedTemporaryFile() as temp_file:
            with open(temp_file.name, 'w') as f:
                f.write('foo')
            with open(temp_file.name, 'r') as f:
                print(f.read())
    ```
    This does work but only on Unix systems (Linux/MacOS). On Windows system it doesn't
    work and leads to `PermissionError`s; the same is indicated in the docs as well. An
    issue on this is https://github.com/python/cpython/issues/88221.

    The workaround implemented by this class exposes a `name` attribute, pointing to a
    file named `temp` inside a `tempfile.TemporaryDirectory`. This simulates the
    functionality of a `tempfile.NamedTemporaryFile` without any of the above problems.
    """

    def __init__(self, **kwargs):
        self._dir = tempfile.TemporaryDirectory()
        self.name = os.path.join(self._dir, 'temp')

    def __enter__(self):
        self._dir.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self._dir.__exit__(exc_type, exc_value, exc_tb)


# apply the patch.
tempfile.NamedTemporaryFile = FileInsideTemporaryDirectory
