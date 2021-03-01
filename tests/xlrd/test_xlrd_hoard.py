# -*- coding: utf-8 -*-

# Collection of tests copied from the xlrd project, modified by
# channelpack.

# Code in this file was collected and merged from the following files
# from the xlrd/tests directory (with some possible copyright
# mentioned in them) from commit d470bc9374ee3a1cf149c2bab0684e63c1dcc575

# test_alt_sharedstrings_loc.py -- portions (C) 2010, Manfred Moitzi BSD
# test_biffh.py
# test_cell.py -- portions (C) 2010, Manfred Moitzi BSD
# test_formats.py -- portions (C) 2010, Manfred Moitzi BSD
# test_formulas.py -- portions (C) 2010, Manfred Moitzi BSD
# test_ignore_workbook_corruption_error.py
# test_missing_records.py
# test_open_workbook.py
# test_sheet.py -- portions (C) 2010, Manfred Moitzi BSD
# test_workbook.py -- portions (C) 2010, Manfred Moitzi BSD
# test_xldate.py -- portions (C) 2010, Manfred Moitzi BSD
# test_xldate_to_datetime.py
# test_xlsx_comments.py
# test_xlsx_parse.py

import sys
from unittest import TestCase
import unittest
import os
import shutil
import tempfile
import types
from datetime import datetime

parpardir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         os.pardir, os.pardir))
sys.path.insert(0, parpardir)

from channelpack import xlrd
from channelpack.xlrd import open_workbook
from channelpack.xlrd.book import Book
from channelpack.xlrd.sheet import Sheet
from channelpack.xlrd import biffh
from channelpack.xlrd.timemachine import UNICODE_LITERAL
from channelpack.xlrd.biffh import XL_CELL_TEXT
from channelpack.xlrd import xldate
from channelpack.xlrd.timemachine import xrange

print('Testing xlrd package:', xlrd)


def datafile(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'data', filename)



### test_alt_sharedstrings_loc.py


class TestSharedStringsAltLocation(TestCase):

    def setUp(self):
        self.book = open_workbook(datafile('sharedstrings_alt_location.xlsx'))

    def test_open_workbook(self):
        # Without the handling of the alternate location for the sharedStrings.xml file, this would pop.
        self.assertTrue(isinstance(self.book, Book))


### test_biffh.py

if sys.version_info[0] >= 3:
    from io import StringIO
else:
    # Python 2.6+ does have the io module, but io.StringIO is strict about
    # unicode, which won't work for our test.
    from StringIO import StringIO


class TestHexDump(unittest.TestCase):
    def test_hex_char_dump(self):
        sio = StringIO()
        biffh.hex_char_dump(b"abc\0e\01", 0, 6, fout=sio)
        s = sio.getvalue()
        assert "61 62 63 00 65 01" in s, s
        assert "abc~e?" in s, s



### test_cell.py

class TestCell(unittest.TestCase):

    def setUp(self):
        self.book = xlrd.open_workbook(datafile('profiles.xls'), formatting_info=True)
        self.sheet = self.book.sheet_by_name('PROFILEDEF')

    def test_empty_cell(self):
        sheet = self.book.sheet_by_name('TRAVERSALCHAINAGE')
        cell = sheet.cell(0, 0)
        self.assertEqual(cell.ctype, xlrd.book.XL_CELL_EMPTY)
        self.assertEqual(cell.value, '')
        self.assertEqual(type(cell.value), type(UNICODE_LITERAL('')))
        self.assertTrue(cell.xf_index > 0)

    def test_string_cell(self):
        cell = self.sheet.cell(0, 0)
        self.assertEqual(cell.ctype, xlrd.book.XL_CELL_TEXT)
        self.assertEqual(cell.value, 'PROFIL')
        self.assertEqual(type(cell.value), type(UNICODE_LITERAL('')))
        self.assertTrue(cell.xf_index > 0)

    def test_number_cell(self):
        cell = self.sheet.cell(1, 1)
        self.assertEqual(cell.ctype, xlrd.book.XL_CELL_NUMBER)
        self.assertEqual(cell.value, 100)
        self.assertTrue(cell.xf_index > 0)

    def test_calculated_cell(self):
        sheet2 = self.book.sheet_by_name('PROFILELEVELS')
        cell = sheet2.cell(1, 3)
        self.assertEqual(cell.ctype, xlrd.book.XL_CELL_NUMBER)
        self.assertAlmostEqual(cell.value, 265.131, places=3)
        self.assertTrue(cell.xf_index > 0)

    def test_merged_cells(self):
        book = xlrd.open_workbook(datafile('xf_class.xls'), formatting_info=True)
        sheet3 = book.sheet_by_name('table2')
        row_lo, row_hi, col_lo, col_hi = sheet3.merged_cells[0]
        self.assertEqual(sheet3.cell(row_lo, col_lo).value, 'MERGED')
        self.assertEqual((row_lo, row_hi, col_lo, col_hi), (3, 7, 2, 5))

    def test_merged_cells_xlsx(self):
        book = xlrd.open_workbook(datafile('merged_cells.xlsx'))

        sheet1 = book.sheet_by_name('Sheet1')
        expected = []
        got = sheet1.merged_cells
        self.assertEqual(expected, got)

        sheet2 = book.sheet_by_name('Sheet2')
        expected = [(0, 1, 0, 2)]
        got = sheet2.merged_cells
        self.assertEqual(expected, got)

        sheet3 = book.sheet_by_name('Sheet3')
        expected = [(0, 1, 0, 2), (0, 1, 2, 4), (1, 4, 0, 2), (1, 9, 2, 4)]
        got = sheet3.merged_cells
        self.assertEqual(expected, got)

        sheet4 = book.sheet_by_name('Sheet4')
        expected = [(0, 1, 0, 2), (2, 20, 0, 1), (1, 6, 2, 5)]
        got = sheet4.merged_cells
        self.assertEqual(expected, got)


### test_formats.py

if sys.version_info[0] >= 3:
    def ucode(s): return s
else:
    def ucode(s):
        return s.decode('utf-8')


class TestCellContent(TestCase):

    def setUp(self):
        self.book = xlrd.open_workbook(datafile('Formate.xls'), formatting_info=True)
        self.sheet = self.book.sheet_by_name(ucode('Blätt1'))

    def test_text_cells(self):
        for row, name in enumerate([ucode('Huber'), ucode('Äcker'), ucode('Öcker')]):
            cell = self.sheet.cell(row, 0)
            self.assertEqual(cell.ctype, xlrd.book.XL_CELL_TEXT)
            self.assertEqual(cell.value, name)
            self.assertTrue(cell.xf_index > 0)

    def test_date_cells(self):
        # see also 'Dates in Excel spreadsheets' in the documentation
        # convert: xldate_as_tuple(float, book.datemode) -> (year, month,
        # day, hour, minutes, seconds)
        for row, date in [(0, 2741.), (1, 38406.), (2, 32266.)]:
            cell = self.sheet.cell(row, 1)
            self.assertEqual(cell.ctype, xlrd.book.XL_CELL_DATE)
            self.assertEqual(cell.value, date)
            self.assertTrue(cell.xf_index > 0)

    def test_time_cells(self):
        # see also 'Dates in Excel spreadsheets' in the documentation
        # convert: xldate_as_tuple(float, book.datemode) -> (year, month,
        # day, hour, minutes, seconds)
        for row, time in [(3, .273611), (4, .538889), (5, .741123)]:
            cell = self.sheet.cell(row, 1)
            self.assertEqual(cell.ctype, xlrd.book.XL_CELL_DATE)
            self.assertAlmostEqual(cell.value, time, places=6)
            self.assertTrue(cell.xf_index > 0)

    def test_percent_cells(self):
        for row, time in [(6, .974), (7, .124)]:
            cell = self.sheet.cell(row, 1)
            self.assertEqual(cell.ctype, xlrd.book.XL_CELL_NUMBER)
            self.assertAlmostEqual(cell.value, time, places=3)
            self.assertTrue(cell.xf_index > 0)

    def test_currency_cells(self):
        for row, time in [(8, 1000.30), (9, 1.20)]:
            cell = self.sheet.cell(row, 1)
            self.assertEqual(cell.ctype, xlrd.book.XL_CELL_NUMBER)
            self.assertAlmostEqual(cell.value, time, places=2)
            self.assertTrue(cell.xf_index > 0)

    def test_get_from_merged_cell(self):
        sheet = self.book.sheet_by_name(ucode('ÖÄÜ'))
        cell = sheet.cell(2, 2)
        self.assertEqual(cell.ctype, xlrd.book.XL_CELL_TEXT)
        self.assertEqual(cell.value, 'MERGED CELLS')
        self.assertTrue(cell.xf_index > 0)

    def test_ignore_diagram(self):
        sheet = self.book.sheet_by_name(ucode('Blätt3'))
        cell = sheet.cell(0, 0)
        self.assertEqual(cell.ctype, xlrd.book.XL_CELL_NUMBER)
        self.assertEqual(cell.value, 100)
        self.assertTrue(cell.xf_index > 0)


### test_formulas.py

try:
    ascii
except NameError:
    # For Python 2
    def ascii(s):
        a = repr(s)
        if a.startswith(('u"', "u'")):
            a = a[1:]
        return a


class TestFormulas(TestCase):

    def setUp(self):
        book = xlrd.open_workbook(datafile('formula_test_sjmachin.xls'))
        self.sheet = book.sheet_by_index(0)

    def get_value(self, col, row):
        return ascii(self.sheet.col_values(col)[row])

    def test_cell_B2(self):
        self.assertEqual(
            self.get_value(1, 1),
            r"'\u041c\u041e\u0421\u041a\u0412\u0410 \u041c\u043e\u0441\u043a\u0432\u0430'",
        )

    def test_cell_B3(self):
        self.assertEqual(self.get_value(1, 2), '0.14285714285714285')

    def test_cell_B4(self):
        self.assertEqual(self.get_value(1, 3), "'ABCDEF'")

    def test_cell_B5(self):
        self.assertEqual(self.get_value(1, 4), "''")

    def test_cell_B6(self):
        self.assertEqual(self.get_value(1, 5), '1')

    def test_cell_B7(self):
        self.assertEqual(self.get_value(1, 6), '7')

    def test_cell_B8(self):
        self.assertEqual(
            self.get_value(1, 7),
            r"'\u041c\u041e\u0421\u041a\u0412\u0410 \u041c\u043e\u0441\u043a\u0432\u0430'",
        )

class TestNameFormulas(TestCase):

    def setUp(self):
        book = xlrd.open_workbook(datafile('formula_test_names.xls'))
        self.sheet = book.sheet_by_index(0)

    def get_value(self, col, row):
        return ascii(self.sheet.col_values(col)[row])

    def test_unaryop(self):
        self.assertEqual(self.get_value(1, 1), '-7.0')

    def test_attrsum(self):
        self.assertEqual(self.get_value(1, 2), '4.0')

    def test_func(self):
        self.assertEqual(self.get_value(1, 3), '6.0')

    def test_func_var_args(self):
        self.assertEqual(self.get_value(1, 4), '3.0')

    def test_if(self):
        self.assertEqual(self.get_value(1, 5), "'b'")

    def test_choose(self):
        self.assertEqual(self.get_value(1, 6), "'C'")



### test_ignore_workbook_corruption_error.py

class TestIgnoreWorkbookCorruption(TestCase):

    def test_not_corrupted(self):
        with self.assertRaises(Exception) as context:
            xlrd.open_workbook(datafile('corrupted_error.xls'))
        self.assertTrue('Workbook corruption' in str(context.exception))

        xlrd.open_workbook(datafile('corrupted_error.xls'),
                           ignore_workbook_corruption=True)



### test_missing_records.py

class TestMissingRecords(TestCase):

    def setUp(self):
        path = datafile('biff4_no_format_no_window2.xls')
        self.book = open_workbook(path)
        self.sheet = self.book.sheet_by_index(0)

    def test_default_format(self):
        cell = self.sheet.cell(0, 0)
        self.assertEqual(cell.ctype, XL_CELL_TEXT)

    def test_default_window2_options(self):
        self.assertEqual(self.sheet.cached_page_break_preview_mag_factor, 0)
        self.assertEqual(self.sheet.cached_normal_view_mag_factor, 0)


### test_open_workbook.py

class TestOpen(TestCase):
    # test different uses of open_workbook

    def test_names_demo(self):
        # For now, we just check this doesn't raise an error.
        open_workbook(
            datafile(datafile('namesdemo.xls')),
        )

    def test_tilde_path_expansion(self):
        with tempfile.NamedTemporaryFile(suffix='.xlsx', dir=os.path.expanduser('~')) as fp:
            shutil.copyfile(datafile('text_bar.xlsx'), fp.name)
            # For now, we just check this doesn't raise an error.
            open_workbook(os.path.join('~', os.path.basename(fp.name)))

    def test_ragged_rows_tidied_with_formatting(self):
        # For now, we just check this doesn't raise an error.
        open_workbook(datafile('issue20.xls'),
                      formatting_info=True)

    def test_BYTES_X00(self):
        # For now, we just check this doesn't raise an error.
        open_workbook(datafile('picture_in_cell.xls'),
                      formatting_info=True)

    def test_xlsx_simple(self):
        # For now, we just check this doesn't raise an error.
        open_workbook(datafile('text_bar.xlsx'))
        # we should make assertions here that data has been
        # correctly processed.

    def test_xlsx(self):
        # For now, we just check this doesn't raise an error.
        open_workbook(datafile('reveng1.xlsx'))
        # we should make assertions here that data has been
        # correctly processed.


    def test_err_cell_empty(self):
        # For cell with type "e" (error) but without inner 'val' tags
        open_workbook(datafile('err_cell_empty.xlsx'))

    def test_xlsx_lower_case_cellnames(self):
        # Check if it opens with lower cell names
        open_workbook(datafile('test_lower_case_cellnames.xlsx'))



### test_sheet.py

SHEETINDEX = 0
NROWS = 15
NCOLS = 13

ROW_ERR = NROWS + 10
COL_ERR = NCOLS + 10


class TestSheet(TestCase):

    sheetnames = ['PROFILEDEF', 'AXISDEF', 'TRAVERSALCHAINAGE',
                  'AXISDATUMLEVELS', 'PROFILELEVELS']

    def setUp(self):
        self.book = xlrd.open_workbook(datafile('profiles.xls'), formatting_info=True)

    def check_sheet_function(self, function):
        self.assertTrue(function(0, 0))
        self.assertTrue(function(NROWS-1, NCOLS-1))

    def check_sheet_function_index_error(self, function):
        self.assertRaises(IndexError, function, ROW_ERR, 0)
        self.assertRaises(IndexError, function, 0, COL_ERR)

    def check_col_slice(self, col_function):
        _slice = col_function(0, 2, NROWS-2)
        self.assertEqual(len(_slice), NROWS-4)

    def check_row_slice(self, row_function):
        _slice = row_function(0, 2, NCOLS-2)
        self.assertEqual(len(_slice), NCOLS-4)

    def test_nrows(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.assertEqual(sheet.nrows, NROWS)

    def test_ncols(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.assertEqual(sheet.ncols, NCOLS)

    def test_cell(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.assertNotEqual(xlrd.empty_cell, sheet.cell(0, 0))
        self.assertNotEqual(xlrd.empty_cell, sheet.cell(NROWS-1, NCOLS-1))

    def test_cell_error(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.check_sheet_function_index_error(sheet.cell)

    def test_cell_type(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.check_sheet_function(sheet.cell_type)

    def test_cell_type_error(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.check_sheet_function_index_error(sheet.cell_type)

    def test_cell_value(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.check_sheet_function(sheet.cell_value)

    def test_cell_value_error(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.check_sheet_function_index_error(sheet.cell_value)

    def test_cell_xf_index(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.check_sheet_function(sheet.cell_xf_index)

    def test_cell_xf_index_error(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.check_sheet_function_index_error(sheet.cell_xf_index)

    def test_col(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        col = sheet.col(0)
        self.assertEqual(len(col), NROWS)

    def test_row(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        row = sheet.row(0)
        self.assertEqual(len(row), NCOLS)

    def test_getitem_int(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        row = sheet[0]
        self.assertEqual(len(row), NCOLS)

    def test_getitem_tuple(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.assertNotEqual(xlrd.empty_cell, sheet[0, 0])
        self.assertNotEqual(xlrd.empty_cell, sheet[NROWS-1, NCOLS-1])

    def test_getitem_failure(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        with self.assertRaises(ValueError):
            sheet[0, 0, 0]

        with self.assertRaises(TypeError):
            sheet["hi"]

    def test_get_rows(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        rows = sheet.get_rows()
        self.assertTrue(isinstance(rows, types.GeneratorType), True)
        self.assertEqual(len(list(rows)), sheet.nrows)

    def test_iter(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        rows = []
        # check syntax
        for row in sheet:
            rows.append(row)
        self.assertEqual(len(rows), sheet.nrows)

    def test_col_slice(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.check_col_slice(sheet.col_slice)

    def test_col_types(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.check_col_slice(sheet.col_types)

    def test_col_values(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.check_col_slice(sheet.col_values)

    def test_row_slice(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.check_row_slice(sheet.row_slice)

    def test_row_types(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.check_row_slice(sheet.col_types)

    def test_row_values(self):
        sheet = self.book.sheet_by_index(SHEETINDEX)
        self.check_col_slice(sheet.row_values)


class TestSheetRagged(TestCase):

    def test_read_ragged(self):
        book = xlrd.open_workbook(datafile('ragged.xls'), ragged_rows=True)
        sheet = book.sheet_by_index(0)
        self.assertEqual(sheet.row_len(0), 3)
        self.assertEqual(sheet.row_len(1), 2)
        self.assertEqual(sheet.row_len(2), 1)
        self.assertEqual(sheet.row_len(3), 4)
        self.assertEqual(sheet.row_len(4), 4)


class TestMergedCells(TestCase):

    def test_tidy_dimensions(self):
        book = xlrd.open_workbook(datafile('merged_cells.xlsx'))
        for sheet in book.sheets():
            for rowx in xrange(sheet.nrows):
                self.assertEqual(sheet.row_len(rowx), sheet.ncols)



### test_workbook.py

SHEETINDEX = 0
NROWS = 15
NCOLS = 13


class TestWorkbook(TestCase):
    sheetnames = ['PROFILEDEF', 'AXISDEF', 'TRAVERSALCHAINAGE',
                  'AXISDATUMLEVELS', 'PROFILELEVELS']

    def setUp(self):
        self.book = open_workbook(datafile('profiles.xls'))

    def test_open_workbook(self):
        self.assertTrue(isinstance(self.book, Book))

    def test_nsheets(self):
        self.assertEqual(self.book.nsheets, 5)

    def test_sheet_by_name(self):
        for name in self.sheetnames:
            sheet = self.book.sheet_by_name(name)
            self.assertTrue(isinstance(sheet, Sheet))
            self.assertEqual(name, sheet.name)

    def test_sheet_by_index(self):
        for index in range(5):
            sheet = self.book.sheet_by_index(index)
            self.assertTrue(isinstance(sheet, Sheet))
            self.assertEqual(sheet.name, self.sheetnames[index])

    def test_sheets(self):
        sheets = self.book.sheets()
        for index, sheet in enumerate(sheets):
            self.assertTrue(isinstance(sheet, Sheet))
            self.assertEqual(sheet.name, self.sheetnames[index])

    def test_sheet_names(self):
        self.assertEqual(self.sheetnames, self.book.sheet_names())

    def test_getitem_ix(self):
        sheet = self.book[SHEETINDEX]
        self.assertNotEqual(xlrd.empty_cell, sheet.cell(0, 0))
        self.assertNotEqual(xlrd.empty_cell, sheet.cell(NROWS - 1, NCOLS - 1))

    def test_getitem_name(self):
        sheet = self.book[self.sheetnames[SHEETINDEX]]
        self.assertNotEqual(xlrd.empty_cell, sheet.cell(0, 0))
        self.assertNotEqual(xlrd.empty_cell, sheet.cell(NROWS - 1, NCOLS - 1))

    def test_iter(self):
        sheets = [sh.name for sh in self.book]
        self.assertEqual(sheets, self.sheetnames)



### test_xldate.py


DATEMODE = 0 # 1900-based

class TestXLDate(unittest.TestCase):
    def test_date_as_tuple(self):
        date = xldate.xldate_as_tuple(2741., DATEMODE)
        self.assertEqual(date, (1907, 7, 3, 0, 0, 0))
        date = xldate.xldate_as_tuple(38406., DATEMODE)
        self.assertEqual(date, (2005, 2, 23, 0, 0, 0))
        date = xldate.xldate_as_tuple(32266., DATEMODE)
        self.assertEqual(date, (1988, 5, 3, 0, 0, 0))

    def test_time_as_tuple(self):
        time = xldate.xldate_as_tuple(.273611, DATEMODE)
        self.assertEqual(time, (0, 0, 0, 6, 34, 0))
        time = xldate.xldate_as_tuple(.538889, DATEMODE)
        self.assertEqual(time, (0, 0, 0, 12, 56, 0))
        time = xldate.xldate_as_tuple(.741123, DATEMODE)
        self.assertEqual(time, (0, 0, 0, 17, 47, 13))

    def test_xldate_from_date_tuple(self):
        date = xldate.xldate_from_date_tuple( (1907, 7, 3), DATEMODE )
        self.assertAlmostEqual(date, 2741.)
        date = xldate.xldate_from_date_tuple( (2005, 2, 23), DATEMODE )
        self.assertAlmostEqual(date, 38406.)
        date = xldate.xldate_from_date_tuple( (1988, 5, 3), DATEMODE )
        self.assertAlmostEqual(date, 32266.)

    def test_xldate_from_time_tuple(self):
        time = xldate.xldate_from_time_tuple( (6, 34, 0) )
        self.assertAlmostEqual(time, .273611, places=6)
        time = xldate.xldate_from_time_tuple( (12, 56, 0) )
        self.assertAlmostEqual(time, .538889, places=6)
        time = xldate.xldate_from_time_tuple( (17, 47, 13) )
        self.assertAlmostEqual(time, .741123, places=6)

    def test_xldate_from_datetime_tuple(self):
        date = xldate.xldate_from_datetime_tuple( (1907, 7, 3, 6, 34, 0), DATEMODE)
        self.assertAlmostEqual(date, 2741.273611, places=6)
        date = xldate.xldate_from_datetime_tuple( (2005, 2, 23, 12, 56, 0), DATEMODE)
        self.assertAlmostEqual(date, 38406.538889, places=6)
        date = xldate.xldate_from_datetime_tuple( (1988, 5, 3, 17, 47, 13), DATEMODE)
        self.assertAlmostEqual(date, 32266.741123, places=6)



### test_xldate_to_datetime.py

not_1904 = False
is_1904 = True


class TestConvertToDateTime(unittest.TestCase):
    """
    Testcases to test the _xldate_to_datetime() function against dates
    extracted from Excel files, with 1900/1904 epochs.

    """

    def test_dates_and_times_1900_epoch(self):
        """
        Test the _xldate_to_datetime() function for dates and times in
        the Excel standard 1900 epoch.

        """
        # Test Excel dates strings and corresponding serial date numbers taken
        # from an Excel file.
        excel_dates = [
            # Excel's 0.0 date in the 1900 epoch is 1 day before 1900.
            ('1899-12-31T00:00:00.000', 0),

            # Date/time before the false Excel 1900 leapday.
            ('1900-02-28T02:11:11.986', 59.09111094906),

            # Date/time after the false Excel 1900 leapday.
            ('1900-03-01T05:46:44.068', 61.24078782403),

            # Random date/times in Excel's 0-9999.9999+ range.
            ('1982-08-25T00:15:20.213', 30188.010650613425),
            ('2065-04-19T00:16:48.290', 60376.011670023145),
            ('3222-06-11T03:08:08.251', 483014.13065105322),
            ('4379-08-03T06:14:48.580', 905652.26028449077),
            ('5949-12-30T12:59:54.263', 1479232.5416002662),

            # End of Excel's date range.
            ('9999-12-31T23:59:59.000', 2958465.999988426),
        ]

        # Convert the Excel date strings to datetime objects and compare
        # against the dateitme return value of xldate.xldate_as_datetime().
        for excel_date in excel_dates:
            exp = datetime.strptime(excel_date[0], "%Y-%m-%dT%H:%M:%S.%f")
            got = xldate.xldate_as_datetime(excel_date[1], not_1904)

            self.assertEqual(got, exp)

    def test_dates_only_1900_epoch(self):
        """
        Test the _xldate_to_datetime() function for dates in the Excel
        standard 1900 epoch.

        """
        # Test Excel dates strings and corresponding serial date numbers taken
        # from an Excel file.
        excel_dates = [
            # Excel's day 0 in the 1900 epoch is 1 day before 1900.
            ('1899-12-31', 0),

            # Excel's day 1 in the 1900 epoch.
            ('1900-01-01', 1),

            # Date/time before the false Excel 1900 leapday.
            ('1900-02-28', 59),

            # Date/time after the false Excel 1900 leapday.
            ('1900-03-01', 61),

            # Random date/times in Excel's 0-9999.9999+ range.
            ('1902-09-27', 1001),
            ('1999-12-31', 36525),
            ('2000-01-01', 36526),
            ('4000-12-31', 767376),
            ('4321-01-01', 884254),
            ('9999-01-01', 2958101),

            # End of Excel's date range.
            ('9999-12-31', 2958465),
        ]

        # Convert the Excel date strings to datetime objects and compare
        # against the dateitme return value of xldate.xldate_as_datetime().
        for excel_date in excel_dates:
            exp = datetime.strptime(excel_date[0], "%Y-%m-%d")
            got = xldate.xldate_as_datetime(excel_date[1], not_1904)

            self.assertEqual(got, exp)

    def test_dates_only_1904_epoch(self):
        """
        Test the _xldate_to_datetime() function for dates in the Excel
        Mac/1904 epoch.

        """
        # Test Excel dates strings and corresponding serial date numbers taken
        # from an Excel file.
        excel_dates = [
            # Excel's day 0 in the 1904 epoch.
            ('1904-01-01', 0),

            # Random date/times in Excel's 0-9999.9999+ range.
            ('1904-01-31', 30),
            ('1904-08-31', 243),
            ('1999-02-28', 34757),
            ('1999-12-31', 35063),
            ('2000-01-01', 35064),
            ('2400-12-31', 181526),
            ('4000-01-01', 765549),
            ('9999-01-01', 2956639),

            # End of Excel's date range.
            ('9999-12-31', 2957003),
        ]

        # Convert the Excel date strings to datetime objects and compare
        # against the dateitme return value of xldate.xldate_as_datetime().
        for excel_date in excel_dates:
            exp = datetime.strptime(excel_date[0], "%Y-%m-%d")
            got = xldate.xldate_as_datetime(excel_date[1], is_1904)

            self.assertEqual(got, exp)

    def test_times_only(self):
        """
        Test the _xldate_to_datetime() function for times only, i.e, the
        fractional part of the Excel date when the serial date is 0.

        """
        # Test Excel dates strings and corresponding serial date numbers taken
        # from an Excel file. The 1899-12-31 date is Excel's day 0.
        excel_dates = [
            # Random times in Excel's 0-0.9999+ range for 1 day.
            ('1899-12-31T00:00:00.000', 0),
            ('1899-12-31T00:15:20.213', 1.0650613425925924E-2),
            ('1899-12-31T02:24:37.095', 0.10042934027777778),
            ('1899-12-31T04:56:35.792', 0.2059698148148148),
            ('1899-12-31T07:31:20.407', 0.31343063657407405),
            ('1899-12-31T09:37:23.945', 0.40097158564814817),
            ('1899-12-31T12:09:48.602', 0.50681252314814818),
            ('1899-12-31T14:37:57.451', 0.60969271990740748),
            ('1899-12-31T17:04:02.415', 0.71113906250000003),
            ('1899-12-31T19:14:24.673', 0.80167445601851861),
            ('1899-12-31T21:39:05.944', 0.90215212962962965),
            ('1899-12-31T23:17:12.632', 0.97028509259259266),
            ('1899-12-31T23:59:59.999', 0.99999998842592586),
        ]

        # Convert the Excel date strings to datetime objects and compare
        # against the dateitme return value of xldate.xldate_as_datetime().
        for excel_date in excel_dates:
            exp = datetime.strptime(excel_date[0], "%Y-%m-%dT%H:%M:%S.%f")
            got = xldate.xldate_as_datetime(excel_date[1], not_1904)

            self.assertEqual(got, exp)



### test_xlsx_comments.py

class TestXlsxComments(TestCase):

    def test_excel_comments(self):
        book = open_workbook(datafile('test_comments_excel.xlsx'))
        sheet = book.sheet_by_index(0)

        note_map = sheet.cell_note_map
        self.assertEqual(len(note_map), 1)
        self.assertEqual(note_map[(0, 1)].text, 'hello')

    def test_excel_comments_multiline(self):
        book = open_workbook(datafile('test_comments_excel.xlsx'))
        sheet = book.sheet_by_index(1)

        note_map = sheet.cell_note_map
        self.assertEqual(note_map[(1, 2)].text, '1st line\n2nd line')

    def test_excel_comments_two_t_elements(self):
        book = open_workbook(datafile('test_comments_excel.xlsx'))
        sheet = book.sheet_by_index(2)

        note_map = sheet.cell_note_map
        self.assertEqual(note_map[(0, 0)].text, 'Author:\nTwo t elements')

    def test_excel_comments_no_t_elements(self):
        book = open_workbook(datafile('test_comments_excel.xlsx'))
        sheet = book.sheet_by_index(3)

        note_map = sheet.cell_note_map
        self.assertEqual(note_map[(0,0)].text, '')

    def test_gdocs_comments(self):
        book = open_workbook(datafile('test_comments_gdocs.xlsx'))
        sheet = book.sheet_by_index(0)

        note_map = sheet.cell_note_map
        self.assertEqual(len(note_map), 1)
        self.assertEqual(note_map[(0, 1)].text, 'Just a test')

    def test_excel_comments_with_multi_sheets(self):
        book = open_workbook(datafile('test_comments_excel_sheet2.xlsx'))
        sheet = book.sheet_by_index(1)

        note_map = sheet.cell_note_map
        self.assertEqual(len(note_map), 1)
        self.assertEqual(note_map[(1, 1)].text, 'Note lives here')
        self.assertEqual(len(book.sheet_by_index(0).cell_note_map), 0)



### test_xlsx_parse.py

class TestXlsxParse(unittest.TestCase):
    # Test parsing of problematic xlsx files. These are usually submitted
    # as part of bug reports as noted below.

    def test_for_github_issue_75(self):
        # Test <cell> inlineStr attribute without <si> child.
        # https://github.com/python-excel/xlrd/issues/75
        workbook = xlrd.open_workbook(datafile('apachepoi_52348.xlsx'))
        worksheet = workbook.sheet_by_index(0)

        # Test an empty inlineStr cell.
        cell = worksheet.cell(0, 0)
        self.assertEqual(cell.value, '')
        self.assertEqual(cell.ctype, xlrd.book.XL_CELL_EMPTY)

        # Test a non-empty inlineStr cell.
        cell = worksheet.cell(1, 2)
        self.assertEqual(cell.value, 'Category')
        self.assertEqual(cell.ctype, xlrd.book.XL_CELL_TEXT)

    def test_for_github_issue_96(self):
        # Test for non-Excel file with forward slash file separator and
        # lowercase names. https://github.com/python-excel/xlrd/issues/96
        workbook = xlrd.open_workbook(datafile('apachepoi_49609.xlsx'))
        worksheet = workbook.sheet_by_index(0)

        # Test reading sample data from the worksheet.
        cell = worksheet.cell(0, 1)
        self.assertEqual(cell.value, 'Cycle')
        self.assertEqual(cell.ctype, xlrd.book.XL_CELL_TEXT)

        cell = worksheet.cell(1, 1)
        self.assertEqual(cell.value, 1)
        self.assertEqual(cell.ctype, xlrd.book.XL_CELL_NUMBER)

    def test_for_github_issue_101(self):
        # Test for non-Excel file with forward slash file separator
        # https://github.com/python-excel/xlrd/issues/101
        workbook = xlrd.open_workbook(datafile('self_evaluation_report_2014-05-19.xlsx'))
        worksheet = workbook.sheet_by_index(0)

        # Test reading sample data from the worksheet.
        cell = worksheet.cell(0, 0)
        self.assertEqual(cell.value, 'one')
        self.assertEqual(cell.ctype, xlrd.book.XL_CELL_TEXT)

    def test_for_github_issue_150(self):
        # Test for non-Excel file with a non-lowercase worksheet filename.
        # https://github.com/python-excel/xlrd/issues/150
        workbook = xlrd.open_workbook(datafile('issue150.xlsx'))
        worksheet = workbook.sheet_by_index(0)

        # Test reading sample data from the worksheet.
        cell = worksheet.cell(0, 1)
        self.assertEqual(cell.value, 'Cycle')
        self.assertEqual(cell.ctype, xlrd.book.XL_CELL_TEXT)

        cell = worksheet.cell(1, 1)
        self.assertEqual(cell.value, 1)
        self.assertEqual(cell.ctype, xlrd.book.XL_CELL_NUMBER)


if __name__=='__main__':
    unittest.main()
