# Installation

MSYS2 packages will soon be available for Styrene,
but in the meantime you can install it manually.

Styrene expects to be installed into the
Cygwin-like `MSYS` environment of an MSYS2 installation,
and run with its Python binary.
However it expects to be invoked from the
native `MINGW32` or `MINGW64` environments that MSYS2 provides.
Thus, the only supported way of installing the script is

    python3 setup.py install --prefix=/some/where

invoked from the MSYS2 shell.
