import functools
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

    # the `cached_property` decorator prevents the regex from being recompiled on every
    # call to this property.

    @classmethod
    @functools.cached_property
    def regex(cls):
        return re.compile(r'(\d+(?:\.\d+){0,2})')

    @classmethod
    def parse(cls, verstr):
        """Parse a version string."""
        ver = verstr.split('.')
        assert len(ver) <= 3, 'version must have at most 3 fields major, minor and patch'
        assert all(v.isdigit() for v in ver), 'version must contain only digits'
        return cls(*(int(v) for v in ver))

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
