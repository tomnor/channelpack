# -*- coding: utf-8 -*-
"""
Funtions for reading data from text files.
"""
from __future__ import print_function
import re
from collections import namedtuple, defaultdict
import io
import locale

import numpy as np

from . import pack as cp

# The scanf kind of regular expressions as suggested by python docs
# the re module: r'[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?'
# non-capturing groups
DNUMRX = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'  # With decimal point
CNUMRX = r'[-+]?(?:\d+(?:,\d*)?|,\d+)(?:[eE][-+]?\d+)?'  # With decimal comma


def _escape(s):
    """Escape re-special characters in s and return it."""
    s = s.replace('+', r'\+')
    s = s.replace('.', r'\.')
    return s


def _floatit(s):
    """Replace ',' with '.' and convert to float."""
    return float(s.replace(',', '.'))


def _floatit_bytes(b):
    """Replace b',' with b'.' and convert to float."""
    return float(b.replace(b',', b'.'))


def preparse(lines, firstfieldrx=r'\w'):
    """Populate a dict with keyword arguments to use with data readers.

    Works with numerical data files, which might have a header with
    extra information to ignore.

    Populate a dict with following data

    delimiter : str
        String used as data delimiter
    skiprows : int
        Number of rows before first line of data.
    converters : dict
        Keys are column numbers and values are a function to make floats
        of text. None if converters are not needed.
    usecols : tuple
        Elements are 0-based integers representing all columns parsed.
    chnames : dict
        Keys are column numbers and values are the field names, "channel
        names". {} if field names was not parsed successfully.

    Parameters
    ----------
    lines : sequence
        Must include some number of data lines for the function to
        succeed.

    Returns
    -------
    dict
        Empty at failure to parse file.

    """

    # d like in decimal dot
    # c like in decimal comma
    dresults, cresults = [], []
    nodigsrx = r'(\D+)'

    for line in lines:
        # collect all numbers on the line
        dnumbersline = re.findall(DNUMRX, line)
        cnumbersline = re.findall(CNUMRX, line)

        # rx to search for data separator on the line:
        dsep_rx = nodigsrx.join(map(_escape, dnumbersline))
        csep_rx = nodigsrx.join(map(_escape, cnumbersline))

        dsepmatch = re.search(dsep_rx, line)
        if dsepmatch:
            dsepsline = dsepmatch.groups()
        else:
            dsepsline = ()

        csepmatch = re.search(csep_rx, line)
        if csepmatch:
            csepsline = csepmatch.groups()
        else:
            csepsline = ()

        # if there are seps that include both non-whites and some
        # whitespace, it is probably better to strip off the whitespace
        dsepsline = [sep.strip() if sep.strip() else sep for sep in dsepsline]
        csepsline = [sep.strip() if sep.strip() else sep for sep in csepsline]

        dresults.append((dnumbersline, dsepsline))
        cresults.append((cnumbersline, csepsline))

    Triplet = namedtuple('Triplet', ('numcnt', 'sepcnt', 'septypcnt'))
    dcounts = [Triplet(len(tup[0]), len(tup[1]), len(set(tup[1]))) for tup
               in dresults]
    ccounts = [Triplet(len(tup[0]), len(tup[1]), len(set(tup[1]))) for tup
               in cresults]

    # check last line, let the lowest numcnt be valid. Require the set
    # of seps to be 1.

    if dcounts[-1].numcnt <= ccounts[-1].numcnt:  # dot likely decimal sep
        validcounts = dcounts
        flag = 'd'
    else:
        validcounts = ccounts
        flag = 'c'

    if validcounts[-1].numcnt == 1:
        exp_septypcnt = 0       # one column of data
    else:
        exp_septypcnt = 1

    if validcounts[-1].septypcnt != exp_septypcnt:
        return {}

    # if only one column of data (exp_septypcnt == 0) there shouldn't be
    # any non-numbers, non-whites around the number
    elif exp_septypcnt == 0:
        if ((flag == 'd' and any(m.strip()
                                 for m in re.split(DNUMRX, lines[-1])))
            or (flag == 'c' and any(m.strip()
                                    for m in re.split(CNUMRX, lines[-1])))):
            return {}

    # Data starts before line where number of different seps is not 1
    # anymore, checking backwards. Or where there is no numbers found
    # with one column of data.
    for i, triplet in enumerate(reversed(validcounts)):
        if triplet.septypcnt != exp_septypcnt:
            break
        elif triplet.septypcnt == 0 and triplet.numcnt == 0:
            break
    else:
        i = len(validcounts)  # there was no seps != 1, assume first line

    # normal_i = len - rev_i - 1
    startline = len(validcounts) - i  # not - 1 because just passed the line
    if exp_septypcnt == 1:
        delimiter = flag == 'd' and dresults[-1][1][-1] or cresults[-1][1][-1]
    else:
        delimiter = None
    converters = (flag == 'c' and {column: _floatit for column
                                   in range(validcounts[-1].numcnt)} or None)

    chnames = {}
    # line above startline and up, (no iteration if startline=0)
    for line in lines[:startline][::-1]:
        fields = [field.strip() for field in
                  line.split(delimiter) if field.strip()]
        if len(fields) != validcounts[-1].numcnt:
            continue
        elif re.match(firstfieldrx, fields[0]):
            chnames = {colnum: field for colnum, field in enumerate(fields)}
            break

    kwdict = dict(skiprows=startline, delimiter=delimiter,
                  converters=converters, chnames=chnames,
                  usecols=tuple(range(validcounts[-1].numcnt)))

    return kwdict


# np.loadtxt(fname, dtype=<type 'float'>, comments='#', delimiter=None,
# converters=None, skiprows=0, usecols=None, unpack=False, ndmin=0,
# encoding='bytes', max_rows=None)


def lazy_loadtxt_pack(fname, parselines=25, chnames={}, firstfieldrx=r'\w',
                      **loadtxtkwargs):
    """Return a ChannelPack instance using numpy loadtxt function.

    Try to automatically derive values for the numpy loadtxt keyword
    arguments 'delimiter', 'skiprows' and 'converters'. Also try to
    parse out the field names, "channel names".

    Works with numerical data files, which might have a header with
    extra information to ignore. The only kind of converter derived is
    one that converts numbers with decimal comma to a float.

    Keyword arguments provided to this function overrides any derived
    equivalents.

    Parameters
    ----------
    fname : file, str
        Encoding given in loadtxtkwargs is respected.
    parselines : int
        The number of lines to preparse. For a successful preparse it
        must include at least one line of numeric data.
    chnames : dict
        Keys are integers (0-based column numbers) and values are
        channel names. If provided it will be set in the pack and is
        mutually exclusive with the usecols argument in loadtxtkwargs.
    firstfieldrx : str
    **loadtxtkwargs
        Other keyword arguments accepted by numpy loadtxt. Overrides
        derived keyword arguments if duplicated.

    """

    derived = {}
    bytesalert = ('encoding' not in loadtxtkwargs or
                  (loadtxtkwargs.get('encoding', 'None') == 'bytes'))
    parseencoding = loadtxtkwargs.get('encoding', None)
    # 'bytes' has a meaning to np.loadtxt but not for preparse
    parseencoding = ((parseencoding and (parseencoding != 'bytes'))
                     and parseencoding or None)

    filename = ''
    if type(fname) is str:
        with io.open(fname, encoding=parseencoding) as fo:
            derived = preparse(fo.readlines()[:parselines], firstfieldrx)
        filename = fname

    elif hasattr(fname, 'readlines') and 'b' in fname.mode:
        # questionable, maybe we need to parse bytes if encoding is
        # 'bytes' and bytes are given. Consider an extra argument,
        # (parseencoding) for the preparse otherwise.
        lineencoding = parseencoding or locale.getpreferredencoding()
        lines = [line.decode(encoding=lineencoding) for line
                 in fname.readlines()[:parselines]]
        derived = preparse(lines, firstfieldrx)
        fname.seek(0)
        try:
            filename = fname.name
        except AttributeError:  # assuming some other io
            pass
    elif hasattr(fname, 'readlines'):
        derived = preparse(fname.readlines()[:parselines], firstfieldrx)
        fname.seek(0)
        try:
            filename = fname.name
        except AttributeError:  # assuming some other io
            pass
    else:
        fmt = 'not str or has no readlines method: {}'
        raise TypeError(fmt.format(type(fname)))

    # in any case where encoding is not given or encoding is 'bytes',
    # loadtxt send bytes to the converter.
    if bytesalert and 'converters' in derived:
        try:
            for key in derived['converters']:
                derived['converters'][key] = _floatit_bytes
        except TypeError:
            # converters is None
            pass

    if chnames:
        derived['usecols'] = sorted(chnames)  # the integer keys (columns)
        packnames = chnames
    elif 'usecols' in loadtxtkwargs:
        usecols = loadtxtkwargs['usecols']
        usecols = type(usecols) is int and (usecols,) or usecols
        packnames = derived.get('chnames', {})
        for key in set(packnames) - set(usecols):
            packnames.pop(key, None)
        derived['usecols'] = usecols
    else:
        packnames = derived.get('chnames', {})

    loadtxtkwargs.pop('usecols', None)
    derived.pop('chnames', None)

    derived.update(loadtxtkwargs)
    derived.update(unpack=True)  # enforce unpack (transpose)
    derived.update(ndmin=2)      # enforce ndim=2 (for single col or row)

    data = np.loadtxt(fname, **derived)

    packdata = {col: array for col, array in
                zip(sorted(derived['usecols']), data)}

    pack = cp.ChannelPack(data=packdata, chnames=packnames)
    pack.fn = filename

    return pack


# backwards compatibility
txtpack = lazy_loadtxt_pack


# np.loadtxt(fname, dtype=<type 'float'>, comments='#', delimiter=None,
# converters=None, skiprows=0, usecols=None, unpack=False, ndmin=0,
# encoding='bytes', max_rows=None)


def textpack(fname, chnames=None, delimiter=None, skiprows=0, usecols=None,
             names=False, encoding=None, converters=None, stripstrings=False,
             debug=False):
    """Make a ChannelPack from delimited text data.

    First line of data is the line following skiprows.

    First line of data determines what fields (splitted by delimiter)
    can be converted to a float. Fields that can't be converted to float
    will be treated as strings. Converters in converters are used if
    given.

    Numeric fields with decimal comma are understood as numeric (if
    delimiter is not a comma).

    Parameters:
    fname : str, file or io stream
    chnames : dict
        Keys are integers (0-based column numbers) and values are
        channel names. If provided it will be set in the pack and is
        mutually exclusive with the usecols argument.
    delimiter : str or bytes
        If not given, any white space is assumed. If fname is a stream
        of bytes, delimiter must be bytes if not None.
    skiprows : int
        The number of lines to ignore in the top of fname. First line
        following skiprows is data.
    usecols : sequence or int
        The columns to read. A single integer means read that one
        column. Ignore if chnames is given.
    names : bool
        If True, the last line of skiprows is assumed to be field names
        and will be used to set chnames in the pack. Ignored if chnames
        is given.
    encoding : str
        Use encoding to open fname. If None, use default encoding with
        io.open. Valid when fname is as string. If fname is a stream of
        bytes and encoding is given, use encoding to decode bytes in
        text fields.
    converters : dict
        A mapping of column numbers and functions. Each function take
        one string argument and return a value.
    stripstrings : bool
        For string fields, strip off leading and trailing whitespace
        resulting from whitespace around the delimiter.
    debug : bool
        If true, output the functions used on fields and the last
        successful line number read, before an exception is raised.

    """

    if usecols is not None:
        usecols = (usecols,) if type(usecols) is int else usecols

    if chnames is not None:
        usecols = sorted(chnames)
        names = False
    elif names:
        skiprows = skiprows - 1
        chnames = {}

    bytehint = False

    def datadict(fo, debugoutput=False):

        linetupler = linetuples(fo, delimiter=delimiter, usecols=usecols,
                                bytehint=bytehint, converters=converters,
                                stripstrings=stripstrings, names=names)

        debugdict = dict(funcs=next(linetupler))

        if names and usecols is not None:
            for col, name in zip(usecols, next(linetupler)):
                chnames[col] = name
        elif names:
            for col, name in enumerate(next(linetupler)):
                chnames[col] = name

        if not debugoutput:
            if usecols is not None:
                return {col: data for col, data
                        in zip(usecols, zip(*linetupler))}
            else:
                return {col: data for col, data
                        in enumerate(zip(*linetupler))}

        # Then debug is on. Do the exact same thing but loop over the
        # tuples so we can count lines and provide meaningful debug
        # output prior to an exception.
        columndata = defaultdict(list)
        try:
            for i, linetuple in enumerate(linetupler):
                debugdict['linum'] = i
                if usecols is not None:
                    for column, value in zip(usecols, linetuple):
                        columndata[column].append(value)
                else:
                    for column, value in enumerate(linetuple):
                        columndata[column].append(value)
        except Exception:
            for i, converter in enumerate(debugdict['funcs']):
                print('converter func field', i, converter)
            print('last successful parse 1-based line number:',
                  debugdict['linum'] + skiprows + 1)
            print('Traceback follows...')
            raise

        return columndata

    if type(fname) is str:
        with io.open(fname, encoding=encoding) as fo:
            for i in range(skiprows):
                fo.readline()
            packdict = datadict(fo, debugoutput=debug)

    else:                       # some kind of io
        if type(fname.read(1)) is bytes:
            bytehint = encoding or True
        fname.seek(0)
        for i in range(skiprows):
            fname.readline()
        packdict = datadict(fname, debugoutput=debug)

    return cp.ChannelPack(data=packdict, chnames=chnames or {})


def linetuples(fo, bytehint=False, delimiter=None, usecols=None,
               converters=None, stripstrings=False, names=False):
    """Yield data tuples from io stream fo.

    First yield is the list of functions that will be used (for
    debug).

    """

    # require an io stream with readline method. don't concern about
    # encoding here. but have a flag for bytes decoding if the io stream
    # is bytes.

    # process data from given stream position.

    # usecols is a sequence to this function

    # bytehint argument: True means bytes are coming in, but don't
    # decode them. A string means bytes are coming in and the string is
    # a codec for decoding them. With bytes io the given delimiter must
    # be byte(s)

    # stripstrings True means to strip white space from things that are
    # not numeric data.

    # names True means fo is on the line of names and a split of this
    # line will be the second yield (after funcs).

    encoding = bytehint

    def as_is(s):
        return s

    def as_is_stripped(s):
        return s.strip()

    def as_is_decode(b):
        return b.decode(encoding)

    def as_is_stripped_decode(b):
        return b.strip().decode(encoding)

    if names:
        fieldnames = [field.strip() for field in
                      fo.readline().strip().split(delimiter)]

    firstvals = fo.readline().strip().split(delimiter)  # delimiter bytes?
    funcs = []
    for val in firstvals:
        try:
            float(val)          # works with bytes too
            funcs.append(float)
            continue
        except ValueError:
            pass
        try:
            if not bytehint:
                _floatit(val)
                funcs.append(_floatit)
            else:
                _floatit_bytes(val)
                funcs.append(_floatit_bytes)
            continue
        except ValueError:
            if not stripstrings:
                if type(bytehint) is not str:
                    funcs.append(as_is)
                else:
                    funcs.append(as_is_decode)
            else:
                if type(bytehint) is not str:
                    funcs.append(as_is_stripped)
                else:
                    funcs.append(as_is_stripped_decode)

    # If any of the floating funcs is the func for decimal comma, then
    # assume all floating funcs should be for decimal comma. Problem is
    # with numbers that are 0, the usual float succeed.
    decfloatfunc = _floatit if not bytehint else _floatit_bytes
    if decfloatfunc in funcs:
        funcs = [decfloatfunc if func is float else func for func in funcs]

    # Replace functions with caller functions if any
    if converters:
        for key in converters:
            funcs[key] = converters[key]

    allcols = range(len(firstvals))
    if usecols is None:
        usecols = allcols

    yield tuple(funcs)

    if names:
        yield tuple(name for name, col in
                    zip(fieldnames, allcols) if col in usecols)

    yield tuple(func(val) for func, val, col in
                zip(funcs, firstvals, allcols) if col in usecols)

    for line in fo:
        yield tuple(func(val) for func, val, col in
                    zip(funcs, line.strip().split(delimiter), allcols)
                    if col in usecols)
