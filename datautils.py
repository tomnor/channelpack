
"""
Helper module for processing data arrays and such.
"""

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
        b = eval(con)
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
