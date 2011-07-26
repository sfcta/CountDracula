"""

DTA is a python module that facilitates network coding, analysis and visualization for
DTA (Dynamic Traffic Assignment).  This is a stub file to illustrate header convention; this
module docstring will be improved during development.

"""

__copyright__   = "Copyright 2011 SFCTA"
__license__     = """
    This file is part of DTA.

    DTA is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    DTA is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with DTA.  If not, see <http://www.gnu.org/licenses/>.
"""

from .MassUploadFiles import MassUploadFiles
from .ParseXlsToCDCommandsList import ParseXlsToCDCommandsList
from .ReadFromCD import ReadFromCD
from .WriteToCD import WriteToCD


__all__ = ['MassUploadFiles', 'ParseXlsToCommandsList', 'ReadFromCD',
           'WriteToCD'
]
