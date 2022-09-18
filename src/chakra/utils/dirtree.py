import pathlib

def _path(p):
    return pathlib.Path(p)

class HFile(object):

    def __init__(self, name):
        self.name = _path(name)
        self.parent = None

    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.name!r}, parent={self.parent!r})'

    @property
    def path(self):
        return self.parent / self.name

    def create(self, parent=pathlib.Path.cwd()):
        self.parent = _path(parent)
        self.path.touch()

class HDirectory(object):

    def __init__(self, name, files=[], subdirs=[]):
        self.name = _path(name)
        self.parent = None
        self._files = files
        self._subdirs = subdirs

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(name={self.name!r}, parent={self.parent!r}, '
            f'_files={self._files!r}, _subdirs={self._subdirs!r})'
        )

    @property
    def path(self):
        return self.parent / self.name

    @property
    def files(self):
        return {str(file.name): file for file in self._files}

    @property
    def subdirs(self):
        return {str(subdir.name): subdir for subdir in self._subdirs}

    def create(self, parent=pathlib.Path.cwd()):
        self.parent = _path(parent)
        self.path.mkdir()
        for file in self._files:
            file.create(parent=self.path)
        for subdir in self._subdirs:
            subdir.create(parent=self.path)
