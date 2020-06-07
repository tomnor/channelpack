"""
Functions to read data from spread sheets.
"""
import re
from collections import namedtuple

import xlrd
import numpy as np

from .pack import ChannelPack

# Type symbol      Type     Python value
#                  number
# XL_CELL_EMPTY    0 	    empty string u''
# XL_CELL_TEXT     1 	    a Unicode string
# XL_CELL_NUMBER   2 	    float
# XL_CELL_DATE     3 	    float
# XL_CELL_BOOLEAN  4 	    int; 1 means TRUE, 0 means FALSE
# XL_CELL_ERROR    5 	    int representing internal Excel codes; for a text
#                           representation, refer to the supplied dictionary
#                           error_text_from_code

# XL_CELL_BLANK    6	    empty string u''. Note: this type will appear only
#                           with open_workbook(..., formatting_info=True)

# Data type flags for the cell objects. See
# https://secure.simplistix.co.uk/svn/xlrd/trunk/xlrd/doc/xlrd.html?p=4966#sheet.Cell-class
# for details.

CellRef = namedtuple('CellRef', ('row', 'col'))


def cellreference(row=0, col=0, xladdr=None):
    """Return a CellRef object with 0-based row and col.

    xladdr is a xl notation address string like 'C7', if given. Can also
    only be the column letter, in which case row is taken as row.
    """

    if not xladdr:
        return CellRef(int(row), int(col))

    m = re.match(r'([A-Za-z]+)(\d*)', xladdr)
    if not m:
        raise ValueError('Invalid notation:', xladdr)
    if not m.group(2):
        return CellRef(row, letter2num(m.group(1)))
    else:
        rownotation = int(m.group(2))
        if rownotation < 1:
            raise ValueError('Invalid notation:', xladdr)
        return CellRef(rownotation - 1, letter2num(m.group(1)))


def sheet_columns(ws, startref, stopref, usecols):
    """Yield data columns from work sheet ws.

    startref and stopref to be CellRef objects."""

    numericset = {xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_EMPTY,
                  xlrd.XL_CELL_ERROR, xlrd.XL_CELL_BLANK}
    textset = {xlrd.XL_CELL_TEXT, xlrd.XL_CELL_EMPTY,
               xlrd.XL_CELL_ERROR, xlrd.XL_CELL_BLANK}
    missingtypes = (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_ERROR,
                    xlrd.XL_CELL_BLANK)
    datemode = ws.book.datemode

    for colnum in usecols:
        values = ws.col_values(colnum, start_rowx=startref.row,
                               end_rowx=stopref.row + 1)
        types = ws.col_types(colnum, start_rowx=startref.row,
                             end_rowx=stopref.row + 1)
        typeset = set(types)

        if not typeset - numericset:  # numbers and missing in column
            yield [val if typ not in missingtypes else np.nan for
                   val, typ in zip(values, types)]

        elif not typeset - textset:  # text and missing in column
            yield [val if typ not in missingtypes else '' for
                   val, typ in zip(values, types)]

        else:
            vals = []
            for value, typ in zip(values, types):
                if typ == xlrd.XL_CELL_DATE:
                    value = xlrd.xldate_as_datetime(value, datemode)
                elif typ in missingtypes:
                    value = None
                elif typ == xlrd.XL_CELL_BOOLEAN:
                    value = value == 1
                vals.append(value)

            yield vals


def sheetpack(fname, sheet=0, header=True, startcell=None, stopcell=None,
              usecols=None):
    """Return a ChannelPack instance loaded from spread sheet file.

    Parameters
    ----------
    fname: str
        The file name to read from.
    sheet: int or str
        Sheet enumeration or name string.
    header: bool or str
        True means the data range include field names (top record).
        False means the whole range is data. A string can be used to
        specify the startcell of the header row, like "C1".
    startcell: str
        Spread sheet style notation of the upper left cell of the data
        range, like "C3".
    stopcell: str
        Spread sheet style notation of the lower right cell of the data
        range, like "H10".
    usecols: str or seqence of ints
        The columns to use, 0-based. 0 is the spread sheet column
        "A". Can be given as a string also - 'C:E, H' for columns C, D,
        E and H.

    """

    startref = cellreference(xladdr=startcell)
    stopref = cellreference(xladdr=stopcell)

    with xlrd.open_workbook(fname) as wb:
        try:
            ws = wb.sheet_by_index(sheet)
        except TypeError:
            ws = wb.sheet_by_name(sheet)
        if not stopcell:
            stopref = cellreference(ws.nrows - 1, ws.ncols - 1)

        usecols = normalize_usecols(usecols or
                                    range(startref.col, stopref.col + 1))

        if startref.col > usecols[0] or stopref.col < usecols[-1]:
            raise ValueError('usecols outside of start and stop range')

        if header is True:
            names = [ws.cell_value(startref.row, col) for col in usecols]
            startref = cellreference(startref.row + 1, startref.col)
        elif type(header) is str:
            nameref = cellreference(xladdr=header)
            names = [ws.cell_value(nameref.row, col) for col in usecols]

        data = {i: column for i, column in
                zip(usecols, sheet_columns(ws, startref, stopref, usecols))}

    chnames = {}
    if header:
        chnames = {i: name for i, name in zip(usecols, names)}
    pack = ChannelPack(data, chnames)
    pack.fn = fname
    return pack


def normalize_usecols(usecols):
    """Normalize usecols to a sequence of integers."""

    try:
        patterns = [p.strip() for p in usecols.split(',') if p.strip()]
    except AttributeError:
        return sorted([int(c) for c in usecols])  # fail if int cast fail

    columns = []
    for pattern in patterns:
        if ':' in pattern:
            c1, c2 = pattern.split(':')
            columns += list(range(letter2num(c1), letter2num(c2) + 1))
        else:
            columns.append(letter2num(pattern))

    return sorted(columns)


def letter2num(letters, zbase=True):
    """A = 0, C = 2 and so on. Convert spreadsheet style column
    enumeration to a number.

    Answers:
    A = 0, Z = 25, AA = 26, AZ = 51, ZZ = 701, AMJ = 1023

    >>> from channelpack.readxl import letter2num

    >>> letter2num('A') == 0
    True
    >>> letter2num('Z') == 25
    True
    >>> letter2num('AZ') == 51
    True
    >>> letter2num('ZZ') == 701
    True
    >>> letter2num('AMJ') == 1023
    True
    >>> letter2num('AMJ', zbase=False) == 1024
    True
    >>> letter2num('A', zbase=False) == 1
    True

    """

    letters = letters.upper()
    res = 0
    weight = len(letters) - 1
    assert weight >= 0, letters
    for i, c in enumerate(letters):
        assert 65 <= ord(c) <= 90, c  # A-Z
        res += (ord(c) - 64) * 26**(weight - i)
    if not zbase:
        return res
    return res - 1
