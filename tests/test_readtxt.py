from __future__ import print_function
import unittest
import sys
import os
import io

pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, pardir)

import channelpack.readtxt as rt

print('Testing readtxt module:', rt)
print('Testing with', unittest)
print()


class TestSmallFuncs(unittest.TestCase):

    def test__floatit_comma(self):
        self.assertIsInstance(rt._floatit(',12'), float)
        self.assertEqual(rt._floatit(',12'), 0.12)
        self.assertEqual(rt._floatit('3,14'), 3.14)
        self.assertEqual(rt._floatit('314,'), 314.0)

    def test__floatit_dot(self):
        self.assertEqual(rt._floatit('3.14'), 3.14)
        self.assertEqual(rt._floatit('314.'), 314.0)

    def test__escape_plus(self):
        self.assertEqual(rt._escape('12+34'), r'12\+34')

    def test__escape_dot(self):
        self.assertEqual(rt._escape('12.34'), r'12\.34')

    def test__escape_dotplus(self):
        self.assertEqual(rt._escape('12.34+56'), r'12\.34\+56')

    def test__escape_plusdot(self):
        self.assertEqual(rt._escape('12+34.56'), r'12\+34\.56')

    def test__escape_plusplus(self):
        self.assertEqual(rt._escape('12+34+56'), r'12\+34\+56')

    def test__escape_dotdot(self):
        self.assertEqual(rt._escape('12.34.56'), r'12\.34\.56')

    def test__escape_dotplusdotplus(self):
        self.assertEqual(rt._escape('12.34+56.78+90'), r'12\.34\+56\.78\+90')


class TestPreParse(unittest.TestCase):
    """Test the preparse function."""

    def setUp(self):
        self.maxDiff = None

    def readlines(self, f, cnt):
        """Read cnt lines from file f and return the lines.

        f is a file name string"""

        with io.open(f) as fo:
            return fo.readlines()[:cnt]

    def test_dat_0000(self):
        expected = {'chnames': {0: 'Time [s]',
                                1: 'Quantity1 - 12345678;  [qunit]',
                                2: 'Distance - 12345678;  [mm]',
                                3: 'Stresslevel& - 12345678;  [kLevel]'},
                    'converters': {0: rt._floatit,
                                   1: rt._floatit,
                                   2: rt._floatit,
                                   3: rt._floatit},
                    'delimiter': '\t',
                    'skiprows': 11,
                    'usecols': (0, 1, 2, 3)}
        lines = self.readlines('../testdata/dat_0000.txt', 20)
        self.assertEqual(rt.preparse(lines), expected)

    def test_dat_0000_nodata(self):
        expected = {}
        lines = self.readlines('../testdata/dat_0000.txt', 11)
        self.assertEqual(rt.preparse(lines), expected)

    def test_MesA1(self):
        expected = {'chnames': {0: 'Time_100Hz',
                                1: 'P_cyl',
                                2: 'F_cyl',
                                3: 'L_cyl',
                                4: 'Fc1_cal',
                                5: 'Fc2_cal'},
                    'converters': None,
                    'delimiter': ';',
                    'skiprows': 23,
                    'usecols': (0, 1, 2, 3, 4, 5)}
        lines = self.readlines('../testdata/MesA1.csv', 25)
        self.assertEqual(rt.preparse(lines), expected)

    def test_MesA1_nodata(self):
        expected = {}
        lines = self.readlines('../testdata/MesA1.csv', 23)
        self.assertEqual(rt.preparse(lines), expected)

    def test_sampledat1(self):
        expected = {'chnames': {0: 'RPT',
                                1: 'B_CACT',
                                2: 'P_CACT',
                                3: 'VG_STOP',
                                4: 'AR_BST',
                                5: 'PLRT_1',
                                6: 'TOQ_BUM'},
                    'converters': None,
                    'delimiter': '\t',
                    'skiprows': 1,
                    'usecols': (0, 1, 2, 3, 4, 5, 6)}
        lines = self.readlines('../testdata/sampledat1.txt', 2)
        self.assertEqual(rt.preparse(lines), expected)

    def test_sampledat1_nodata(self):
        expected = {}
        lines = self.readlines('../testdata/sampledat1.txt', 1)
        # fails because there is a number in one of the names
        # we can fix it in the parser FIXME
        self.assertEqual(rt.preparse(lines), expected)

    def test_loremipsum(self):
        expected = {}
        lines = self.readlines('../testdata/loremipsum', 25)
        self.assertEqual(rt.preparse(lines), expected)

    def test_loremipsum_numsend(self):
        expected = {'chnames': {0: 'molestie',
                                1: 'eu,',
                                2: 'feugiat',
                                3: 'in,',
                                4: 'orci.',
                                5: 'In',
                                6: 'hac',
                                7: 'habitasse',
                                8: 'platea',
                                9: 'dictumst.'},
                    'converters': None,
                    'delimiter': ' ',
                    'skiprows': 21,
                    'usecols': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)}
        lines = self.readlines('../testdata/loremipsum-numsend', 25)
        self.assertEqual(rt.preparse(lines), expected)

    def test_loremipsum_numsend_delok(self):
        expected = {'chnames': {0: 'ch0',
                                1: 'ch1',
                                2: 'ch2',
                                3: 'ch3',
                                4: 'ch4',
                                5: 'ch5',
                                6: 'ch6',
                                7: 'ch7',
                                8: 'ch8',
                                9: 'ch9'},
                    'converters': None,
                    'delimiter': ';',
                    'skiprows': 23,
                    'usecols': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)}
        lines = self.readlines('../testdata/loremipsum-numsend-delok', 25)
        self.assertEqual(rt.preparse(lines), expected)

    def test_loremipsum_numsmid(self):
        expected = {}
        lines = self.readlines('../testdata/loremipsum-numsmid', 25)
        self.assertEqual(rt.preparse(lines), expected)

    def test_onecolumn(self):
        expected = {'chnames': {},
                    'converters': None,
                    'delimiter': None,
                    'skiprows': 0,
                    'usecols': (0,)}
        lines = self.readlines('../testdata/onecolumn', 5)
        self.assertEqual(rt.preparse(lines), expected)
