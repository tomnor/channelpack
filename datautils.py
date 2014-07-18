
"""
Helper module for processing data arrays and such.
"""

# http://nbviewer.ipython.org/github/demotu/BMC/blob/master/notebooks/DetectPeaks.ipynb
# See it for a cool peak detection function. Rep, interresting stuff:
# https://github.com/demotu/BMC

import numpy as np

# TO DO: Put the eval things in try block and reraise exceptions. Else they are
# mysterious.

def array_and(d, conditions):
    """Produce a boolean array based on conditions

    d: dict
        numpy 1d arrays. All arrays of the same shape (length). Keys are
        integers

    conditions: list
        list of string conditions. Like 
        ['d[12] == 2', 'd[1] > d[10]'].

    The condition strings are stripped from leading and trailing white
    space. 

    """

    conlist = [con.strip() for con in conditions]
    print conlist, "'and'"
    a = np.ones(len(d[d.keys()[0]])) == 1.0 # Initial True array.
    if not conditions:                      # Maybe ''.
        return a
    for con in conlist:
        try:
            b = eval(con)
        except SyntaxError as se:
            raise SyntaxError('Error at eval in ' + __file__ + ' array_and.')
        a = np.logical_and(a, b)
    return a

def array_or(d, conditions):
    """Produce a boolean array based on conditions

    d: dict
        numpy 1d arrays. All arrays of the same shape (length). Keys are
        integers

    conditions: list
        A list of conditions. Like 
        ['d[12] == 2', 'd[1] > d[10]'].

    The condition strings are stripped from leading and trailing white
    space. 
    """    
    conlist = [con.strip() for con in conditions]
    print conlist, "'or'"
    a = np.ones(len(d[d.keys()[0]])) == 1.0 # True
    if not conlist or not conditions:
        return a                # All True if no conditions.
    a = a == 0.0                # False
    for con in conlist:
        try:
            b = eval(con)
        except SyntaxError as se:
            raise SyntaxError('Error at eval in ' + __file__ + ' array_or.')
        a = np.logical_or(a, b)
    return a

def masked(a, b):
    """Return a numpy array with values from a where elements in b are
    not False. Populate with numpy.nan where b is False. When plotting,
    those elements look like missing, which can be a desired result.

    NOTE: This is to updated with my home stuff!

    """

    n = np.array([np.nan for i in range(len(a))])
    return np.where(b, a, n) # a if b is True, else n.

def duration_bool(b, dur, durtype):
    """
    Mask the parts in b being True but does not meet the duration
    rules. Return an updated copy of b.

    b: 1d array with True or False elements.

    dur: int
        The number of consecutive elements to be True.

    durtype: str
        'strict', 'min' or 'max' accepted.

    """
    assert durtype in ['strict', 'min', 'max'], durtype
    
    slicelst = slicelist(b)
    b2 = np.array(b)
    
    dt = durtype
    for sc in slicelst:
        cnt = sc.stop - sc.start
        if ((dt == 'strict' and dur != cnt) or 
           (dt == 'min' and dur > cnt) or
           (dt == 'max' and dur < cnt)):
                b2[sc] = False
        
    return b2

def trigger_bool(d, start_con, stop_con):
    """Make a bool array based on start and stop conditions.

    d: dict
        numpy 1d arrays. All arrays of the same shape (length). Keys are
        integers 

    start_con: str
        One or more start conditions. If more than one, they are comma
        delimited. 

    stop_con: str
        One or more stop conditions. If more than one, they are comma
        delimited. 

    Conditions is like for the array_or and array_and functions. The strings are
    likely produced by a ChannelPack instance.

    NOTE: This function does not work yet.
    """ 

    try:
        s_bool = eval(start_con)
        p_bool = eval(stop_con)
    except SyntaxError as se:
        raise SyntaxError('Error at eval in ' + __file__ + ' trigger_bool.')

    start_slices = slicelist(s_bool)
    stop_slices = slicelist(p_bool)

    res = np.zeros(len(s_bool)) == True # All false

    stop = slice(0, 0)           # For initial check
    for start in start_slices:
        if start.start < stop.start:
            continue
        for stop in stop_slices:
            if stop.start > start.start:
                res[start.start: stop.start] = True

    if start.start > stop.start: # Was not Truified in loop.
        res[start.start:] = True

    return res

def slicelist(b):
    """Produce a list of slices given the boolean array b.

    Start and stop in each slice describe the True sections in b."""

    # This functionality must be in numpy somewhere.

    slicelst = []
    started = False
    for i, e in enumerate(b):
        if e and not started:
            start = i
            started = True
        if not e and started:
            slicelst.append(slice(start, i))
            started = False
    
    if e:
        slicelst.append(slice(start, i + 1))

    return slicelst
