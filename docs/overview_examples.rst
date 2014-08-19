Overview and examples
*********************

The idea behind `channelpack` is to provide a quick and convinient way of
loading and anlyzing (test) data.

channelpack requires `numpy <https://pypi.python.org/pypi/numpy>`_, but does not attempt to
install that for you during installation of channelpack. It's not a huge deal to
install numpy, but maybe not trivial either, and there might be reasons you
prefer to do that yourself.

.. automodule:: channelpack

Loading and exploring data files
================================

Examples of loading files.

Slicing out relevant parts of data
==================================

Examples of conditions. Spitting and eating conditions from a conf_file file.

AND and OR conditions
---------------------

Basic conditions

START and STOP conditions
-------------------------

Often referred to as `start trigger` and `stop trigger` with data acqusition
tools.

Duration conditions
-------------------

When given conditions is not enough.

Spitting to and eating from a file
==================================

Store the conditions figured out for later use with a data file with the same
lay-out.

Stripping "channel" names
-------------------------

Explain usage of `firstwordonly` keyword argument. Especially when spitting.
