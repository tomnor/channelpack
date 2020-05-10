# -*- coding: utf-8 -*-

"""This module provides the ChannelPack class.

Example
-------

>>> import channelpack as cp
>>> pack = cp.ChannelPack(data={0: ('A', 'B', 'C', 'C', 'D'),
                                1: (22, 22, 10, 15, 15)})

>>> pack
ChannelPack(
data={0: array(['A', 'B', 'C', 'C', 'D'], dtype='|S1'),
      1: array([22, 22, 10, 15, 15])},
chnames={})

>>> pack.set_chnames({0: 'section', 1: 'seats'})
>>> pack
ChannelPack(
data={0: array(['A', 'B', 'C', 'C', 'D'], dtype='|S1'),
      1: array([22, 22, 10, 15, 15])},
chnames={0: 'section',
         1: 'seats'})

>>> pack('section')
array(['A', 'B', 'C', 'C', 'D'], dtype='|S1')

>>> pack.mask = pack('section') == 'C'
>>> pack('section', part=0)
array(['C', 'C'], dtype='|S1')

>>> pack('seats', part=0)
array([10, 15])
"""
import re
from collections import Counter, namedtuple

import numpy as np

from . import pulldbf, pullxl
from . import datautils


class IntKeyDict(dict):
    """Subclass of dict that only accepts integers as keys."""

    def __init__(self, *args, **kwargs):
        if args and (len(args) > 1 or isinstance(args[0], str)):
            super(IntKeyDict, self).__init__(*args, **kwargs)  # delegate fail
        self.update(*args, **kwargs)

    def __setitem__(self, key, value):
        if not isinstance(key, int):
            raise TypeError(self._key_error_message(key))
        super(IntKeyDict, self).__setitem__(key, value)

    def update(self, *args, **kwargs):

        # only concern about keys being integers, let parent handle
        # other dict violations
        if args and isinstance(args[0], dict):
            for key in args[0]:
                if not isinstance(key, int):
                    raise TypeError(self._key_error_message(key))

        elif args and (hasattr(args[0], '__iter__') and not
                       isinstance(args[0], str)):
            for seq in args[0]:
                if hasattr(seq, '__len__') and len(seq) > 2:
                    break       # not our problem
                elif (hasattr(seq, '__getitem__') and not
                      isinstance(seq[0], int)):
                    raise TypeError(self._key_error_message(seq[0]))

        for key, value in kwargs.items():
            if not isinstance(key, int):
                raise TypeError(self._key_error_message(key))

        super(IntKeyDict, self).update(*args, **kwargs)

    def setdefault(self, key, value=None):
        if not isinstance(key, int):
            raise TypeError(self._key_error_message)
        super(IntKeyDict, self).setdefault(key, value)

    def _key_error_message(self, key):
        return 'Only integer keys accepted, got: {}'.format(repr(key))


class NpDict(IntKeyDict):
    """Subclass of IntKeyDict converting values to np.ndarray as necessary.

    Values are expected to be flat sequences. If the resulting numpy
    array has ndim != 1, ValueErrror is raised.

    """

    def __init__(self, *args, **kwargs):
        if args and (len(args) > 1 or isinstance(args[0], str)):
            super(NpDict, self).__init__(*args, **kwargs)  # delage fail
        self.update(*args, **kwargs)

    def __setitem__(self, key, value):
        proxyarr = np.array(value, copy=False)
        # let non-int key error raise first
        super(NpDict, self).__setitem__(key, proxyarr)
        if proxyarr.ndim != 1:
            raise ValueError('ndim != 1 in resulting array')

    def update(self, *args, **kwargs):

        proxyargs = []
        proxykwargs = {}

        if args and isinstance(args[0], dict):
            proxydict = {}
            for key in args[0]:
                proxydict[key] = np.array(args[0][key], copy=False)

            proxyargs.append(proxydict)
            # append any (invalid) additional items in args to get familiar
            # errors from dict constructor:
            proxyargs += args[1:]

        elif args and hasattr(args[0], '__iter__'):
            proxypairs = []
            # loop over the key, value pairs
            for seq in args[0]:
                if hasattr(seq, '__getitem__'):
                    proxyarr = np.array(seq[-1], copy=False)
                    # let possible invalid length of key, value pairs remain
                    proxypairs.append([val for val in seq[:-1]] + [proxyarr])
                else:           # just append what was given
                    proxypairs.append(seq)

            proxyargs.append(proxypairs)
            # append any (invalid) additional items in args to get familiar
            # errors from dict constructor:
            proxyargs += args[1:]

        elif args:              # a number of positional arguments (err)
            proxyargs = args

        for key, value in kwargs.items():
            proxykwargs[key] = np.array(value, copy=False)

        # first report on key and other dict errors
        super(NpDict, self).update(*proxyargs, **proxykwargs)
        self._audit_ndim()

    def setdefault(self, key, value=None):
        proxyval = np.array(value, copy=False)
        # let non-int key error raise first
        super(NpDict, self).setdefault(key, proxyval)
        if proxyval.ndim != 1:
            raise ValueError('ndim != 1 in resulting array')

    def _audit_ndim(self):
        """Walk through all arrays and check ndim == 1.

        Assumes all values has ndim attribute. Raise ValueError on first
        ndim !=1 found.
        """

        for key, arr in self.items():
            if arr.ndim != 1:
                raise ValueError('ndim != 1 for key {}'.format(key))


class ChannelPack(object):
    """Callable collection of data.

    Hold a dict of data (numpy 1d arrays) and make possible to refer to
    them by calls of this object, (pack(ch)). A boolean mask is kept
    with the pack, used to optionally filter out sections of data in
    calls.

    Attributes
    ----------
    data : dict
        Dict with numpy arrays. The dict is not supposed to be accessed
        directly, call the ChannelPack object to refer to arrays. Keys
        are integers representing column numbers.
    mask : numpy.ndarray
        A boolean array of the same size as the data arrays. Initially
        all True.
    nof : str or None
        'nan', 'filter' or None. In calls to the object, this attribute
        is consulted to determine how to return data arrays. If None,
        arrays are returned as is (the default). If 'nan', elements in
        the returned array with corresponding False element in `mask`
        are replaced with numpy.nan or None, equivalent to
        `np.where(array, mask, np.full(len(array), np.nan))`. 'filter'
        yeilds the equivalent to `array[mask]` -- the array is stripped
        down to elements with corresponding True elements in `mask`. The
        effect of this attribute can be overridden in calls of the
        object.
    chnames : dict
        Keys are integers representing column numbers (like in `data`),
        values are strings, the channel names. Keys in `chnames` aligned
        with keys in `data` makes it possible to refer to arrays by
        channel names. This alignment is not enforced.
    FALLBACK_PREFIX : str
        Defaults to 'ch'. This can be used in calls of the pack in place
        of a "proper" name. If 4 is a key in the data dict, pack('ch4')
        can be used to get at that data. This is also used as requested
        in calls to the `records` method. Everything after this prefix
        is assumed to be a number. The prefix should be a valid python
        variable name.
    fn : str
         File name of a possible source data file. After initialization
         it is up to the caller to set this attribute.
    filenames : list of str
        If `fn` is set in some other pack, or this attribute is not
        empty in some other pack provided to the method `append_pack`,
        the file name of the other pack is appended to the `filenames`
        attribute of this pack.

    """
    nofvalids = ('nan', 'filter', None)
    id_rx = r'[^\d\W]\w*'       # valid python identifier in some string

    def __init__(self, data=None, chnames=None):
        """Initiate a ChannelPack

        Convert given sequences in `data` to numpy arrays if necessary.

        Parameters
        ----------
        data : dict
            Keys are integers representing column numbers, values are
            sequences representing column data.
        chnames : dict
            Keys are integers representing column numbers (like in
            data), values are strings, the channel names.

        """
        self.FALLBACK_PREFIX = 'ch'
        self.data = NpDict(data or {})
        # self.set_datadict(data)  # set self.data
        self.fn = ''             # Possible file name
        self.filenames = []
        self.chnames = IntKeyDict(chnames or {})
        self.nof = None
        self.mask_reset()       # set self.mask

    def __setattr__(self, name, value):
        if name == 'nof' and value not in ChannelPack.nofvalids:
            raise ValueError('Expected one of ' + repr(ChannelPack.nofvalids))
        elif name == 'FALLBACK_PREFIX' and not isinstance(value, str):
            raise TypeError('Expected a string')
        elif name == 'mask' and not isinstance(value, np.ndarray):
            raise TypeError('Expected a numpy array')
        elif name == 'data' and not isinstance(value, NpDict):
            object.__setattr__(self, name, NpDict(value))
            self.mask_reset()
        elif name == 'chnames' and not isinstance(value, IntKeyDict):
            object.__setattr__(self, name, IntKeyDict(value))
        else:
            object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name in ('FALLBACK_PREFIX', 'data', 'fn',
                    'filenames', 'chnames', 'nof'):
            raise AttributeError('Cannot delete {}'.format(name))
        else:
            object.__delattr__(self, name)

    def set_nof(self, value):
        """Set the nof attribute to value.

        See class attributes description for the meaning of `nof`.

        Parameters
        ----------
        value : str or None
            If str it shall be one of 'nan' or 'filter', else None.

        Raises ValueError if value is not one of 'nan', 'filter' or
        None.

        """

        self.nof = value

    def set_chnames(self, chnames):
        """Set the chnames attribute to chnames.

        Parameters
        ----------
        chnames : dict
            Keys in the dict should correspond with the integer keys in
            the data attribute. Values are any str channel names.

        Raises
        ------
        TypeError if keys are not integers.

        """

        self.chnames = chnames

    def set_data(self, data):
        """Convert sequences to numpy arrays as needed.

        This method replaces any existing data with `data`.

        Parameters
        ----------
        data : dict

        Raises
        ------
        TypeError
            If keys are not integers.
        ValueError
            If a value in dict are not a sequence that result in a numpy
            array with ndim equal to 1, (1D array).

        """
        self.data = data
        self.mask_reset()

    def append_pack(self, other):
        """Append data from other into this pack.

        If this pack has data (attribute data is non-empty), it has to
        have the same set of keys as other.data (if that is non-empty).
        Same is true for the attribute chnames.

        Array dtypes in respective pack.data are at the mercy of numpy
        append function.

        If the attribute fn is not the empty string in other, append
        other.fn to the filenames list attribute. Ignore
        other.filenames.

        mask_reset is called after the append.

        Parameters
        ----------
        other : ChannelPack instance

        Raises
        ------
        ValueError
            If non-empty dicts in packs do not align.

        """

        if not self.data:
            self.set_data(other.data)
        elif other.data:
            if not set(self.data.keys()) == set(other.data.keys()):
                raise ValueError('Data dicts set of keys not equal')
            for key in other.data:
                self.data[key] = np.append(self.data[key], other.data[key])

        if not self.chnames:
            self.set_chnames(other.chnames)
        elif other.chnames:
            if not set(self.chnames.keys()) == set(other.chnames.keys()):
                raise ValueError('chnames dicts set of keys not equal')

        if self.fn and self.fn not in self.filenames:
            self.filenames.append(self.fn)
        if other.fn:
            self.filenames.append(other.fn)

        self.mask_reset()

    def mask_reset(self):
        """Set the mask attribute to the length of data and all True.

        If this pack's data dict is empty, set mask to an empty array.
        Size of the mask is based on the array with the lowest key in
        data.

        """

        if not self.data:
            self.mask = np.array([])
        else:
            lowest = sorted(self.data)[0]
            self.mask = self.data[lowest] == self.data[lowest]

    def min_duration(self, duration, samplerate=1):
        """Require each true part to be at least duration long.

        Make false any true part in the mask attribute that is not
        `duration` long. Any true part in the packs mask attribute not
        fulfilling duration together with samplerate will be set to
        false.

        Parameters
        ----------
        duration : int or float
        samplerate : int or float
            If samplerate is 10 and duration is 1, a True part of
            minimum 10 elements is required.

        Returns
        -------
        The possibly altered mask.

        """

        req_duration = int(duration * samplerate)
        for sc in self.slicelist():
            if sc.stop - sc.start < req_duration:
                self.mask[sc] = False

        return self.mask

    def startstop(self, startb, stopb, apply=True):
        """Start and stop trigger masking.

        Elements in startb and stopb are start and stop triggers for
        masking. A true stop dominates a true start.

        Parameters
        ----------
        startb, stopb : sequence
            Elements are tested with `if el...`
        apply : bool
            If True, apply the result of this method to the mask
            attribute by anding it, (mask &= result).

        Returns
        -------
        A bool ndarray, the result of this method.

        Example
        -------
        One descend

        height: 1 2 3 4 5 4 3 2 1
        startb: F F F F T F F F F (height == 5)
        stobb:  T F F F F F F F T (height == 1)
        result: F F F F T T T T F
        -> height:      5 4 3 2

        """

        result = np.array(tuple(datautils.startstop_bool(startb, stopb)))
        if apply:
            self.mask &= result
        return result

    def slicelist(self):
        """Return a slicelist based on self.mask.

        Return a list of python slice objects corresponding to the True
        sections in self.mask. If mask is all True, there is one slice
        in the list covering the whole mask. The len of returned list
        corresponds to the number of True sections in self.mask.

        """
        return datautils.slicelist(self.mask)

    def parts(self):
        """Return the enumeration of the True parts.

        The list is always consecutive or empty. Each index in the
        returned list can be used to refer to a True part in the mask
        attribute.

        """

        return list(range(len(self.slicelist())))  # 2&3

    def counter(self, ch, part=None, nof=None):
        """Return a counter on the channel ch.

        A collections.Counter instance.

        Parameters
        ----------
        ch: string or integer.
            The channel key, name or fallback string.
        part: int
            The 0-based enumeration of a True part to return. Overrides
            any setting of the nof attribute.
        nof : str
            One of 'nan', 'filter' or 'ignore'. Providing this argument
            overrides any setting of the corresponding attribute `nof`,
            and have the same effect on the returned data as the
            attribute `nof`. The value 'ignore' can be used to get the
            full array despite a setting of the attribute `nof`.

        """

        return Counter(self(self.datakey(ch), part=part, nof=nof))

    def __call__(self, ch, part=None, nof=None):
        """Return data from "channel" ch.

        If `part` is not given, return the array for `ch` respecting the
        setting of attribute `nof`. See the class attributes description
        for the meaning of `nof`.

        Parameters
        ----------
        ch : str or int
            The channel key, name or fallback string. The lookup order
            is keys in the data dict, names in the chnames dict and
            finally if `ch` matches a fallback string.
        part : int
            The 0-based enumeration of a True part to return. Overrides
            the effect of attribute or argument `nof`.
        nof : str
            One of 'nan', 'filter' or 'ignore'. Providing this argument
            overrides any setting of the corresponding attribute `nof`,
            and have the same effect on the returned data as the
            attribute `nof`. The value 'ignore' can be used to get the
            full array despite a setting of the attribute `nof`.

        """

        key = self.datakey(ch)

        if part is not None:
            sl = self.slicelist()
            try:
                return self.data[key][sl[part]]
            except IndexError:
                raise IndexError(str(part) + ' is out of range')
        elif nof == 'nan':
            return datautils.masked(self.data[key], self.mask)
        elif nof == 'filter':
            return self.data[key][self.mask]
        elif nof == 'ignore':
            return self.data[key]
        elif self.nof == 'nan':
            return datautils.masked(self.data[key], self.mask)
        elif self.nof == 'filter':
            return self.data[key][self.mask]
        elif self.nof:
            raise ValueError('nof = ' + repr(nof))
        else:
            return self.data[key]

    def records(self, part=None, nof=None, fallback=False):
        """Return a generator producing records of the pack.

        Each record is supplied as a collections.namedtuple with the
        channel names as field names. This is useful if each record make
        a meaningful data set on its own.

        Parameters
        ----------
        part : int
            The 0-based enumeration of a True part to return. Overrides
            the effect of attribute or argument `nof`.
        nof : str
            One of 'nan', 'filter' or 'ignore'. Providing this argument
            overrides any setting of the corresponding attribute `nof`,
            and have the same effect on the returned data as the
            attribute `nof`. The value 'ignore' can be used to get all
            the records despite a setting of the attribute `nof`.
        fallback: bool
            The named tuple requires python-valid naming. If fallback is
            False, ValueError is raised if any of the names in chnames
            is an invalid identifier. fallback=True will use
            FALLBACK_PREFIX to produce names.

        Raises
        ------
        ValueError
            In iteration of the generator if any of the names used for
            the namedtuple is invalid python identifiers.

        """

        # fixme: use the name method and add a firstwordonly argument
        # here. But then the pack call has to be done on keys.
        names = [self.chnames[key] for key in sorted(self.chnames)]
        if fallback:
            names = [self.FALLBACK_PREFIX + str(key) for key in
                     sorted(self.data)]

        try:
            Record = namedtuple('Record', names)
        except ValueError:      # bad names
            raise ValueError('Includes invalid names: {}'.format(names))

        for record in map(Record._make, zip(*[self(name, part=part, nof=nof)
                                              for name in names])):
            yield record

    def datakey(self, ch):
        """Return the integer key for ch.

        Parameters
        ----------
        ch : int or str
            The channel key, name or fallback string. The lookup order
            is keys in the data dict, names in the chnames dict and
            finally if `ch` matches a fallback string.

        Raises
        ------
        KeyError
            If `ch` do not evaluate to a key in the data dict.

        """

        if ch in self.data:
            return ch

        # if ch is an int and we are here, there is no match
        if isinstance(ch, int):
            raise KeyError('{} not in data'.format(ch))

        for key, name in self.chnames.items():
            if ch == name:
                if key not in self.data:
                    fmt = '{} value in chnames with key {} but {} not in data'
                    raise KeyError(fmt.format(name, key, key))
                return key

        # not in data, not a good name in chnames, last chance is a
        # fallback string

        prefix_rx = self.FALLBACK_PREFIX + r'(\d+)'
        m = re.match(prefix_rx, ch)

        if m:
            key = int(m.group(1))
            if key in self.data:
                return key

        raise KeyError

    def name(self, ch, firstwordonly=False, fallback=False):
        """Return a name string for channel `ch` in chnames.

        A helper method to get a name string, possibly modified
        according to arguments. Succeeds only if `ch` corresponds to a
        key in data.

        Parameters
        ----------
        ch: int or str.
            The channel key or name. An integer key has precedence.
        firstwordonly: bool or str
            If True, return only the first space-stripped word in the
            name. If a string, use as a regex pattern with re.findall on
            the name string and return the first element found.
        fallback : bool
            If True, return the fallback string <FALLBACK_PREFIX><N>,
            where N corresponds to the data key. Ignore the
            firstwordonly argument.

        """

        key = self.datakey(ch)

        if fallback:
            return self.FALLBACK_PREFIX + str(key)

        if not firstwordonly:
            return self.chnames[key]
        elif firstwordonly is True:
            return self.chnames.split()[0]
        elif type(firstwordonly) is str:
            return re.findall(firstwordonly, self.chnames[key])[0]
        else:
            raise TypeError(firstwordonly)

    def __repr__(self):
        """Return a string representing creation of the pack.

        """

        fmtstr = 'ChannelPack(\ndata={{{}}},\nchnames={{{}}})'
        datjoinstr = ',\n      '
        chjoinstr = ',\n         '
        datkeyvalstr = (datjoinstr.join(str(key) + ': ' + repr(self.data[key])
                                        for key in sorted(self.data.keys())))
        chkeyvalstr = (chjoinstr.join(str(key) + ': ' + repr(self.chnames[key])
                                      for key in sorted(self.chnames.keys())))

        return fmtstr.format(datkeyvalstr, chkeyvalstr)


def dbfpack(fn, usecols=None):
    """Return a ChannelPack instance loaded with dbf data file fn.

    This is a lazy function to get a loaded instance, using pulldbf
    module."""

    loadfunc = pulldbf.dbf_asdict
    cp = ChannelPack(loadfunc)
    cp.load(fn, usecols)
    names = pulldbf.channel_names(fn, usecols)
    cp.set_channel_names(names)
    # cp.set_basefilemtime()
    return cp


def sheetpack(fn, sheet=0, header=True, startcell=None, stopcell=None,
              usecols=None):
    """Return a ChannelPack instance loaded with data from the spread
    sheet file fn, (xls, xlsx).

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

    startcell: str
        If given, a spread sheet style notation of the cell where reading
        start, ("F9").

    stopcell: str
        A spread sheet style notation of the cell where data end,
        ("F9").

    usecols: str or seqence of ints
        The columns to use, 0-based. 0 is the spread sheet column
        "A". Can be given as a string also - 'C:E, H' for columns C, D,
        E and H.

    Might not be a favorite, but the header row can be offset from the
    data range. The meaning of usecols is then applied on both the data
    range and the header row. However, usecols is always specified with
    regards to the data range.
    """

    cp = ChannelPack(pullxl.sheet_asdict)
    chnames = []
    cp.load(fn, sheet=sheet, header=header, startcell=startcell,
            stopcell=stopcell, usecols=usecols, chnames_out=chnames)

    cp.set_channel_names(chnames or None)
    return cp
