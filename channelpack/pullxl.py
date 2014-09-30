"""
Helper module for reading tabular data from spread sheets.

Spread sheet reading principles:

1 Data is assumed to be arranged column-wise.

2 Default is to read a whole sheet. nrows, ncols is assumed (attributes
  in xlrd:s Sheet objects). Top row defaults to be a header row with
  field names.

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
    in sheet 'sheet3'.

6 Type detection is done by checking the Cell object's ctype
  attribute for each field's data range. If the ctype is all the same,
  the type is given. If there are two types, and one of them is
  'XL_CELL_EMPTY', the type is assumed to be the other. Then the empty
  cell's values will be replaced by numpy nan if the type is float, else
  None. If there are more than two ctypes in the data range, the type
  will be object, and empty cells replaced by None.

"""
import re

import xlrd

XLNOT_RX = r'([A-Za-z]+)(\d+)'

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

def read_sheet(sheet, startcell=None, stopcell=None):
    """Read data from a spread sheet. Yield each record as a list of
    cell objects.

    sheet: xlrd.sheet.Sheet instance
        Ready for use.

    startcell: str or None
        If given, a spread sheet style notation of the cell where data
        start, ("F9").

    stopcell: str or None
        A spread sheet style notation of the cell where data end,
        ("F9"). startcell and stopcell can be used in any combination.

    Return an iterator over the records. But first, monkey-patch the
    sheet object with attributes channelpack_start and channelpack_stop,
    as determined here. Keep in mind that stop is non-inclusive, (like
    python indexing). Also keep in mind that at least one record need to
    be consumed before the sheet object have the monkey-patched
    attributes, since this is a generator.

    It seems I am already on the way to depricate this function. Make a
    version of it called `parse_range` and keep the part parsing the cell
    notations.
    """
    raise DeprecationWarning('Not gonna use this function')

    start = [0, 0]              # [row, col]
    stop = [sheet.nrows, sheet.ncols]
    # For this function, ignore the headers argument.

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
    
    # Monkey-patch the sheet object. Since we have an object here. Is this
    # risky?
    sheet.channelpack_start = tuple(start)
    sheet.channelpack_stop = tuple(stop)

    for rownum in range(start[0], stop[0]):
        yield sheet.row_slice(rownum, start_colx=start[1], end_colx=stop[1])

def _get_startstop(sheet, startcell=None, stopcell=None):
    """
    Return a start and stop tuple [(row0, col0), (row1, col1)].

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
    # For this function, ignore the headers argument.

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
    return [tuple(start), tuple(stop)]

def sheet_asdict(sheet, header=True, startcell=None, stopcell=None, 
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

    start, stop = _get_startstop(sheet, startcell=startcell, stopcell=stopcell)
    usecols = _sanitize_usecols(usecols)
    if usecols is not None:
        mess =  'Column in usecols outside defined range.'
        assert start[1] <= min(usecols) and stop[1] > max(usecols), mess
    

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
