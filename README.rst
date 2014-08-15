
***********
channelpack
***********

A python package for loading, analyzing and slicing out acqusition data based on
conditions. Conditions and naming of channels can be saved as config files and
reused later in a convenient way.

channelpack origins from test engineering experience of handling data files from
test measurements. If those file are text kind of files, they might have some
inconvinient need-to-know featarues before loadable into python:

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

* Any text kind of file (numpy's loadtxt is used)
* dbf files (Raymond Hettinger `recipe
  <http://code.activestate.com/recipes/362715>`_ ) as low level reader.
* MS excel file support coming up. (Will use xlrd).
* Any file read by your own tools, provide a function returning a dict
  with channels to the ChannelPack class.

Depends
=======

channelpack imports numpy. Installation of channelpack will not arrange for
numpy to be installed. Do it your way. It is likely that if you consider
channelpack, you already have numpy installed.

Examples
=====

TODO: Make examples.
