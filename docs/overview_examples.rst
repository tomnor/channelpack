Overview and examples
*********************

The idea behind `channelpack` is to provide a quick and convenient way of
loading and analyzing (test) data.

channelpack requires `numpy <https://pypi.python.org/pypi/numpy>`_, but does not
attempt to install that for you during installation of channelpack. It's not a
huge deal to install numpy, but maybe not trivial either, and there might be
reasons you prefer to do that yourself.

.. automodule:: channelpack

The function :func:`~pack.txtpack` try to determine delimiters and possible
"channel" names and start of data automatically, but this works only if data is
numerical. There is no limitation of the :class:`~channelpack.ChannelPack` class
for the data it holds - the arrays are numpy 1d arrays.

Loading and exploring data files
================================

If your data is numeric and in a text file, the function `txtpack` try to be
smart and figure out data delimiter, decimal separator, start-row of data and
the channel names::

    >>> import channelpack as cp
    >>> tp = cp.txtpack('MesA1.csv')
    >>> tp
    <channelpack.pack.ChannelPack instance at 0xb6202eac>
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
    '/path/to/data/MesA1.blob'
    >>> tp.mtimestamp
    'Tue Sep  9 23:00:04 2014'

given that there was some file with the same base name as the loaded file, but
with an extension as listed in `originextensions` value. The loaded file was::

    >>> tp.filename
    '/path/to/data/MesA1.csv'

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

An update of the script follows to show `and` and `or` conditions to sort out
some relevant parts of data:

.. literalinclude:: ../testdata/plotit2.py

Setting the mask on sets the samples not fulfilling the criteria to numpy.nan,
on calls. This is useful when plotting since nans are nicely handled by
matplotlib. In this case, `RPT` need to be bigger than `AR_BST` and `VG_STOP`
need to be either 70 or 90:

.. image:: pics/fig2.png

::

   # A hint on what was available in the VG_STOP channel:
   >>> tp.set_mask_on(False)
   >>> sorted(set(tp('VG_STOP')))
   [50.0, 60.0, 70.0, 90.0, 110.0]

Any channel called will have nan's the same way.

Related methods:

* :func:`~channelpack.ChannelPack.add_conditions`
* :func:`~channelpack.ChannelPack.clear_conditions`
* :func:`~channelpack.ChannelPack.mask_or_filter`
* :func:`~channelpack.ChannelPack.set_mask_on`
* :func:`~channelpack.ChannelPack.pprint_conditions`

START and STOP conditions
-------------------------

Often referred to as `start trigger` and `stop trigger` with data acquisition
tools.

Sometimes it is easier to slice out relevant parts by specifying a start and a
stop. This can be done using the same method as above,
:func:`~channelpack.ChannelPack.add_conditions`, (or
:func:`~channelpack.ChannelPack.set_conditions`) setting the `conkey` argument to one
of

* 'start_and'
* 'start_or'
* 'stop_and'
* 'stop_or'

From the record where the start condition(s) are True, the part will remain True
until the condition(s) for stop is True, even though the start conditions might
cease to be True in between.

A similar script again:

.. literalinclude:: ../testdata/plotit3.py

Early in the data, `AR_BST` has a quick peak exceeding 200, a fulfilled start
condition. When `VG_STP` is 90 and `RPT` is bigger than `VG_STOP`, the first
relevant part is defined by a stop condition fulfilled:

.. image:: pics/fig3.png

Note that the start condition is fulfilled in parallel with the stop condition,
but the stop condition dominate. As soon as the stop condition is not True
anymore, a new start is defined (condition fulfilled). The new start is not
meeting any fulfilled stop condition, and so is valid the rest of data.

A related method is :func:`~channelpack.ChannelPack.set_stop_extend`. For cases
when some extra elements should be added to the end of the start-stop part.

Duration conditions
-------------------

Consider the plotit3.py example above and the plot. A new start happened after
the first part had been defined. This was maybe not desired and could obviously
be avoided by playing further with conditions. But at times it might be easier
to set a duration rule.

    >>> tp = plotit3.tp
    >>> tp('VG_STOP', 0).size
    2133
    >>> tp('VG_STOP', 1).size
    2766
    >>> tp('VG_STOP', 2).size
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/usr/local/lib/python2.7/dist-packages/channelpack/pack.py", line 567, in __call__
        return self.D[i][sl[part]]
    IndexError: list index out of range

An un-mentioned feature sneaked in, see the
:func:`~channelpack.ChannelPack.__call__` signature for docs. Anyway, two relevant
parts was defined by the start-stop conditions, and they can be retrieved
respectively by enumeration this way. Now I know the length of each part, and
add a duration rule to the script to exclude the second part:

.. literalinclude:: ../testdata/plotit4.py

And a new plot to show off the difference:

.. image:: pics/fig4.png

Related methods:

* :func:`~channelpack.ChannelPack.set_duration`
* :func:`~channelpack.ChannelPack.set_sample_rate`
* :func:`~channelpack.ChannelPack.__call__`

Spitting and eating a file
==========================

It's about time to mention that details on the conditions settings can be
reviewed interactively by:

    >>> tp.pprint_conditions()
    and: None
    or: None
    start_and: AR_BST >= 200
    start_or: None
    stop_and: VG_STOP == 90, RPT > VG_STOP
    stop_or: None
    stop_extend: None
    dur: 2500
    durtype: max
    samplerate: None

Oftentimes, conditions are played with interactively until a setting satisfying
the needs is found. It can also be so that the setting will work equally well
with some other data file, because the structure of the data is the same, as
well as the channel names. In this case it might be convenient to store away the
settings found out:

    >>> tp.spit_config()

The command spits a file to the directory where the loaded data file sits by
default. It look like this:

.. literalinclude:: ../testdata/conf_file.cfg

And is given by default the name ``conf_file.cfg``.

When this is done, setting the same conditions on a similar data file again is
easier, if :func:`~channelpack.ChannelPack.eat_config` is used. If to
eat_config a file with a name other than ``conf_file.cfg``, the name is given as
an argument, but now just eat the default file:

.. literalinclude:: ../testdata/plotit5.py

And so the condition settings don't have to be figured out again. No plot this
time, but I promise, I have tried it.

--------------

The ``conf_file.cfg`` can be used to customize the channel names and / or
experimenting with the conditions. The work flow could look like this:

    >>> tp = cp.txtpack('sampledat.txt')
    >>> tp.chnames
    {0: 'RPT', 1: 'B_CACT', 2: 'P_CACT', 3: 'VG_STOP', 4: 'AR_BST', 5: 'PLRT_1', 6: 'TOQ_BUM'}
    >>> tp.pprint_conditions()
    and: None
    or: None
    start_and: None
    start_or: None
    stop_and: None
    stop_or: None
    stop_extend: None
    dur: None
    durtype: None
    samplerate: None
    >>> tp.spit_config('conf_file_mod.cfg')

Open the spitted file, make some work and save it:

.. literalinclude:: ../testdata/conf_file_mod.cfg

Then eat the file and changes should be applied:

   >>> tp.eat_config()
   >>> tp.chnames
   {0: 'RPT_MOD', 1: 'B_CACT', 2: 'ABC', 3: 'DEF', 4: 'AR_BST', 5: 'PLRT_1', 6: 'TOQ_BUM'}
   >>> tp.pprint_conditions()
   and: RPT_MOD > 250
   or: None
   start_and: None
   start_or: None
   stop_and: None
   stop_or: None
   stop_extend: None
   dur: None
   durtype: None
   samplerate: None



Related methods:

* :func:`~channelpack.ChannelPack.spit_config`
* :func:`~channelpack.ChannelPack.eat_config`

Stripping "channel" names
-------------------------

The :func:`~channelpack.ChannelPack.name` method is maybe worth a mention. It has
some tricks to fiddle with the name returned. Consider this example:

    >>> import channelpack as cp
    ORIGINEXTENSIONS: ['b8b', 'blob']
    >>> tp = cp.txtpack('dat_0000.txt')
    >>> tp.name(0)
    'Time [s]'
    >>> tp.name(1)
    'Quantity_ - 12345678;  [qunit]'
    >>> tp.name(2)
    'Distance - 12345678;  [mm]'
    >>> tp.name(3)
    'Stresslevel& - 12345678;  [kLevel]'

Sometimes names look like that. Fiddle with the name:

    >>> tp.name(0, firstwordonly=True)
    'Time'
    >>> tp.name(1, firstwordonly=True)
    'Quantity_'
    >>> tp.name(1, firstwordonly=r'[A-Za-z]+')
    'Quantity'
    >>> tp.name(3, firstwordonly=r'\w+')
    'Stresslevel'

The same keyword (`firstwordonly`) exist also for the `spit_config` method, so
names can be stripped also to the spitted file. But names in the pack are not
modified until a eat_config is done.

Related methods:

* :func:`~channelpack.ChannelPack.name`
* :func:`~channelpack.ChannelPack.spit_config`
* :func:`~channelpack.ChannelPack.eat_config`

An error detour
^^^^^^^^^^^^^^^

When working with the above section, before cheating with the data file, I got problem:

    >>> tp = cp.txtpack('dat_0000.txt')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/usr/local/lib/python2.7/dist-packages/channelpack/pack.py", line 856, in txtpack
        cp.load(fn, **kwargs)
      File "/usr/local/lib/python2.7/dist-packages/channelpack/pack.py", line 149, in load
        self.D = self.loadfunc(*args, **kwargs)
      File "/usr/local/lib/python2.7/dist-packages/channelpack/pulltxt.py", line 317, in loadtxt_asdict
        d = loadtxt(fn, **kwargs)
      File "/usr/local/lib/python2.7/dist-packages/channelpack/pulltxt.py", line 307, in loadtxt
        return np.loadtxt(fn, **txtargs)
      File "/usr/lib/pymodules/python2.7/numpy/lib/npyio.py", line 805, in loadtxt
        items = [conv(val) for (conv, val) in zip(converters, vals)]
      File "/usr/local/lib/python2.7/dist-packages/channelpack/pulltxt.py", line 282, in _floatit
        return float(s.replace(',', '.'))
    ValueError: could not convert string to float: Time [s]

The function :func:`~pack.txtpack` is not guaranteed to succeed, and it
didn't. The traceback suggest that computing the number of rows to skip has
failed, (trying to float a channel name). Then it can be a work-around to check
up on the rows to skip and pass that information:

    >>> tp = cp.txtpack('dat_0000.txt', skiprows=11)
    [] 'and'
    [] 'or'

Also, the output revealed here is debug output that will be removed shortly. In
the rest of the document I have hidden this.

This failure is likely to occur currently if there is a row before actual data,
delimited as the data, being cluttered with numbers, counting to the same number
of fields as in the data rows. 
