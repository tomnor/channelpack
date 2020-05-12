# -*- coding: utf-8 -*-
from __future__ import print_function
import unittest
import sys
import os
import io

pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, pardir)

import channelpack.readtxt as rt
import channelpack as cp

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
        expected = {'chnames': {0: 'col0',
                                1: 'col1',
                                2: 'col2',
                                3: 'col3',
                                4: 'col4',
                                5: 'col5',
                                6: 'col6',
                                7: 'col7',
                                8: 'col8',
                                9: 'col9'},
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


class TestLazyLoadTxtPack(unittest.TestCase):

    def test_dat_0000(self):

        pack = rt.lazy_loadtxt_pack('../testdata/dat_0000.txt', 20)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack(0)[-1], 31.175)
        self.assertEqual(pack(2)[-1], 11.835044)

    def test_dat_0000_txtIO(self):

        with io.open('../testdata/dat_0000.txt', 'r') as fo:
            pack = rt.lazy_loadtxt_pack(fo, 12)

        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack(0)[-1], 31.175)
        self.assertEqual(pack(2)[-1], 11.835044)

    def test_dat_0000_bytesIO(self):

        with io.open('../testdata/dat_0000.txt', 'rb') as fo:
            pack = rt.lazy_loadtxt_pack(fo, 12)

        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack(0)[-1], 31.175)
        self.assertEqual(pack(2)[-1], 11.835044)

    def test_dat_0000_too_few_lines(self):

        with self.assertRaises(ValueError):
            # ValueError: could not convert string to float: 'Data'
            rt.lazy_loadtxt_pack('../testdata/dat_0000.txt', 11)

    def test_loremipsum(self):
        # ValueError: could not convert string to float: Lorem
        with self.assertRaises(ValueError):
            rt.lazy_loadtxt_pack('../testdata/loremipsum', 20)

    def test_loremipsum_txtIO(self):
        # ValueError: could not convert string to float: Lorem
        with io.open('../testdata/loremipsum', 'r') as fo:
            with self.assertRaises(ValueError):
                rt.lazy_loadtxt_pack(fo, 20)

    def test_loremipsum_bytesIO(self):
        # ValueError: could not convert string to float: Lorem
        with io.open('../testdata/loremipsum', 'rb') as fo:
            with self.assertRaises(ValueError):
                rt.lazy_loadtxt_pack(fo, 20)

    def test_loremipsum_numsend(self):

        pack = rt.lazy_loadtxt_pack('../testdata/loremipsum-numsend', 22)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack(0)[-1], 1)
        self.assertEqual(pack(2)[-1], 3)

    def test_loremipsum_numsend_txtIO(self):

        with io.open('../testdata/loremipsum-numsend', 'r') as fo:
            pack = rt.lazy_loadtxt_pack(fo, 22)

        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack(0)[-1], 1)
        self.assertEqual(pack(2)[-1], 3)

    def test_loremipsum_numsend_bytesIO(self):

        with io.open('../testdata/loremipsum-numsend', 'rb') as fo:
            pack = rt.lazy_loadtxt_pack(fo, 22)

        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack(0)[-1], 1)
        self.assertEqual(pack(2)[-1], 3)

    def test_loremipsum_numsend_too_few_lines(self):

        with self.assertRaises(ValueError):
            # ValueError: could not convert string to float: 'Lorem'
            rt.lazy_loadtxt_pack('../testdata/loremipsum-numsend', 11)

    def test_loremipsum_numsend_delok(self):

        fn = '../testdata/loremipsum-numsend-delok'
        pack = rt.lazy_loadtxt_pack(fn, 24)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack('col0')[-1], 1)
        self.assertEqual(pack('col2')[-1], 3)

    def test_loremipsum_numsend_delok_txtIO(self):

        fn = '../testdata/loremipsum-numsend-delok'
        with io.open(fn, 'r') as fo:
            pack = rt.lazy_loadtxt_pack(fo, 24)

        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack('col0')[-1], 1)
        self.assertEqual(pack('col2')[-1], 3)

    def test_loremipsum_numsend_delok_bytesIO(self):

        fn = '../testdata/loremipsum-numsend-delok'
        with io.open(fn, 'rb') as fo:
            pack = rt.lazy_loadtxt_pack(fo, 24)

        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack('col0')[-1], 1)
        self.assertEqual(pack('col2')[-1], 3)

    def test_loremipsum_numsend_delok_too_few_lines(self):

        fn = '../testdata/loremipsum-numsend-delok'
        with self.assertRaises(ValueError):
            # ValueError: could not convert string to float: 'Lorem'
            rt.lazy_loadtxt_pack(fn, 11)

    def test_loremipsum_numsmid(self):
        # ValueError: could not convert string to float: Lorem
        with self.assertRaises(ValueError):
            rt.lazy_loadtxt_pack('../testdata/loremipsum-numsmid', 20)

    def test_loremipsum_numsmid_txtIO(self):
        # ValueError: could not convert string to float: Lorem
        with io.open('../testdata/loremipsum-numsmid', 'r') as fo:
            with self.assertRaises(ValueError):
                rt.lazy_loadtxt_pack(fo, 20)

    def test_loremipsum_numsmid_bytesIO(self):
        # ValueError: could not convert string to float: Lorem
        with io.open('../testdata/loremipsum-numsmid', 'rb') as fo:
            with self.assertRaises(ValueError):
                rt.lazy_loadtxt_pack(fo, 20)

    def test_MesA1(self):

        pack = rt.lazy_loadtxt_pack('../testdata/MesA1.csv', 24)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack(0)[-1], 176.64000000)
        self.assertEqual(pack(2)[-1], 0.07213194)

    def test_MesA1_txtIO(self):

        with io.open('../testdata/MesA1.csv', 'r') as fo:
            pack = rt.lazy_loadtxt_pack(fo, 24)

        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack(0)[-1], 176.64000000)
        self.assertEqual(pack(2)[-1], 0.07213194)

    def test_MesA1_txtIO_chnames(self):

        with io.open('../testdata/MesA1.csv', 'r') as fo:
            pack = rt.lazy_loadtxt_pack(fo, 24)

        for name in 'Time_100Hz;P_cyl;F_cyl;L_cyl;Fc1_cal;Fc2_cal'.split(';'):
            self.assertEqual(pack.name(name), name)

    def test_MesA1_bytesIO(self):

        with io.open('../testdata/MesA1.csv', 'rb') as fo:
            pack = rt.lazy_loadtxt_pack(fo, 24)

        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack(0)[-1], 176.64000000)
        self.assertEqual(pack(2)[-1], 0.07213194)

    def test_MesA1_too_few_lines(self):

        with self.assertRaises(ValueError):
            # ValueError: could not convert string to float: 'Data'
            rt.lazy_loadtxt_pack('../testdata/MesA1.csv', 11)

    def test_onecolumn(self):

        pack = rt.lazy_loadtxt_pack('../testdata/onecolumn', 24)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack(0)[0], 1)
        self.assertEqual(pack(0)[-1], 12)

    def test_onecolumn_txtIO(self):

        with io.open('../testdata/onecolumn', 'r') as fo:
            pack = rt.lazy_loadtxt_pack(fo, 24)

        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack(0)[0], 1)
        self.assertEqual(pack(0)[-1], 12)

    def test_onecolumn_bytesIO(self):

        with io.open('../testdata/onecolumn', 'rb') as fo:
            pack = rt.lazy_loadtxt_pack(fo, 24)

        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack('ch0')[0], 1)
        self.assertEqual(pack('ch0')[-1], 12)

    def test_sampledat1(self):

        pack = rt.lazy_loadtxt_pack('../testdata/sampledat1.txt', 2)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack(0)[0], 0)
        self.assertEqual(pack(6)[-1], 20.285)

    def test_sampledat1_txtIO(self):

        with io.open('../testdata/sampledat1.txt', 'r') as fo:
            pack = rt.lazy_loadtxt_pack(fo, 2)

        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack(0)[0], 0)
        self.assertEqual(pack(6)[-1], 20.285)

    def test_sampledat1_txtIO_chnames(self):

        with io.open('../testdata/sampledat1.txt', 'r') as fo:
            pack = rt.lazy_loadtxt_pack(fo, 2)

        names = ('RPT', 'B_CACT', 'P_CACT', 'VG_STOP',
                 'AR_BST', 'PLRT_1', 'TOQ_BUM')
        for name in names:
            self.assertEqual(pack.name(name), name)

    def test_sampledat1_bytesIO(self):

        with io.open('../testdata/sampledat1.txt', 'rb') as fo:
            pack = rt.lazy_loadtxt_pack(fo, 2)

        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack(0)[0], 0)
        self.assertEqual(pack(6)[-1], 20.285)

    def test_sampledat1_too_few_lines(self):

        with self.assertRaises(ValueError):
            # ValueError: could not convert string to float: 'Data'
            rt.lazy_loadtxt_pack('../testdata/sampledat1.txt', 1)


datstring_comma = \
    u"""date: 20-05-01 17:39
room: east lab hall, floor 2, room 8
operator: Goran Operatorsson

time, speed, onoff, distance
0, 23, on, 0.3
1, 21, off, 0.28
"""


class TestLineTuples(unittest.TestCase):

    def test_dat_0000(self):
        numvals = 4
        with open('../testdata/dat_0000.txt') as fo:
            for i in range(11):
                fo.readline()
            linetupler = rt.linetuples(fo)
            funcs = next(linetupler)
            self.assertEqual(len(funcs), numvals)
            for func in funcs:
                self.assertIs(func, rt._floatit)
            firstline = next(linetupler)
            for value in firstline:
                self.assertIsInstance(value, float)
            self.assertEqual(len(firstline), numvals)
            secondline = next(linetupler)
            for value in secondline:
                self.assertIsInstance(value, float)
            self.assertEqual(len(secondline), numvals)

    def test_MesA1(self):
        numvals = 7             # last due to trailing delimiter
        with open('../testdata/MesA1.csv') as fo:
            for i in range(23):
                fo.readline()
            linetupler = rt.linetuples(fo, delimiter=';')
            funcs = next(linetupler)
            self.assertEqual(len(funcs), numvals)
            for func in funcs[:-1]:
                self.assertIs(func, float)
            firstline = next(linetupler)
            for value in firstline[:-1]:
                self.assertIsInstance(value, float)
            self.assertEqual(len(firstline), numvals)
            secondline = next(linetupler)
            for value in secondline[:-1]:
                self.assertIsInstance(value, float)
            self.assertEqual(len(secondline), numvals)
            self.assertEqual(secondline[-1], '')

    def test_onecolumn(self):
        numvals = 1
        with open('../testdata/onecolumn') as fo:
            linetupler = rt.linetuples(fo)
            funcs = next(linetupler)
            self.assertEqual(len(funcs), numvals)
            for func in funcs:
                self.assertIs(func, float)

            for tup, should in zip(linetupler, range(1, 13)):
                self.assertEqual(tup[-1], should)

            self.assertEqual(tup[0], 12)

    def test_sampledat1(self):
        numvals = 7
        with open('../testdata/sampledat1.txt') as fo:
            for i in range(1):
                fo.readline()
            linetupler = rt.linetuples(fo)
            funcs = next(linetupler)
            self.assertEqual(len(funcs), numvals)
            for func in funcs:
                self.assertIs(func, float)
            firstline = next(linetupler)
            for value in firstline:
                self.assertIsInstance(value, float)
            self.assertEqual(len(firstline), numvals)
            secondline = next(linetupler)
            for value in secondline:
                self.assertIsInstance(value, float)
            self.assertEqual(len(secondline), numvals)

    def test_sampledat1_names(self):
        numvals = 7
        names = ('RPT', 'B_CACT', 'P_CACT', 'VG_STOP',
                 'AR_BST', 'PLRT_1', 'TOQ_BUM')
        with open('../testdata/sampledat1.txt') as fo:
            linetupler = rt.linetuples(fo, names=True)
            funcs = next(linetupler)
            self.assertEqual(len(funcs), numvals)
            for name, should in zip(next(linetupler), names):
                self.assertEqual(name, should)
            self.assertEqual(name, names[-1])
            for func in funcs:
                self.assertIs(func, float)
            firstline = next(linetupler)
            for value in firstline:
                self.assertIsInstance(value, float)
            self.assertEqual(len(firstline), numvals)
            secondline = next(linetupler)
            for value in secondline:
                self.assertIsInstance(value, float)
            self.assertEqual(len(secondline), numvals)

    def test_usecols(self):

        sio = io.StringIO(datstring_comma)

        for i in range(5):
            sio.readline()

        linetupler = rt.linetuples(sio, usecols=(0, 1, 3), delimiter=',')
        next(linetupler)        # consume the funcs
        line1should = (0, 23, 0.3)
        line2should = (1, 21, 0.28)
        for i, val in enumerate(next(linetupler)):
            self.assertEqual(val, line1should[i])

        for i, val in enumerate(next(linetupler)):
            self.assertEqual(val, line2should[i])

    def test_converters(self):

        sio = io.StringIO(datstring_comma)

        for i in range(5):
            sio.readline()

        linetupler = rt.linetuples(sio, converters={0: int, 1: int},
                                   delimiter=',')
        next(linetupler)        # consume the funcs
        line1 = next(linetupler)
        line2 = next(linetupler)
        self.assertIsInstance(line1[0], int)
        self.assertIsInstance(line1[1], int)
        self.assertIsInstance(line2[0], int)
        self.assertIsInstance(line2[1], int)

    def test_stripstrings_false(self):

        sio = io.StringIO(datstring_comma)

        for i in range(5):
            sio.readline()

        linetupler = rt.linetuples(sio, stripstrings=False, delimiter=',')
        next(linetupler)        # consume the funcs
        line1 = next(linetupler)
        line2 = next(linetupler)
        self.assertEqual(line1[2], ' on')
        self.assertEqual(line2[2], ' off')

    def test_stripstrings_true(self):

        sio = io.StringIO(datstring_comma)

        for i in range(5):
            sio.readline()

        linetupler = rt.linetuples(sio, stripstrings=True, delimiter=',')
        next(linetupler)        # consume the funcs
        line1 = next(linetupler)
        line2 = next(linetupler)
        self.assertEqual(line1[2], 'on')
        self.assertEqual(line2[2], 'off')


class TestTextPack(unittest.TestCase):
    pass
