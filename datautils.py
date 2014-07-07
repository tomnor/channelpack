
"""
Helper module for processing data arrays and such.
"""

import numpy as np

def array_and(d, conditions):
    """Produce a boolean array based on conditions

    d: dict
        numpy 1d arrays. All arrays of the same shape (length). Keys are
        integers

    conditions: str
        A comma delimited list of conditions. Like 
        'd[12] == 2, d[1] > d[10]'.

    """

    conlist = [con.strip() for con in conditions.split(',')]
    print conlist
    a = np.ones(len(d[d.keys()[0]])) == 1 # Initial True array.
    for con in conlist:
        b = eval(con)
        a = np.logical_and(a, b)
    return a


def mask(a, b):
    """Return a numpy array with values from a where elements in b are not
    False.  Populate with None where b is False. When plotting, those
    elements look like missing, which can be a desired result.

    NOTE: This is to updated with my home stuff!

    """

    n = np.array([None for i in range(len(a))])
    return np.where(b, a, n) # a if b is True, else n.
