import re

def _version_cmp(nver1, nver2):
    """Compare versions in the form of n-dimensional lists/tuples."""
    assert len(nver1) == len(nver2), 'cannot compare versions of differing lengths'
    try:
        if nver1[0] > nver2[0]:
            return '>'
        elif nver1[0] < nver2[0]:
            return '<'
        else:
            return _version_cmp(nver1[1:], nver2[1:])
    except IndexError:  # no elements left
        return '='

class Version(object):
    """Numerical representation of a version."""

    _regex = re.compile(r'(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.(?P<patch>\d+))?')

    def __init__(self, major, minor=None, patch=None):
        self.major = major
        self.minor = minor
        self.patch = patch

    def __repr__(self):
        return f'{self.__class__.__name__}(major={self.major}, minor={self.minor}, patch={self.patch})'

    def _totuple(self):
        tuple_ = (self.major, self.minor, self.patch)
        return tuple(t for t in tuple_ if t is not None)

    def __str__(self):
        return '.'.join(str(i) for i in self._totuple())

    @classmethod
    def parse(cls, verstr):
        match_ = cls._regex.match(verstr)
        parsed = [int(g) if g is not None else None for g in match_.groups()]
        return cls(*parsed)

    def __gt__(self, other):
        return _version_cmp(self._totuple(), other._totuple()) == '>'

    def __lt__(self, other):
        return _version_cmp(self._totuple(), other._totuple()) == '<'

    def __eq__(self, other):
        return _version_cmp(self._totuple(), other._totuple()) == '='

    def __ge__(self, other):
        return (self > other) or (self == other)

    def __le__(self, other):
        return (self < other) or (self == other)

    def __ne__(self, other):
        return not (self == other)
