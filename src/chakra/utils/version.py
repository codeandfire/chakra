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

    def __init__(self, major, minor):
        self.major = major
        self.minor = minor

    def __repr__(self):
        return f'{self.__class__.__name__}(major={self.major}, minor={self.minor})'

    def __str__(self):
        return f'{self.major}.{self.minor}'

    def __len__(self):
        return 2

    def __getitem__(self, idx):
        if idx == 0:
            return self.major
        elif idx == 1:
            return self.minor
        else:
            raise IndexError('version is of the form major.minor')

    @classmethod
    def parse(cls, verstr):
        """Parse a version string."""
        ver = verstr.split('.')
        assert len(ver) == 2, 'version must be of the form major.minor'
        assert all(v.isdigit() for v in ver), 'version must contain only digits'
        return cls(*(int(v) for v in ver))

    def __gt__(self, other):
        return _version_cmp(tuple(self), tuple(other)) == '>'

    def __lt__(self, other):
        return _version_cmp(tuple(self), tuple(other)) == '<'

    def __eq__(self, other):
        return _version_cmp(tuple(self), tuple(other)) == '='

    def __ge__(self, other):
        return (self > other) or (self == other)

    def __le__(self, other):
        return (self < other) or (self == other)

    def __ne__(self, other):
        return not (self == other)
