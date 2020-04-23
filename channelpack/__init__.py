
    # This is channelpack. Load and filter acquisition data.
    # Copyright (C) 2014, 2015, 2016, 2017 Tomas Nordin

    # This program is free software: you can redistribute it and/or modify
    # it under the terms of the GNU General Public License as published by
    # the Free Software Foundation, either version 3 of the License, or
    # (at your option) any later version.

    # This program is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU General Public License for more details.

    # You should have received a copy of the GNU General Public License
    # along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
The functions :func:`~pack.txtpack` and :func:`~pack.dbfpack` and
:func:`~pack.sheetpack`, returning laoded instances of the ChannelPack
class, are made available by an import of channelpack. The class
`ChannelPack` is also made available. Those objects are what channelpack
mainly mean to deliver, and live in the module `pack`. So, most of the
time it should be enough to import the namespace of channelpack:

    >>> import channelpack as cp

    >>> type(cp.txtpack)
    <type 'function'>
    >>> type(cp.dbfpack)
    <type 'function'>
    >>> type(cp.sheetpack)
    <type 'function'>
    >>> type(cp.ChannelPack)
    <type 'classobj'>

The intention is to make channelpack self-documenting. Try introspecting the
objects.

"""

from .pack import ChannelPack, dbfpack, sheetpack

__version__ = '0.4.0'
