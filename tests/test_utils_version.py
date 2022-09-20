import unittest

from chakra.utils import Version

class TestParse(unittest.TestCase):

    def test_major(self):
        ver = Version.parse('3')
        assert ver.major == 3
        assert ver.minor is None
        assert ver.patch is None

    def test_major_minor(self):
        ver = Version.parse('3.8')
        assert ver.major == 3
        assert ver.minor == 8
        assert ver.patch is None

    def test_major_minor_patch(self):
        ver = Version.parse('3.8.11')
        assert ver.major == 3
        assert ver.minor == 8
        assert ver.patch == 11

    @unittest.expectedFailure
    def test_four_fields(self):
        Version.parse('3.8.9.10')

    @unittest.expectedFailure
    def test_non_digits(self):
        Version.parse('3.11.0rc1')

    @unittest.expectedFailure
    def test_weird(self):
        Version.parse('.5.a7')

    @unittest.expectedFailure
    def test_weird2(self):
        Version.parse('3..11')

    @unittest.expectedFailure
    def test_empty(self):
        Version.parse('')

class TestComparison(unittest.TestCase):

    def test_equal_to(self):
        assert Version(3) == Version(3)
        assert Version(3, 8) == Version(3, 8)
        assert Version(3, 8, 11) == Version(3, 8, 11)

    def test_less_than(self):
        assert Version(2) < Version(3)
        assert Version(3, 7) < Version(3, 8)
        assert Version(3, 8, 10) < Version(3, 8, 11)
        assert Version(2, 6) < Version(3, 8)
        assert Version(2, 6, 10) < Version(3, 8, 11)

    def test_greater_than(self):
        assert Version(3) > Version(2)
        assert Version(3, 8) > Version(3, 7)
        assert Version(3, 8, 11) > Version(3, 8, 10)
        assert Version(3, 8) > Version(2, 6)
        assert Version(3, 8, 11) > Version(2, 6, 10)

    def test_less_than_or_equal_to(self):
        assert Version(3) <= Version(3)
        assert Version(3, 8) <= Version(3, 8)
        assert Version(3, 8, 11) <= Version(3, 8, 11)
        assert Version(2) <= Version(3)
        assert Version(3, 7) <= Version(3, 8)
        assert Version(3, 8, 10) <= Version(3, 8, 11)
        assert Version(2, 6) <= Version(3, 8)
        assert Version(2, 6, 10) <= Version(3, 8, 11)

    def test_greater_than_or_equal_to(self):
        assert Version(3) >= Version(3)
        assert Version(3, 8) >= Version(3, 8)
        assert Version(3, 8, 11) >= Version(3, 8, 11)
        assert Version(3) >= Version(2)
        assert Version(3, 8) >= Version(3, 7)
        assert Version(3, 8, 11) >= Version(3, 8, 10)
        assert Version(3, 8) >= Version(2, 6)
        assert Version(3, 8, 11) >= Version(2, 6, 10)

    def test_not_equal_to(self):
        assert Version(2) != Version(3)
        assert Version(3, 7) != Version(3, 8)
        assert Version(3, 8, 10) != Version(3, 8, 11)
        assert Version(2, 6) != Version(3, 8)
        assert Version(2, 6, 10) != Version(3, 8, 11)

        # need to assert the symmetric conditions as well
        assert Version(3) != Version(2)
        assert Version(3, 8) != Version(3, 7)
        assert Version(3, 8, 11) != Version(3, 8, 10)
        assert Version(3, 8) != Version(2, 6)
        assert Version(3, 8, 11) != Version(2, 6, 10)


class TestStr(unittest.TestCase):

    def test(self):
        assert str(Version(3)) == '3'
        assert str(Version(3, 8)) == '3.8'
        assert str(Version(3, 8, 11)) == '3.8.11'
