# -*- coding: utf-8 -*-
"""This module provides the ChannelPack class.

See docs at https://channelpack.readthedocs.org/en/latest/

"""
import re
from collections import namedtuple

import numpy as np

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
            super(NpDict, self).__init__(*args, **kwargs)  # delegate fail
        self.update(*args, **kwargs)

    def __setitem__(self, key, value):
        array = np.array(value, copy=False)
        self._check_raise_ndim(array, value)
        super(NpDict, self).__setitem__(key, array)

    def update(self, *args, **kwargs):

        proxyargs = []
        proxykwargs = {}

        if args and isinstance(args[0], dict):
            proxydict = {}
            for key in args[0]:
                array = np.array(args[0][key], copy=False)
                self._check_raise_ndim(array, args[0][key])
                proxydict[key] = array

            proxyargs.append(proxydict)
            # append any (invalid) additional items in args to get familiar
            # errors from dict constructor:
            proxyargs += args[1:]

        elif args and hasattr(args[0], '__iter__'):
            proxypairs = []
            # loop over the key, value pairs
            for seq in args[0]:
                if hasattr(seq, '__getitem__'):
                    array = np.array(seq[-1], copy=False)
                    self._check_raise_ndim(array, seq[-1])
                    # let possible invalid length of key, value pairs remain
                    proxypairs.append([val for val in seq[:-1]] + [array])
                else:           # just append what was given
                    proxypairs.append(seq)

            proxyargs.append(proxypairs)
            # append any (invalid) additional items in args to get familiar
            # errors from dict constructor:
            proxyargs += args[1:]

        elif args:              # a number of positional arguments (err)
            proxyargs = args

        for key, value in kwargs.items():
            array = np.array(value, copy=False)
            self._check_raise_ndim(array, value)
            proxykwargs[key] = array

        super(NpDict, self).update(*proxyargs, **proxykwargs)

    def setdefault(self, key, value=None):
        array = np.array(value, copy=False)
        self._check_raise_ndim(array, value)
        super(NpDict, self).setdefault(key, array)  # return? FIXME

    def _check_raise_ndim(self, array, value):
        """Check array for ndim == 1 and raise error if fail.
        """
        if array.ndim != 1:
            raise ValueError('array.ndim != 1 results from', value)


class ChannelPack(object):
    """Callable collection of data.

    Hold a dict of data (numpy 1d arrays) and make possible to refer to
    them by calls of this object, (`pack(ch)`). A boolean mask is kept
    with the pack, used to optionally filter out sections of data in
    calls.

    Attributes
    ----------
    data : dict
        The dict is not supposed to be consulted directly, call the
        ChannelPack object to refer to arrays. Keys are integers
        representing column numbers. Setting this attribute to a new
        dict of data will convert values to numpy arrays and call
        mask_reset() automatically.
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
    names : dict
        Keys are integers representing column numbers (like in `data`),
        values are strings, the field names. Keys in `names` aligned
        with keys in `data` makes it possible to refer to arrays by
        field names. This alignment is not enforced.
    FALLBACK_PREFIX : str
        Defaults to 'ch'. This can be used in calls of the pack in place
        of a "proper" name. If 4 is a key in the data dict, pack('ch4')
        can be used to get at that data. This is also used as requested
        in calls to the `records` method. Everything after this prefix
        is assumed to be a number. The prefix should be a valid python
        variable name.
    fn : str
         File name of a possible source data file. After initialization
         it is up to the caller to set this attribute, else it is the
         empty string.
    filenames : list of str
        Maintained by the pack when setting `fn`. Extended with
        `other.filenames` in calls to `append_pack(other)`. A list of
        one or more empty strings if `fn` is not set.

    """
    nofvalids = ('nan', 'filter', None)
    id_rx = r'[^\d\W]\w*'       # valid python identifier in some string

    def __init__(self, data=None, names=None):
        """Initiate a ChannelPack

        Convert given sequences in `data` to numpy arrays if necessary.

        Parameters
        ----------
        data : dict
            Keys are integers representing column numbers, values are
            sequences representing column data.
        names : dict
            Keys are integers representing column numbers (like in
            data), values are strings, the field names.

        """
        self.FALLBACK_PREFIX = 'ch'
        self.data = NpDict(data or {})
        self.filenames = []
        self.fn = ''             # Possible file name
        self.names = IntKeyDict(names or {})
        self.nof = None
        self.mask_reset()       # set self.mask

    def __setattr__(self, name, value):
        if name == 'nof' and value not in ChannelPack.nofvalids:
            raise ValueError('Expected one of ' + repr(ChannelPack.nofvalids))
        elif name == 'FALLBACK_PREFIX' and not isinstance(value, str):
            raise TypeError('Expected a string')
        elif name == 'mask' and not isinstance(value, np.ndarray):
            raise TypeError('Expected a numpy array')
        elif name == 'mask':
            object.__setattr__(self, name, value)
            self._cached_slicelist = self._slicelist()
        elif name == 'data' and not isinstance(value, NpDict):
            object.__setattr__(self, name, NpDict(value))
            self.mask_reset()
        elif name == 'names' and not isinstance(value, IntKeyDict):
            object.__setattr__(self, name, IntKeyDict(value))
        elif name == 'fn':
            if not isinstance(value, str):
                raise TypeError('Expected a string')
            elif not self.filenames:
                self.filenames.append(value)
            else:
                self.filenames[0] = value
            object.__setattr__(self, name, value)
        else:
            object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name in ('FALLBACK_PREFIX', 'data', 'fn',
                    'filenames', 'names', 'nof'):
            raise AttributeError('Cannot delete {}'.format(name))
        else:
            object.__delattr__(self, name)

    def append_pack(self, other):
        """Append data from other into this pack.

        If this pack has data (attribute data is non-empty), it has to
        have the same set of keys as other.data (if that is non-empty).
        Same is true for the attribute names.

        Array dtypes in respective pack.data are at the mercy of numpy
        append function.

        Extend `filenames` with `other.filenames`.

        mask_reset is called after the append.

        Parameters
        ----------
        other : ChannelPack instance
            The other pack.

        Raises
        ------
        ValueError
            If non-empty dicts in packs do not align.

        """

        if not self.data:
            self.data = other.data
        elif other.data:
            if not set(self.data.keys()) == set(other.data.keys()):
                raise ValueError('Data dicts set of keys not equal')
            for key in other.data:
                self.data[key] = np.append(self.data[key], other.data[key])

        if not self.names:
            self.names = other.names
        elif other.names:
            if not set(self.names.keys()) == set(other.names.keys()):
                raise ValueError('names dicts set of keys not equal')

        self.filenames.extend(other.filenames)

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

    def duration(self, duration, samplerate=1, mindur=True):
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
        mindur : bool
            If False, require parts to be at most duration long instead.

        Returns
        -------
        array
            The possibly altered mask.

        """

        req_duration = int(duration * samplerate)

        for sc in self._cached_slicelist:
            part_duration = sc.stop - sc.start
            if part_duration < req_duration and mindur:
                self.mask[sc] = False
            elif part_duration > req_duration and not mindur:
                self.mask[sc] = False

        # need to reset _cached_slicelist because the __setattr__ is not called
        # when mask is manipulated this way
        self._cached_slicelist = self._slicelist()

        return self.mask

    def startstop(self, startb, stopb, apply=True):
        """Start and stop trigger masking.

        Elements in startb and stopb are start and stop triggers for
        masking. A true stop dominates a true start.

        Parameters
        ----------
        startb : sequence
        stopb : sequence
            Elements are tested with `if el...`
        apply : bool
            If True, apply the result of this method to the mask
            attribute by anding it, (mask &= result).

        Returns
        -------
        array
            A bool ndarray, the result of this method.

        Example
        -------
        One descend::

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

    def _slicelist(self):
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

        return list(range(len(self._cached_slicelist)))  # 2&3

    def __call__(self, ch, part=None, nof=None):
        """Return data from "channel" ch.

        If `part` is not given, return the array for `ch` respecting the
        setting of attribute `nof`. See the class attributes description
        in :class:`~channelpack.ChannelPack` for the meaning of `nof`.

        Parameters
        ----------
        ch : str or int
            The channel key, name or fallback string. The lookup order
            is keys in the data dict, names in the names dict and
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

        key = self._datakey(ch)

        if part is not None:
            sl = self._cached_slicelist
            try:
                return self.data[key][sl[part]]
            except IndexError:
                raise IndexError(str(part) + ' is out of parts range')
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

        Each record is provided as a collections.namedtuple with the
        packs names as field names. This is useful if each record make
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
            False, ValueError is raised if any of the names in `names`
            is an invalid identifier. fallback=True will use
            FALLBACK_PREFIX to produce names.

        Raises
        ------
        ValueError
            In iteration of the generator if any of the names used for
            the namedtuple is invalid python identifiers.

        Note
        ----
        Either there must be names defined in the pack or argument
        `fallback` must be True, else there will be no records.

        """

        names = [self.names[key] for key in sorted(self.names)]
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

    def _datakey(self, ch):
        """Return the integer key for ch.

        Parameters
        ----------
        ch : int or str
            The channel key, name or fallback string. The lookup order
            is keys in the data dict, names in the names dict and
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

        for key, name in self.names.items():
            if ch == name:
                if key not in self.data:
                    fmt = '{} value in names with key {} but {} not in data'
                    raise KeyError(fmt.format(name, key, key))
                return key

        # not in data, not a good name in names, last chance is a
        # fallback string

        prefix_rx = self.FALLBACK_PREFIX + r'(\d+)'
        m = re.match(prefix_rx, ch)

        if m:
            key = int(m.group(1))
            if key in self.data:
                return key

        raise KeyError(ch)

    def name(self, ch, firstwordonly=False, fallback=False):
        """Return a name string for channel `ch` in names.

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

        key = self._datakey(ch)

        if fallback is True:
            return self.FALLBACK_PREFIX + str(key)
        elif fallback:
            raise TypeError('`fallback` should be True or False')

        if not firstwordonly:
            return self.names[key]
        elif firstwordonly is True:
            return self.names[key].split()[0]
        elif type(firstwordonly) is str:
            mlist = re.findall(firstwordonly, self.names[key])
            if mlist:
                return mlist[0]
            raise ValueError('No match with regex: {}'.format(firstwordonly))
        else:
            raise TypeError(firstwordonly)

    def __repr__(self):
        """Return a string representing creation of the pack.

        """

        fmtstr = 'ChannelPack(\ndata={{{}}},\nnames={{{}}})'
        datjoinstr = ',\n      '
        nmjoinstr = ',\n       '
        datkeyvalstr = (datjoinstr.join(str(key) + ': ' + repr(self.data[key])
                                        for key in sorted(self.data.keys())))
        nmkeyvalstr = (nmjoinstr.join(str(key) + ': ' + repr(self.names[key])
                                      for key in sorted(self.names.keys())))

        return fmtstr.format(datkeyvalstr, nmkeyvalstr)
