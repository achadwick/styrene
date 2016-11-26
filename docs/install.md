# Installation

MSYS2 packages will soon be available for Styrene,
but in the meantime you can install it manually.

Styrene expects to be invoked from the
native `MINGW32` or `MINGW64` environments that MSYS2 provides.
It can run with any of MSYS2's Python interpreters.
The current approach is to use the native Python interpreter
of your target system.

To install, run

    python3 setup.py install --prefix=/some/where

from either a MINGW64 or a MINGW32 shell.
