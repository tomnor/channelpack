
# -*- coding: UTF-8 -*-

"""Provide ChannelPack. Provide lazy functions to get loaded instances
of ChannelPack.

ChannelPack is a class holding data read from some data file. It takes a
function as its only argument for init. The function is responsible for
returning a dict with numpy 1d arrays corresponding to the "channels" in
the data file. Keys are integers corresponding to the "columns" used,
0-based. The loadfunc is called from an instance of ChannelPack by
calling 'load'.

"""
import re
import glob, fnmatch
import os, time
import ConfigParser
from collections import OrderedDict

import numpy as np

from . import pulltxt, pulldbf
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
CONFIG_SECS = ['channels',  'conditions']
DURTYPES = ['strict', 'min', 'max'] # TO DO: Check validity with this.
FALLBACK_PREFIX = 'ch'              # TO DO: Use this global constant so it is
                                    # possible to work-around a possible
                                    # conflict. DONE (in _fallback func).
NONES = [None, 'None', 'none', "''", '""', '']

class ConditionMappingError(Exception):
    """Raise when channels are not found in conditions."""
    pass

class ChannelPack:
    """Pack of data. Hold a dict with channel index numbers as keys
    (column number).  This object is callable by channel name or index.
    """

    # TO DO: More important - start and stop trigger conditions. Enabling
    # hysterises kind of checking. Like start: "ch21 > 4.3" and
    # stop: "ch21 < 1.3". Include it to the conditions dict. DONE, (testing).

    # TO DO: Consider possibility to write some chanel names with indexing, like
    # MyCh3[0] > MyCh5.

    # TODO: Make some sort of steady_state condition. Some way to detect a
    # signal that keeps it's values within a tolerance. A flat value, so I guess
    # steady_state refers to a naive kind of steady_state. This might be
    # implemented by a meethod. The method makes a mask based on steady_state,
    # then the "normal" _make_mask method is called.

    # TODO: A proper way of concatenating packs. I would prefer not to
    # have to have already loaded packs to merge, that makes for
    # duplicates. I want the possibility to have them added based on
    # basefilemtime, (if available). Maybe I need a MultiPack class. Not
    # so nice. But else, how will base files be tracked. Always the last
    # file?

    def __init__(self, loadfunc=None):
        """Return a pack

        loadfunc is a function that returns a dict holding numpy
        arrays, being the channels. Keys are the index integer numbers,
        (column numbers). Each array is of np.shape(N,).

        See method :meth:`~channelpack.ChannelPack.load`.

        """
        self.loadfunc = loadfunc
        self.D = None           # Dict of data.
        self.fn = None          # The loaded filename
        self.chnames = None       # Channel names maybe. dict
        self.chnames_0 = None     # Fall back names, always available. ch0,
                                  # ch1... dict
        self.keys = None          # Sorted list of keys for the data dict.
        self.rec_cnt = 0          # Number of records.

        self._mask_on = False    # Yeahh...
        self._filter_on = False
        self.mask = None
        # Dict with condition specs for the mask array:
        # self.conditions = {'and': '', 'or': '', 'dur': 0, 'durtype': 'min',
                           # 'start': '', 'stop': ''}
        self.conconf = _ConditionConfigure(self)


    def load(self, *args, **kwargs):
        """Load data using loadfunc.

        args, kwargs:
            forward to the loadfunc. args[0] must be the filename, so it
            means that loadfunc must take the filename as it's first
            argument.

        Set the filename attribute.

        ChannelPack is assuming a need for loading data from disc. If
        there is a desire to load some made-up data, a filename pointing
        to some actual file is nevertheless required. Here is a
        suggestion:

        >>> import channelpack as cp
        >>> import tempfile

        >>> tf = tempfile.NamedTemporaryFile()

        >>> d = {2: np.arange(5), 5: np.arange(10, 15)}
        >>> def lf(fn):
        ...     return d
        ...

        >>> pack = cp.ChannelPack(lf)
        >>> pack.load(tf.name)
        >>> pack.filename
        # maybe '/tmp/tmp9M4PqD'
        >>> pack.chnames_0
        {2: 'ch2', 5: 'ch5'}

        """
        # D = self.loadfunc(*args, **kwargs)
        self.D = self.loadfunc(*args, **kwargs)
        usecols = kwargs.get('usecols', None) # Whats this for? Remove
        self.keys = sorted(self.D.keys())
        self.rec_cnt = len(self.D[self.keys[0]]) # If not all the same, there
                                           # should have been an error
                                           # already

        fallnames  = _fallback_names(self.keys)
        self.chnames_0 = dict(zip(self.keys, fallnames))
        self._set_filename(args[0])
        self.set_basefilemtime()

        self._make_mask()

    def append_load(self, *args, **kwargs):
        """Append data using loadfunc.

        args, kwargs:
            forward to the loadfunc. args[0] must be the filename, so it
            means that loadfunc must take the filename as it's first
            argument.

        If self is not already a loaded instance, call load and return.

        Make error if there is a missmatch of channels indexes or
        channels count.

        Append the data to selfs existing data. Set filename to the new
        file.

        Create new attribute - a dict with metadata on all files loaded,
        'metamulti.'
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

        self._make_mask()

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
        continous. Like, not start over from 0, when data is appended
        from multiple files. Or simply to rebase a channel on 'start'.

        If start is None, and the instance is loaded from one file only,
        this method has no effect.

        NOTE: The instance channel is modified on success.
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
        start = start or self(key)[0]
        self.D[self._key(key)] = np.arange(start, d * self.rec_cnt + start, d)

        assert len(self(key)) == self.rec_cnt, 'Semantic error'

    def _set_filename(self, fn):
        """Set the filename attributes. (They are multiple for personal
        reasons)."""
        fn = os.path.abspath(fn)
        self.filename = self.fs = self.fn = fn

    def set_sample_rate(self, rate):
        """Set sample rate to rate.

        rate: int or float

        rate is given as samples / timeunit. If sample rate is set, it
        will have an impact on the duration value in conditions. If
        duration is set to 2.5 and samplerate is 100, a duration of 250
        records is required for the logical conditions to be true."""

        # Test and set value:
        float(rate)
        self.conconf.set_condition('samplerate', rate)
        self._make_mask()

    def add_conditions(self, conkey, con):
        """Add condition(s) con to the conditions conkey.

        conkey: str
            One of the conditions that can be a comma seperated list of
            conditions.

        con: str
            Condition like 'ch1 > 5' or comma delimited conditions like
            'ch5 == ch14, ch0 <= (ch1 + 2)'. 'ch5', for example, can be
            a custom channel name if available.

        NOTE: If custom names are used, they must consist of one word
        only, not delimited with spaces.

        """

        # Audit:
        for c in con.split(','):
            self._prep_condition(c)

        current = self.conconf.get_condition(conkey)
        if current:
            newcon = ','.join([current, con]).strip(',')
        else:
            newcon = con

        self.conconf.set_condition(conkey, newcon)

        self._make_mask()       # On every update so errors are detected.

    def _prep_condition(self, constr):
        """Replace parts in the string constr (ONE condition) that matches
        a channel name, with 'd[i]', and set i to the correct integer
        key string. Make error if no mapping to channel name.

        """
        conres = constr

        matches = re.findall(r'ch\d+', conres)
        for ch in matches:
            i = self._key(ch)
            conres = conres.replace(ch, 'd[' + str(i) + ']')

        if not self.chnames:
            if conres == constr: # No mapping.
                raise ValueError('This condition did not resolve to a valid' +
                                 ' channel: ' + constr)
            else:
                return conres

        for ch in self.chnames.values():
            for m in re.findall(r'\w+', conres):
                if ch == m:
                    i = self._key(ch)
                    conres = conres.replace(ch, 'd[' + str(i) + ']')

        if conres == constr: # No mapping.
            raise ValueError('This condition did not resolve to a any valid' +
                             ' channel: ' + constr)

        return conres

    def set_conditions(self, conkey, con):
        """Remove existing conditions in conkey and replace with con.

        conkey: str
            One of the conditions that can be a comma seperated list of
            conditions.

        con: str or None
            Condition like 'ch1 > 5' or comma delimited conditions like
            'ch5 == ch14, ch0 <= (ch1 + 2)'. 'ch5', for example, can be
            a custom channel name if available.

        NOTE: If custom names are used, they must consist of one word
        only, not delimited with spaces.
        """
        # TODO: This function should maybe not be limited to certain
        # conditions. Not intuitive.

        # Audit:
        if not con in NONES:
            for c in con.split(','):
                self._prep_condition(c)

        self.conconf.set_condition(conkey, con)

        self._make_mask()

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

        Note: If the config_file exist because of an earlier spit, and
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
        self._make_mask()

    def pprint_conditions(self):
        """Pretty print conditions."""

        self.conconf.pprint_conditions()

    def set_stop_extend(self, n):
        """n is an integer >= 0."""
        self.conconf.set_condition('stop_extend', n)
        self._make_mask()

    def set_duration(self, dur, durtype='min'):
        """Set the duration condition to dur.

        dur: int or float
            The count of duration. If self.samplerate is not set, dur is
            the number of records to count. If samplerate is set, number
            of records to count is int(self.samplerate * dur).

        durtype: str
            Accepted is one of 'strict', 'min' or 'max'. Default is
            'min'.

        Setting dur = 0 and durtype = 'min' is a safe way to make the
        duration condition have no effect. (Besides clearing the
        conditions).
        """
        # Test:
        assert durtype in DURTYPES, durtype
        float(dur)

        self.conconf.set_condition('dur', dur)
        self.conconf.set_condition('durtype', durtype)
        self._make_mask()

    def clear_conditions(self, *conkeys, **noclear):
        """Clear conditions. Clear only the conditions conkeys if
        specified. Clear only the conditions not specified by conkeys if
        noclear is True (False default).
        """

        offenders = set(conkeys) - set(self.conconf.conditions.keys())
        if offenders:
            raise KeyError(', '.join([off for off in offenders]))

        noclear = noclear.get('noclear', False)

        for ck in self.conconf.conditions:
            if not conkeys:
                self.conconf.set_condition(ck, None)
            elif not noclear and ck in conkeys:
                self.conconf.set_condition(ck, None)
            elif noclear and not ck in conkeys:
                self.conconf.set_condition(ck, None)

        self._make_mask()

    def set_mask_on(self, b=True):
        """If mask is on, any calls for a channel will be
        masked. Meaning, the parts of the array not meeting the
        conditions are replaced with numpy.nan.

        Setting mask on, turns the filter off."""

        self._mask_on = b == True
        if self._mask_on:
            self._filter_on = False

    def set_filter_on(self, b=True):
        """If filter is on, any calls for a channel will be
        reduced. Meaning, the parts of the array not meeting the
        conditions are removed. It means that self.rec_cnt is probably
        greater than the len of the array returned from a call. However,
        any array called for, will have the same len as the other.

        Setting filter on, turns the mask off.

        TODO: Implement the effect of this. Probably a slicelist
        functionality is desired then. A way to specify one of possibly
        multiple true sections which are otherwise just merged
        together. Consider a keyword argument to the __call__ func.
        """

        self._filter_on = b == True
        if self._filter_on:
            self._mask_on = False

    def mask_or_filter(self):
        """Return 'mask' or 'filter' or None depending on which one is
        turned on."""

        if self._mask_on:
            return 'mask'
        elif self._filter_on:
            return 'filter'
        return None

    def _make_mask(self):
        """Set the attribute self.mask to a mask based on
        self.conditions"""

        cc = self.conconf
        andmask = datautils.array_and(self.D, cc.conditions_list('and'))
        ormask = datautils.array_or(self.D, cc.conditions_list('or'))

        ssmask = datautils.startstop_bool(self)

        self.mask = np.logical_and(andmask, ormask)
        self.mask = np.logical_and(self.mask, ssmask)

        # Duration conditions:
        dur = cc.get_duration()
        durtype = cc.get_duration_type()
        self.mask = datautils.duration_bool(self.mask, dur, durtype)

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
        """Return a slicelist based on self.mask."""

        return datautils.slicelist(self.mask)

    def __call__(self, key, part=None):
        """Make possible to retreive channels by key.

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
        elif self._mask_on:
            return datautils.masked(self.D[i], self.mask)
        elif self._filter_on:
            return self.D[i][self.mask]
        else:
            return self.D[i]

    def _key(self, ch):
        """Return the integer key for ch. It is the key for the first
        value found in chnames and chnames_0, that matches ch. Or if
        ch is an int, ch is returned if it is a key in self.D"""

        try:
            int(ch)
            if ch in self.D:
                return ch
        except ValueError:
            pass                # Not intable.

        if self.chnames:
            for item in self.chnames.items():
                if item[1] == ch:
                    return item[0]
        for item in self.chnames_0.items():
            if item[1] == ch:
                return item[0]

        raise KeyError(ch)

    def valforvalin(self, val, ch0, ch1, portion=None):
        """Return value in ch1 where value in ch0 is closest to val.

        val: int, float
            The value to look for in ch0.

        ch0: str or int
            The channel name or indexed number for the array with a
            value close to val.

        ch0: str or int
            The channel name or indexed number for the array to return
            the corresponding value from.

        portion: None or tuple
            If a tuple it is percentage portion of the data arrays to
            study. (start, stop), where the full array is (0, 100).

            NOTE: Not implemented. (Or testing)

        If ch0 has multiple values equally close to val, return the
        first one found.

        NOTES: This might or might not be very helpful. If val is
        repeatadly close in ch0, propably a not desired value in ch1 is
        returned.

        TO DO: Interpolation. If values are few. Does one want some sort
        of interpolation? What happens then if ... Nahh. I think
        not. Either this is of help or it is not.

        TO DO: Think about how this shall function in combination with
        the conditions. It is depending on conditions as for now becaues
        data is called for.
        """

        ch = self(ch0)
        sc = slice(0, ch.size)
        if portion is not None:
            start = int(portion[0] / 100.0 * ch.size) - 1
            if start < 0:
                start = 0
            stop = int(portion[1] / 100.0 * ch.size)
            sc = slice(start, stop)
            print sc
            # Review this code.

        diffs = abs(self(ch0)[sc] - val)
        m = min(diffs)
        t = np.where(diffs == m)
        i = t[0][0] + sc.start             # First one found

        # BUG: Need to translate back to index for the full array. (As given by
        # the call). + sc.start ok?
        return self(ch1)[i]

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
        try:
            i = int(ch)
        except ValueError:
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


    def ch(self, key, part=None):
        """Return the channel data vector.

        key: string or integer.
            The channel index number or channel name.

        part: int or None
            The 0-based enumeration of a True part to return. This
            has an effect whether or not the mask or filter is turned
            on. Raise IndexError if the part does not exist.
        """
        return self.__call__(chname, part)

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

        This is supposed to be a convinience in cases the data file
        loaded is some sort of "exported" file format, and the original
        file creation time is of interest.
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
    """Provide handling of conditions and the config file as support to
    the ChannelPack class. Provide smooth methods to get one condition
    at a time or a list of conditions. Keep the logic of handling the
    config file here.

    Keep a dictionary of conditions. Let's stick to values as either
    strings or None.
    """

# TODO: Establish an opportunity to have multiple sections of
# conditions. Distinguished by an appended digit. Like conditions5.

    def __init__(self, pack):

        self.pack = pack
        conpairs = [('and', None), ('or', None),
                    ('start_and', None), ('start_or', None),
                    ('stop_and', None), ('stop_or', None),
                    ('stop_extend', None),
                    ('dur', None), ('durtype', None),
                    ('samplerate', None)]
        self.conditions = OrderedDict(conpairs)

    def set_condition(self, conkey, val):
        """Set condition conkey to value val. Convert val to str if not
        None.

        conkey: str
            A condition that exist in the conditions dict (as a key).

        val: str, int, float, None
            Can always be None. Can be number or string depending on conkey.
        """

        if conkey not in self.conditions:
            raise KeyError(conkey)

        if val in NONES:
            self.conditions[conkey] = None
        else:
            self.conditions[conkey] = str(val)

    def spit_config(self, conf_file, firstwordonly=False):
        """conf_file a file opened for writing."""

        cfg = ConfigParser.ConfigParser()
        for sec in CONFIG_SECS:
            cfg.add_section(sec)

        sec = 'channels'
        for i in sorted(self.pack.D):
            cfg.set(sec, str(i), self.pack.name(i, firstwordonly=firstwordonly))

        sec = 'conditions'
        for k, v in self.conditions.items():
            cfg.set(sec, k, v)

        cfg.write(conf_file)

    def eat_config(self, conf_file):
        """conf_file a file opened for reading.

        Update the packs channel names and the conditions, accordingly.

        """

        # Read the file:
        cfg = ConfigParser.ConfigParser()
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

        conkeys = set(self.conditions.keys())
        conops = set(cfg.options(sec))

        if conops - conkeys:
            offenders = ["'" + off + "'" for off in conops - conkeys]
            mess = ', '.join(offenders)
            raise KeyError('Not valid condition option(s): ' + mess)
        for con in conkeys - conops: # Removed conditions.
            self.set_condition(con, None)
        for con in conops:
            self.set_condition(con, cfg.get(sec, con))

        # That's it

    def conditions_list(self, conkey):
        """Return conditions conkey as a list prepared for eval. Return an
        empty list if there is no condition. conkey should be one of the
        conditions that can be a list of comma seperated conditions.

        conkey: str
            One of the conditions that can be a comma seperated list of
            conditions.
        """

        if self.conditions[conkey] is None:
            return []
        L = self.conditions[conkey].split(',')
        L = [c.strip() for c in L if c] # if c in case of trailing comma.
        L = [self.pack._prep_condition(c) for c in L]
        return L

    def get_condition(self, conkey):
        """As it is."""
        return self.conditions[conkey]

    def get_stop_extend(self):
        """As an integer. Return 0 if None."""

        try:
            return int(self.conditions['stop_extend'])
        except TypeError:
            return 0

    def get_duration(self):
        """Get duration as an integer."""

        if self.conditions['samplerate']:
            samplerate = float(self.conditions['samplerate'])
        else:
            samplerate = 1.0

        dur = self.conditions['dur'] or 0 # zero default

        dur = int(float(dur) * samplerate)

        return dur

    def get_duration_type(self):
        """Defaults to 'min' if None"""
        return self.conditions['durtype'] or 'min'

    def pprint_conditions(self):
        for key, val in self.conditions.items():
            print key + ':', val

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

# Look for rc file:
_aspirants = []
if os.getenv('HOME'):
    _aspirants.append(os.getenv('HOME'))
_aspirants += [os.path.expanduser('~')]

_cfg = ConfigParser.ConfigParser()

for _asp in _aspirants:
    try:
        with open(os.path.join(_asp, CHANNELPACK_RC_FILE)) as fp:
            try:
                _cfg.readfp(fp)
                exts = _cfg.get('channelpack', 'originextensions')
                ORIGINEXTENSIONS += [ext.strip() for ext in exts.split(',')]
                print 'ORIGINEXTENSIONS:', ORIGINEXTENSIONS
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
