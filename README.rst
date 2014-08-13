***********
channelpack
***********

channelpack - A python package for loading acqusition data.

channelpack intend to deal with the inconvinence of text data files having a
number of non-data lines of text before the data begin, unknown data separator
and sometimes comma used as decimal separator.

When loaded, channelpack intend to provide convinient interactive retrival of
data "channels", either by a "channel" name parsed from the data file, or the
data column index number. There are tools to mask off parts of the data which is
not of interest, and to filter out parts that are of interest. This is done by a
set of conditions that can be saved for re-use. It is common that a file with
the same channel names from a new test need to be put to the same analyses. Then
it can happen that the new test-file have a different number of non-data rows
and different data delimiter and even decimal separator. channelpack should be
able to load the data without prior research of the file.

Depends
=======

channelpack imports numpy. channelpack will not arrange for numpy to be
installed. Do it your way. It is likely so that if you consider channelpack, you
already have numpy installed.

Usage
=====

TODO: Expand on usage.
