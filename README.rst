channelpack
===========

The ChannelPack class provides a callable container of data. The channelpack
package also provides some factory functions to get such a pack from data
files.

Channelpack is a Python project (a small library) assuming Numpy being
available and that numpy arrays are the preferred data sequences.

Example
-------

Produce some data and make a pack::

    >>> import channelpack as cp
    >>> data = {0: range(5), 1: ('A', 'B', 'C', 'D', 'E')}
    >>> names = {0: 'seq', 1: 'abc'}
    >>> pack = cp.ChannelPack(data=data, names=names)
    >>> pack
    ChannelPack(
    data={0: array([0, 1, 2, 3, 4]),
          1: array(['A', 'B', 'C', 'D', 'E'], dtype='<U1')},
    names={0: 'seq',
           1: 'abc'})
    >>> pack(0)
    array([0, 1, 2, 3, 4])
    >>> pack(0) is pack('seq')
    True

Set the pack mask and use it to slice or filter out parts::

    >>> pack.mask = (pack('seq') < 2) | (pack('abc') == 'D')
    >>> pack('seq', part=0)
    array([0, 1])
    >>> pack('seq', part=1)
    array([3])
    >>> pack('abc', nof='filter')
    array(['A', 'B', 'D'], dtype='<U1')
    >>> pack('abc', nof='nan')
    array(['A', 'B', None, 'D', None], dtype=object)
    >>> pack('seq', nof='nan')
    array([ 0.,  1., nan,  3., nan])

Read data from file::

    >>> import io
    >>> datstring = \
    ... u"""date: 20-05-01 17:39
    ... room: east lab hall, floor 2, room 8
    ... operator: Goran Operatorsson
    ...
    ... time, speed, onoff, distance
    ... 0, 23, on, 0.3
    ... 1, 21, off, 0.28
    ... """
    >>> sio = io.StringIO(datstring)
    >>> pack = cp.textpack(sio, delimiter=',', skiprows=5, hasnames=True)
    >>> pack
    ChannelPack(
    data={0: array([0., 1.]),
          1: array([23., 21.]),
          2: array([' on', ' off'], dtype='<U4'),
          3: array([0.3 , 0.28])},
    names={0: 'time',
           1: 'speed',
           2: 'onoff',
           3: 'distance'})

Lazy read numeric data::

    >>> datstring = \
    ... u"""date: 20-05-01 17:39
    ... room: east lab hall, floor 2, room 8
    ... operator: Goran Operatorsson
    ...
    ... time, speed, distance
    ... 0, 23, 0.3
    ... 1, 21, 0.28
    ... """
    >>> sio = io.StringIO(datstring)
    >>> pack = cp.lazy_textpack(sio)
    >>> pack
    ChannelPack(
    data={0: array([0., 1.]),
          1: array([23., 21.]),
          2: array([0.3 , 0.28])},
    names={0: 'time',
           1: 'speed',
           2: 'distance'})


Channel?
--------

The naming (channelpack) sort of origins from work with measurements and data
acquisition. Using tools for that, the recorded arrays of data are often called
"channels", because it was acquired through some IO channel.


Install
-------
::

    $ pip install channelpack

Documentation and repository
----------------------------

There is some documentation at `Read the Docs`_ and the code repository is on
`GitHub`_.

.. _Read the Docs: https://channelpack.readthedocs.org/en/latest/
.. _GitHub: https://github.com/tomnor/channelpack
