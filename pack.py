
# -*- coding: UTF-8 -*-

"""
Provide one or more baseclasses for holding a dict with data vectors,
(numpy arrays loaded from some data acqusition).

Sub clacces might load data from different sources, but the interface
from any class deriving from Pack should be the same.

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

----------------------------
"""
import re
import glob
import os, time

import numpy as np

from . import pulltxt, pulldbf
from . import datautils

ORIGINEXTENSIONS =  ['iad', 'd7d']

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

        self.mask_on = False    # Yeahh...
        self.filter_on = False
        self.mask = None
        # Dict with condition specs for the mask array:
        self.conditions = {'and': '', 'or': '', 'dur': 0, 'dur_min': 0,
                           'dur_max': 0} 

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

    def set_sammple_rate(self, rate):
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
        matches = re.findall(r'ch\d+', constr)
        for ch in matches:
            i = self._key(ch)
            constr = constr.replace(ch, 'd[' + str(i) + ']')

        if self.chnames:
            for ch in self.chnames.values():
                for m in re.findall(r'\w+', constr):
                    if ch == m:
                        i = self._key(ch)
                        constr = constr.replace(ch, 'd[' + str(i) + ']')

        # Check:
        for con in constr.split(','):
            if not re.search(r'd\[\d+\]', con):
                raise ValueError('This condition did not resolve to a valid' +
                                 ' channel: ' + con)
            # Still to check maybe if some d[4] has been used and 4 is not
            # available...

        current = self.conditions[andor]
        self.conditions[andor] = ','.join([current, constr]).strip(',')
        
    def _make_mask(self):
        """Set the attribute self.mask to a mask based on
        self.conditions"""
        
        self.mask = datautils.array_and(self.D, self.conditions['and'])


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
        try:
            return self.D[key]
        except KeyError:
            pass

        i = self._key(key)
        return self.D[i]

    def _key(self, chstr):
        """Return the integer key for chstr. It is the key for the first
        value found in chnames and chnames_0, that matches chstr."""

        if self.chnames:
            for item in self.chnames.items():
                if item[1] == chstr:
                    return item[0]
        for item in self.chnames_0.items():
            if item[1] == chstr:
                return item[0]

        raise KeyError(chstr)

    def name(self, ch, firstwordonly=False):
        """Return channel name for ch. ch is the channel name or the
        index number for the channel name, 0-based.

        ch: str or int. 
            The channel name or indexed number.

        firstwordonly: bool or "pattern".
            If True, return only the first non-spaced word in the name.
            If a string, use as a re-pattern to re.findall and return
            the first element found. There will be error if no match.

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
        for ext in ORIGINEXTENSIONS:
            res = glob.glob(dirpath + '/' + name + '.' + ext)
            if res: # Assume first match is valid.
                self.mtimefs = res[0]
                # Time stamp string:
                self.mtimestamp = time.ctime(os.path.getmtime(self.mtimefs)) 
                break
        else:
            self.mtimefs = self.filename
            self.mtimestamp = time.ctime(os.path.getmtime(self.mtimefs)) 

def fallback_names(nums):
    """Return a list like ['ch0', 'ch1',...], based on nums. nums is a
    list with integers."""

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

