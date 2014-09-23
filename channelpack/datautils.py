
"""
Helper module for processing data arrays and such.
"""

# http://nbviewer.ipython.org/github/demotu/BMC/blob/master/notebooks/DetectPeaks.ipynb
# See it for a cool peak detection function. Rep, interresting stuff:
# https://github.com/demotu/BMC

# TODO: Make all helper functions take a ChannelPack instance pack instead of
# all possible arguments.

import numpy as np

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
    
    Return all elements True if conditions is an empty list.
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

# def startstop_bool(d, start_con, stop_con, start_andor='and', stop_andor='and'):
def startstop_bool(pack):
    """Make a bool array based on start and stop conditions.

    d: dict
        numpy 1d arrays. All arrays of the same shape (length). Keys are
        integers 

    start_and, start_or, stop_and, stop_or_: list
        lists of conditions. Like 
        ['d[12] == 2', 'd[1] > d[10]'].

    Conditions formatting are as with the array_or and array_and
    functions. The strings are likely produced by a ChannelPack
    instance.

    If no start conditions are set, return all True.

    If there is start conditions but no stop conditions, this is legal,
    the True section will begin at first start and remain the rest of
    the array. Likewise, if there is stop conditions but no start
    condition, the returned array will be all True until the first stop
    slice, and the rest of the array is set to False.

    NOTE: This function does not work yet. IN WORK.
    UPDATE: I think it does work now. Update the docstring.
    """ 
    
    d = pack.D
    b = np.ones(len(d[d.keys()[0]])) == True

    start_and = pack.conconf.conditions_list('start_and')
    start_or = pack.conconf.conditions_list('start_or')
    stop_and = pack.conconf.conditions_list('stop_and')
    stop_or = pack.conconf.conditions_list('stop_or')

    # Pre-check:
    runflag = 'startstop'
    if not start_and and not start_or and not stop_and and not stop_or:
        return b
    elif not start_and and not start_or:
        runflag = 'stoponly'
    elif not stop_and and not stop_or:
        runflag = 'startonly'

    # startb:
    if runflag == 'stoponly':
        startb = b == False     # All False (Dummy assignment).
    elif not start_and and start_or:
        startb = array_or(d, start_or)
    elif start_and and not start_or:
        startb = array_and(d, start_and)
    elif start_and and start_or:
        a1 = array_and(d, start_and)
        a2 = array_or(d, start_or)
        startb = np.logical_and(a1, a2)
    else:
        assert 0, 'Semantic error'

    # stopb:
    if runflag == 'startonly':
        stopb = b == False      # All False (Dummy assignment).
    elif not stop_and and stop_or:
        stopb = array_or(d, stop_or)
    elif stop_and and not stop_or:
        stopb = array_and(d, stop_and)
    elif stop_and and stop_or:
        a1 = array_and(d, stop_and)
        a2 = array_or(d, stop_or)
        stopb = np.logical_and(a1, a2)
    else:
        assert 0, 'Semantic error'

    stop_extend = pack.conconf.get_stop_extend()

    return _startstop_bool(startb, stopb, runflag, stop_extend)

def _startstop_bool(startb, stopb, runflag, stop_extend):
    """Return boolean array based on start and stop conditions.

    startb, stopb: Numpy 1D arrays of the same length.
        Boolean arrays for start and stop conditions being fullfilled or not.

    """
    res = np.zeros(len(startb)) == True # All false at start

    start_slices = slicelist(startb)
    stop_slices = slicelist(stopb)

    # Special case when there is a start but no stop slice or vice versa:
    # if start_slices and not stop_slices:
    if runflag == 'startonly':
        try:
            start = start_slices[0]
            res[start.start:] = True  # Make True from first start and rest of array.
            return res
        except IndexError:
            return res          # Only start specified but no start condition
                                # fullfilled. Return all False.
    # elif not start_slices and stop_slices:
    elif runflag == 'stoponly':
        try:
            stop = stop_slices[0]
            res[:stop.start + stop_extend] = True # Make True up to first stop.
            return res
        except IndexError:
            return res == False # Only stop specified but no stop condition
                                # fullfilled. Return all True.

    stop = slice(0, 0)           # For first check
    start = slice(0, 0)          # For a possibly empty list start_slices.
    for start in start_slices:
        if start.start < stop.start:
            continue
        for stop in stop_slices:
            if stop.start > start.start:
                res[start.start: stop.start + stop_extend] = True
                break           # Next start
        else:
            # On a given start slice, the entire list of stop slices was
            # exhausted, none being later than the given start. It must mean
            # that from this given start, the rest is to be True:
            break

    if start.start > stop.start: # There was no stop for the last start in loop.
        res[start.start:] = True

    return res    

def slicelist(b):
    """Produce a list of slices given the boolean array b.

    Start and stop in each slice describe the True sections in b."""

    # This functionality must be in numpy somewhere?

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
        slicelst.append(slice(start, i + 1)) # True in the end.

    return slicelst
