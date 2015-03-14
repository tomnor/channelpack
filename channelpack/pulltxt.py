
# -*- coding: UTF-8 -*-

"""
The study of a numerical data file works by extracting matches of a
digit pattern on each row up to a count of rows. When the count of
matches start to be constant, it is assumed the data rows has
started. Comma or point is accepted as decimal delimiter. So there is
two patterns for digits. Both are tried, and the wrong one normally give
a higher count of matches on each row, because matches are then found
around the correct decimal delimiter. It is then simply assumed that the
pattern with lesser match count is the correct one.

When the decimal delimiter and start row is determined, the delimiter
for data is determined. This is done by doing a re match with the digits
found on the first row of data. Each delimiter is extracted with re
groups.

This is not too bad, because no assumption is made on what the data
delimiter is. The code here could possibly be more elegant by re
splitting on a number of optional data delimiters, but then that range
of delimiters are assumed. Let's see.

Bad is that if, say, there is only one column of data, and
data starts with only zero for a number of rows exceeding the
EQUAL_CNT_REQ. There will be no difference between the match count with
decimal comma and decimal point. Then decdel will be assumed to be
point. That can be wrong.

"""



import re, string

import numpy as np

# The scanf kind of regular expressions as suggested by python docs on
# the re module: r'[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?'
DATPRX = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?' # With decimal point.
DATCRX = r'[-+]?(?:\d+(?:,\d*)?|,\d+)(?:[eE][-+]?\d+)?' # With decimal comma.

# Consider this pattern:
# '(?<![A-Za-z])[-+]?(?:\\d+(?:,\\d*)?|,\\d+)(?:[eE][-+]?\\d+)?' (for comma)
# This comment added in dox branch because discovered that when channel names
# are cluttered with some numbers, those numbers can qualify as a valid data
# row, in case just before actual data. This is maybe risky however. Or at least
# it requires that numbers are never directly preceeded by a letter
# A-Za-z. (negative lookbehind assertion).

ALPHAS = tuple(string.lowercase + string.uppercase + '_' +  u'åäöÅÄÖ')

EQUAL_CNT_REQ = 10              # Number of rows with equal number of data
                                # pattern matches

NUMROWS = 50                    # Number of rows in total to read, (it
                                # will be <= NUMROWS).

PP = None                       # A cache of the last pull for debug.

class PatternError(Exception):
    """Raise at failure to evaluate the data file"""
    pass

class PatternPull:
    """Build useful attributes for determining decimal delimiter and
    data delimiter, and hopefully some channel names.

    Note: This class is a helper utility.
    """

    def __init__(self, fn):
        """Read a data file and build useful attributes for determining
        decimal delimiter and data delimiter, and hopefully some channel
        names.
        """
        self.fn = fn
        self.rows = None        # The rows read.
        self.matches_p = None   # match count per line using point as
                                # decimal delimiter.
        self.matches_c = None   # match count per line using comma as
                                # decimal delimiter.
        self.rts = None         # Rows to skip
        self.decdel = None      # Decimal delimiter.
        self.datdelgroups = None # re groups result on searching for data
                                 # delimiter.
        self.datdel = None       # Determined data delimiter. This will remain
                                 # None if delimiter was only white space other
                                 # than a sole tab ('\t').
        self.datrx = None        # DATPRX or DATCRX depending on file study.
        self.warnings = []       # Keep a list of (debug) warnings.
        self.cnt = None          # Resulting equal data pattern count. Should be
                                 # EQUAL_CNT_REQ.

        self.count_matches()    # File input only here.
        self.set_decdel_rts()
        self.study_datdel()

    def count_matches(self):
        """Set the matches_p, matches_c and rows attributes."""
        rows = []
        with open(self.fn) as fo:
            for i in range(NUMROWS):
                line = fo.readline()
                if not line:
                    break
                rows += [line]

        matches_p = []
        matches_c = []
        for line in rows:
            cnt = len(re.findall(DATPRX, line))
            matches_p.append(cnt)
            cnt = len(re.findall(DATCRX, line))
            matches_c.append(cnt)

        self.rows = rows        # Is newlines in the end a problem?
        self.matches_p = matches_p
        self.matches_c = matches_c

    def rows2skip(self, decdel):
        """
        Return the number of rows to skip based on the decimal delimiter
        decdel.

        When each record start to have the same number of matches, this
        is where the data starts. This is the idea. And the number of
        consecutive records to have the same number of matches is to be
        EQUAL_CNT_REQ.
        """

        if decdel == '.':
            ms = self.matches_p
        elif decdel == ',':
            ms = self.matches_c
        # else make error...

        cnt = row = 0

        for val1, val2 in zip(ms, ms[1:]):
            # val2 is one element ahead.
            row += 1
            if val2 == val1 != 0: # 0 is no matches, so it doesn't count.
                cnt += 1
            else:
                cnt = 0

            if cnt == EQUAL_CNT_REQ:
                break
        else:
            # print 'No break-out for', decdel, 'cnt:', cnt
            pass

        self.cnt = cnt
        return row - EQUAL_CNT_REQ  # rts.

    def set_decdel_rts(self):
        """Figure out the decimal seperator and rows to skip and set
        corresponding attributes.
        """

        lnr = max(self.rows2skip(','), self.rows2skip('.')) + 1
        # If EQUAL_CNT_REQ was not met, raise error. Implement!
        if self.cnt > EQUAL_CNT_REQ:
            raise PatternError('Did not find ' + str(EQUAL_CNT_REQ) +
                          ' data rows with equal data pattern in file: ' +
                          self.fn)
        elif self.cnt < EQUAL_CNT_REQ: # Too few rows
            raise PatternError('Less than', str(EQUAL_CNT_REQ) + 'data rows in',
                               self.fn + '?', '\nTry lower the EQUAL_CNT_REQ')
        if self.matches_p[lnr] <= self.matches_c[lnr]:
            self.decdel = '.'   # If equal, assume decimal point is used.
            self.datrx = DATPRX
        else:
            self.decdel = ','        # Assume the lesser count is correct.
            self.datrx = DATCRX

        self.rts = self.rows2skip(self.decdel)

    def study_datdel(self):
        """Figure out the data delimiter."""

        nodigs = r'(\D+)'

        line = self.rows[self.rts + 1] # Study second line of data only.

        digs = re.findall(self.datrx, line)
        pat = nodigs.join(digs)
        m = re.search(pat, line)
        groups = m.groups()

        # If the count of data on the row is 1, the groups tuple (the
        # data delimiters) is empty.
        if not groups:
            self.datdelgroups = groups
            return              # self.datdel remain None.

        rpt_cnt = groups.count(groups[0])

        if rpt_cnt != len(groups):
            self.warnings.append('Warning, data seperator not consistent.')

        if groups[0].strip():
            # If a delimiter apart from white space is included, let that be the
            # delimiter for numpys loadtxt.
            self.datdel = groups[0].strip()
        elif groups[0] == '\t':
            # If specifically a tab as delimiter, use that.
            self.datdel = groups[0]
        # For other white space delimiters, let datdel remain None.

        # work-around for the event that numbers clutters the channel names and
        # rts is one number low:
        res = [dat.strip() for dat in self.rows[self.rts].split(self.datdel)
               if dat.strip()]
        if not all([re.match(self.datrx, dat) for dat in res]):
            self.rts += 1
            print 'DEBUG: rts was adjusted with 1'

        # Keep the groups for debug:
        self.datdelgroups = groups

    def loadtxtargs(self):
        """Return a dict (kwargs) to provide to numpys loadtxt, based on the
        resulting attributes.

        The usecols attribute is set to be all columns in the file. This
        is done because some data file exporters put an (extra) data
        delimiter just after last data on each row. This is not
        expected by numpys loadtxt, but it's not a problem if the usecols
        item is set."""

        d = dict()
        d.update(delimiter=self.datdel, skiprows=self.rts)

        if self.decdel == '.':
            cols = range(self.matches_p[self.rts + 1]) # First valid row of data.
        else:
            cols = range(self.matches_c[self.rts + 1])
            # Converter needed for float, decdel is comma:
            convd = {}
            for i in cols:
                convd[i] = _floatit
                d.update(converters=convd)
        d.update(usecols=cols)
        # d.update(unpack=True)   # Un-packable by default. Yes, but this is not
        # the task of this class to decide.

        return d

    def channel_names(self, usecols=None):
        """Attempt to extract the channel names from the data
        file. Return a list with names. Return None on failed attempt.

        usecols: A list with columns to use. If present, the returned
        list will include only names for columns requested. It will
        align with the columns returned by numpys loadtxt by using the
        same keyword (usecols).
        """

        # Search from [rts - 1] and up (last row before data). Split respective
        # row on datdel. Accept consecutive elements starting with alphas
        # character after strip. If the count of elements equals the data count
        # on row rts + 1, accept it as the channel names.

        if self.decdel == '.':
            datcnt = self.matches_p[self.rts]
        elif self.decdel == ',':
            datcnt = self.matches_c[self.rts]

        if usecols and max(usecols) >= datcnt:
            mess = ' Max column index is '
            raise IndexError(str(usecols) + mess + str(datcnt - 1))

        names = None
        if not self.rts:                        # Only data.
            return None

        for row in self.rows[self.rts - 1::-1]: # From last row before data and up.
            splitlist = row.split(self.datdel) # datdel might be None,
                                               # (whitespace).
            for i, word in enumerate(splitlist):
                if not word.strip().startswith(ALPHAS):
                    break
                elif i + 1 == datcnt: # Accept
                    names = [ch.strip() for ch in splitlist[:datcnt]]
                    break
            if names:
                break

        if usecols:
            names = [names[i] for i in sorted(usecols)]

        return names

def _floatit(s):
    """Convert string s to a float. s use ',' as a decimal delimiter."""
    return float(s.replace(',', '.'))

# TODO: Make some sort of closure function to get the instance of PatternPull,
# so that the global PP variable can be removed. This function can have some
# optional argument to get the last instance if any. (Not thread safe? Yea, but
# come on. Need to worry about that?)

def loadtxt(fn, **kwargs):
    """Study the text data file fn. Call numpys loadtxt with keyword
    arguments based on the study.

    Return data returned from numpy `loadtxt <http://docs.scipy.org/doc/numpy/reference/generated/numpy.loadtxt.html#numpy-loadtxt>`_.

    kwargs: keyword arguments accepted by numpys loadtxt. Any keyword
    arguments provided will take prescedence over the ones resulting
    from the study.

    Set the module attribute PP to the instance of PatternPull used.

    """
    global PP
    PP = PatternPull(fn)
    txtargs = PP.loadtxtargs()
    # kwargs.pop('unpack', None) # Let me handle this one. No. Why? User.
    txtargs.update(kwargs)      # Let kwargs dominate.
    return np.loadtxt(fn, **txtargs)

def loadtxt_asdict(fn, **kwargs):
    """Return what is returned from loadtxt as a dict.

    The 'unpack' keyword is enforced to True.
    The keys in the dict is the column numbers loaded. It is the
    integers 0...N-1 for N loaded columns, or the numbers in usecols."""

    kwargs.update(unpack=True)
    d = loadtxt(fn, **kwargs)
    if len(np.shape(d)) == 2:
        keys = kwargs.get('usecols', None) or range(len(d))
        D = dict([(k, v) for k, v in zip(keys, d)])
    elif len(np.shape(d)) == 1:
        keys = kwargs.get('usecols', None) or [0]
        D = dict([(keys[0], d)])
    else:
        raise Exception('Unknown dimension of loaded data.')

    return D

