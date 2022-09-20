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

    _regex = re.compile(
        r'^(?P<major>\d+)(?P<minor>\.\d+)?(?P<patch>\.\d+)?(?P<tag>\w+)?$')

    def __init__(self, major, minor=None, patch=None, tag=None):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.tag = tag

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(major={self.major}, minor={self.minor}, '
            f'patch={self.patch}, tag={self.tag!r})')

    def _asnumeric(self):
        tuple_ = (self.major, self.minor, self.patch)
        return tuple(t for t in tuple_ if t is not None)

    def __str__(self):
        s = '.'.join(str(i) for i in self._asnumeric())
        s += self.tag if self.tag is not None else ''
        return s

    @classmethod
    def parse(cls, verstr):
        match_ = cls._regex.match(verstr)
        match_ = match_.groupdict()
        for key, value in match_.items():
            if value is not None:
                if key in ('minor', 'patch'):
                    value = value[1:]     # remove the leading .
                if key != 'tag':
                    value = int(value)
                match_[key] = value
        return cls(**match_)

    def __gt__(self, other):
        return _version_cmp(self._asnumeric(), other._asnumeric()) == '>'

    def __lt__(self, other):
        return _version_cmp(self._asnumeric(), other._asnumeric()) == '<'

    def __eq__(self, other):
        return \
            _version_cmp(self._asnumeric(), other._asnumeric()) == '=' and self.tag == other.tag

    def __ge__(self, other):
        return (self > other) or (self == other)

    def __le__(self, other):
        return (self < other) or (self == other)

    def __ne__(self, other):
        return not (self == other)
