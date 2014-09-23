
    # This file is part of channelpack.

    # channelpack is free software: you can redistribute it and/or modify
    # it under the terms of the GNU General Public License as published by
    # the Free Software Foundation, either version 3 of the License, or
    # (at your option) any later version.

    # channelpack is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU General Public License for more details.

    # You should have received a copy of the GNU General Public License
    # along with channelpack.  If not, see <http://www.gnu.org/licenses/>.

"""
The functions :func:`~pack.txtpack` and :func:`~pack.dbfpack`, returning
laoded instances of the ChannelPack class, are made available by an
import of channelpack. The class `ChannelPack` is also made
available. Those objects are what channelpack mainly mean to deliver,
and live in the module `pack`. So, most of the time it should be enough
to import the namespace of channelpack:

    >>> import channelpack as cp
    >>> cp.txtpack
    <function txtpack at 0x8a44c34>
    >>> cp.dbfpack
    <function dbfpack at 0x8a44e9c>
    >>> cp.ChannelPack
    <class channelpack.pack.ChannelPack at 0x896171c>

The intention is to make channelpack self-documenting. Try introspecting the
objects.
"""

from .pack import ChannelPack, txtpack, dbfpack

__version__ = '0.1.4'
