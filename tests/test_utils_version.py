import unittest

from chakra.utils import Version

class TestParse(unittest.TestCase):

    def test_correct(self):
        ver = Version.parse('3.8')
        assert ver.major == 3
        assert ver.minor == 8

    @unittest.expectedFailure
    def test_just_one_number(self):
        Version.parse('3')

    @unittest.expectedFailure
    def test_more_than_two_numbers(self):
        Version.parse('3.8.9')

    @unittest.expectedFailure
    def test_non_digits(self):
        Version.parse('3.8rc1')

    @unittest.expectedFailure
    def test_weird(self):
        Version.parse('.5')

class TestComparison(unittest.TestCase):

    def test_equal_to(self):
        assert Version(3, 8) == Version(3, 8)

    def test_less_than(self):
        assert Version(2, 8) < Version(3, 8)
        assert Version(3, 7) < Version(3, 8)

    def test_greater_than(self):
        assert Version(3, 8) > Version(2, 8)
        assert Version(3, 8) > Version(3, 7)

    def test_less_than_or_equal_to(self):
        assert Version(3, 8) <= Version(3, 8)
        assert Version(2, 8) <= Version(3, 8)
        assert Version(3, 7) <= Version(3, 8)

    def test_greater_than_or_equal_to(self):
        assert Version(3, 8) >= Version(3, 8)
        assert Version(3, 8) >= Version(2, 8)
        assert Version(3, 8) >= Version(3, 7)

    def test_not_equal_to(self):
        assert Version(3, 8) != Version(2, 7)
        assert Version(3, 8) != Version(2, 8)
        assert Version(3, 8) != Version(3, 7)

class TestStr(unittest.TestCase):

    def test(self):
        assert str(Version.parse('3.8')) == '3.8'
