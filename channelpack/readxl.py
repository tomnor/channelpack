"""
Helper module for reading tabular data from spread sheets.

Spread sheet reading principles:

1. Data is assumed to be arranged column-wise.

2. Default is to read a whole sheet. nrows, ncols is assumed (attributes
   in xlrd:s Sheet objects). Top row defaults to be a header row with
   field names, (header=True).

3. A startcell and stopcell can be given. It is then given in spread
   sheet notation ("B15"). header option can be True or False or a cell
   specification of where the header start ("B15").

4. The interpretation of startcell and stopcell in combination with
   header is as follows:

   - If nothing specified, see 2.

   - If startcell is given (say 'C3') and header is True, header row is
     3 with spread sheet enumeration. Data start at row 4

   - If startcell is given, say 'C3', and header is 'C3', header row is
     3 with spread sheet enumeration. Data start at row 4.

   - If startcell is given (say 'C3') and header is False, data start at
     row 3.

5. Type detection is done by checking the Cell object's ctype attribute
   for each field's data range. If the ctype is all the same, the type
   is given. If there are two types, and one of them is 'XL_CELL_EMPTY',
   the type is assumed to be the other. Then the empty cell's values
   will be replaced by numpy nan if the type is float, else None. If
   there are more than two ctypes in the data range, the type will be
   object, and empty cells replaced by None. Dates will be python
   datetime objects.

"""
import re
import datetime

import xlrd
import numpy as np

# Two groups, col and row spread sheet notation.
XLNOT_RX = r'([A-Za-z]+)(\d+)'

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

    start = StartStop(0, 0)     # row, col
    stop = StartStop(sheet.nrows, sheet.ncols)

    if startcell:
        m = re.match(XLNOT_RX, startcell)
        start.row = int(m.group(2)) - 1
        start.col = letter2num(m.group(1), zbase=True)

    if stopcell:
        m = re.match(XLNOT_RX, stopcell)
        stop.row = int(m.group(2))
        # Stop number is exclusive
        stop.col = letter2num(m.group(1), zbase=False)

    return [start, stop]


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
    headstart, headstop = StartStop(0, 0), StartStop(0, 0)  # Holders

    def typicalprep():
        headstart.row, headstart.col = datstart.row, datstart.col
        headstop.row, headstop.col = datstart.row + 1, datstop.col
        # Tick the data start row by 1:
        datstart.row += 1

    def offsetheaderprep():
        headstart.row, headstart.col = headrow, headcol
        headstop.row = headrow + 1
        headstop.col = headcol + (datstop.col - datstart.col)  # stop > start

    if header is True:          # Simply the toprow of the table.
        typicalprep()
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


def sheetheader(sheet, startstops, usecols=None):
    """Return the channel names in a list suitable as an argument to
    ChannelPack's `set_channel_names` method. Return None if first two
    StartStops are None.

    This function is slightly confusing, because it shall be called with
    the same parameters as sheet_asdict. But knowing that, it should be
    convenient.

    sheet: xlrd.sheet.Sheet instance
        Ready for use.

    startstops: list
        Four StartStop objects defining the data to read. See
        :func:`~channelpack.pullxl.prepread`, returning such a list.

    usecols: str or sequence of ints or None
        The columns to use, 0-based. 0 is the spread sheet column
        "A". Can be given as a string also - 'C:E, H' for columns C, D,
        E and H.
    """

    headstart, headstop, dstart, dstop = startstops
    if headstart is None:
        return None
    assert headstop.row - headstart.row == 1, ('Field names must be in '
                                               'same row so far. Or '
                                               'this is a bug')
    header = []
    # One need to make same offsets within start and stop as in usecols:
    usecols = _sanitize_usecols(usecols)
    cols = usecols or range(dstart.col, dstop.col)
    headcols = [c + (headstart.col - dstart.col) for c in cols]

    for col in headcols:
        fieldname = sheet.cell(headstart.row, col).value
        header.append(unicode(fieldname))

    return header


def _sheet_asdict(sheet, startstops, usecols=None):
    """Read data from a spread sheet. Return the data in a dict with
    column numbers as keys.

    sheet: xlrd.sheet.Sheet instance
        Ready for use.

    startstops: list
        Four StartStop objects defining the data to read. See
        :func:`~channelpack.pullxl.prepread`.

    usecols: str or seqence of ints or None
        The columns to use, 0-based. 0 is the spread sheet column
        "A". Can be given as a string also - 'C:E, H' for columns C, D,
        E and H.

    Values in the returned dict are numpy arrays. Types are set based on
    the types in the spread sheet.
    """

    _, _, start, stop = startstops
    usecols = _sanitize_usecols(usecols)

    if usecols is not None:
        iswithin = start.col <= min(usecols) and stop.col > max(usecols)
        mess = 'Column in usecols outside defined data range, got '
        assert iswithin, mess + str(usecols)
    else:                       # usecols is None.
        usecols = tuple(range(start.col, stop.col))

    # cols = usecols or range(start.col, stop.col)
    D = dict()

    for c in usecols:
        cells = sheet.col(c, start_rowx=start.row, end_rowx=stop.row)
        types = set([cell.ctype for cell in cells])

        # Replace empty values with nan if appropriate:
        if (not types - NANABLE) and xlrd.XL_CELL_NUMBER in types:
            D[c] = np.array([np.nan if cell.value == '' else cell.value
                             for cell in cells])
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
            D[c] = np.array(vals)

    return D


def sheet_asdict(fn, sheet=0, header=True, startcell=None, stopcell=None,
                 usecols=None, chnames_out=None):
    """Read data from a spread sheet. Return the data in a dict with
    column numbers as keys.

    fn: str
        The file to read from.

    sheet: int or str
        If int, it is the index for the sheet 0-based. Else the sheet
        name.

    header: bool or str
        True if the defined data range includes a header with field
        names. Else False - the whole range is data. If a string, it is
        a spread sheet style notation of the startcell for the header
        ("F9"). The "width" of this record is the same as for the data.


    startcell: str or None
        If given, a spread sheet style notation of the cell where reading
        start, ("F9").

    stopcell: str or None
        A spread sheet style notation of the cell where data end,
        ("F9").

    usecols: str or seqence of ints
        The columns to use, 0-based. 0 is the spread sheet column
        "A". Can be given as a string also - 'C:E, H' for columns C, D,
        E and H.

    usecols: str or sequence of ints or None
        The columns to use, 0-based. 0 is the spread sheet column
        "A". Can be given as a string also - 'C:E, H' for columns C, D,
        E and H.

    chnames_out: list or None
        If a list it will be populated with the channel names. The size
        of the list will equal to the number of channel names extracted.
        Whatever is in the list supplied will first be removed.

    Values in the returned dict are numpy arrays. Types are set based on
    the types in the spread sheet.
    """
    book = xlrd.open_workbook(fn)
    try:
        sh = book.sheet_by_index(sheet)
    except TypeError:
        sh = book.sheet_by_name(sheet)

    ss = prepread(sh, header=header, startcell=startcell, stopcell=stopcell)

    chnames = sheetheader(sh, ss, usecols=usecols)

    if chnames_out is not None and chnames is not None:
        vals = list(chnames_out)
        [chnames_out.remove(v) for v in vals]
        chnames_out.extend(chnames)

    return _sheet_asdict(sh, ss, usecols=usecols)


def _sanitize_usecols(usecols):
    """Make a tuple of sorted integers and return it. Return None if
    usecols is None"""

    if usecols is None:
        return None

    try:
        pats = usecols.split(',')
        pats = [p.strip() for p in pats if p]
    except AttributeError:
        usecols = [int(c) for c in usecols]  # Make error if mix.
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

    >>> from channelpack.pullxl import letter2num

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
        assert 65 <= ord(c) <= 90, c  # A-Z
        res += (ord(c) - 64) * 26**(weight - i)
    if not zbase:
        return res
    return res - 1


def toxldate(datetime, datemode=1):
    """Return a xl-date number from the datetime object datetime.

    datetime: datetime.datetime
        The python datetime object

    datemode: int
        0: 1900-based, 1: 1904-based. See xlrd documentation.
    """
    return xlrd.xldate.xldate_from_datetime_tuple(datetime.timetuple()[:6],
                                                  datemode)


def fromxldate(xldate, datemode=1):
    """Return a python datetime object

    xldate: float
        The xl number.

    datemode: int
        0: 1900-based, 1: 1904-based. See xlrd documentation.
    """

    t = xlrd.xldate_as_tuple(xldate, datemode)
    return datetime.datetime(*t)
