
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
import glob, fnmatch
import os, time
import ConfigParser
from collections import OrderedDict, Counter

import numpy as np
import xlrd

from . import pulltxt, pulldbf, pullxl
from . import datautils

ORIGINEXTENSIONS =  []
"""A list of file extensions excluding the dot. See
:py:meth:`~.ChannelPack.set_basefilemtime` for a description.
"""

CHANNELPACK_RC_FILE = '.channelpackrc'
"""The humble rc file of channelpack. It can exist and have a section
``[channelpack]``. In this section, an option is ``originextensions``
with a comma separated list of extensions as value that will be loaded
to the ORIGINEXTENSIONS list on import of channelpack. Use
`os.path.expanduser('~')` to see where channelpack look for this file,
and then place it there.
"""

CONFIG_FILE = "conf_file.cfg"
_CONFIG_SECS = ['channels',  'conditions']

_COND_PREFIXES = ['cond', 'startcond', 'stopcond', 'stopextend',  'duration',
                 'samplerate']
_ADDABLES = ['cond', 'startcond', 'stopcond']

FALLBACK_PREFIX = 'ch'

NONES = [None, 'None', 'none', "''", '""', '']

CHANNEL_IDENTIFIER_RX = r'[\w ]+'
"""Pattern used to find format strings for the channel identifiers. The
pattern can be monkey patched for specific needs. It is used as is, not
compiled or held by some instance of something apart from this module in
the python session."""

CHANNEL_FMT_RX = r"""%\(["']?({})["']?\)""" # Allowing quotes to remain
"""Pattern used for the format string. The enclosing part around the
channel identifier. It includes the re group, which must remain, (the
inner-most ``()``). The ``{}`` part is replaced with
CHANNEL_IDENTIFIER_RX."""

class ChannelPack:
    """Pack of data. Hold a dict with channel index numbers as keys
    (column number). This object is callable by channel name or index.
    """

    def __init__(self, loadfunc=None):
        """Return a pack

        loadfunc is a function that returns a dict holding numpy
        arrays, being the channels. Keys are the index integer numbers,
        (column numbers). Each array is of np.shape(N,).

        See method :meth:`~channelpack.ChannelPack.load`.

        """
        self.loadfunc = loadfunc
        self.D = None           # Dict of data
        self.fn = None          # The loaded filename
        self.chnames = None       # Channel names maybe. dict
        self.chnames_0 = None     # Fall back names, always available. ch0,
                                  # ch1... dict

        self.keys = None          # Sorted list of keys for the data dict
        self.rec_cnt = 0          # Number of records
        self.nof = None          # 'nan', 'filter' or None (nan or filter)

        self.mask = None
        self.conconf = _ConditionConfigure(self)
        self.no_auto = False

    def load(self, *args, **kwargs):
        """Load data using loadfunc.

        args, kwargs:
            forward to the loadfunc. args[0] must be the filename, so it
            means that loadfunc must take the filename as it's first
            argument.

        Set the filename attribute.

        .. note::
           Updates the mask if not no_auto.

        ChannelPack is assuming a need for loading data from disc. If
        there is a desire to load some made-up data, a filename pointing
        to some actual file is nevertheless required. Here is a
        suggestion::

            >>> import channelpack as cp
            >>> import tempfile

            >>> tf = tempfile.NamedTemporaryFile()

            >>> d = {2: np.arange(5), 5: np.arange(10, 15)}
            >>> def lf(fn):
            ...     return d
            ...

            >>> pack = cp.ChannelPack(lf)
            >>> pack.load(tf.name)
            >>> pack.filename is not None
            True
            >>> pack.chnames_0
            {2: 'ch2', 5: 'ch5'}

        """
        D = self.loadfunc(*args, **kwargs)

        if self.chnames is not None:
            if set(D) - set(self.chnames):
                raise ValueError('New data set have different keys')

        self.D = D
        self.keys = sorted(self.D.keys())
        self.rec_cnt = len(self.D[self.keys[0]]) # If not all the same, there
                                                 # should have been an error
                                                 # already

        fallnames  = _fallback_names(self.keys)
        self.chnames_0 = dict(zip(self.keys, fallnames))
        self._set_filename(args[0])
        self.set_basefilemtime()

        self.args = args
        self.kwargs = kwargs

        if not self.no_auto:
            self.make_mask()       # Called here if a reload is done on the
                                   # current instance I guess.

    def append_load(self, *args, **kwargs):
        """Append data using loadfunc.

        args, kwargs:
            forward to the loadfunc. args[0] must be the filename, so it
            means that loadfunc must take the filename as it's first
            argument.

        If self is not already a loaded instance, call load and return.

        Make error if there is a mismatch of channels indexes or
        channels count.

        Append the data to selfs existing data. Set filename to the new
        file.

        Create new attribute - a dict with meta-data on all files loaded,
        'metamulti.'

        .. note::
           Updates the mask if not no_auto.

        """
        if not self.D:
            self.load(*args, **kwargs)
            return

        newD = self.loadfunc(*args, **kwargs)

        s1, s2 = set(self.D.keys()), set(newD.keys())
        offenders = s1 ^ s2
        if offenders:
            mess = ('Those keys (respectively) were in one of the dicts ' +
                    'but not the other: {}.')
            offs = ', '.join([str(n) for n in offenders])
            raise KeyError(mess.format(offs))

        # Append the data early to fail if fail before other actions.
        for k, a in self.D.iteritems():
            self.D[k] = np.append(a, newD.pop(k))

        if not hasattr(self, 'metamulti'):
            self.metamulti = dict(filenames=[], mtimestamps=[], mtimenames=[],
                                  slices=[])

            self.metamulti['filenames'].append(self.filename)
            self.metamulti['mtimestamps'].append(self.mtimestamp)
            self.metamulti['mtimenames'].append(self.mtimefs)
            self.metamulti['slices'].append(slice(0, self.rec_cnt))


        self.rec_cnt = len(self.D[self.keys[0]])
        self._set_filename(args[0])
        self.set_basefilemtime()

        start = self.metamulti['slices'][-1].stop
        stop = self.rec_cnt

        self.metamulti['filenames'].append(self.filename)
        self.metamulti['mtimestamps'].append(self.mtimestamp)
        self.metamulti['mtimenames'].append(self.mtimefs)
        self.metamulti['slices'].append(slice(start, stop))

        if not self.no_auto:
            self.make_mask()

    def rebase(self, key, start=None, decimals=5):
        """Rebase a channel (key) on start.

        The step (between elements) need to be constant all through,
        else ValueError is raised. The exception to this is the border
        step between data loaded from two different files.

        key: int or str
            The key for the channel to rebase.

        start: int or float or None
            If specified - replace the first element in the first loaded
            data channel with start.

        decimals: int
            Diffs are rounded to this number of decimals before the step
            through arrays are checked. The diffs are otherwise likely never to
            be all equal.

        Typically this would be used to make a time channel
        continuous. Like, not start over from 0, when data is appended
        from multiple files. Or simply to rebase a channel on 'start'.

        If start is None, and the instance is loaded from one file only,
        this method has no effect.

        .. note::
           The instance channel is modified on success.

        """
        diffs = []

        def diffsappend(d, sc):
            diff = np.around(np.diff(d), decimals)
            diffs.append((diff, diff[0], sc))

        if hasattr(self, 'metamulti'):
            for sc in self.metamulti['slices']:
                diffsappend(self(key)[sc], sc)
        else:
            diffsappend(self(key), slice(0, self.rec_cnt))

        for diff, d, sc in diffs:
            if not np.all(diff == d):
                raise ValueError('All diffs not equal within ' +
                                 'indexes ' + str(sc))

        S = set([t[1] for t in diffs])
        if len(S) > 1:
            raise ValueError('Diffs not equal between appended data files: ' +
                             str(S))

        # Now modify:
        if start is None:
            start = self(key)[0]
        self.D[self._key(key)] = np.linspace(start, d * self.rec_cnt + start,
                                             num=self.rec_cnt, endpoint=False)

        assert len(self(key)) == self.rec_cnt, 'Semantic error'

    def _set_filename(self, fn):
        """Set the filename attributes. (They are multiple for personal
        reasons)."""
        fn = os.path.abspath(fn)
        self.filename = self.fs = self.fn = fn

    def set_samplerate(self, rate):
        """Set sample rate to rate.

        rate: int or float

        rate is given as samples / timeunit. If sample rate is set, it
        will have an impact on the duration rule conditions. If duration
        is set to 2.5 and samplerate is 100, a duration of 250 records
        is required for the logical conditions to be true.

        .. note::
           Updates the mask if not no_auto."""

        # Test and set value:
        float(rate)
        self.conconf.set_condition('samplerate', rate)
        if not self.no_auto:
            self.make_mask()

    def add_condition(self, conkey, cond):
        """Add a condition, one of the addable ones.

        conkey: str
            One of 'cond', startcond' or 'stopcond'. 'start' or 'stop'
            is accepted as shorts for 'startcond' or 'stopcond'. If the
            conkey is given with an explicit number (like 'stopcond3')
            and already exist, it will be over-written, else created.

            When the trailing number is implicit, the first condition
            with a value of None is taken. If no None value is found, a
            new condition is added.

        cond: str
            The condition string. See ...

        .. note::
           Updates the mask if not no_auto.

        .. seealso::
           :meth:`~channelpack.ChannelPack.set_duration`
           :meth:`~channelpack.ChannelPack.set_samplerate`
           :meth:`~channelpack.ChannelPack.set_stopextend`
           :meth:`~channelpack.ChannelPack.clear_conditions`

        """

        # Audit:
        if conkey == 'start' or conkey == 'stop':
            conkey += 'cond'
        if not any(conkey.startswith(addable) for addable in _ADDABLES):
            raise KeyError(conkey)
        if not self.conconf.valid_conkey(conkey):
            raise KeyError(conkey)

        self._parse_cond(cond)  # Checking

        conkey = self.conconf.next_conkey(conkey)
        self.conconf.set_condition(conkey, cond)

        if not self.no_auto:
            self.make_mask()       # On every update so errors are detected.

    def _parse_cond(self, cond):
        """Replace the format strings in cond with ``self.D[i]`` so it can
        be used in eval calls. Use ``CHANNEL_RX`` as pattern. Return the
        parsed string.

        This method should be exposed so that one can experiment with
        conditions and see that they are properly parsed."""

        CHANNEL_RX = CHANNEL_FMT_RX.format(CHANNEL_IDENTIFIER_RX)

        res = re.findall(CHANNEL_RX, cond)
        for ident in res:
            rx = CHANNEL_FMT_RX.format(ident)
            i = self._key(ident) # integer key

            # repl = 'self(' + str(i) + ')'
            # Cannot be. Calls (__call__) can be replaced by nan. So must call
            # the array in the dict directly:

            repl = 'self.D[' + str(i) + ']'
            cond = re.sub(rx, repl, cond) # %(<identifier>) replaced with
                                          # self.D[i]
        return cond

    def _mask_array(self, cond):
        """
        Let the Boolean array mask production be here. Call this for
        each condition. The _parse_cond method is called here.
        """
        cond = self._parse_cond(cond)
        return eval(cond)

    def spit_config(self, conf_file=None, firstwordonly=False):
        """Write a config_file based on this instance.

        conf_file: str (or Falseish)
            If conf_file is Falseish, write the file to the directory
            where self.filename sits, if self is not already associated
            with such a file. If associated, and conf_file is Falseish,
            use self.conf_file. If conf_file is a file name, write to
            that file and set self.conf_file to conf_file.

        firstwordonly: bool or "pattern"
            Same meaning as in name method, and applies to the channel
            names spitted. There is no effect on the instance channel
            names until eat_config is called.

        Sections in the ini/cfg kind of file can be:

            [channels]
            A mapping of self.D integer keys to channel names. Options
            are numbers corresponding to the keys. Values are the
            channel names, being the fallback names if custom names are
            not available (self.chnames). (When spitting that is).

            [conditions]
            Options correspond to the keys in self.conditions, values
            correspond to the values in the same.
        """

        chroot = os.path.dirname(self.filename)
        chroot = os.path.abspath(chroot)

        # Figure out file name of conf_file:
        if hasattr(self, 'conf_file') and not conf_file:
            cfgfn = self.conf_file
        elif conf_file:
            cfgfn = conf_file
        else:
            cfgfn = os.path.join(chroot, CONFIG_FILE)

        with open(cfgfn, 'wb') as fo:
            self.conconf.spit_config(fo, firstwordonly=firstwordonly)

        self.conf_file = os.path.abspath(cfgfn)

    def eat_config(self, conf_file=None):
        """
        Read the the conf_file and update this instance accordingly.

        conf_file: str or Falseish
            If conf_file is Falseish, look in the directory where
            self.filename sits if self is not already associated with a
            conf_file. If associated, and conf_file arg is Falseish,
            read self.conf_file. If conf_file arg is a file name, read
            from that file, but do not update self.conf_file
            accordingly. An Implicit IOError is raised if no conf_file
            was found.

        See spit_config for documentation on the file layout.

        .. note::
           Updates the mask if not no_auto.

        .. note::
           If the config_file exist because of an earlier spit, and
           custom channel names was not available, channels are listed as the
           fallback names in the file. Then after this eat, self.chnames
           will be set to the list in the conf_file section 'channels'. The
           result can be that self.chnames and self.chnames_0 will be
           equal.

        The message then is that, if channel names are updated, you
        should spit before you eat.

        """

        chroot = os.path.dirname(self.filename) # "channels root dir"
        chroot = os.path.abspath(chroot)

        # Figure out file name of conf_file:
        if hasattr(self, 'conf_file') and not conf_file:
            cfgfn = self.conf_file
        elif conf_file:
            cfgfn = conf_file
        else:
            cfgfn = os.path.join(chroot, CONFIG_FILE)

        with open(cfgfn, 'r') as fo:
            self.conconf.eat_config(fo)

        # Update mask:
        if not self.no_auto:
            self.make_mask()
        else:
            self.make_mask(dry=True) # Produce possible error.

    def pprint_conditions(self):
        """Pretty print conditions.

        This is the easiest (only exposed) way to view
        all conditions interactively.

        .. seealso::
           :meth:`~channelpack.ChannelPack.spit_config`
        """

        self.conconf.pprint_conditions()

    def set_stopextend(self, n):
        """Extend the True elements by n when setting the conditions
        based on a 'stopcond' condition.

        n is an integer >= 0.

        .. note::
           Updates the mask if not no_auto.
        """
        self.conconf.set_condition('stopextend', n)
        if not self.no_auto:
            self.make_mask()

    def set_duration(self, rule):
        """Set the duration according to rule.

        rule: str
            The rule operating on the variable ``dur``.

        rule is an expression like::

            >>> rule = 'dur == 150 or dur > 822'

        setting a duration rule assuming a pack sp::

            >>> sp.set_duration(rule)

        The identifier ``dur`` must be present or the rule will fail.

        .. note::
           The logical ``or`` and ``and`` operators must be used. ``dur`` is a
           primitive, not an array.

        .. note::
           Updates the mask if not no_auto.

        .. seealso::
           :meth:`~channelpack.ChannelPack.set_samplerate`
           :meth:`~channelpack.ChannelPack.add_condition`
           :meth:`~channelpack.ChannelPack.pprint_conditions`

        """

        self.conconf.set_condition('duration', rule)
        if not self.no_auto:
            self.make_mask()

    def clear_conditions(self, *conkeys, **noclear):
        """Clear conditions.

        Clear only the conditions conkeys if specified. Clear only the
        conditions not specified by conkeys if noclear is True (False
        default).

        .. note::
           Updates the mask if not no_auto.
        """

        offenders = set(conkeys) - set(self.conconf.conditions.keys())
        if offenders:
            raise KeyError(', '.join([off for off in offenders]))

        offenders = set(noclear) - set({'noclear'}) # Valid keywords subtracted
        if offenders:
            raise KeyError(', '.join([off for off in offenders]))

        noclear = noclear.get('noclear', False)

        for ck in self.conconf.conditions:
            if not conkeys:
                # self.conconf.set_condition(ck, None)
                self.conconf.reset()
                break
            elif not noclear and ck in conkeys:
                self.conconf.set_condition(ck, None)
            elif noclear and not ck in conkeys:
                self.conconf.set_condition(ck, None)

        if not self.no_auto:
            self.make_mask()

    def make_mask(self, clean=True, dry=False):
        """Set the attribute self.mask to a mask based on
        the conditions.

        clean: bool
            If not True, let the current mask be a condition as well. If
            True, the mask is set solely on the pack's current
            conditions

        dry: bool
            If True, only try to make a mask, but don't touch self.mask

        This method is called automatically unless ``no_auto`` is set to
        True, whenever conditions are updated.

        .. seealso::
           :meth:`~channelpack.ChannelPack.pprint_conditions`
        """

        cc = self.conconf
        mask = np.ones(self.rec_cnt) == True # All True initially.
        for cond in cc.conditions_list('cond'):
            try:
                mask = mask & self._mask_array(cond)
            except Exception as e:
                print cond
                print 'produced an error:'
                raise           # re-raise


        mask = mask & datautils.startstop_bool(self)

        samplerate = cc.get_condition('samplerate')
        if samplerate is not None:
            samplerate = float(samplerate)
        mask = datautils.duration_bool(mask, cc.get_condition('duration'),
                                       samplerate)

        if  dry:
            return
        if not clean and self.mask is not None:
            self.mask = self.mask & mask
        else:
            self.mask = mask

    def set_channel_names(self, names):
        """
        Set self.chnames. Custom channel names that can be used in calls
        on this object and in condition strings.

        names: list or None
            It is the callers responsibility to make sure the list is in
            column order. self.chnames will be a dict with channel
            integer indexes as keys. If names is None, self.chnames will
            be None.

        """
        if not names:
            self.chnames = None
            return

        if len(names) != len(self.keys):
            raise ValueError('len(names) != len(self.D.keys())')

        self.chnames = dict(zip(self.keys, names))

    def slicelist(self):
        """Return a slicelist based on self.mask.

        This is used internally and might not be very useful from
        outside. It's exposed anyway in case of interest to quickly see
        where the parts are along the arrays.

        It is a list of python slice objects corresponding to the True
        sections in self.mask. If no conditions are set, there shall be
        one slice in the list with start == 0 and stop == self.rec_cnt,
        (the mask is all True). The len of this list corresponds to the
        number of True sections in self.mask. (So a hint on the result
        from the conditions).

        .. seealso:: :meth:`~channelpack.ChannelPack.parts`

        """

        return datautils.slicelist(self.mask)

    def parts(self):
        """Return the enumeration of the True parts.

        The list is always consecutive or empty.

        .. seealso:: :meth:`~channelpack.ChannelPack.slicelist`
        """

        return range(len(self.slicelist()))

    def counter(self, ch, part=None):
        """Return a counter on the channel ch.

        ch: string or integer.
            The channel index number or channel name.

        part: int or None
            The 0-based enumeration of a True part to return. This
            has an effect whether or not the mask or filter is turned
            on. Raise IndexError if the part does not exist.

        See `Counter
        <https://docs.python.org/2.7/library/collections.html#counter-objects>`_
        for the counter object returned.

        """
        return Counter(self(self._key(ch), part=part))

    def __call__(self, key, part=None):
        """Make possible to retrieve channels by key.

        key: string or integer.
            The channel index number or channel name.

        part: int or None
            The 0-based enumeration of a True part to return. This
            has an effect whether or not the mask or filter is turned
            on. Raise IndexError if the part does not exist.
        """
        # Primary need is to get an integer from key since D.keys are integers.

        i = self._key(key)

        if part is not None:
            sl = datautils.slicelist(self.mask)
            return self.D[i][sl[part]]
        elif self.nof == 'nan':
            return datautils.masked(self.D[i], self.mask)
        elif self.nof == 'filter':
            return self.D[i][self.mask]
        elif self.nof:
            raise ValueError('The nof value is invalid: ' + str(self.nof) +
                             '\nmust be "nan", "filter" or falsish')
        else:
            return self.D[i]

    def _key(self, ch):
        """Return the integer key for ch. It is the key for the first
        value found in chnames and chnames_0, that matches ch. Or if
        ch is an int, ch is returned if it is a key in self.D"""

        if ch in self.D:
            return ch

        if isinstance(ch, int):
            raise KeyError(ch)  # dont accept integers as custom names

        if self.chnames:
            for item in self.chnames.items():
                if item[1] == ch:
                    return item[0]
        for item in self.chnames_0.items():
            if item[1] == ch:
                return item[0]

        # If we got here, ch can be an int represented by a string if it comes
        # from a condition string:
        try:
            chint = int(ch)
            if chint in self.D:
                return chint
        except ValueError:
            pass

        raise KeyError(ch)

    def name(self, ch, firstwordonly=False):
        """Return channel name for ch. ch is the channel name or the
        index number for the channel name, 0-based.

        ch: str or int.
            The channel name or indexed number.

        firstwordonly: bool or "pattern".
            If True, return only the first non-spaced word in the name.
            If a string, use as a re-pattern to re.findall and return
            the first element found. There will be error if no
            match. r'\w+' is good pattern for excluding
            leading and trailing obscure characters.

        Returned channel name is the fallback string if "custom" names
        are not available.

        """

        names = self.chnames or self.chnames_0
        i = self._key(ch)

        if not firstwordonly:
            return names[i]
        elif firstwordonly == True or firstwordonly == 1:
            return names[i].split()[0].strip()

        return re.findall(firstwordonly, names[i])[0] # According to user
                                                      # pattern.

    def query_names(self, pat):
        """pat a shell pattern. See fnmatch.fnmatchcase. Print the
        results to stdout."""

        for item in self.chnames.items():
            if fnmatch.fnmatchcase(item[1], pat):
                print item

    def set_basefilemtime(self):
        """Set attributes mtimestamp and mtimefs. If the global list
        ORIGINEXTENSIONS include any items, try and look for files (in
        the directory where self.filename is sitting) with the same base
        name as the loaded file, but with an extension specified in
        ORIGINEXTENSIONS.

        mtimestamp is a timestamp and mtimefs is the file (name) with
        that timestamp.

        ORIGINEXTENSIONS is empty on delivery. Which means that the
        attributes discussed will be based on the file that was loaded,
        (unless ORIGINEXTENSIONS is populated before this call).

        This is supposed to be a convenience in cases the data file
        loaded is some sort of "exported" file format, and the original
        file creation time is of interest.

        .. note::
           If the provided functions in this module is used to get a
           pack, this method does not have to be called. It is called by
           those functions.
        """

        dirpath = os.path.split(self.filename)[0]
        name = os.path.basename(self.fs).split('.')[0]
        for ext in ORIGINEXTENSIONS: # This should be some user configuration.
            res = glob.glob(dirpath + '/' + name + '.' + ext)
            if res: # Assume first match is valid.
                self.mtimefs = os.path.normpath(res[0]) # If some shell patterns
                                                        # will be used later.
                # Time stamp string:
                self.mtimestamp = time.ctime(os.path.getmtime(self.mtimefs))
                break
        else:
            self.mtimefs = self.filename
            self.mtimestamp = time.ctime(os.path.getmtime(self.mtimefs))

def _fallback_names(nums):
    """Return a list like ['ch0', 'ch1',...], based on nums. nums is a
    list with integers.

    This is the one function allowed to return fallback names to
    ChannelPack"""

    return [FALLBACK_PREFIX + str(i) for i in nums]

class _ConditionConfigure:

    def __init__(self, pack):

        self.pack = pack
        self.numrx = r'[\w]+?(\d+)' # To extract the trailing number.
        self.reset()

    def reset(self):
        conpairs = [('cond1', None), ('startcond1', None),
                    ('stopcond1', None), ('stopextend', None),
                    ('duration', None), ('samplerate', None)]
        # Ordered dict is of no use any more. cond<n> will be inserted later
        # on, and that is to be printed together with the cond conditions.
        self.conditions = OrderedDict(conpairs)

    def set_condition(self, conkey, val):
        """Set condition conkey to value val. Convert val to str if not
        None.

        conkey: str
            A valid condition key.

        val: str, int, float, None
            Can always be None. Can be number or string depending on conkey.
        """

        if not any([conkey.startswith(c) for c in _COND_PREFIXES]):
            raise KeyError(conkey)

        if val in NONES:
            self.conditions[conkey] = None
        else:
            self.conditions[conkey] = str(val)

    def spit_config(self, conf_file, firstwordonly=False):
        """conf_file a file opened for writing."""

        cfg = ConfigParser.RawConfigParser()
        for sec in _CONFIG_SECS:
            cfg.add_section(sec)

        sec = 'channels'
        for i in sorted(self.pack.D):
            cfg.set(sec, str(i), self.pack.name(i, firstwordonly=firstwordonly))

        sec = 'conditions'
        for k in self.sorted_conkeys():
            cfg.set(sec, k, self.conditions[k])

        cfg.write(conf_file)

    def eat_config(self, conf_file):
        """conf_file a file opened for reading.

        Update the packs channel names and the conditions, accordingly.

        """

        # Read the file:
        cfg = ConfigParser.RawConfigParser()
        cfg.readfp(conf_file)

        # Update channel names:
        sec = 'channels'
        mess = 'missmatch of channel keys'
        assert(set(self.pack.D.keys()) == set([int(i) for i in cfg.options(sec)])), mess
        if not self.pack.chnames:
            self.pack.chnames = dict(self.pack.chnames_0)
        for i in cfg.options(sec): # i is a string.
            self.pack.chnames[self.pack._key(int(i))] = cfg.get(sec, i)

        # Update conditions:
        sec = 'conditions'

        # conkeys = set(self.conditions.keys())
        # conops = set(cfg.options(sec))

        # This check should be superfluous:
        # --------------------------------------------------
        # for conkey in conkeys:
        #     if not any([conkey.startswith(c) for c in _COND_PREFIXES]):
        #         raise KeyError(conkey)
        # --------------------------------------------------

        # for con in conkeys - conops: # Removed conditions.
            # self.set_condition(con, None)
        conops = cfg.options(sec)
        self.reset()            # Scary
        for con in conops:
            self.set_condition(con, cfg.get(sec, con))

        # That's it

    def conditions_list(self, conkey):
        """
        Return a (possibly empty) list of conditions based on
        conkey. The conditions are returned raw, not parsed.

        conkey: str
            for cond<n>, startcond<n> or stopcond<n>, specify only the
            prefix. The list will be filled with all conditions.
        """
        L = []
        keys = [k for k in self.conditions if k.startswith(conkey)] # Sloppy
                                                                    # check
        if not keys:
            raise KeyError(conkey)
        for k in keys:
            if self.conditions[k] is None:
                continue
            raw = self.conditions[k]
            L.append(raw)

        return L

    def get_condition(self, conkey):
        """As it is."""
        return self.conditions[conkey]

    def get_stopextend(self):
        """As an integer. Return 0 if None."""

        try:
            return int(self.conditions['stopextend'])
        except TypeError:
            return 0

    def cond_int(self, conkey):
        """Return the trailing number from cond if any, as an int. If no
        trailing number, return the string conkey as is.

        This is used for sorting the conditions properly even when
        passing the number 10. The name of this function could be
        improved since it might return a string."""

        m = re.match(self.numrx, conkey)
        if not m:
            return conkey
        return int(m.group(1))

    def valid_conkey(self, conkey):
        """Check that the conkey is a valid one. Return True if valid. A
        condition key is valid if it is one in the _COND_PREFIXES
        list. With the prefix removed, the remaining string must be
        either a number or the empty string."""

        for prefix in _COND_PREFIXES:
            trailing = conkey.lstrip(prefix)
            if trailing == '' and conkey: # conkey is not empty
                return True
            try:
                int(trailing)
                return True
            except ValueError:
                pass

        return False

    def next_conkey(self, conkey):
        """Return the next <conkey><n> based on conkey as a
        string. Example, if 'startcond3' and 'startcond5' exist, this
        will return 'startcond6' if 'startcond5' value is not None,
        else startcond5 is returned.

        It is assumed conkey is a valid condition key.

        .. warning::
           Under construction. There is work to do. This function in
           combination with the pack.add_condition. But now it's time for
           bed.

        """

        if conkey in self.conditions:
            return conkey       # Explicit conkey

        conkeys = self.sorted_conkeys(prefix=conkey) # Might be empty.
        if not conkeys:
            return conkey       # A trailing number given that does not already
                                # exist. Accept possible gap from previous
                                # number.
        for candidate in conkeys:
            if self.conditions[candidate] is None:
                return candidate

        i = self.cond_int(candidate) # The last one.
        return re.sub(r'\d+', str(i + 1), candidate)

    def sorted_conkeys(self, prefix=None):
        """Return all condition keys in self.conditions as a list sorted
        suitable for print or write to a file. If prefix is given return
        only the ones prefixed with prefix."""

        # Make for defined and sorted output:
        conkeys = []
        for cond in _COND_PREFIXES:
            conkeys += sorted([key for key in self.conditions
                               if key.startswith(cond)], key=self.cond_int)
        if not prefix:
            return conkeys
        return [key for key in conkeys if key.startswith(prefix)]

    def pprint_conditions(self):

        for k in self.sorted_conkeys():
            print k + ':', self.conditions[k]

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
    cp._patpull = pulltxt.PP              # Give a reference to the patternpull.
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

    startcell: str or None
        If given, a spread sheet style notation of the cell where reading
        start, ("F9").

    stopcell: str or None
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

# Look for rc file:
_aspirants = []
if os.getenv('HOME'):
    _aspirants.append(os.getenv('HOME'))
_aspirants += [os.path.expanduser('~')]

_cfg = ConfigParser.RawConfigParser()

for _asp in _aspirants:
    try:
        with open(os.path.join(_asp, CHANNELPACK_RC_FILE)) as fp:
            try:
                _cfg.readfp(fp)
                exts = _cfg.get('channelpack', 'originextensions')
                ORIGINEXTENSIONS += [ext.strip() for ext in exts.split(',')]
                # print 'ORIGINEXTENSIONS:', ORIGINEXTENSIONS
                break           # First read satisfy.
            except (ConfigParser.NoSectionError,
                    ConfigParser.NoOptionError,
                    ConfigParser.ParsingError) as e:
                print fp.name, 'exist, but:'
                print e
                break           # Not gonna look for a file that work when one
                                # that fails exist.

    except IOError:
        pass
    except Exception as e:
        print 'Unexpected error when searching for', CHANNELPACK_RC_FILE
        print e
