# -*- coding: utf-8 -*-
from __future__ import print_function
import unittest
import sys
import os
import io
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

import numpy as np

pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, pardir)

import channelpack.readtext as rt
import channelpack as cp

print('Testing readtext module:', rt)
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

    def test__floatit_bytes_comma(self):
        self.assertIsInstance(rt._floatit_bytes(b',12'), float)
        self.assertEqual(rt._floatit_bytes(b',12'), 0.12)
        self.assertEqual(rt._floatit_bytes(b'3,14'), 3.14)
        self.assertEqual(rt._floatit_bytes(b'314,'), 314.0)

    def test__floatit_bytes_dot(self):
        self.assertEqual(rt._floatit_bytes(b'3.14'), 3.14)
        self.assertEqual(rt._floatit_bytes(b'314.'), 314.0)

    def test_floatits_missing(self):
        self.assertTrue(np.isnan(rt._floatit('')))
        self.assertTrue(np.isnan(rt._floatit_bytes(b'')))

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


onecolumnheader = u"""\
A
1.2
1.27
1.22
"""


class TestPreParse(unittest.TestCase):
    """Test the preparse function."""

    def setUp(self):
        self.maxDiff = None

    def readlines(self, f, cnt):
        """Read cnt lines from file f and return the lines.

        f is a file name string"""

        with io.open(f) as fo:
            return fo.readlines()[:cnt]

    def test_onecolumnheader(self):
        sio = io.StringIO(onecolumnheader)
        lines = sio.readlines()
        expected = {'skiprows': 1, 'delimiter': None, 'converters': None,
                    'names': {0: 'A'}, 'usecols': (0,)}
        self.assertEqual(rt.preparse(lines), expected)

    def test_dat_0000(self):
        expected = {'names': {0: 'Time [s]',
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
        expected = {'names': {0: 'Time_100Hz',
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
        expected = {'names': {0: 'RPT',
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
        self.assertEqual(rt.preparse(lines), expected)

    def test_loremipsum(self):
        expected = {}
        lines = self.readlines('../testdata/loremipsum', 25)
        self.assertEqual(rt.preparse(lines), expected)

    def test_loremipsum_numsend(self):
        expected = {'names': {0: 'molestie',
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
        expected = {'names': {0: 'col0',
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
        expected = {'names': {},
                    'converters': None,
                    'delimiter': None,
                    'skiprows': 0,
                    'usecols': (0,)}
        lines = self.readlines('../testdata/onecolumn', 5)
        self.assertEqual(rt.preparse(lines), expected)


datstring_comma = \
    u"""date: 20-05-01 17:39
room: east lab hall, floor 2, room 8
operator: Goran Operatorsson

time, speed, onoff, distance
0, 23, on, 0.3
1, 21, off, 0.28
"""

datstring_ru = \
    u"""дата: 20-05-01 17:39
комната: восточный лабораторный зал, этаж 2, комната 8
оператор: Горан Операторссон

время, скорость, onoff, расстояние
0, 23, вкл, 0.3
1, 21, выкл, 0.28
"""
encoding_ru = 'cp866'

datstring_space_f2missing = \
    u"""0 23 0.3
1  0.28
2 21.5 0.27
"""

datstring_space_blanks = \
    u"""0 23 0.3

1 22.1 0.28
2 21.5 0.27


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
                self.assertEqual(func.__name__, 'maybenan')
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
                self.assertEqual(func.__name__, 'maybenan')

            for tup, should in zip_longest(linetupler, range(1, 13)):
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
                self.assertEqual(func.__name__, 'maybenan')
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
            linetupler = rt.linetuples(fo, hasnames=True)
            funcs = next(linetupler)
            self.assertEqual(len(funcs), numvals)
            for name, should in zip_longest(next(linetupler), names):
                self.assertEqual(name, should)
            self.assertEqual(name, names[-1])
            for func in funcs:
                self.assertEqual(func.__name__, 'maybenan')
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

    def test_dat_0000(self):
        fname = '../testdata/dat_0000.txt'
        pack = rt.textpack(fname, skiprows=11)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack.fn, fname)
        self.assertEqual(pack(0)[-1], 31.175)
        self.assertEqual(pack(2)[-1], 11.835044)

    def test_MesA1(self):
        fname = '../testdata/MesA1.csv'
        pack = rt.textpack(fname, skiprows=23, delimiter=';')
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack.fn, fname)
        self.assertEqual(pack(0)[-1], 176.64000000)
        self.assertEqual(pack(2)[-1], 0.07213194)
        self.assertEqual(pack(6)[0], '')  # due to trailing delim

    def test_MesA1_usecols(self):
        fname = '../testdata/MesA1.csv'
        pack = rt.textpack(fname, skiprows=23, delimiter=';', usecols=range(6))
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack.fn, fname)
        self.assertEqual(pack(0)[-1], 176.64000000)
        self.assertEqual(pack(2)[-1], 0.07213194)
        self.assertRaises(KeyError, pack, 6)

    def test_onecolumn(self):
        fname = '../testdata/onecolumn'
        pack = rt.textpack(fname)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack.fn, fname)
        self.assertEqual(pack(0)[0], 1.0)
        self.assertEqual(pack(0)[-1], 12.0)

    def test_sampledat1(self):
        fname = '../testdata/sampledat1.txt'
        pack = rt.textpack(fname, skiprows=1)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack.fn, fname)
        self.assertEqual(pack(0)[0], 0)
        self.assertEqual(pack(6)[-1], 20.285)

    def test_sampledat1_names(self):
        fname = '../testdata/sampledat1.txt'
        pack = rt.textpack(fname, skiprows=1, hasnames=True)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack.fn, fname)
        self.assertEqual(pack('RPT')[0], 0)
        self.assertEqual(pack('TOQ_BUM')[-1], 20.285)

    def test_datstringspace_f2missing(self):
        sio = io.StringIO(datstring_space_f2missing)
        pack = rt.textpack(sio)
        self.assertEqual(len(pack.data), 2)  # should be 3
        self.assertEqual(pack(1)[1], 0.28)  # field 3 became field 2
        self.assertEqual(pack(1)[2], 21.5)  # as expected

    def test_datstringspace_f2missing_delimspec(self):
        sio = io.StringIO(datstring_space_f2missing)
        pack = rt.textpack(sio, delimiter=' ')
        # missing value between two spaces
        self.assertTrue(np.isnan(pack(1)[1]))

    def test_datstringspace_f2missing_delimspec_converter(self):
        sio = io.StringIO(datstring_space_f2missing)

        def maybemissing(s):
            return float(s) if s else -999

        pack = rt.textpack(sio, delimiter=' ', converters={1: maybemissing})
        self.assertEqual(len(pack.data), 3)
        self.assertEqual(pack(1)[1], -999)
        self.assertEqual(pack(1)[2], 21.5)

    def test_datstring_space_blanks(self):

        sio = io.StringIO(datstring_space_blanks)
        pack = rt.textpack(sio)
        self.assertIsInstance(pack, cp.ChannelPack)
        for i in range(3):
            self.assertEqual(pack(i).size, 3)
        self.assertEqual(len(pack.data), 3)
        self.assertEqual(pack(1)[1], 22.1)

    def test_datstring_comma_names(self):

        sio = io.StringIO(datstring_comma)
        pack = rt.textpack(sio, skiprows=5, hasnames=True, delimiter=',')
        names = 'time', 'speed', 'onoff', 'distance'
        for key, name in zip_longest(sorted(pack.names), names):
            # names stripped by default
            self.assertEqual(pack.name(key), name)

        for val, should in zip_longest(pack('onoff'), (' on', ' off')):
            self.assertEqual(val, should)

        for val, should in zip_longest(pack('distance'), (0.3, 0.28)):
            self.assertEqual(val, should)

    def test_datstring_comma_stripstrings(self):

        sio = io.StringIO(datstring_comma)
        pack = rt.textpack(sio, skiprows=5, hasnames=True, delimiter=',',
                           stripstrings=True)
        names = 'time', 'speed', 'onoff', 'distance'
        for key, name in zip_longest(sorted(pack.names), names):
            # names stripped by default
            self.assertEqual(pack.name(key), name)

        for val, should in zip_longest(pack('onoff'), ('on', 'off')):
            self.assertEqual(val, should)

        for val, should in zip_longest(pack('distance'), (0.3, 0.28)):
            self.assertEqual(val, should)

    def test_datstring_comma_asbytes(self):

        bio = io.BytesIO(datstring_comma.encode('latin1'))
        pack = rt.textpack(bio, skiprows=5, delimiter=b',')

        for val, should in zip_longest(pack(2), (b' on', b' off')):
            self.assertEqual(val, should)

        for val, should in zip_longest(pack(3), (0.3, 0.28)):
            self.assertEqual(val, should)

    def test_datstring_comma_asbytes_stripstrings(self):

        bio = io.BytesIO(datstring_comma.encode('latin1'))
        pack = rt.textpack(bio, skiprows=5, delimiter=b',',
                           stripstrings=True)

        for val, should in zip_longest(pack(2), (b'on', b'off')):
            self.assertEqual(val, should)

        for val, should in zip_longest(pack(3), (0.3, 0.28)):
            self.assertEqual(val, should)

    def test_datstring_comma_asbytes_decoded(self):

        bio = io.BytesIO(datstring_comma.encode('latin1'))
        pack = rt.textpack(bio, skiprows=5, delimiter=b',', encoding='latin1')

        for val, should in zip_longest(pack(2), (' on', ' off')):
            self.assertEqual(val, should)

        for val, should in zip_longest(pack(3), (0.3, 0.28)):
            self.assertEqual(val, should)

    def test_datstring_comma_cp866(self):

        bio = io.BytesIO(datstring_ru.encode('cp866'))
        pack = rt.textpack(bio, skiprows=5, delimiter=b',')

        for val, should in zip_longest(pack(3), (0.3, 0.28)):
            self.assertEqual(val, should)

    def test_datstring_comma_cp866_decode(self):

        bio = io.BytesIO(datstring_ru.encode('cp866'))
        pack = rt.textpack(bio, skiprows=5, delimiter=b',', encoding='cp866')

        for val, should in zip_longest(pack(2), (u' вкл', u' выкл')):
            self.assertEqual(val, should)

        for val, should in zip_longest(pack(3), (0.3, 0.28)):
            self.assertEqual(val, should)

    def test_datstring_comma_cp866_decode_names(self):

        bio = io.BytesIO(datstring_ru.encode('cp866'))
        pack = rt.textpack(bio, skiprows=5, delimiter=b',',
                           encoding='cp866', hasnames=True)

        for val, should in zip_longest(pack(u'onoff'), (u' вкл', u' выкл')):
            self.assertEqual(val, should)

        for val, should in zip_longest(pack(u'расстояние'), (0.3, 0.28)):
            self.assertEqual(val, should)


class TestTextPackLazy(unittest.TestCase):

    def test_dat_0000(self):
        fname = '../testdata/dat_0000.txt'
        pack = rt.lazy_textpack(fname)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack.fn, fname)
        self.assertEqual(pack(0)[-1], 31.175)
        self.assertEqual(pack(2)[-1], 11.835044)
        self.assertEqual(len(pack.data), 4)
        names = ('Time [s]', 'Quantity1 - 12345678;  [qunit]',
                 'Distance - 12345678;  [mm]',
                 'Stresslevel& - 12345678;  [kLevel]')
        for key, should in zip_longest(sorted(pack.data), names):
            self.assertEqual(pack.name(key), should)

    def test_MesA1(self):
        fname = '../testdata/MesA1.csv'
        pack = rt.lazy_textpack(fname)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack.fn, fname)
        self.assertEqual(pack(0)[-1], 176.64000000)
        self.assertEqual(pack(2)[-1], 0.07213194)
        self.assertEqual(len(pack.data), 6)
        names = ('Time_100Hz', 'P_cyl', 'F_cyl', 'L_cyl', 'Fc1_cal', 'Fc2_cal')
        for key, should in zip_longest(sorted(pack.data), names):
            self.assertEqual(pack.name(key), should)

    def test_MesA1_usecols(self):
        fname = '../testdata/MesA1.csv'
        pack = rt.lazy_textpack(fname, usecols=(0, 2, 5))
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack.fn, fname)
        self.assertEqual(pack(0)[-1], 176.64000000)
        self.assertEqual(pack(2)[-1], 0.07213194)
        self.assertEqual(len(pack.data), 3)
        self.assertRaises(KeyError, pack, 1)
        self.assertRaises(KeyError, pack, 3)
        self.assertRaises(KeyError, pack, 4)
        names = ('Time_100Hz', 'F_cyl', 'Fc2_cal')
        for key, should in zip_longest(sorted(pack.data), names):
            self.assertEqual(pack.name(key), should)

    def test_MesA1_names(self):
        fname = '../testdata/MesA1.csv'
        names = {0: 'names', 2: 'fcyl', 5: 'fc2'}
        pack = rt.lazy_textpack(fname, names=names)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack.fn, fname)
        self.assertEqual(pack(0)[-1], 176.64000000)
        self.assertEqual(pack(2)[-1], 0.07213194)
        self.assertEqual(len(pack.data), 3)
        self.assertRaises(KeyError, pack, 1)
        self.assertRaises(KeyError, pack, 3)
        self.assertRaises(KeyError, pack, 4)
        for key in pack.data:
            self.assertEqual(pack.name(key), names[key])

    def test_orgtable(self):
        fname = '../testdata/orgtable.txt'
        pack = rt.lazy_textpack(fname, delimiter='|', hasnames=True,
                                encoding='utf8', stripstrings=True,
                                usecols=(1, 2, 3, 4))
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack.fn, fname)
        self.assertEqual(len(pack.data), 4)
        self.assertEqual(pack('Kod')[-1], 2584)
        self.assertEqual(pack('Kommun')[0], u'Upplands Väsby')
        self.assertEqual(pack('qty')[-1], 64)
        self.assertEqual(pack('meanprice')[-1], 1668)

    def test_onecolumn(self):
        fname = '../testdata/onecolumn'
        pack = rt.lazy_textpack(fname)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack.fn, fname)
        self.assertEqual(len(pack.data), 1)
        self.assertEqual(pack(0)[0], 1.0)
        self.assertEqual(pack(0)[-1], 12.0)

    def test_sampledat1(self):
        fname = '../testdata/sampledat1.txt'
        pack = rt.lazy_textpack(fname)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack.fn, fname)
        self.assertEqual(len(pack.data), 7)
        self.assertEqual(pack(0)[0], 0)
        self.assertEqual(pack(6)[-1], 20.285)

    def test_sampledat1_usecols1col(self):
        fname = '../testdata/sampledat1.txt'
        pack = rt.lazy_textpack(fname, usecols=3)
        self.assertIsInstance(pack, cp.ChannelPack)
        self.assertEqual(pack.fn, fname)
        self.assertEqual(len(pack.data), 1)
        self.assertEqual(pack('VG_STOP')[0], 60.0)

    def test_datstringspace_f2missing(self):
        sio = io.StringIO(datstring_space_f2missing)
        # delimiter parses to ' ',
        pack = rt.lazy_textpack(sio)
        # missing value between two spaces
        self.assertTrue(np.isnan(pack(1)[1]))

    def test_datstringspace_f2missing_converter(self):
        sio = io.StringIO(datstring_space_f2missing)

        def maybemissing(s):
            return float(s) if s else -999

        pack = rt.lazy_textpack(sio, converters={1: maybemissing})
        self.assertEqual(len(pack.data), 3)
        self.assertEqual(pack(1)[1], -999)
        self.assertEqual(pack(1)[2], 21.5)

    def test_datstring_space_blanks(self):

        # expecting two lines of data and first line numbers as
        # names

        sio = io.StringIO(datstring_space_blanks)
        pack = rt.lazy_textpack(sio)
        self.assertIsInstance(pack, cp.ChannelPack)
        for i in range(3):
            self.assertEqual(pack(i).size, 2)
        self.assertEqual(len(pack.data), 3)
        self.assertEqual(pack(1)[0], 22.1)
        names = ('0', '23', '0.3')
        for key, should in zip_longest(sorted(pack.data), names):
            self.assertEqual(pack.name(key), should)

    def test_datstring_comma_fail(self):

        sio = io.StringIO(datstring_comma)
        with self.assertRaises(ValueError) as context:
            rt.lazy_textpack(sio)

        self.assertEqual(context.exception.args[0], 'Failed lazy preparse')

    def test_datstring_comma_provideargs(self):

        sio = io.StringIO(datstring_comma)
        pack = rt.lazy_textpack(sio, skiprows=5, delimiter=',')
        self.assertIsInstance(pack, cp.ChannelPack)
        for val, should in zip_longest(pack(2), (' on', ' off')):
            self.assertEqual(val, should)
        for val, should in zip_longest(pack(3), (0.3, 0.28)):
            self.assertEqual(val, should)

    def test_datstring_comma_stripstrings_provideargs(self):

        sio = io.StringIO(datstring_comma)
        pack = rt.lazy_textpack(sio, skiprows=5, delimiter=',',
                                stripstrings=True)

        for val, should in zip_longest(pack(2), ('on', 'off')):
            self.assertEqual(val, should)

        for val, should in zip_longest(pack(3), (0.3, 0.28)):
            self.assertEqual(val, should)

    def test_datstring_comma_asbytes_provideargs(self):

        bio = io.BytesIO(datstring_comma.encode('latin1'))
        pack = rt.lazy_textpack(bio, skiprows=5, delimiter=b',')

        for val, should in zip_longest(pack(2), (b' on', b' off')):
            self.assertEqual(val, should)

        for val, should in zip_longest(pack(3), (0.3, 0.28)):
            self.assertEqual(val, should)

    def test_datstring_comma_asbytes_stripstrings(self):

        bio = io.BytesIO(datstring_comma.encode('latin1'))
        pack = rt.lazy_textpack(bio, skiprows=5, delimiter=b',',
                                stripstrings=True)

        for val, should in zip_longest(pack(2), (b'on', b'off')):
            self.assertEqual(val, should)

        for val, should in zip_longest(pack(3), (0.3, 0.28)):
            self.assertEqual(val, should)

    def test_datstring_comma_asbytes_decoded(self):

        bio = io.BytesIO(datstring_comma.encode('latin1'))
        pack = rt.lazy_textpack(bio, skiprows=5, delimiter=b',',
                                encoding='latin1')

        for val, should in zip_longest(pack(2), (' on', ' off')):
            self.assertEqual(val, should)

        for val, should in zip_longest(pack(3), (0.3, 0.28)):
            self.assertEqual(val, should)

    def test_datstring_comma_cp866(self):

        bio = io.BytesIO(datstring_ru.encode('cp866'))
        pack = rt.lazy_textpack(bio, skiprows=5, delimiter=b',',
                                encoding='cp866')

        for val, should in zip_longest(pack(3), (0.3, 0.28)):
            self.assertEqual(val, should)

    def test_datstring_comma_cp866_decode(self):

        bio = io.BytesIO(datstring_ru.encode('cp866'))
        pack = rt.lazy_textpack(bio, skiprows=5, delimiter=b',',
                                encoding='cp866')

        for val, should in zip_longest(pack(2), (u' вкл', u' выкл')):
            self.assertEqual(val, should)

        for val, should in zip_longest(pack(3), (0.3, 0.28)):
            self.assertEqual(val, should)

    def test_datstring_comma_cp866_decode_names(self):

        bio = io.BytesIO(datstring_ru.encode('cp866'))
        pack = rt.lazy_textpack(bio, skiprows=5, delimiter=b',',
                                encoding='cp866', hasnames=True)

        for val, should in zip_longest(pack(u'onoff'), (u' вкл', u' выкл')):
            self.assertEqual(val, should)

        for val, should in zip_longest(pack(u'расстояние'), (0.3, 0.28)):
            self.assertEqual(val, should)
