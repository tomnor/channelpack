
"""
Play with data extraction from an arbtrary text data file.

Assumptions:

1: There is some data delimiter used between data.
2: Decimal point is not used as data delimiter.
3: Data delimiter apart from white space is the same by count and
   character between all data.
4: As decimal delimiter is used either '.' or ','.

Prototyping a flexible data loading package.

One objective is to use numpys loadtxt without having to know delimiter
for data and delimiter for integer and fraction part for numbers.
So whatever is done here to accomplish this objective, only a wrapper
around numpys loadtxt should be exposed.

Another objective is to find channel names if any. One other
function can do that. Will it take two arguments - fn and usecols? Or
will it take no arguments and use cached data from the last pull? But
that might be confusing. I could just try out both versions. Having no
arguments seem a bit odd. You might want to operate a file without
loading data. But a module level instance of the last pull should be
available for the module tools, but not exposed, meaning underscore
prefix.

So the situation is that the loadtxt tools are one thing on its own,
kind of generic. But the channel names pulling is more exoteric and
related to a possible channelpack holder. And the tools used for both
are here in some module.
"""

from .pack import ChannelPack, txtpack, dbfpack

__version__ = '0.1.0'
