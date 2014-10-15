"""
Helper module for reading tabular data from spread sheets.

Spread sheet reading principles:

1 Data is assumed to be arranged column-wise.

2 Default is to read a whole sheet. nrows, ncols is assumed (attributes
  in xlrd:s Sheet objects). Top row defaults to be a header row with
  field names, (header=True).

3 Default sheet is sheet with index 0. Selectable with a string name or
  index number. No. Actually, functions in this module take a sheet
  object, so it's already defined here.

4 A startcell can be given. It is then given in spread sheet notation
  ("B15"). If startcell is given - a stopcell is mandatory. The range
  defined assumes to include the header row if any.

  Rewrite, because stopcell is not mandatory just because startcell is
  given. Any combination allowed.

5 The interpretation of startcell and stopcell in combination with
  header is as follows:

  - If nothing specified, see 2.
  - If startcell is given (say 'C3') and header is True, header row is
    3 with spread sheet enumeration. Data start at row 4
  - If startcell is given (say 'C3') and header is 'C3', header row is
    3 with spread sheet enumeration. Data start at row 4.
  - If startcell is given (say 'C3') and header is False, data start at
    row 3.
  - If startcell is given (say 'C3') and header is 'sheet3:E20', data
    start at row 3, and the header row is picked starting from cell E20
    in sheet 'sheet3'. No, remove the idea with supporting field names
    in another sheet. But do support finding field names at arbitary
    location within the data sheet.

6 Type detection is done by checking the Cell object's ctype
  attribute for each field's data range. If the ctype is all the same,
  the type is given. If there are two types, and one of them is
  'XL_CELL_EMPTY', the type is assumed to be the other. Then the empty
  cell's values will be replaced by numpy nan if the type is float, else
  None. If there are more than two ctypes in the data range, the type
  will be object, and empty cells replaced by None. Dates will be python
  datetime objects.

"""
import re
import datetime

import xlrd
import numpy as np

XLNOT_RX = r'([A-Za-z]+)(\d+)'  # Two groups, col and row spread sheet notation.

# StartStop = namedtuple('StartStop', ('row', 'col'))

class StartStop:
    """Zero-based integers for row and column, xlrd style. Meaning, the
    stop values are non-inclusive. This object is used for either start
    or stop."""
    def __init__(self, row, col):
        self.row = row
        self.col = col
    def __getitem__(self, k):
        return [self.row, self.col][k]
    def __repr__(self):
        return 'StartStop({}, {})'.format(*self)

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
#                           when open_workbook(..., formatting_info=True) is used.

# Data type flags for the cell objects. See
# https://secure.simplistix.co.uk/svn/xlrd/trunk/xlrd/doc/xlrd.html?p=4966#sheet.Cell-class
# for details.

NANABLE = set((xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_EMPTY))
NONABLES = (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_ERROR)

def _get_startstop(sheet, startcell=None, stopcell=None):
    """
    Return two StartStop objects, based on the sheet and startcell and
    stopcell.

    sheet: xlrd.sheet.Sheet instance
        Ready for use.

    startcell: str or None
        If given, a spread sheet style notation of the cell where data
        start, ("F9").

    stopcell: str or None
        A spread sheet style notation of the cell where data end,
        ("F9"). startcell and stopcell can be used in any combination.

    """

    start = [0, 0]              # [row, col]
    stop = [sheet.nrows, sheet.ncols]

    if startcell:
        m = re.match(XLNOT_RX, startcell)
        start[0] = int(m.group(2)) - 1 # The row number
        start[1] = letter2num(m.group(1), zbase=True) # The column number from
                                                      # letter.

    if stopcell:
        m = re.match(XLNOT_RX, stopcell)
        stop[0] = int(m.group(2)) # The row number
        stop[1] = letter2num(m.group(1), zbase=False) # The column number from
                                                      # letter. Stop
                                                      # enumerations are
                                                      # exclusive.
    # return [tuple(start), tuple(stop)]
    return [StartStop(*start), StartStop(*stop)]

def prepread(sheet, header=True, startcell=None, stopcell=None):
    """Return four StartStop objects, defining the outer bounds of
    header row and data range, respectively. If header is False, the
    first two items will be None.

    --> [headstart, headstop, datstart, datstop]

    sheet: xlrd.sheet.Sheet instance
        Ready for use.

    header: bool or str
        True if the defined data range includes a header with field
        names. Else False - the whole range is data. If a string, it is
        spread sheet style notation of the startcell for the header
        ("F9"). The "width" of this record is the same as for the data.

    startcell: str or None
        If given, a spread sheet style notation of the cell where reading
        start, ("F9").

    stopcell: str or None
        A spread sheet style notation of the cell where data end,
        ("F9").

   startcell and stopcell can both be None, either one specified or
   both specified.

   Note to self: consider making possible to specify headers in a column.

    """
    datstart, datstop = _get_startstop(sheet, startcell, stopcell)
    headstart, headstop = StartStop(0, 0), StartStop(0, 0) # Holders

    def typicalprep():
        headstart.row, headstart.col = datstart.row, datstart.col
        headstop.row, headstop.col = datstart.row, datstop.col
        # Tick the data start row by 1:
        datstart.row += 1

    def offsetheaderprep():
        headstart.row, headstart.col = headrow, headcol
        headstop.row = headrow
        headstop.col = headcol + (datstop.col - datstart.col)

    if header is True:          # Simply the toprow of the table.
        typicalprep()
        print headstop.row, headstop.col
        return [headstart, headstop, datstart, datstop]
    elif header:                # Then it is a string if not False. ("F9")
        m = re.match(XLNOT_RX, header)
        headrow = int(m.group(2)) - 1
        headcol = letter2num(m.group(1), zbase=True)
        if headrow == datstart.row and headcol == datstart.col:
            typicalprep()
            return [headstart, headstop, datstart, datstop]
        elif headrow == datstart.row:
            typicalprep()
            offsetheaderprep()
            return [headstart, headstop, datstart, datstop]
        else:
            offsetheaderprep()
            return [headstart, headstop, datstart, datstop]
    else:                       # header is False
        return [None, None, datstart, datstop]

def sheetheader(sheet, startstops, busecols):
    """Return the channel names in a list suitable as an argument to
    ChannelPack's `set_channel_names` method.

    sheet: xlrd.sheet.Sheet instance
        Ready for use.

    startstops: list
        Four StartStop objects defining the data to read. See
        :func:`~channelpack.pullxl.prepread`, returning such a list.

    usecols: str or seqence of ints
        The columns to use, 0-based. 0 is the spread sheet column
        "A". Can be given as a string also - 'C:E, H' for columns C, D,
        E and H.
    """

    raise NotImplementedError

    headstart, headstop, _, _ = startstops

def sheet_asdict(sheet, startstops, usecols=None):
    """Read data from a spread sheet. Return the data in a dict with
    column numbers as keys.

    sheet: xlrd.sheet.Sheet instance
        Ready for use.

    startstops: list
        Four StartStop objects defining the data to read. See
        :func:`~channelpack.pullxl.prepread`.

    usecols: str or seqence of ints
        The columns to use, 0-based. 0 is the spread sheet column
        "A". Can be given as a string also - 'C:E, H' for columns C, D,
        E and H.

    Values in the returned dict are numpy arrays. Types are set based on
    the types in the spread sheet.
    """

    _, _, start, stop = startstops
    # Consider checking if usecols is within range.
    cols = usecols or range(start.col, stop.col)
    D = dict()

    for c in cols:
        cells = sheet.col(c, start_rowx=start.row, end_rowx=stop.row)
        types = set([cell.ctype for cell in cells])

        # Replace empty values with nan if appropriate:
        if (not types - NANABLE) and xlrd.XL_CELL_NUMBER in types:
            D[c] = np.array([np.nan if cell.value is '' else cell.value for cell
                          in cells])
        elif xlrd.XL_CELL_DATE in types:
            dm = sheet.book.datemode
            vals = []
            for cell in cells:
                if cell.ctype == xlrd.XL_CELL_DATE:
                    dtuple = xlrd.xldate_as_tuple(cell.value, dm)
                    vals.append(datetime.datetime(*dtuple))
                elif cell.ctype in NONABLES:
                    vals.append(None)
                else:
                    vals.append(cell.value)
            D[c] = np.array(vals)
        else:
            vals = [None if cell.ctype in NONABLES else cell.value
                    for cell in cells]
            D[c] = np.array([vals])

    return D

def sheet_asdictBAK(sheet, header=True, startcell=None, stopcell=None,
                 usecols=None):
    """Read data from a spread sheet. Return the data in a dict with
    column numbers as keys.

    sheet: xlrd.sheet.Sheet instance
        Ready for use.

    header: bool or str
        True if the defined data range includes a header with field
        names. Else False - the whole range is data. If a string, it is
        spread sheet style notation of the startcell for the header
        ("F9"). The "width" of this record is the same as for the data.

    startcell: str or None
        If given, a spread sheet style notation of the cell where reading
        start, ("F9").

    stopcell: str or None
        A spread sheet style notation of the cell where data end,
        ("F9"). startcell and stopcell can be used in any combination.

    usecols: str or seqence of ints
        The columns to use, 0-based. 0 is the spread sheet column
        "A". Can be given as a string also - 'C:E, H' for columns C, D,
        E and H.

    Values in the returned dict are numpy arrays. Types are set based on
    the types in the spread sheet.
    """

    # The indexes to be used as keys shall correspond with the spread sheet
    # columns.

    # Make a usecols always, whether it is specified as an argument or
    # not. (Even if None). Sanitize usecols to integers always.

    raise DeprecationWarning('Not gonna use it.')

    start, stop = _get_startstop(sheet, startcell=startcell, stopcell=stopcell)
    usecols = _sanitize_usecols(usecols)
    if usecols is not None:
        mess =  'Column in usecols outside defined range.'
        assert start[1] <= min(usecols) and stop[1] > max(usecols), mess
    else:                       # usecols is None.
        usecols = tuple(range(start.col, stop.col))

    # Sort out if the header is on top of defined data range:
    tickit = False
    if header is True:
        tickit = True
    elif header:                # Then it is a string if not False.
        m = re.match(XLNOT_RX, header)
        headrow = int(m.group(2)) - 1

def _sanitize_usecols(usecols):
    """Make a tuple of sorted integers and return it. Return None if
    usecols is None"""

    if usecols is None:
        return None

    try:
        pats = usecols.split(',')
        pats = [p.strip() for p in pats if p]
    except AttributeError:
        usecols = [int(c) for c in usecols] # Make error if mix.
        usecols.sort()
        return tuple(usecols)   # Assume sane sequence of integers.

    cols = []
    for pat in pats:
        if ':' in pat:
            c1, c2 = pat.split(':')
            n1 = letter2num(c1, zbase=True)
            n2 = letter2num(c2, zbase=False)
            cols += range(n1, n2)
        else:
            cols += [letter2num(pat, zbase=True)]

    # Remove duplicates:
    cols = list(set(cols))
    cols.sort()
    return tuple(cols)

def letter2num(letters, zbase=False):
    """A = 1, C = 3 and so on. Convert spreadsheet style column
    enumeration to a number.

    Answers:
    A = 1, Z = 26, AA = 27, AZ = 52, ZZ = 702, AMJ = 1024

    >>> letter2num('A') == 1
    True
    >>> letter2num('Z') == 26
    True
    >>> letter2num('AZ') == 52
    True
    >>> letter2num('ZZ') == 702
    True
    >>> letter2num('AMJ') == 1024
    True
    >>> letter2num('AMJ', zbase=True) == 1023
    True
    >>> letter2num('A', zbase=True) == 0
    True

    """

    letters = letters.upper()
    res = 0
    weight = len(letters) - 1
    assert weight >= 0, letters
    for i, c in enumerate(letters):
        assert 65 <= ord(c) <= 90, c # A-Z
        # print c, ord(c)
        res += (ord(c) - 64) * 26**(weight - i)
    if not zbase:
        return res
    return res - 1
