
"""
Helper module for processing data arrays and such.
"""

# http://nbviewer.ipython.org/github/demotu/BMC/blob/master/notebooks/DetectPeaks.ipynb
# See it for a cool peak detection function. Rep, interresting stuff:
# https://github.com/demotu/BMC

# TODO: Make all helper functions take a ChannelPack instance pack instead of
# all possible arguments.

import numpy as np


def masked(a, b):
    """Return a numpy array with values from a where elements in b are
    not False. Populate with numpy.nan where b is False. When plotting,
    those elements look like missing, which can be a desired result.

    """

    if np.any([a.dtype.kind.startswith(c) for c in ['i', 'u', 'f', 'c']]):
        n = np.array([np.nan for i in range(len(a))])
    else:
        n = np.array([None for i in range(len(a))])
        # a = a.astype(object)
    return np.where(b, a, n)    # a if b is True, else n.


def duration_bool(b, rule, samplerate=None):
    """
    Mask the parts in b being True but does not meet the duration
    rules. Return an updated copy of b.

    b: 1d array with True or False elements.

    rule: str
        The rule including the string 'dur' to be evaled.

    samplerate: None or float
        Has an effect on the result.

    For each part of b that is True, a variable ``dur`` is set to the
    count of elements, or the result of (len(part) / samplerate). And then
    eval is called on the rule.

    """
    if rule is None:
        return b

    slicelst = slicelist(b)
    b2 = np.array(b)

    if samplerate is None:
        samplerate = 1.0

    for sc in slicelst:
        dur = (sc.stop - sc.start) / samplerate  # NOQA
        if not eval(rule):
            b2[sc] = False

    return b2


def startstop_bool(pack):
    """Make a bool array based on start and stop conditions.

    pack:
        pack.ChannelPack instance

    If there is start conditions but no stop conditions, this is legal,
    the True section will begin at first start and remain the rest of
    the array. Likewise, if there is stop conditions but no start
    condition, the returned array will be all True until the first stop
    slice, and the rest of the array is set to False.

    """
    b_TRUE = np.ones(pack.rec_cnt) == True  # NOQA

    start_list = pack.conconf.conditions_list('startcond')
    stop_list = pack.conconf.conditions_list('stopcond')

    # Pre-check:
    runflag = 'startstop'
    if not start_list and not stop_list:
        return b_TRUE
    elif not start_list:
        runflag = 'stoponly'
    elif not stop_list:
        runflag = 'start_only'

    # startb:
    if runflag == 'stoponly':
        # all False (dummy assignment)
        startb = b_TRUE == False  # NOQA
    else:
        startb = b_TRUE
        for cond in start_list:
            startb = startb & pack._mask_array(cond)

    # stopb:
    if runflag == 'startonly':
        # all False (dummy assignment)
        stopb = b_TRUE == False  # NOQA
    else:
        stopb = b_TRUE
        for cond in stop_list:
            stopb = stopb & pack._mask_array(cond)

    stopextend = pack.conconf.get_stopextend()

    return _startstop_bool(startb, stopb, runflag, stopextend)


def _startstop_bool(startb, stopb, runflag, stopextend):
    """Return boolean array based on start and stop conditions.

    startb, stopb: Numpy 1D arrays of the same length.
        Boolean arrays for start and stop conditions being fullfilled or not.

    """
    # All false at start
    res = np.zeros(len(startb)) == True  # NOQA

    start_slices = slicelist(startb)
    stop_slices = slicelist(stopb)

    # Special case when there is a start but no stop slice or vice versa:
    # if start_slices and not stop_slices:
    if runflag == 'startonly':
        try:
            start = start_slices[0]
            # Make True from first start and rest of array.
            res[start.start:] = True
            return res
        except IndexError:
            # Only start specified but no start condition
            # fullfilled. Return all False.
            return res

    elif runflag == 'stoponly':
        try:
            stop = stop_slices[0]
            res[:stop.start + stopextend] = True  # Make True up to first stop.
            return res
        except IndexError:
            # Only stop specified but no stop condition fullfilled
            # Return all True
            return res == False  # NOQA

    stop = slice(0, 0)           # For first check
    start = slice(0, 0)          # For a possibly empty list start_slices.
    for start in start_slices:
        if start.start < stop.start:
            continue
        for stop in stop_slices:
            if stop.start > start.start:
                res[start.start: stop.start + stopextend] = True
                break           # Next start
        else:
            # On a given start slice, the entire list of stop slices was
            # exhausted, none being later than the given start. It must mean
            # that from this given start, the rest is to be True:
            break

    # There was no stop for the last start in loop
    if start.start > stop.start:
        res[start.start:] = True

    return res


def slicelist(b):
    """Produce a list of slices given the boolean array b.

    Start and stop in each slice describe the True sections in b."""

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
        slicelst.append(slice(start, i + 1))  # True in the end.

    return slicelst
