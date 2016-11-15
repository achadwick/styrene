# Copyright © 2016 Andrew Chadwick.
#
# This file is part of ’Styrene.
#
# ’Styrene is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# ’Styrene is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ’Styrene.  If not, see <http://www.gnu.org/licenses/>.


import enum
import os
import logging

logger = logging.getLogger(__name__)


#: Where to store generated .ico files (relative to bundle root)
ICO_FILE_SUBDIR = "_icons"

#: Where to write launcher and postinst scripts
SCRIPTS_SUBDIR = "_scripts"

#: Data subfolder in the styrene Python package.
PACKAGE_DATA_SUBDIR = "data"

#: Basename of the postinst .cmd launcher for POSTINST_SH_FILE.
POSTINST_CMD_FILE = "postinst.cmd"

#: Basename of the shell script that's called to configure the bundle,
#: after it has been installed.
POSTINST_SH_FILE = "postinst.sh"

#: State file used by the launchers to record the last-configured
#: location for the bundle, or by the postinst scripting to indicate
#: that launchers do not need to configure the bundle.
LAUNCHER_LOCATION_STATE_FILE = "_location.txt"


# Types and casts:

class MSYSTEM (enum.Enum):
    """Native-Windows build targets in an MSYS2 insllation.

    Each enumeration member corresponds to a value for the MSYSTEM
    environment variable that refers to one of the two native-Windows
    build targets on an MSYS2 installation.

    Enumeration members have additional properties in addition to the
    normal enum stuff.

    """

    MINGW64 = "MINGW64"
    MINGW32 = "MINGW32"

    # Class convenience methods:

    @classmethod
    def from_environ(cls):
        """Get the MSYSTEM enum member for the current environment."""
        msystem_str = os.environ.get("MSYSTEM")
        try:
            return cls.from_str(msystem_str)
        except ValueError:
            logger.error("Not running in the correct MSYS2 environment.")
            raise

    @classmethod
    def from_str(cls, s):
        """Get the MSYSTEM enum member for a string. Case-insensitive."""
        s = str(s)
        s = s.casefold()
        for member_name, member in cls.__members__.items():
            if member.value.casefold() == s:
                return member
        raise ValueError(
            "Unknown MSYSTEM value. Valid strings: %r",
            [m.value for m in cls.__members__.values()],
        )

    # Member properties:

    @property
    def subdir(self):
        """Basename of this MSYSTEM's dir at the / of the MSYS2 install."""
        return {
            MSYSTEM.MINGW64: "mingw64",
            MSYSTEM.MINGW32: "mingw32",
        }[self]

    @property
    def bits(self):
        """Number of bits, 32 or 64."""
        return {
            MSYSTEM.MINGW64: 64,
            MSYSTEM.MINGW32: 32,
        }[self]

    @property
    def arch(self):
        """CPU architecture code, either "x86_64" or "i686"."""
        return {
            MSYSTEM.MINGW64: "x86_64",
            MSYSTEM.MINGW32: "i686",
        }[self]

    @property
    def package_name_prefix(self):
        """Name prefix for pacman packages"""
        return "mingw-w64-%s-" % (self.arch,)

    @property
    def bundle_name_suffix(self):
        """Name suffix for generated bundles."""
        return "-w%02d" % (self.bits,)

    @property
    def substs(self):
        """Standard subsitution variables for templating."""
        return {
            "msystem_subdir": self.subdir,
            "bits": self.bits,
            "pkg_prefix": self.package_name_prefix,
        }
