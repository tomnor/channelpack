import struct
import datetime
from collections import namedtuple

import numpy as np

from .readtext import contextopen
from .pack import ChannelPack

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
        name = name.decode('ascii')
        fields.append((name, typ, size, deci))
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
            if typ == b'N':
                value = value.replace(b'\0', b'').lstrip()
                if value == b'':
                    value = np.nan
                elif deci:
                    value = float(value)
                else:
                    value = int(value)
            elif typ == b'D':
                if value.strip():
                    y, m, d = int(value[:4]), int(value[4:6]), int(value[6:8])
                    value = datetime.date(y, m, d)
                else:
                    value = None
            elif typ == b'L':
                value = ((value in b'YyTt' and 'T')
                         or (value in b'NnFf' and 'F') or '?')
            elif typ == b'F':
                if value.strip():
                    value = float(value)
                else:
                    value = np.nan
            else:
                value = value.decode('ascii')  # type = 'C' or other type
            result.append(value)
        yield result


FI = namedtuple('FieldInfo', ('name', 'typ', 'size', 'deci',
                              'fmt', 'fmtsiz', 'keep', 'seekme'))


def dbfrecords(f, names):
    """Returns an iterator over records in a Xbase DBF file.

    The first row returned contains the field names. The second row
    contains field specs: (type, size, decimal places). Subsequent rows
    contain the data records. If a record is marked as deleted, it is
    skipped.

    names is the field names to extract.

    File should be opened for binary reads.

    """
    numrec, lenheader = struct.unpack('<xxxxLH22x', f.read(32))
    numfields = (lenheader - 33) // 32

    # discarded in main loop
    fields = [FI('DeletionFlag', 'C', 1, 0,
                 '1s', struct.calcsize('1s'), True, 0)]

    for fieldno in range(numfields):
        name, typ, size, deci = struct.unpack('<11sc4xBB14x', f.read(32))
        name = name.replace(b'\0', b'')       # eliminate NULs from string
        name = name.decode('ascii')
        fmt = str(size) + 's'
        prev = fields[fieldno]
        fi = FI(name, typ, size, deci, fmt,
                struct.calcsize(fmt), name in names, prev.seekme + prev.size)
        fields.append(fi)

    selfields = [field for field in fields if field.keep]
    yield [field.name for field in selfields[1:]]
    yield [tuple(field[1:4]) for field in selfields[1:]]

    terminator = f.read(1)
    assert terminator == b'\r'

    for i in range(numrec):
        refaddr = f.tell()
        record = []
        for field in selfields:
            f.seek(refaddr + field.seekme)
            record.append(struct.unpack(field.fmt, f.read(field.fmtsiz))[0])

        if record[0] != b' ':
            continue                        # deleted record
        result = []
        for sf, value in zip(selfields, record):
            if sf.name == 'DeletionFlag':
                continue
            if sf.typ == b'N':
                value = value.replace(b'\0', b'').lstrip()
                if value == b'':
                    value = np.nan
                elif sf.deci:
                    value = float(value)
                else:
                    value = int(value)
            elif sf.typ == b'D':
                if value.strip():
                    y, m, d = int(value[:4]), int(value[4:6]), int(value[6:8])
                    value = datetime.date(y, m, d)
                else:
                    value = None
            elif sf.typ == b'L':
                value = ((value in b'YyTt' and 'T')
                         or (value in b'NnFf' and 'F') or '?')
            elif sf.typ == b'F':
                if value.strip():
                    value = float(value)
                else:
                    value = np.nan
            else:
                value = value.decode('ascii')  # type = 'C' or other type
            result.append(value)
        f.seek(refaddr + fields[-1].seekme + fields[-1].fmtsiz)
        yield result


def dbfpack(dbf, names=None):
    """Make a ChannelPack from dbf data file.

    Parameters
    ----------
    dbf : str or file
        If a file it should be opened for binary reads.
    names : list of str
        A sequence of names to read. If not provided read all.

    """

    if not names:
        with contextopen(dbf, 'rb') as context:
            fo = context.fo
            dbfrecs = dbfreader(fo)
            fieldnames = next(dbfrecs)
            next(dbfrecs)       # specs
            columns = zip(*dbfrecs)

        data = {i: column for i, column in enumerate(columns)}
        chnames = {i: name for i, name in enumerate(fieldnames)}
        pack = ChannelPack(data, chnames)
        pack.fn = context.name
        return pack

    with contextopen(dbf, 'rb') as context:
        fo = context.fo
        sniffnames = dbfreader(fo)
        allnames = next(sniffnames)
        fo.seek(0)
        dbfrecs = dbfrecords(fo, names)
        next(dbfrecs)
        next(dbfrecs)
        columns = zip(*dbfrecs)

    chnames = {}
    for i, name in enumerate(allnames):
        if name in names:
            chnames[i] = name  # duplicates possible

    data = {i: column for i, column in zip(sorted(chnames), columns)}
    pack = ChannelPack(data, chnames)
    pack.fn = context.name

    return pack
