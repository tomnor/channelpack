# -*- coding: utf-8 -*-
from __future__ import print_function
import unittest
import sys
import os
import io
import datetime
import numpy as np
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, pardir)

import channelpack.dbf as dbf

print('Testing dbf module:', dbf)
print('Testing with', unittest)
print()

MESDAT2 = '../testdata/mesdat2.dbf'

mesdat2names = ['TWOLET', 'LINENO', 'WINDATE', 'TIME', 'NUM', 'ID',
                'RPT', 'SPEED', 'T1', 'P1', 'DEC', 'LOOP',
                'YESNO', 'SPEED1', 'SPEED0', 'SPEED3', 'SPEED4',
                'SPEED5', 'SLOW0', 'SLOW1', 'BTIME', 'BDIST',
                'PDEM_1', 'PACT', 'PMN', 'PMAX', 'TURN',
                'TURND_1', 'TURNSUM', 'T12', 'T2', 'T3']

mesdat2specs = [(b'C', 2, 0), (b'N', 7, 2), (b'N', 15, 9), (b'N', 9, 2),
                (b'N', 5, 2), (b'N', 5, 2), (b'N', 6, 2), (b'N', 5, 2),
                (b'N', 6, 2), (b'N', 4, 2), (b'N', 4, 2), (b'N', 4, 2),
                (b'C', 3, 0), (b'N', 6, 2), (b'N', 5, 2), (b'N', 5, 2),
                (b'N', 5, 2), (b'N', 5, 2), (b'N', 5, 3), (b'N', 5, 3),
                (b'N', 5, 2), (b'N', 6, 2), (b'N', 4, 2), (b'N', 4, 2),
                (b'N', 4, 2), (b'N', 4, 2), (b'N', 5, 3), (b'N', 5, 3),
                (b'N', 6, 3), (b'N', 6, 2), (b'N', 6, 2), (b'N', 6, 2)]

MESDAT2LEN = 4191

SIDS = '../testdata/sids.dbf'

sidsnames = ['AREA', 'PERIMETER', 'CNTY_', 'CNTY_ID', 'NAME', 'FIPS',
             'FIPSNO', 'CRESS_ID', 'BIR74', 'SID74', 'NWBIR74',
             'BIR79', 'SID79', 'NWBIR79']

sidsspecs = [(b'N', 12, 3), (b'N', 12, 3), (b'N', 11, 0), (b'N', 11, 0),
             (b'C', 32, 0), (b'C', 5, 0), (b'N', 16, 0), (b'N', 3, 0),
             (b'N', 12, 6), (b'N', 9, 6), (b'N', 11, 6), (b'N', 12, 6),
             (b'N', 9, 6), (b'N', 12, 6)]

sidsxnames = ['AREA', 'BIR79', 'NWBIR79']

sidsxspecs = [(b'N', 12, 3), (b'N', 12, 6), (b'N', 12, 6)]

SIDSLEN = 100

DBASE = '../testdata/dbase_8b.dbf'
DBASENAMES = {0: 'CHARACTER',
              1: 'NUMERICAL',
              2: 'DATE',
              3: 'LOGICAL',
              4: 'FLOAT',
              5: 'MEMO'}

DBASENAMES_SELECTION = {2: 'DATE',
                        3: 'LOGICAL',
                        4: 'FLOAT'}


class TestDbfReader(unittest.TestCase):

    def test_mesdat2_first_yield(self):
        with io.open(MESDAT2, 'rb') as fo:
            dbfrecs = dbf.dbfreader(fo)
            names = next(dbfrecs)

        for name, should in zip_longest(names, mesdat2names):
            self.assertEqual(name, should)

    def test_sids_first_yield(self):
        with io.open(SIDS, 'rb') as fo:
            dbfrecs = dbf.dbfreader(fo)
            names = next(dbfrecs)

        for name, should in zip_longest(names, sidsnames):
            self.assertEqual(name, should)

    def test_mesdat2_second_yield(self):
        with io.open(MESDAT2, 'rb') as fo:
            dbfrecs = dbf.dbfreader(fo)
            next(dbfrecs)
            specs = next(dbfrecs)

        for spec, should in zip_longest(specs, mesdat2specs):
            self.assertEqual(spec, should)

    def test_sids_second_yield(self):
        with io.open(SIDS, 'rb') as fo:
            dbfrecs = dbf.dbfreader(fo)
            next(dbfrecs)
            specs = next(dbfrecs)

        for spec, should in zip_longest(specs, sidsspecs):
            self.assertEqual(spec, should)

    def test_mesdat2_data_yields(self):
        with io.open(MESDAT2, 'rb') as fo:
            dbfrecs = dbf.dbfreader(fo)
            next(dbfrecs)
            next(dbfrecs)
            records = [record for record in dbfrecs]

        self.assertEqual(len(records), MESDAT2LEN)
        firstrec, lastrec = records[0], records[-1]
        self.assertEqual(firstrec[0], 'AV')
        self.assertEqual(firstrec[-1], 135.0)
        self.assertEqual(lastrec[0], 'AV')
        self.assertEqual(lastrec[-1], 150.0)

    def test_sids_data_yields(self):
        with io.open(SIDS, 'rb') as fo:
            dbfrecs = dbf.dbfreader(fo)
            next(dbfrecs)
            next(dbfrecs)
            records = [record for record in dbfrecs]

        self.assertEqual(len(records), SIDSLEN)
        firstrec, lastrec = records[0], records[-1]
        self.assertEqual(firstrec[0], 0.114)
        self.assertEqual(firstrec[-1], 19.0)
        self.assertEqual(lastrec[0], 0.212)
        self.assertEqual(lastrec[-1], 841.0)

        self.assertEqual(lastrec[2], 2241)
        self.assertIsInstance(lastrec[2], int)


class TestDbfRecords(unittest.TestCase):

    def test_mesdat2_first_yield(self):
        with io.open(MESDAT2, 'rb') as fo:
            dbfrecs = dbf.dbfrecords(fo, mesdat2names)
            names = next(dbfrecs)

        for name, should in zip_longest(names, mesdat2names):
            self.assertEqual(name, should)

    def test_sids_first_yield(self):
        with io.open(SIDS, 'rb') as fo:
            dbfrecs = dbf.dbfrecords(fo, sidsnames)
            names = next(dbfrecs)

        for name, should in zip_longest(names, sidsnames):
            self.assertEqual(name, should)

    def test_sids_first_yield_xnames(self):
        with io.open(SIDS, 'rb') as fo:
            dbfrecs = dbf.dbfrecords(fo, sidsxnames)
            names = next(dbfrecs)

        for name, should in zip_longest(names, sidsxnames):
            self.assertEqual(name, should)

    def test_mesdat2_second_yield(self):
        with io.open(MESDAT2, 'rb') as fo:
            dbfrecs = dbf.dbfrecords(fo, mesdat2names)
            next(dbfrecs)
            specs = next(dbfrecs)

        for spec, should in zip_longest(specs, mesdat2specs):
            self.assertEqual(spec, should)

    def test_sids_second_yield(self):
        with io.open(SIDS, 'rb') as fo:
            dbfrecs = dbf.dbfrecords(fo, sidsnames)
            next(dbfrecs)
            specs = next(dbfrecs)

        for spec, should in zip_longest(specs, sidsspecs):
            self.assertEqual(spec, should)

    def test_sids_second_yield_xnames(self):
        with io.open(SIDS, 'rb') as fo:
            dbfrecs = dbf.dbfrecords(fo, sidsxnames)
            next(dbfrecs)
            specs = next(dbfrecs)

        for spec, should in zip_longest(specs, sidsxspecs):
            self.assertEqual(spec, should)

    def test_mesdat2_data_yields(self):
        with io.open(MESDAT2, 'rb') as fo:
            dbfrecs = dbf.dbfrecords(fo, mesdat2names)
            next(dbfrecs)
            next(dbfrecs)
            records = [record for record in dbfrecs]

        self.assertEqual(len(records), MESDAT2LEN)
        firstrec, lastrec = records[0], records[-1]
        self.assertEqual(firstrec[0], 'AV')
        self.assertEqual(firstrec[-1], 135.0)
        self.assertEqual(lastrec[0], 'AV')
        self.assertEqual(lastrec[-1], 150.0)

    def test_sids_data_yields(self):
        with io.open(SIDS, 'rb') as fo:
            dbfrecs = dbf.dbfrecords(fo, sidsnames)
            next(dbfrecs)
            next(dbfrecs)
            records = [record for record in dbfrecs]

        self.assertEqual(len(records), SIDSLEN)
        firstrec, lastrec = records[0], records[-1]
        self.assertEqual(firstrec[0], 0.114)
        self.assertEqual(firstrec[-1], 19.0)
        self.assertEqual(lastrec[0], 0.212)
        self.assertEqual(lastrec[-1], 841.0)

        self.assertEqual(lastrec[2], 2241)
        self.assertIsInstance(lastrec[2], int)

    def test_sids_data_yields_xnames(self):
        with io.open(SIDS, 'rb') as fo:
            dbfrecs = dbf.dbfrecords(fo, sidsxnames)
            next(dbfrecs)
            next(dbfrecs)
            records = [record for record in dbfrecs]

        self.assertEqual(len(records), SIDSLEN)
        firstrec, lastrec = records[0], records[-1]
        self.assertEqual(firstrec[0], 0.114)
        self.assertEqual(firstrec[-2], 1364.0)
        self.assertEqual(firstrec[-1], 19.0)
        self.assertEqual(lastrec[0], 0.212)
        self.assertEqual(lastrec[-2], 2655.0)
        self.assertEqual(lastrec[-1], 841.0)


class TestDbfPack(unittest.TestCase):

    def test_mesdat2(self):
        pack = dbf.dbfpack(MESDAT2)
        self.assertEqual(pack(0).size, MESDAT2LEN)

        for i in pack.data:
            self.assertIsInstance(pack(i), np.ndarray)
            self.assertEqual(pack.name(i), mesdat2names[i])

        self.assertEqual(pack('TWOLET')[0], 'AV')
        self.assertEqual(pack('T3')[0], 135.0)
        self.assertEqual(pack('TWOLET')[-1], 'AV')
        self.assertEqual(pack('T3')[-1], 150.0)

    def test_sids(self):
        pack = dbf.dbfpack(SIDS)
        self.assertEqual(pack(0).size, SIDSLEN)

        for i in pack.data:
            self.assertIsInstance(pack(i), np.ndarray)
            self.assertEqual(pack.name(i), sidsnames[i])

        self.assertEqual(pack('AREA')[0], 0.114)
        self.assertEqual(pack('NWBIR79')[0], 19.0)
        self.assertEqual(pack('AREA')[-1], 0.212)
        self.assertEqual(pack('NWBIR79')[-1], 841.0)

        self.assertEqual(pack('CNTY_')[-1], 2241)

    def test_sids_names(self):
        pack = dbf.dbfpack(SIDS, sidsxnames)
        self.assertEqual(pack('AREA').size, SIDSLEN)
        self.assertEqual(len(pack.data), 3)

        for name in sidsxnames:
            self.assertIn(name, pack.names.values())

        for i in pack.data:
            self.assertIsInstance(pack(i), np.ndarray)
            # column number retained in pack (sidsnames w/o x)
            self.assertEqual(pack.name(i), sidsnames[i])

        self.assertEqual(pack('AREA')[0], 0.114)
        self.assertEqual(pack('NWBIR79')[0], 19.0)
        self.assertEqual(pack('AREA')[-1], 0.212)
        self.assertEqual(pack('NWBIR79')[-1], 841.0)

    def test_sids_names_openfile(self):

        with io.open(SIDS, 'rb') as fo:
            pack = dbf.dbfpack(fo, sidsxnames)

        self.assertEqual(pack('AREA').size, SIDSLEN)
        self.assertEqual(len(pack.data), 3)

        for name in sidsxnames:
            self.assertIn(name, pack.names.values())

        for i in pack.data:
            self.assertIsInstance(pack(i), np.ndarray)
            # column number retained in pack (sidsnames w/o x)
            self.assertEqual(pack.name(i), sidsnames[i])

        self.assertEqual(pack('AREA')[0], 0.114)
        self.assertEqual(pack('NWBIR79')[0], 19.0)
        self.assertEqual(pack('AREA')[-1], 0.212)
        self.assertEqual(pack('NWBIR79')[-1], 841.0)

    def test_dbase_8b(self):

        pack = dbf.dbfpack(DBASE)

        for letter, should in zip_longest(pack('LOGICAL'),
                                          ['T', 'T', '?', '?', '?', '?', '?',
                                           '?', '?', '?']):
            self.assertEqual(letter, should)

        self.assertEqual(pack.names, DBASENAMES)
        self.assertEqual(pack('DATE')[0], datetime.date(1970, 1, 1))
        self.assertEqual(pack('DATE')[-1], None)

    def test_dbase_8b_names(self):

        pack = dbf.dbfpack(DBASE, DBASENAMES_SELECTION.values())
        self.assertEqual(pack.names, DBASENAMES_SELECTION)
        self.assertTrue(np.isnan(pack('FLOAT')[-2]))
        self.assertEqual(pack('FLOAT')[-1], 0.1)
