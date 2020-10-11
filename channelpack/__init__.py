# This is channelpack, load and filter data.
# Copyright (C) 2014-2017, 2020 Tomas Nordin

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
Provide access to the ChannelPack class and som factory functions to get
a pack.
"""

from .pack import ChannelPack
from .readtext import textpack, lazy_textpack
from .dbf import dbfpack
from .readxl import sheetpack

__version__ = '0.6.2'
