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

    def test_major_minor_patch_tag(self):
        ver = Version.parse('3.11.0rc1')
        assert ver.major == 3
        assert ver.minor == 11
        assert ver.patch == 0
        assert ver.tag == 'rc1'

    def test_major_minor_tag(self):
        ver = Version.parse('1.0a1')
        assert ver.major == 1
        assert ver.minor == 0
        assert ver.patch is None
        assert ver.tag == 'a1'

    def test_major_tag(self):      # this is technically legal, yet nonsenical
        ver = Version.parse('1a1')
        assert ver.major == 1
        assert ver.minor is None
        assert ver.patch is None
        assert ver.tag == 'a1'

    def test_four_fields(self):
        with self.assertRaises(AssertionError):
            Version.parse('3.8.9.10')

    def test_non_digits(self):
        with self.assertRaises(AssertionError):
            Version.parse('3.11.abc')

    def test_weird(self):
        with self.assertRaises(AssertionError):
            Version.parse('.5.a7')

    def test_weird2(self):
        with self.assertRaises(AssertionError):
            Version.parse('3..11')

    def test_empty(self):
        with self.assertRaises(AssertionError):
            Version.parse('')

class TestComparison(unittest.TestCase):

    def test_equal_to(self):
        assert Version(3) == Version(3)
        assert Version(3, 8) == Version(3, 8)
        assert Version(3, 8, 11) == Version(3, 8, 11)
        assert Version(3, 8, 11, 'b5') == Version(3, 8, 11, 'b5')

    def test_less_than(self):
        assert Version(2) < Version(3)
        assert Version(3, 7) < Version(3, 8)
        assert Version(3, 7, 'a1') < Version(3, 7, 'b5')
        assert Version(3, 8, 10) < Version(3, 8, 11)
        assert Version(3, 8, 10, 'rc1') < Version(3, 8, 11, 'rc1')
        assert Version(2, 6) < Version(3, 8)
        assert Version(2, 6, 10) < Version(3, 8, 11)
        assert Version(2, 6, 10, 'b5') < Version(3, 8, 11, 'a1')

    def test_greater_than(self):
        assert Version(3) > Version(2)
        assert Version(3, 8) > Version(3, 7)
        assert Version(3, 8, 'b5') > Version(3, 7, 'a1')
        assert Version(3, 8, 11) > Version(3, 8, 10)
        assert Version(3, 8, 11, 'a1') > Version(3, 8, 10, 'b5')
        assert Version(3, 8) > Version(2, 6)
        assert Version(3, 8, 'b3') > Version(2, 6, 'b3')
        assert Version(3, 8, 11) > Version(2, 6, 10)

    def test_less_than_or_equal_to(self):
        assert Version(3) <= Version(3)
        assert Version(3, 8) <= Version(3, 8)
        assert Version(3, 8, 11) <= Version(3, 8, 11)
        assert Version(3, 8, 11, 'b5') == Version(3, 8, 11, 'b5')
        assert Version(2) <= Version(3)
        assert Version(3, 7) <= Version(3, 8)
        assert Version(3, 7, 'a1') <= Version(3, 7, 'b5')
        assert Version(3, 8, 10) <= Version(3, 8, 11)
        assert Version(3, 8, 10, 'rc1') <= Version(3, 8, 11, 'rc1')
        assert Version(2, 6) <= Version(3, 8)
        assert Version(2, 6, 10) <= Version(3, 8, 11)
        assert Version(2, 6, 10, 'b5') <= Version(3, 8, 11, 'a1')

    def test_greater_than_or_equal_to(self):
        assert Version(3) >= Version(3)
        assert Version(3, 8) >= Version(3, 8)
        assert Version(3, 8, 11) >= Version(3, 8, 11)
        assert Version(3, 8, 11, 'b5') >= Version(3, 8, 11, 'b5')
        assert Version(3) >= Version(2)
        assert Version(3, 8) >= Version(3, 7)
        assert Version(3, 8, 'b5') >= Version(3, 7, 'a1')
        assert Version(3, 8, 11) >= Version(3, 8, 10)
        assert Version(3, 8, 11, 'a1') >= Version(3, 8, 10, 'b5')
        assert Version(3, 8) >= Version(2, 6)
        assert Version(3, 8, 'b3') >= Version(2, 6, 'b3')
        assert Version(3, 8, 11) >= Version(2, 6, 10)

    def test_not_equal_to(self):
        assert Version(2) != Version(3)
        assert Version(3, 7) != Version(3, 8)
        assert Version(3, 8, 'b5') != Version(3, 7, 'a1')
        assert Version(3, 8, 'b5') != Version(3, 8, 'a1')
        assert Version(3, 8, 10) != Version(3, 8, 11)
        assert Version(3, 8, 10, 'b5') != Version(3, 8, 11, 'a1')
        assert Version(3, 8, 10, 'a1') != Version(3, 8, 11, 'b5')
        assert Version(2, 6) != Version(3, 8)
        assert Version(2, 6, 10) != Version(3, 8, 11)
        assert Version(2, 6, 10, 'rc1') != Version(3, 8, 11, 'rc1')

        # need to assert the symmetric conditions as well
        assert Version(3) != Version(2)
        assert Version(3, 8) != Version(3, 7)
        assert Version(3, 7, 'a1') != Version(3, 8, 'b5')
        assert Version(3, 8, 'a1') != Version(3, 8, 'b5')
        assert Version(3, 8, 11) != Version(3, 8, 10)
        assert Version(3, 8, 11, 'a1') != Version(3, 8, 10, 'b5')
        assert Version(3, 8, 11, 'b5') != Version(3, 8, 10, 'a1')
        assert Version(3, 8) != Version(2, 6)
        assert Version(3, 8, 11) != Version(2, 6, 10)
        assert Version(3, 8, 11, 'rc1') != Version(2, 6, 10, 'rc1')

class TestStr(unittest.TestCase):

    def test(self):
        assert str(Version(3)) == '3'
        assert str(Version(3, 8)) == '3.8'
        assert str(Version(3, 8, 11)) == '3.8.11'
        assert str(Version(3, 8, 11, 'b5')) == '3.8.11b5'
        assert str(Version(3, 8, None, tag='rc1')) == '3.8rc1'
        assert str(Version(3, None, None, 'a1')) == '3a1'   # again, nonsensical
