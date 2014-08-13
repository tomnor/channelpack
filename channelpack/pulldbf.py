
import struct, datetime, decimal, itertools

import numpy as np

# Created by Raymond Hettinger on Tue, 11 Jan 2005 (PSF) 
# http://code.activestate.com/recipes/362715/
# There is also a writer there. Keep in mind, should I need it.
def dbfreader(f):
    """Returns an iterator over records in a Xbase DBF file.

    The first row returned contains the field names.
    The second row contains field specs: (type, size, decimal places).
    Subsequent rows contain the data records.
    If a record is marked as deleted, it is skipped.

    File should be opened for binary reads.

    """
    # See DBF format spec at:
    #     http://www.pgts.com.au/download/public/xbase.htm#DBF_STRUCT

    numrec, lenheader = struct.unpack('<xxxxLH22x', f.read(32))    
    numfields = (lenheader - 33) // 32

    fields = []
    for fieldno in xrange(numfields):
        name, typ, size, deci = struct.unpack('<11sc4xBB14x', f.read(32))
        name = name.replace('\0', '')       # eliminate NULs from string   
        fields.append((name, typ, size, deci))
    yield [field[0] for field in fields]
    yield [tuple(field[1:]) for field in fields]

    terminator = f.read(1)
    assert terminator == '\r'

    fields.insert(0, ('DeletionFlag', 'C', 1, 0))
    fmt = ''.join(['%ds' % fieldinfo[2] for fieldinfo in fields])
    fmtsiz = struct.calcsize(fmt)
    for i in xrange(numrec):
        record = struct.unpack(fmt, f.read(fmtsiz))
        if record[0] != ' ':
            continue                        # deleted record
        result = []
        for (name, typ, size, deci), value in itertools.izip(fields, record):
            if name == 'DeletionFlag':
                continue
            if typ == "N":
                value = value.replace('\0', '').lstrip()
                if value == '':
                    value = 0
                elif deci:
                    value = float(value)
                    # value = decimal.Decimal(value) Not necessary.
                else:
                    value = int(value)
            elif typ == 'D':
                y, m, d = int(value[:4]), int(value[4:6]), int(value[6:8])
                value = datetime.date(y, m, d)
            elif typ == 'L':
                value = (value in 'YyTt' and 'T') or (value in 'NnFf' and 'F') or '?'
            elif typ == 'F':
                value = float(value)
            result.append(value)
        yield result


def numpytypes(field_specs):
    """Return a comma-separated string to provide to numpy as value to
    numpys dtype function.

    field_specs is the second record from Hettingers dbf iterator,
    "dbfreader"."""

    typestr = ''
    for spec in field_specs:
        typ, size, deci = spec
        if typ == 'N' and deci or typ == 'F':
            typestr += 'f4,'
        elif typ == 'N':
            typestr += 'i4,'
        elif typ == 'D':
            typestr += 'object,' # datetime
        else:                    # Assume a string then?
            typestr += 'a{},'.format(size)
            
    return typestr[:-1]

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

    if not keystyle in ['ints', 'names']:
        raise ValueError('Unknown keyword: ' + str(keystyle))
    
    with open(fn, 'rb') as fo:
        rit = dbfreader(fo)
        names = rit.next()
        specs = rit.next()
        R = [tuple(r) for r in rit]

    def getkey(i):
        if keystyle == 'ints': 
            return i
        else:
            return names[i]

    R = np.array(R, dtype=numpytypes(specs))
    d = dict()
    for i in usecols or range(len(names)):
        d[getkey(i)] = R['f' + str(i)]  # Default numpy fieldname
    return d

def channel_names(fn, usecols=None):
    """Return the fieldnames (channel names) from dbf file fn. With
    usecols, return only names corresponding to the integers in
    usecols."""
    
    with open(fn, 'rb') as fo:
        names = dbfreader(fo).next()

    return usecols and [names[i] for i in usecols] or names # A bit too smart.
                       
