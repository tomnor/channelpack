
# -*- coding: UTF-8 -*-

"""Provide ChannelPack. Provide lazy functions to get loaded instances
of ChannelPack.

:class:`~channelpack.ChannelPack` is a class holding data read from some
data file. It takes a function as its only argument for ``__init__``.
The function is responsible for returning a dict with numpy 1d arrays
corresponding to the "channels" in the data file. Keys are integers
corresponding to the "columns" used, 0-based. The load-function is
called with an instance of ChannelPack by calling
:meth:`~channelpack.ChannelPack.load`.

Making a pack
=============

There are functions in this module for easy pack creation:
:func:`~txtpack`, :func:`~dbfpack`, :func:`~sheetpack`. Using one of
those, a call to load is not necessary::

    >>> import channelpack as cp
    >>> tp = cp.txtpack('testdata/sampledat2.txt')
    >>> for k in sorted(tp.chnames):
    ...     print tp.name(k)
    ...
    RPT
    B_CACT
    P_CACT
    VG_STOP
    AR_BST
    PLRT_1
    TOQ_BUM

    # Arrays are callable by name or column number
    >>> tp('RPT') is tp(0)
    True

Setting the mask
================

The ChannelPack is holding a dict with numpy arrays and provide ways to
get at them by familiar names or column numbers, as just shown. The pack
also holds a Boolean array, initially all true. channelpack calls the
array ``mask``, and it is of the same length as the channels in the
pack::

    >>> import numpy as np
    >>> np.all(tp.mask)
    True
    >>> tp(0).size == tp.mask.size
    True

The mask is used to retrieve specific parts from the channels or to
filter the returned data::

    >>> sp = cp.sheetpack('testdata/sampledat3.xls')
    >>> for k in sorted(sp.chnames):
    ...     print k, sp.name(k)
    ...
    0 txtdata
    1 nums
    2 floats

    >>> sp('txtdata')
    array([u'A', u'A', u'C', u'D', u'D'],
          dtype='<U1')

    >>> sp.mask = (sp('txtdata') == 'A') | (sp('txtdata') == 'D')
    >>> sp.mask
    array([ True,  True, False,  True,  True], dtype=bool)
    >>> sp('txtdata', 0)
    array([u'A', u'A'],
          dtype='<U1')
    >>> sp('txtdata', 1)
    array([u'D', u'D'],
          dtype='<U1')
    >>> sp('txtdata', 2)
    Traceback (most recent call last):
        ...
    IndexError: list index out of range

The above example try to say that *parts* are chunks of the channel
elements that has corresponding True elements in the mask. And they are
retrieved by adding an enumeration of the part in the call for the
channel, see :meth:`~channelpack.ChannelPack.__call__`.

For filtering, an attribute ``nof`` is set to the string 'filter'::

    >>> sp.nof = 'filter'
    >>> sp('txtdata')
    array([u'A', u'A', u'D', u'D'],
          dtype='<U1')

The attribute ``nof`` can have the values 'filter', ``None`` or 'nan'.
``None`` mean that the attribute has no effect. The effect of 'nan' is
that elements that is not corresponding to a True element in ``mask`` is
replaced with ``numpy.nan`` or ``None`` in calls::

    >>> sp.nof = 'nan'
    >>> sp('txtdata')
    array([u'A', u'A', None, u'D', u'D'], dtype=object)
    >>> sp('nums')
    array([   0.,   30.,   nan,   90.,  120.])

Calls for a specific part are not affected by the attribute ``nof``::

    >>> sp('txtdata', 1)
    array([u'D', u'D'],
          dtype='<U1')

Calling load on a running instance
==================================

If the pack is to be loaded with a new data set that is to be subjected
to the same conditions, do like this::

    >>> sp.add_condition('cond', "(%('txtdata') == 'A') | (%('txtdata') == 'D')")
    >>> sp.pprint_conditions()
    cond1: (%('txtdata') == 'A') | (%('txtdata') == 'D')
    ...

Note that the string for the condition is the same as in the above
assignment (``sp.mask = (sp('txtdata') == 'A') | (sp('txtdata') ==
'D')``) with the identifier for the pack replaced with ``%``. Now a new
file with the same data lay-out can be loaded and receive the same
state::

    >>> sp.load('testdata/sampledat4.xls', stopcell='c6')
    >>> sp('txtdata')
    array([u'A', None, None, None, u'D'], dtype=object)
    >>> sp.nof = None
    >>> sp('txtdata')
    array([u'A', u'C', u'C', u'C', u'D'],
          dtype='<U1')

    array([A, C, C, C, D], dtype=object)
"""
import re
from collections import Counter, namedtuple

import numpy as np

from . import pulltxt, pulldbf, pullxl
from . import datautils


class IntKeyDict(dict):
    """Subclass of dict that only accepts integers as keys."""
    def __init__(self, *args, **kwargs):
        if len(args) > 1:       # dict fail
            super(IntKeyDict, self).__init__(*args, **kwargs)
        self.update(*args, **kwargs)

    def __setitem__(self, key, value):
        if not isinstance(key, int):
            raise TypeError(self._key_error_message(key))
        super(IntKeyDict, self).__setitem__(key, value)

    def update(self, *args, **kwargs):

        # only concern about keys being integers, let parent handle
        # other dict violations
        if args and isinstance(args[0], dict):
            for key in args[0].keys():
                if not isinstance(key, int):
                    raise TypeError(self._key_error_message(key))

        elif args and hasattr(args[0], '__iter__'):
            for seq in args[0]:
                if hasattr(seq, '__len__') and len(seq) > 2:
                    break       # not our problem
                if hasattr(seq, '__getitem__') and not isinstance(seq[0], int):
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
    """Subclass of IntKeyDict casting values to np.ndarray as necessary.

    Values are expected to be flat sequences. If the resulting numpy
    array has ndim != 1, ValueErrror is raised.

    """

    def __init__(self, *args, **kwargs):
        if len(args) > 1:       # dict fail
            super(NpDict, self).__init__(*args, **kwargs)
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
        arrays are returned as is. If 'nan', elements in the returned
        array with corresponding False element in `mask` are replaced
        with numpy.nan or None, equivalent to `np.where(array, mask,
        np.full(len(array), np.nan))`. 'filter' yeilds the equivalent to
        `array[mask]` -- the array is stripped down to elements with
        corresponding True elements in `mask`. The effect of this
        attribute can be overridden in calls of the object.
    chnames : dict
        Keys are integers representing column numbers (like in `data`),
        values are strings, the channel names. A populated `chnames`
        attribute aligned with `data` (having the same set of keys)
        makes it possible to refer to arrays by channel names.
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

    def __init__(self, data={}, chnames={}):
        """Initiate a ChannelPack

        Convert given sequences in `data` to numpy arrays if necessary.

        Parameters
        ----------
        data : dict
            Keys are integers representing column numbers, values are
            sequences representing column data.
        chnames : dict
            Keys are integers representing column numbers (like in D),
            values are strings, the channel names.

        """
        self.FALLBACK_PREFIX = 'ch'
        self.data = NpDict(data)
        # self.set_datadict(data)  # set self.data
        self.fn = ''             # Possible file name
        self.filenames = []
        self.chnames = IntKeyDict(chnames)
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
            raise TypeError('Expected a NpDict')
        else:
            object.__setattr__(self, name, value)

    def set_nof(self, value):
        """Set the nof attribute to value.

        See class attributes description for the meaning of `nof`.

        value : str or None
            If str it shall be one of 'nan' or 'filter', else None.

        Raises ValueError if value is not one of 'nan', 'filter' or
        None.

        """

        self.nof = value

    def set_chnames(self, chnames):
        """Set the attribute chnames to chnames.

        chnames : dict
            Keys in the dict shall correspond with the keys in the
            data dict attribute D. Values are any str channel names.

        """

        self.chnames = IntKeyDict(chnames)

    def set_datadict(self, D):
        """Convert sequences to numpy arrays as needed.

        Raise TypeError if not all keys in data are integers.

        data : dict"""

        # FIXME: when do we check that all arrays are the same size, because it
        # is a requirement, right?

        for key, vals in D.items():
            if not isinstance(key, int):
                raise TypeError('Expected keys to be int: ' + repr(key))
            if isinstance(vals, np.ndarray):
                self.data[key] = vals
            else:
                self.data[key] = np.array(vals)

    def append_pack(self, other):
        """Append data from other into this pack.

        other : ChannelPack instance
            Non-empty data and chnames dicts in this object and the
            provided pack must have equal set of keys, else ValueError
            is raised.

        FIXME: filename(s)?

        """
        if not self.data:
            self.set_datadict(other._D)
        elif other._D:
            if not set(self.data.keys()) == set(other._D.keys()):
                raise ValueError('Data dicts set of keys not equal')
            for key in other._D.keys():
                self.data[key] = np.append(self.data[key], other._D[key])

        if not self.chnames:
            self.set_chnames(other.chnames)
        elif other.chnames:
            if not set(self.chnames.keys()) == set(other.chnames.keys()):
                raise ValueError('chnames dicts set of keys not equal')

        # FIXME: when do we check (require) alignment between keys in
        # self.data and self.chnames? -- Might be just to document the
        # fact that ChannelPack do not take responsibility for this. If
        # a name value in chnames has a corresponding key in datadict
        # and the name is used in a call, we just return that data. If
        # the name is not in chnames values, there will be a key error.

        if other.filenames:
            self.filenames += other.filenames
        elif other.fn:
            self.filenames.append(other.fn)

        self.mask_reset()

    def mask_reset(self):
        """Set the attribute mask to the length of data and all True.

        If this pack's data dict is empty, set mask to an empty
        array.

        """

        if not self.data:
            self.mask = np.array([])
        else:
            somekey = [key for key in self.data.keys()][0]  # 2&3
            self.mask = self.data[somekey] == self.data[somekey]

    def min_duration(self, duration, samplerate=1):
        """Require each true part to be at least duration long.

        Make False any true part in the mask attribute that is not
        `duration` long. Any True part in the packs mask attribute not
        fulfilling duration together with samplerate will be set to
        False.

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

        return list(range(len(self.slicelist()))) # 2&3

    def counter(self, ch, part=None):
        """Return a counter on the channel ch.

        ch: string or integer.
            The channel index number or channel name.

        part: int
            The 0-based enumeration of a True part to return. Overrides
            any setting of the nof attribute.

        See `Counter
        <https://docs.python.org/2.7/library/collections.html#counter-objects>`_
        for the counter object returned.

        FIXME: add nof argument

        """

        return Counter(self(self.datakey(ch), part=part))

    def __call__(self, ch, part=None, nof=None):
        """Return data from "channel" ch.

        If `part` is not given, return the array for `ch` respecting the
        setting of attribute `nof`. See the class attributes description
        for the meaning of `nof`.

        Parameters
        ----------
        ch : str or int
            The channel index number, name or fallback string. The
            lookup order is keys in the data dict, names in the chnames
            dict and finally if `ch` matches a fallback string.
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

    def records(self, part=None, fallback=True):
        """Return an iterator over the records in the pack.

        Each record is supplied as a namedtuple with the channel names
        as field names. This is useful if each record make a meaningful
        data set on its own.

        part: int
            Same meaning as in
            :meth:`~channelpack.ChannelPack.__call__`.

        fallback: boolean
            The named tuple requires python-valid naming. If fallback is
            False, there will be an error if ``self.chnames`` is not
            valid names and not None. If True, fall back to the
            ``self.chnames_0`` on error.

        FIXME: add nof argument and update this documentation and audit
               the code.
        """

        names_0 = [self.chnames_0[k] for k in sorted(self.chnames_0.keys())]
        if self.chnames is not None:
            names = [self.chnames[k] for k in sorted(self.chnames.keys())]

        try:
            Record = namedtuple('Record', names)
        except NameError:       # no names
            Record = namedtuple('Record', names_0)
            names = names_0
        except ValueError:      # no good names
            if fallback:
                Record = namedtuple('Record', names_0)
                names = names_0
            else:
                raise

        for tup in zip(*[self(name, part) for name in names]):
            yield Record(*tup)

    def datakey(self, ch):
        """Return the integer key for ch.

        ch : int or str
            The channel index number, name or fallback string. The
            lookup order is keys in the data dict, names in the chnames
            dict and finally if `ch` matches a fallback string.

        Raise KeyError if `ch` do not correspond to any key in the data
        dict.

        """

        # doc for ch same as in __call__

        if ch in self.data:
            return ch

        for key, name in self.chnames.items():
            if ch == name:
                if key not in self.data.keys():
                    raise KeyError(ch)
                return key

        # not in D, not a name in chnames, last chance is a fallback
        # string

        try:
            key = int(ch.split(self.FALLBACK_PREFIX)[-1])
        except AttributeError:  # ch was an int? but not in D.
            raise KeyError(ch)
        except ValueError:      # no number in end of fallback str
            raise KeyError(ch)

        if key in self.data.keys():
            return key
        else:
            raise KeyError

    def name(self, ch, firstwordonly=False, fallback=False):
        """Return channel name string for ch.

        ch: str or int.
            The channel name or key.

        firstwordonly: bool or "pattern".
            If True, return only the first non-spaced word in the name,
            a name in the attribute chnames. If a string, use as a
            re-pattern with re.findall and return the first element
            found. There will be error if no match. r'\w+' is a good
            pattern for excluding leading and trailing obscure
            characters.

        fallback : bool
            If True, return the fallback string <FALLBACK_PREFIX><N>.
            Ignore the firstwordonly argument.
        """

        key = self.datakey(ch)
        if fallback:
            return self.FALLBACK_PREFIX + str(key)

        if not firstwordonly:
            return self.chnames[key]
        elif firstwordonly is True:
            return self.chnames[key].split()[0]
        else:
            return re.findall(firstwordonly, self.chnames[key])[0]


def txtpack(fn, **kwargs):
    """Return a ChannelPack instance loaded with text data file fn.

    Attempt to read out custom channel names from the file and call
    instance.set_channel_names(). Then return the pack.

    This is a lazy function to get a loaded instance, using the
    cleverness provided by pulltxt module. No delimiter or rows-to-skip
    and such need to be provided. However, if necessary, `**kwargs` can
    be used to override clevered items to provide to numpys
    loadtxt. usecols might be such an item for example. Also, the
    cleverness is only clever if all data is numerical.

    Note that the call signature is the same as numpys `loadtxt
    <http://docs.scipy.org/doc/numpy/reference/generated/numpy.loadtxt.html#numpy-loadtxt>`_, which look like this::

        np.loadtxt(fname, dtype=<type 'float'>, comments='#',
        delimiter=None, converters=None, skiprows=0, usecols=None,
        unpack=False, ndmin=0)

    But, when using this function as a wrapper, the only meaningful
    argument to override should be `usecols`.
"""

    loadfunc = pulltxt.loadtxt_asdict
    cp = ChannelPack(loadfunc)
    cp.load(fn, **kwargs)
    names = pulltxt.PP.channel_names(kwargs.get('usecols', None))
    cp.set_channel_names(names)
    cp._patpull = pulltxt.PP    # Give a reference to the patternpull.
    # cp.set_basefilemtime()
    return cp


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
