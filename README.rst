
***********
channelpack
***********

A python package for loading, analyzing and slicing out acqusition data based on
conditions. Conditions and naming of channels can be saved as config files and
reused later in a convenient way.

channelpack origins from test engineering experience of handling data files from
test measurements. If those file are text kind of files, they might have some
inconvinient need-to-know features before loadable into python:

* Rows to skip - a number of lines (file meta data) prior to test data.
* Data delimiter - The character used to separate one data from the other, often
  space, tab or comma.
* Decimal separator - Depending on your region, the decimal separator is
  sometimes a comma, sometimes a dot.
* The naming of "channels", if named, could be on a row not immediately above
  the data, (following row could be engineering units for example).

channelpack intend to deal with the inconveniences of text data files described
above.

Data files:

* Any text (numeric) kind of file (numpy's loadtxt is used).
* dbf files (Raymond Hettinger `recipe
  <http://code.activestate.com/recipes/362715>`_ as low level reader).
* Spread sheet files (xlrd is used).
* Any file read by your own tools, provide a function returning a dict
  with channels to the ChannelPack class.

Example
=======

channelpack has some convenience functions for getting a pack::

    >>> import channelpack as cp
    >>> sp = cp.sheetpack('testdata/sampledat3.xls')
    >>> sp.chnames
    {0: u'txtdata', 1: u'nums', 2: u'floats'}

Packs are made callable, by name or column index::

    >>> sp(0)
    array([u'A', u'A', u'C', u'D', u'D'],
          dtype='<U1')
    >>> sp(0) is sp('txtdata')
    True

A boolean mask array is kept to keep track of "True parts"::

    >>> sp.parts()
    [0]
    >>> sp.add_condition('cond', '(%(0) == "A") | (%(0) == "D")')
    >>> sp.parts()
    [0, 1]
    >>> sp('txtdata', 0)
    array([u'A', u'A'],
          dtype='<U1')
    >>> sp('txtdata', 1)
    array([u'D', u'D'],
          dtype='<U1')

Now persist the conditions and load a new data set that need the same
conditions::

    >>> sp.spit_config()
    >>> sp = cp.sheetpack('testdata/sampledat4.xls', stopcell='c6')
    >>> sp.parts()
    [0]
    >>> sp.eat_config()
    >>> sp.parts()
    [0, 1]
    >>> sp('txtdata', 0)
    array([u'A'],
          dtype='<U1')
    >>> sp('txtdata', 1)
    array([u'D'],
          dtype='<U1')
    >>> sp('txtdata')
    array([u'A', u'C', u'C', u'C', u'D'],
          dtype='<U1')

Depends
=======

There is a dependency on xlrd as of version 0.2.0. It is installed if not
available.

channelpack imports numpy. Installation of channelpack will not arrange for
numpy to be installed. Do it your way. It is likely that if you consider
channelpack, you already have numpy installed.

Documentation and changes
=========================

`Documentation <http://channelpack.readthedocs.org/en/latest/>`_

`Changes <http://channelpack.readthedocs.org/en/latest/changelog.html>`_

As of version 0.3.0, channelpack is not backwards compatible. The way of storing
and making substitutions of conditions is new, plus a bunch of other changes
that breaks earlier versions. But it's much better now.
