import struct
import datetime
import itertools

import numpy as np


# dbfreader based on Raymond Hettinger recipe
# http://code.activestate.com/recipes/362715/

# dbf spec
# http://www.clicketyclick.dk/databases/xbase/format/dbf.html#DBF_STRUCT

def dbfreader(f):
    """Returns an iterator over records in a Xbase DBF file.

    The first row returned contains the field names.
    The second row contains field specs: (type, size, decimal places).
    Subsequent rows contain the data records.
    If a record is marked as deleted, it is skipped.

    File should be opened for binary reads.

    """

    numrec, lenheader = struct.unpack('<xxxxLH22x', f.read(32))
    numfields = (lenheader - 33) // 32

    fields = []
    for fieldno in range(numfields):
        name, typ, size, deci = struct.unpack('<11sc4xBB14x', f.read(32))
        name = name.replace(b'\0', b'')       # eliminate NULs from string
        fields.append((name.decode('ascii'), typ, size, deci))
    yield [field[0] for field in fields]
    yield [tuple(field[1:]) for field in fields]

    terminator = f.read(1)
    assert terminator == b'\r'

    fields.insert(0, ('DeletionFlag', 'C', 1, 0))
    fmt = ''.join(['%ds' % fieldinfo[2] for fieldinfo in fields])
    fmtsiz = struct.calcsize(fmt)
    for i in range(numrec):
        record = struct.unpack(fmt, f.read(fmtsiz))
        if record[0] != b' ':
            continue                        # deleted record
        result = []
        for (name, typ, size, deci), value in zip(fields, record):
            if name == 'DeletionFlag':
                continue
            if typ == b"N":
                value = value.replace(b'\0', b'').lstrip()
                if value == b'':
                    value = np.NaN
                elif deci:
                    value = float(value)
                else:
                    value = int(value)
            elif typ == b'D':
                y, m, d = int(value[:4]), int(value[4:6]), int(value[6:8])
                value = datetime.date(y, m, d)
            elif typ == b'L':
                value = ((value in b'YyTt' and 'T') or
                         (value in b'NnFf' and 'F') or '?')
            elif typ == b'F':    # Can this type not be null?
                value = float(value)
            elif typ == b'C':
                value = value.decode('ascii')
            result.append(value)
        yield result


def dbf_asdict(fn, usecols=None, keystyle='ints'):
    """Return data from dbf file fn as a dict.

    fn: str
        The filename string.

    usecols: seqence
        The columns to use, 0-based.

    keystyle: str
        'ints' or 'names' accepted. Should be 'ints' (default) when this
        function is given to a ChannelPack as loadfunc. If 'names' is
        used, keys will be the field names from the dbf file.

    """

    if keystyle not in ['ints', 'names']:
        raise ValueError('Unknown keyword: ' + str(keystyle))

    with open(fn, 'rb') as fo:
        rit = dbfreader(fo)
        names = rit.next()
        specs = rit.next()      # NOQA
        R = [tuple(r) for r in rit]

    def getkey(i):
        if keystyle == 'ints':
            return i
        else:
            return names[i]

    R = zip(*R)
    d = dict()
    for i in usecols or range(len(names)):
        # d[getkey(i)] = R['f' + str(i)]  # Default numpy fieldname
        d[getkey(i)] = np.array(R[i])
    return d


def channel_names(fn, usecols=None):
    """Return the field names (channel names) from dbf file fn. With
    usecols, return only names corresponding to the integers in
    usecols."""

    with open(fn, 'rb') as fo:
        names = dbfreader(fo).next()

    return usecols and [names[i] for i in usecols] or names
