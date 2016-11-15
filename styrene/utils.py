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


"""Little utility functions"""

import re
import os.path
import logging

logger = logging.getLogger(__name__)


def nsis_escape(s):
    """Escapes a string for interpolating into an NSIS quoted string."""
    s = str(s)
    s = s.replace("$", r"$$")
    s = s.replace('"', r'$\"')
    s = s.replace('`', r'$\`')
    s = s.replace("'", r"$\'")
    return s


def str2key(s, prefix="", suffix=""):
    """Convert a string to a useful dict/format() key."""
    return prefix + re.sub(r'\W+', "_", s.strip().casefold()) + suffix


def str2filename(s, prefix="", suffix=""):
    """Convert a string to a useful filename part WITHOUT spaces."""
    return prefix + re.sub(r'\W+', "-", s.strip().lower()) + suffix


def winsafe_filename(s):
    """Convert a string to a safe Windows file/folder name. Spaces allowed."""
    s = re.sub(r'[\000-\037<>:"/\\|?*]', '_', s.strip())
    s = re.sub(r'^(CON|PRN|AUX|COM\d|LPT\d)$', r'_\1', s, flags=re.I)
    return s


def uniq(self, seq):
    seen = set()
    for item in seq:
        if item in seen:
            continue
        seen.add(item)
        yield item


def findexe(basename, prefix, exts=(".exe",)):
    """Expands path elements for an executable.

    :param str basename: Basename to search for for.
    :param str prefix: POSIX-style prefix to search, in POSIX notation.
    :param tuple exts: Allowed filename extensions.

    The path returned is relative to the prefix, and is a win32 relative
    path separated by backslashes.

    """
    search_paths = [
        ("local", "bin"),
        ("bin",),
    ]
    for ext in exts:
        for path_elems in search_paths:
            path_elems = list(path_elems)
            path_elems.append(basename + ext)
            path = os.path.join(prefix, *path_elems)
            if os.path.isfile(path):
                return "\\".join(path_elems)
    return None


def js_escape(s):
    """Escapes a string for interpolation into a JS string constant."""
    s = str(s)
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    s = s.replace("'", "\\'")
    return s


def sh_escape(s):
    """Escapes a string for use in single-quoted shell string constant."""
    s = str(s)
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    return s


def c_escape(s):
    """Escapes a string for use in a C wchar_t* constant (L"...")."""
    s = str(s)
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    return s


def boolify(s):
    """Lax convertsion of strings to bools."""
    s = str(s).strip()
    return s.casefold() not in (
        "False".casefold(),
        "0",
        "No".casefold(),
        "N".casefold(),
        "",
    )
