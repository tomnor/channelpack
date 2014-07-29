
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

    Return all elements True if conditions is an empty list.

    """

    conlist = [con.strip() for con in conditions]
    print conlist, "'and'"
    a = np.ones(len(d[d.keys()[0]])) == 1.0 # Initial True array.
    if not conditions:                      # Maybe empty.
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

def startstop_bool(d, start_con, stop_con, start_andor='and', stop_andor='and'):
    """Make a bool array based on start and stop conditions.

    d: dict
        numpy 1d arrays. All arrays of the same shape (length). Keys are
        integers 

    start_con: list
        A list of conditions. Like 
        ['d[12] == 2', 'd[1] > d[10]'].

    stop_con: list
        A list of conditions. Like 
        ['d[12] == 2', 'd[1] > d[10]'].

    start_andor: str
        One of 'and' or 'or'

    stop_andor: str
        One of 'and' or 'or'

    Conditions formatting are as with the array_or and array_and
    functions. The strings are likely produced by a ChannelPack
    instance.

    NOTE: This function does not work yet. IN WORK.
    """ 

    res = np.zeros(len(d.values()[0])) == True # All false at start
    if not start_con or not stop_con:
        return res == False     # Return all True then. Cannot compute.

    if start_andor == 'and':
        s_bool = array_and(d, start_con)
    elif start_andor == 'or':
        s_bool = array_or(d, start_con)
    else:
        raise ValueError(start_andor)

    if stop_andor == 'and':
        p_bool = array_and(d, stop_con)
    elif stop_andor == 'or':
        p_bool = array_or(d, stop_con)
    else:
        raise ValueError(stop_andor)

    start_slices = slicelist(s_bool)
    stop_slices = slicelist(p_bool)

    stop = slice(0, 0)           # For first check
    for start in start_slices:
        if start.start < stop.start:
            continue
        for stop in stop_slices:
            if stop.start > start.start:
                res[start.start: stop.start] = True
                continue

    if start.start > stop.start: # Last start was not Truified in loop.
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
        elif not e and started:
            slicelst.append(slice(start, i))
            started = False
    
    if e:
        slicelst.append(slice(start, i + 1))

    return slicelst
