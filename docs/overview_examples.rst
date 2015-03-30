.. I made a back-up of this file temporarily as BAKoverview_examples.rst and I
.. will bring in here section by section from that file and make a test for each
.. thing. So then I can write and test and write some more and test again.


Overview and examples
*********************

The idea behind `channelpack` is to provide a quick and convenient way of
loading and analyzing (test) data.

channelpack requires `numpy <https://pypi.python.org/pypi/numpy>`_, but does not
attempt to install that for you during installation of channelpack. It's not a
huge deal to install numpy, but maybe not trivial either, and there might be
reasons you prefer to do that yourself.

.. automodule:: channelpack

Loading and exploring data files
================================

If your data is numeric and in a text file, the function :func:`~pack.txtpack`
try to be smart and figure out data delimiter, decimal separator, start-row of
data and the channel names::

    >>> import channelpack as cp
    >>> tp = cp.txtpack('testdata/subdir1/MesA1.csv')
    >>> tp
    <channelpack.pack.ChannelPack instance at ...>
    >>> tp.chnames
    {0: 'Time_100Hz', 1: 'P_cyl', 2: 'F_cyl', 3: 'L_cyl', 4: 'Fc1_cal', 5: 'Fc2_cal'}
    >>> tp.chnames_0
    {0: 'ch0', 1: 'ch1', 2: 'ch2', 3: 'ch3', 4: 'ch4', 5: 'ch5'}

The attribute chnames_0 is always available, it is a sort of fall-back if
chnames is not set. If not set, chnames is None.

The ChannelPack objects are made callable::

    >>> tp(1) is tp('P_cyl') is tp('ch1')
    True
    >>> type(tp(1))
    <type 'numpy.ndarray'>

"Channels" enjoy the functionality of numpy arrays::

    >>> tp.rec_cnt
    17665
    >>> tp(0).size
    17665
    >>> tp(0)[tp(0) < 0.10]
    array([ 0.  ,  0.01,  0.02,  0.03,  0.04,  0.05,  0.06,  0.07,  0.08,  0.09])
    >>> tp(0)[tp(0) < 0.10].size
    10

Esoteric
--------

channelpack make use of a humble rc file. If a file exist in
`os.path.expanduser('~')`, with the name
:data:`channelpack.pack.CHANNELPACK_RC_FILE`, being ``.channelpackrc``, it can
have this content::

    [channelpack]
    originextensions = b8b, blob

The originextensions value is a comma separated list of file extensions. The
only functionality from this currently is that two attributes are set::

    >>> tp.mtimefs
    '.../testdata/subdir1/MesA1.blob'
    >>> tp.mtimestamp
    'Tue Sep  9 23:00:04 2014'

given that there was some file with the same base name as the loaded file, but
with an extension as listed in `originextensions` value. The loaded file was::

    >>> tp.filename
    '.../testdata/subdir1/MesA1.csv'

The idea behind this is that the modification time of the original file (if any)
might be the time when some measurement was done, and so this time is made
available. Such a file is only searched for in the same directory as the loaded
file sits in.

Slicing out relevant parts of data
==================================

The channelpack object is basically holding a dict with data and a Boolean mask
(an array of the same length as the channels) to keep track of the condition
state of the object. The mask can be manipulated directly, but for possible
re-use of the condition settings, conditions are given as strings to the
channelpack.

General conditions
------------------

Assume some listing for a plot like this, using your favorite plotting library,
(`matplotlib <http://matplotlib.org/>`_) (assignment to underscores are just to
be able to test those examples with doctest)::

    >>> # plotit1
    >>> import matplotlib.pyplot as pp

    >>> import channelpack as cp

    >>> tp = cp.txtpack('testdata/sampledat1.txt')
    >>> _ = pp.figure(figsize=(12.5, 6.5))
    >>> ax1 = pp.subplot(111)

    >>> for n in (0, 3, 4):
    ...     _ = ax1.plot(tp(n), label=tp.name(n))

    >>> prop = {'size': 12}
    >>> _ = ax1.legend(loc='upper left', prop=prop)

    >>> pp.show()

producing an overview plot:

.. image:: pics/fig1.png

An update of the plotit1 listing follows to show conditions to sort out some
relevant parts of data::

   >>> # plotit2
   >>> _ = pp.figure(figsize=(12.5, 6.5))
   >>> ax1 = pp.subplot(111)

   >>> for n in (0, 3, 4):
   ...     _ = ax1.plot(tp(n), label=tp.name(n))

   >>> # Add conditions to the channelpack:
   >>> tp.add_condition('cond', '%(RPT) > %(AR_BST)')
   >>> tp.add_condition('cond', '(%(VG_STOP) == 70) |  (%(VG_STOP) == 90)')

   >>> # Make not true sections be replaced by nan's on calls:
   >>> tp.nof = 'nan'

   >>> _ = ax1.plot(tp(4), label=tp.name(4) + ' relevant', marker='x')

   >>> prop = {'size': 12}
   >>> _ = ax1.legend(loc='upper left', prop=prop)

   >>> pp.show()


Setting the `nof` attribute to 'nan' sets the samples not fulfilling the
criteria to numpy.nan, on calls. This is useful when plotting since nans are
nicely handled by matplotlib. In this case, `RPT` need to be bigger than
`AR_BST` and `VG_STOP` need to be either 70 or 90:

.. image:: pics/fig2.png

The ``nof`` attribute can have the values 'nan', 'filter' or ``None``. If
'filter', the effect is that only the samples with a corresponding True element
in the mask are returned on calls.

To see the current conditions, say::

    >>> tp.pprint_conditions()
    cond1: %(RPT) > %(AR_BST)
    cond2: (%(VG_STOP) == 70) |  (%(VG_STOP) == 90)
    startcond1: None
    stopcond1: None
    stopextend: None
    dur: None
    samplerate: None

The syntax of the conditions is python using numpy arrays. Any expression that
produces a Boolean array. Since the pack is callable, one can say
``tp('VG_STOP') == 70`` to produce such an array. When given as a string, the
identifier for the pack is replaced with ``%``. In the string the quotes around
the channel identifier is optional. To give ``tp('VG_STOP') == 70`` as a
condition string, ``tp.add_condition("cond", "%('VG_STOP') == 70")`` will work.

The different conditions are and:ed together.

Related methods:

* :func:`~channelpack.ChannelPack.add_condition`
* :func:`~channelpack.ChannelPack.clear_conditions`
* :func:`~channelpack.ChannelPack.pprint_conditions`

START and STOP conditions
-------------------------
