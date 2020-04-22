# -*- coding: utf-8 -*-
"""
Funtions for reading data from text files.
"""
from __future__ import print_function
import re
from collections import namedtuple

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


def preparse(lines):
    """Populate a dict with keyword arguments to use with data readers.

    Works with numerical data files only, which might have a header with
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
        fields = [field.strip() for field in line.split(delimiter)]
        if len(fields) != validcounts[-1].numcnt:
            continue
        else:
            chnames = {colnum: field for colnum, field in enumerate(fields)}
            break

    kwdict = dict(skiprows=startline, delimiter=delimiter,
                  converters=converters, chnames=chnames,
                  usecols=tuple(range(validcounts[-1].numcnt)))

    return kwdict


# np.loadtxt(fname, dtype=<type 'float'>, comments='#', delimiter=None,
# converters=None, skiprows=0, usecols=None, unpack=False, ndmin=0,
# encoding='bytes', max_rows=None)
