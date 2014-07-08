
# -*- coding: UTF-8 -*-

"""Provide ChannelPack. Provide lazy functions to get loaded instances
of ChannelPack.

ChannelPack is a class holding data read from some data file. It takes a
function as its only argument for init. The function is responsible for
returning a dict with numpy 1d arrays corresponding to the "channels" in
the data file. Keys are integers corresponding to the "columns" used,
0-based. The loadfunc is called from an instance of ChannelPack by
calling 'load'.

----------------------------
Written thinking

Say that I need to load some data from a measurement that repeats,
(every week or so). The measurement is the same every time, but the
set-up configuration files might have been altered so order and spelling
of channel names might suddenly change. I will need to know how the
channels are ordered. There is no obvious way for channelpack to know
this order. So it shall be possible to call channels by index
number. This solves the problem of not knowing the exact spelling of
channel names from a given measurement session. But not the ordering of
channels. 

There could be a function to spit out a config file to the directory
where the data file is sitting. This file is a config file. It has a
section called 'NAMES' where each option is a channel name with
corresponding index as value. 'NAMES' can be extended with an asterisk
saying what data files the mapping is valid for, being all files with an
asterisk. It's a shell pattern, so to limit valid file names, it can be
[NAMES "<valid prefix>*.csv"], or [NAMES "mes_M*.*"] or similar.

Another section gives a possibility to remap the channel index order,
it's called [REMAP], one option: neworder = [3, 2 , 4, 1, 0]. No? This
should conflict with the NAMES section. Not applicable I think. Just
provide a method for this. remap is good name of such a method.

Now the mtime thing. Where should the possible file extensions to look
for be located. This question solve later. Now just store a global list
here with such extensions. 

Now the conditions thing. 

TO DO: Figure out how to specify shell patterns to use when searching
for a possible origin file. Hopefully some default can be set in the
spitted file. Provide smart solution for user to specify
ORIGINEXTENSIONS, which somehow doesn't need to be repeated. It boils
down to all the time that I need some infant location to persist config
data. 


----------------------------

"""
import re
import glob, fnmatch
import os, time
from ConfigParser import ConfigParser as configparser

import numpy as np

from . import pulltxt, pulldbf
from . import datautils

ORIGINEXTENSIONS =  ['iad', 'd7d'] # TO DO: Make configurable persistant.
CONFIG_FILE = "conf_file.cfg"
CONFIG_SECS = ['channels',  'conditions']
DURTYPES = ['strict', 'min', 'max'] # TO DO: Check validity with this.

class ConditionMappingError(Exception):
    """Raise when channels are not found in conditions."""
    pass

class ChannelPack:
    """Base class for a pack of data. Hold a dict with channel index
    numbers as keys. The channels can be called by channel name or
    index. This object is callable by channel name or index.

    """

    # TO DO:
    # Add a "present" method. Pretty printing of the pack. Also implement some
    # __repr__ thing.
    # Implement the set_basefilemtime method properly.
    # Do some reduce functionality. Masking from conditions. Make a new
    # module I guess, with sort of numpy utils.

    # TO DO: More important - start and stop trigger conditions. Enabling
    # hysterises kind of checking. Like start: "ch21 > 4.3" and 
    # stop: "ch21 < 1.3". Include it to the conditions dict. 

    # TO DO: More important - reserved words. Some numpy math stuff like max,
    # min, cos, sin, tan, mean. NOOO, just document how to write it - namely
    # np.sin and so on.

    def __init__(self, loadfunc=None):
        """Return a pack

        loadfunc is a function that returns a dict holding numpy
        arrays, being the channels. Keys are the index integer numbers,
        (column numbers). Each array is of np.shape(N,).

        See method load.
        
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
        self.conditions = {'and': '', 'or': '', 'dur': 0, 'durtype': 'min'} 

    def load(self, *args, **kwargs):
        """load the data using loadfunc.

        args, kwargs: forward to the loadfunc. args[0] must be the
        filename, so it means that loadfunc must take the filename
        as it's first argument.

        Set the filename attribute.

        """
        # D = self.loadfunc(*args, **kwargs)
        self.D = self.loadfunc(*args, **kwargs)
        usecols = kwargs.get('usecols', None)
        self.keys = sorted(self.D.keys())
        self.rec_cnt = len(self.D[self.keys[0]]) # If not all the same, there
                                           # should have been an error
                                           # already

        fallnames  = fallback_names(self.keys)
        self.chnames_0 = dict(zip(self.keys, fallnames))
        self._set_filename(args[0])
        
    def _set_filename(self, fn):
        """Set the filename attributes. (They are multiple for personal
        reasons)."""
        self.filename = self.fs = self.fn = fn

    def set_sample_rate(self, rate):
        """Set sample rate to rate. 

        rate is given as samples / timeunit. If self.samplerate is set,
        it will have an impact on the duration value in
        self.conditions. If duration is set to 2.5 and samplerate is
        100, a duration of 250 records is required for the logical
        conditions to be true."""

        self.samplerate = rate

    def add_conditions(self, constr, andor):
        """Add condition(s) to the conditions.

        constr: str
            Condtion like 'ch01 > 5' or comma delimited conditions like
            'ch05 == ch14, ch0 <= (ch + 2)'. 'ch5', for example, can be
            a custom channel name if available.

        andor: str
            'and' or 'or' accepted.

        NOTE: If custom names are used, they must consist of one word
        only, not delimited with spaces. 

        """

        # Audit:
        for con in constr.split(','):
            self._prep_condition(con)
        
        current = self.conditions[andor]
        self.conditions[andor] = ','.join([current, constr]).strip(',')

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
        

    def set_conditions(self, conditions, andor):
        """Remove existing conditions in andor and replace with conditions.

        See add_conditions for descriptions.
        """
        raise NotImplementedError
    
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
            names spitted.

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
        cfg = configparser()

        # Figure out file name of conf_file:
        if hasattr(self, 'conf_file') and not conf_file:
            cfgfn = self.conf_file
        elif conf_file:
            with open(conf_file, 'w') as fo:
                pass            # Make proper error if problem.
            cfgfn = conf_file
        else:
            cfgfn = os.path.join(chroot, CONFIG_FILE)

        cfg.read(cfgfn)

        for sec in CONFIG_SECS:
            if not cfg.has_section(sec):
                cfg.add_section(sec)

        for sec in CONFIG_SECS:
            if sec == 'channels':
                for i in sorted(self.D):
                    cfg.set(sec, str(i), self.name(i,
                                                   firstwordonly=firstwordonly))
            elif sec == 'conditions':
                for k in self.conditions:
                    val = self.conditions[k]
                    if val:
                        cfg.set(sec, k, val)
                    elif k.startswith('dur'): # Always spit this one.
                        cfg.set(sec, k, val)
                    else:       # pop possible existing option in file:
                        cfg.remove_option(sec, k)
        
        with open(cfgfn, 'wb') as fo:
            cfg.write(fo)
        
        self.conf_file = os.path.abspath(cfgfn)

    def eat_config(self, conf_file=None):
        """
        Read the the conf_file and update this instance accordingly.

        conf_file: str or Falseish
            If conf_file is Falseish, look in the directory where
            self.filename sits, if self is not already associated with a
            conf_file. If associated, and conf_file arg is Falseish,
            read self.conf_file. If conf_file arg is a file name, read
            from that file.

        See spit_config for some documentation on the file layout.

        Note: If the config_file exist because of an earlier spit, and
        custom channel names was not available, channels are listed as the
        fallback names in the file. Then after this eat, self.chnames
        will be set to the list in the conf_file section 'channels'. The
        result can be that self.chnames and self.chnames_0 will be
        equal.

        The message then is that, if channel names are updated, you
        should spit before you eat.
        """
            
        chroot = os.path.dirname(self.filename)
        chroot = os.path.abspath(chroot)
        cfg = configparser()

        # Figure out file name of conf_file:
        if hasattr(self, 'conf_file') and not conf_file:
            cfgfn = self.conf_file
        elif conf_file:
            cfgfn = conf_file
        else:
            cfgfn = os.path.join(chroot, CONFIG_FILE)

        with open(cfgfn, 'r') as fo:
            pass            # Make proper error

        cfg.read(cfgfn)
        
        # Update channel names:
        if not self.chnames:
            self.chnames = dict(self.chnames_0)
        sec = 'channels'
        for i in cfg.options(sec):
            self.chnames[self._key(int(i))] = cfg.get(sec, i)

        # Update conditions:
        sec = 'conditions'
        for op in cfg.options(sec):
            if not op in self.conditions:
                raise KeyError('Not valid condition option: ' + op)
            self.conditions[op] = cfg.get(sec, op)

        # Update mask:
        self._make_mask()

    def pprint_conditions(self):
        """Pretty print conditions with custom names if they were valid
        for conditions, else with 'chx'."""

        raise NotImplementedError

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
        duration condition have no effect.
        """
        raise NotImplementedError
        
    def set_mask_on(self, b=True):
        """If mask is on, any calls for a channel will be
        masked. Meaning, the parts of the array not meeting the
        conditions are replaced with numpy.nan.

        Setting mask on, turns the filter off."""

        self._mask_on = b
        if self._mask_on: self._filter_on = False

    def set_filter_on(self, b=True):
        """If filter is on, any calls for a channel will be
        reduced. Meaning, the parts of the array not meeting the
        conditions are removed. It means that self.rec_cnt is probably
        greater than the len of the array returned from a call. However,
        any aray called for, will have the same len as the other.
        
        Setting filter on, turns the mask off.
        """

        self._filter_on = b
        if self._filter_on: self._mask_on = False        

    def _make_mask(self):
        """Set the attribute self.mask to a mask based on
        self.conditions"""

        andcons = self.conditions['and'].split(',')
        orcons = self.conditions['or'].split(',')

        # if c in risk of the empty string:
        andcons = [self._prep_condition(c) for c in andcons if c]
        orcons = [self._prep_condition(c) for c in orcons if c]
        
        andmask = datautils.array_and(self.D, andcons)
        ormask = datautils.array_or(self.D, orcons)
        self.mask = np.logical_and(andmask, ormask)

    def set_channel_names(self, names):
        """
        Set self.chnames.

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

    def __call__(self, key):
        """Make possible to retreive channels by key.
        
        key: string or integer.
        """
        # Primary need is to get an integer from key since D.keys are integers.

        i = self._key(key)

        if self._mask_on:
            return datautils.masked(self.D[i], self.mask)
        elif self._filter_on:
            raise NotImplementedError
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
        """Pattern a shell pattern. See fnmatch.fnmatchcase. Print the
        results to stdout.""" 

        for item in self.chnames.items():
            if fnmatch.fnmatchcase(item[1], pat):
                print item


    def ch(self, chname):
        """Return the channel data vector.

        chname: The channel name, or the fallback string for the
        channel, or an index integer for the channel.
        """
        return self.__call__(chname)

    def set_basefilemtime(self):
        """Attempt to find the original file in the same folder as
        self.filename is in. If found, set self.mtimestamp and
        self.mtimefs attributes, based on that file. Else, set it based
        on self.filename.

        """

        dirpath = os.path.split(self.filename)[0]
        name = os.path.basename(self.fs).split('.')[0]
        for ext in ORIGINEXTENSIONS: # This must be some user configuration.
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

    return ['ch' + str(i) for i in nums]

def txtpack(fn, **kwargs):
    """Return a ChannelPack instance loaded with text data file fn.

    This is a lazy function to get a loaded instance, using the
    cleverness provided by pulltxt module. No delimiter or rows-to-skip
    and such need to be provided. However, if necessary, **kwargs can be
    used to override clevered items to provide to numpys
    loadtxt. usecols might be such an item for example.

    Note that the call signature is the same as numpys loadtxt."""

    loadfunc = pulltxt.loadtxt_asdict
    cp = ChannelPack(loadfunc)
    cp.load(fn, **kwargs)
    names = pulltxt.PP.channel_names(kwargs.get('usecols', None))
    cp.set_channel_names(names)
    cp._patpull = pulltxt.PP              # Give a reference to the patternpull.
    cp.set_basefilemtime()
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
    cp.set_basefilemtime()
    return cp

