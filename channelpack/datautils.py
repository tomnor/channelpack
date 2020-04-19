
"""
Helper module for processing data arrays and such.
"""
import numpy as np


def masked(a, b):
    """Return values as is in a which are True in b

    a, b : numpy.array
        b should be a boolean array. Both have the same size.

    Populate elements in returned array that are not True in b with
    numpy.nan or None as appropriate in the returned array.

    numpy.nan is used with numerical arrays (numpy.dtype.kind one of
    i, u, f, c). For all other types None is used. Note that integer
    values are upcasted to float when mixed with numpy.nan (which is a
    special kind of float). This happens with Numpy when creating the
    array.

    """

    # https://docs.scipy.org/doc/numpy/reference/generated/numpy.dtype.kind.html#numpy-dtype-kind
    # https://docs.scipy.org/doc/numpy/reference/arrays.scalars.html#arrays-scalars

    if a.dtype.kind in ('i', 'u', 'f', 'c'):
        return np.where(b, a, np.full(len(a), np.nan))
    else:
        return np.where(b, a, np.full(len(a), None))


def startstop_bool(startb, stopb):
    """Generator yielding bool values.

    True elements in startb are used as start triggers and true
    elements in stopb are used as stop triggers.

    True elements in stopb dominates startb.

    Sequences are looped over with `zip`, so will be truncated to the
    shortest sequence.

    Parameters
    ----------
    startb, stopb : sequence
        Elements are tested with `if el...`

    Example
    -------
    One descend

    height: 1 2 3 4 5 4 3 2 1
    startb: F F F F T F F F F (height == 5)
    stobb:  T F F F F F F F T (height == 1)
    result: F F F F T T T T F
    -> height:      5 4 3 2

    """

    started = False
    for start, stop in zip(startb, stopb):
        if stop:
            if started:
                started = False
            yield False
        elif start:
            if not started:
                started = True
            yield True
        elif started:
            yield True
        else:
            yield False


def slicelist(b):
    """Produce a list of slices given the boolean array b.

    Start and stop in each slice describe the True sections in b."""

    slicelst = []
    started, e = False, False

    for i, e in enumerate(b):
        if not started and e:
            start = i
            started = True
        elif started and not e:
            slicelst.append(slice(start, i))
            started = False

    if e:
        slicelst.append(slice(start, i + 1))  # True in the end.

    return slicelst
