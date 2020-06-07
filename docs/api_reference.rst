channelpack API Reference
*************************

All objects and functions documented below are available by::

    import channelpack

in the `channelpack` namespace.

ChannelPack object
==================

.. autoclass:: channelpack.ChannelPack
    :special-members: __init__, __call__
    :members:


Functions to get a pack from data files
=======================================

Text
----

Data stored in readable text files in the form of delimited data
fields, (csv, txt). Fields might be numbers or text:

.. autofunction:: channelpack.textpack

If data is numeric only, a lazy variant is available:

.. autofunction:: channelpack.lazy_textpack

Spread sheet
------------

The library `xlrd` is used, so xls and xlsx types of spread sheets are
supported:

.. autofunction:: channelpack.sheetpack

Xbase DBF format
----------------

Legacy kind of data base format:

.. autofunction:: channelpack.dbfpack
