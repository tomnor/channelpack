.. I made a back-up of this file temporarly as BAKoverview_examples.rst and I
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

Assume a script like this, using your favorite plotting library, (`matplotlib
<http://matplotlib.org/>`_):

.. literalinclude:: ../testdata/plotit1.py

producing an overview plot:

.. image:: pics/fig1.png

AND and OR conditions
---------------------

An update of the script follows to show conditions to sort out some relevant
parts of data:

.. literalinclude:: ../testdata/plotit2.py

Setting the `nof` attribute to 'nan' sets the samples not fulfilling the
criteria to numpy.nan, on calls. This is useful when plotting since nans are
nicely handled by matplotlib. In this case, `RPT` need to be bigger than
`AR_BST` and `VG_STOP` need to be either 70 or 90:

.. image:: pics/fig2.png

::

   # A hint on what was available in the VG_STOP channel:
   >>> tp.nof = None
   >>> sorted(set(tp('VG_STOP')))
   [50.0, 60.0, 70.0, 90.0, 110.0]

Any channel called will have nan's the same way.

Related methods:

* :func:`~channelpack.ChannelPack.add_conditions`
* :func:`~channelpack.ChannelPack.clear_conditions`
* :func:`~channelpack.ChannelPack.mask_or_filter`
* :func:`~channelpack.ChannelPack.set_mask_on`
* :func:`~channelpack.ChannelPack.pprint_conditions`
