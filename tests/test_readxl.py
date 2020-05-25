# -*- coding: utf-8 -*-
from __future__ import print_function
import unittest
import sys
import os
import datetime
import numpy as np
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

import xlrd

pardir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, pardir)

import channelpack.readxl as rxl

print('Testing readxl module:', rxl)
print('Testing with', unittest)
print()

dat3 = '../testdata/sampledat3.xls'
dat4 = '../testdata/sampledat4.xls'
reveng = '../testdata/reveng1.xlsx'

xl_testletters = dict(A=0, z=25, Aa=26, aZ=51, Zz=701, amJ=1023, zZz=18277)
xl_letters = dict(a=0, z=25, aa=26, az=51, zz=701, amj=1023, zzz=18277)


class TestLetter2Num(unittest.TestCase):

    def test_zbase_default(self):
        for key in xl_testletters:
            self.assertEqual(rxl.letter2num(key), xl_testletters[key])

    def test_zbase_false(self):
        for key in xl_testletters:
            self.assertEqual(rxl.letter2num(key, zbase=False),
                             xl_testletters[key] + 1)


class TestCellReference(unittest.TestCase):

    def test_noargs(self):
        cr = rxl.cellreference()
        self.assertEqual(cr.row, 0)
        self.assertEqual(cr.col, 0)

    def test_rowarg(self):
        cr = rxl.cellreference(row=3)
        self.assertEqual(cr.row, 3)
        self.assertEqual(cr.col, 0)

    def test_colarg(self):
        cr = rxl.cellreference(col=3)
        self.assertEqual(cr.row, 0)
        self.assertEqual(cr.col, 3)

    def test_rowcolarg(self):
        cr = rxl.cellreference(row=2, col=3)
        self.assertEqual(cr.row, 2)
        self.assertEqual(cr.col, 3)

    def test_xladdrarg(self):
        cr = rxl.cellreference(xladdr='zz8')
        self.assertEqual(cr.row, 7)
        self.assertEqual(cr.col, xl_letters['zz'])

    def test_xladdrarg_onlyletter(self):
        cr = rxl.cellreference(xladdr='zz')
        self.assertEqual(cr.row, 0)
        self.assertEqual(cr.col, xl_letters['zz'])

    def test_xladdrarg_onlyletter_with_row(self):
        cr = rxl.cellreference(row=2, xladdr='zz')
        self.assertEqual(cr.row, 2)
        self.assertEqual(cr.col, xl_letters['zz'])

    def test_xladdrarg_with_row_col(self):
        cr = rxl.cellreference(row=2, col=3, xladdr='zz7')
        # args row and col is ignored
        self.assertEqual(cr.row, 6)
        self.assertEqual(cr.col, xl_letters['zz'])


class TestNormalizeUsecols(unittest.TestCase):

    def test_integers(self):

        usecols = reversed(range(7))
        normalized = rxl.normalize_usecols(usecols)
        for norm, should in zip_longest(normalized, range(7)):
            self.assertEqual(norm, should)

    def test_integers_spread(self):

        usecols = (3, 1, 10, 8)
        normalized = rxl.normalize_usecols(usecols)
        for norm, should in zip_longest(normalized, (1, 3, 8, 10)):
            self.assertEqual(norm, should)

    def test_string_distinct(self):

        usecols = 'a, b,c, e'
        normalized = rxl.normalize_usecols(usecols)
        for norm, should in zip_longest(normalized, (0, 1, 2, 4)):
            self.assertEqual(norm, should)

    def test_string_ranges(self):

        usecols = 'a, b,d:f'
        normalized = rxl.normalize_usecols(usecols)
        for norm, should in zip_longest(normalized, (0, 1, 3, 4, 5)):
            self.assertEqual(norm, should)

    def test_string_ranges_unsorted(self):

        usecols = 'd:f, a, b'
        normalized = rxl.normalize_usecols(usecols)
        for norm, should in zip_longest(normalized, (0, 1, 3, 4, 5)):
            self.assertEqual(norm, should)

    def test_mix(self):
        # shall be an exception
        usecols = ('a, b', 4, 5)
        with self.assertRaises(ValueError):
            rxl.normalize_usecols(usecols)


class TestSheetColumns(unittest.TestCase):

    def test_dat3(self):
        with xlrd.open_workbook(dat3) as wb:
            sheet = wb.sheet_by_index(0)

        columner = rxl.sheet_columns(sheet, rxl.cellreference(xladdr='a1'),
                                     rxl.cellreference(xladdr='c6'),
                                     usecols=(0, 1, 2))
        col = next(columner)
        self.assertEqual(col[0], 'txtdata')
        self.assertEqual(col[-1], 'D')
        col = next(columner)
        self.assertEqual(col[0], 'nums')
        self.assertEqual(col[-1], 120.0)
        col = next(columner)
        self.assertEqual(col[0], 'floats')
        self.assertEqual(col[-1], 0.8660254037844387)

    def test_dat4(self):
        with xlrd.open_workbook(dat4) as wb:
            sheet = wb.sheet_by_index(0)

        columner = rxl.sheet_columns(sheet, rxl.cellreference(xladdr='a1'),
                                     rxl.cellreference(xladdr='d6'),
                                     usecols=(0, 1, 2, 3))
        col = next(columner)
        self.assertEqual(col[0], 'txtdata')
        self.assertEqual(col[-1], 'D')
        col = next(columner)
        self.assertEqual(col[0], 'nums')
        self.assertEqual(col[-1], 120.0)
        col = next(columner)
        self.assertEqual(col[0], 'floats')
        self.assertEqual(col[-1], 0.8660254037844387)
        col = next(columner)
        self.assertEqual(col[0], 'dates')
        self.assertEqual(col[-1], datetime.datetime(2008, 1, 16))


class TestSheetPack(unittest.TestCase):

    def test_dat3(self):
        pack = rxl.sheet_pack(dat3)

        for key, should in enumerate(('txtdata', 'nums', 'floats')):
            self.assertEqual(pack.name(key), should)

        for key in pack.data:
            self.assertEqual(len(pack(key)), 5)

        self.assertEqual(len(pack.data), 3)

        self.assertEqual(pack('nums').max(), 120)
        self.assertEqual(pack('floats').min(), 0)

    def test_dat4(self):
        pack = rxl.sheet_pack(dat4)

        for key, should in enumerate(('txtdata', 'nums', 'floats', 'dates'
                                      '', '', '')):
            self.assertEqual(pack.name(key), should)

        for key in pack.data:
            self.assertEqual(len(pack(key)), 8)

        self.assertEqual(len(pack.data), 7)

        self.assertEqual(np.nanmax(pack('nums')), 120)
        self.assertEqual(np.nanmin(pack('floats')), 0)
        self.assertEqual(pack(4)[-1], 'letters')

    def test_reveng(self):
        pack = rxl.sheet_pack(reveng)

        for key, should in enumerate(('description', 'entered',
                                      'calculated', '')):
            self.assertEqual(pack.name(key), should)

        for key in pack.data:
            self.assertEqual(len(pack(key)), 55)

        self.assertEqual(len(pack.data), 4)

        self.assertEqual(pack('description')[6], 'one')
        self.assertEqual(pack('entered')[6], 1)
        self.assertEqual(pack('calculated')[6], 1)

    def test_reveng_boolpart(self):
        pack = rxl.sheet_pack(reveng, startcell='b15', stopcell='c16',
                              header='b1')

        for key, should in zip((1, 2), ('entered', 'calculated')):
            self.assertEqual(pack.name(key), should)

        for key in pack.data:
            self.assertEqual(len(pack(key)), 2)

        self.assertEqual(len(pack.data), 2)

        self.assertIs(pack('entered')[0], np.True_)
        self.assertIs(pack('calculated')[0], np.True_)
        self.assertIs(pack('entered')[-1], np.False_)
        self.assertIs(pack('calculated')[-1], np.False_)

    def test_reveng_datepart(self):
        pack = rxl.sheet_pack(reveng, startcell='b28', stopcell='c32',
                              header='b1')

        for key, should in zip((1, 2), ('entered', 'calculated')):
            self.assertEqual(pack.name(key), should)

        for key in pack.data:
            self.assertEqual(len(pack(key)), 5)

        self.assertEqual(len(pack.data), 2)

        delta = datetime.timedelta(days=1)

        for date1, date2 in zip(pack('entered'), pack('calculated')):
            self.assertEqual(date1 + delta, date2)
