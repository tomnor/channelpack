
# -*- coding: UTF-8 -*-

"""
Provide one or more baseclasses for holding a dict with data vectors, (numpy
arrays loaded from some data acqusition).

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
channel names from a given measurement session.

There could be a function to spit out a config file to the directory
where the data file is sitting. This file is a config file. It has a
section called 'NAMES' where each option is a channel name with
corresponding index as value. 'NAMES' can be extended with an asterisk
saying what data files the mapping is valid for, being all files with an
asterisk. It's a shell pattern, so to limit valid file names, it can be
[NAMES "<valid prefix>*.csv"], or [NAMES "mes_M*.*"] or similar.

Another section gives a possibility to remap the channel index order, it's
called [REMAP], one option: neworder = [3, 2 , 4, 1, 0]. No? This should
conflict with the NAMES section. Not applicable I think.
----------------------------
"""
import re

from . import pulltxt

class ChannelPack:
    """Base class for a pack of data. Hold a dict with channel index
    numbers as keys. The channels can be called by channel name or
    index. This object is callable by channel name or index.

    """

    # TO DO:
    # Add a "present" method. Pretty printing of the pack. Also implement some
    # __repr__ thing.

    def __init__(self, loadfunc=None):
        """Return a pack

        loadfunc: Use this function to load the data. It is a function
        that returns un-packable numpy arrays, being the channels
        data. Like ch1, ch2, ch3 = loadfunc(*args, **kwargs)

        If D = loadfunc(*args, **kwargs), then shape(D) gives
        (<num_channels>, <num_records>). Numpy would probably call this
        a transposed matrix, since data files normally have the shape
        (rows, cols).

        See method load.
        
        """
        self.loadfunc = loadfunc
        self.D = dict()
        self.fn = None          # The loaded filename

        # Lists for channel names and indexes. By default, if a reduced number
        # of channels is loaded relative the data file, chindex will reflect
        # that by containing numbers such as [4, 6, 7] for example.
        self.chnames = None       # Channel names if reachable. list.
        self.chnames_0 = None     # Fall back names, always available. ch0, ch1
        self.chindex = None       # 0, 1, 2, ordered index numbers.

        self.rec_cnt = 0

    def load(self, *args, **kwargs):
        """Load the data using loadfunc.

        args, kwargs: Forward to the loadfunc. args[0] must be the
        filename. And so it means that loadfunc must take the filename
        as it's first argument.

        Set channel names attributes and the filename attribute.

        """
        D = self.loadfunc(*args, **kwargs)                
        usecols = kwargs.get('usecols', None)
        # Below is problem when there is only one channel. Then D is ONE array
        # of data and this goes wrong.
        self.chindex = usecols or range(len(D))
        self.chnames_0 = fallback_names(self.chindex)

        for i, n in enumerate(self.chindex):
            self.D[n] = D[i]

        i = self.chindex[0]
        self.rec_cnt = len(self.D[i]) # If not all the same, there should have
                                      # been an error already

    def __call__(self, key):
        """Make possible to retreive channels by key.
        
        key: string or integer.
        """
        # Primary need is to get an integer from key since D.keys are integers.
        try:
            return self.D[key]
        except KeyError:
            pass

        i = self._channelindex(key)
                
        return self.D[i]

    def _channelindex(self, chstr, callindex=True):
        """Helper for getting index on based on string chstr. Make error if
        ch does not exist in chnames or chnames_0. Returned index i can be
        used for self.D[i], if callindex is True. If callindex is false,
        then i is used for self.chnames[i]."""

        if self.chnames and chstr in self.chnames:
            i = self.chnames.index(chstr)
        elif chstr in self.chnames_0:
            i = self.chnames_0.index(chstr)
        else:
            raise KeyError(str(chstr))  

        if callindex:
            return self.chindex[i]
        else:
            return i

    def name(self, ch, firstwordonly=False):
        """Return channel name for ch. ch is the channel name or the index
        number for the channel name, 0-based.

        ch: str or int. 
            The channel name or indexed number.

        firstwordonly: bool or "pattern".
            If True, return only the first non-spaced word in the name.
            If a string, use as a re-pattern to re.findall and return the
            first element found. There will be error if no match.

        Returned channel name is the fallback string if "custom" names
        are not available.

        """

        # Consider some control over the error produced on failure based on
        # non-existent channel name or index.

        names = self.chnames or self.chnames_0
        try:
            i = int(ch)
        except ValueError:
            i = self._channelindex(ch, callindex=False)

        if not firstwordonly:
            return names[i]
        elif firstwordonly == True:
            return names[i].split()[0].strip()

        return re.findall(firstwordonly, names[i])[0] # Remove trailing
                                                      # non-alphanumerics. Also,
                                                      # make error if no match.

    def ch(self, chname):
        """Return the channel data vector.

        chname: The channel name, or the fallback string for the channel,
        or an index integer for the channel.
        """
        return self.__call__(chname)

    def set_basefilemtime(self):
        """Attempt to find the original file in the same folder as fs is
        in. If found, set self.mtimestamp and self.mtimefs
        attributes. This might fail, and the attributes won't exist. It
        might also get wrong. But, if a file is found, and it is the
        base data file, and it has not been modified since storage, its
        probably correct.

        #######
        NOTE: This method just copied from my other stuff. Improve by
        testing and figure out smart way of keeping extensions to look
        for. Also - structure module not available. 
        Remove structure dependency and rely on stdlib stuff.
        Also, let the fallback timestamp be for self.fn. (fs).
        #####
        """

        dirpath = os.path.split(self.fs)[0]
        # name = self.name.split('.')[0]
        name = os.path.basename(self.fs).split('.')[0]
        for ext in ['iad', 'd7d']:
            res = structure.globfind(dirpath, 
                                     name + '.' + ext, slash_cnt=1, 
                                     res_mess=False)
            if res: # Assume first match is valid.
                self.mtimefs = res[0]
                # Time stamp string:
                self.mtimestamp = time.ctime(os.path.getmtime(self.mtimefs)) 
                break

def fallback_names(nums):
    """Return a list like ['ch0', 'ch1',...], based on nums. nums is a list
    with integers."""

    return ['ch' + str(i) for i in nums]

def txtpack(fn, **kwargs):
    """Return a ChannelPack instance loaded with data file fn.

    This is a lazy function to get a loaded instance, using the cleverness
    provided by pulltxt module. No delimiter or rows-to-skip and such
    need to be provided. However, if deemed necesseray, **kwargs can be
    used to override clevered items to provide to numpys
    loadtxt. usecols might be such an item for example.

    Note that the call signature is the same as numpys loadtxt."""

    loadfunc = pulltxt.loadtxt
    cp = ChannelPack(loadfunc)
    cp.load(fn, **kwargs)
    cp.patpull = pulltxt.PP              # Give a reference to the patternpull.
    cp.chnames = cp.patpull.channel_names(kwargs.get('usecols', None))['names']
    cp.fn = fn
    return cp
