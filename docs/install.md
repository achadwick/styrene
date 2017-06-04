# Installation

MSYS2 packages will soon be available for Styrene,
but in the meantime you can install it manually with pip.
Don't forget to install pip3 first.

    pacman -S mingw-w64-{i686,x86_64}-python3-pip

Styrene expects to be invoked from the
native `MINGW32` or `MINGW64` environments that MSYS2 provides.
It can run with any of MSYS2's Python interpreters.
The current approach is to use the native Python interpreter
of your target system.

To install, run

    pip3 install .

in the distribution folder using 
either MINGW64 or a MINGW32 shell.
Note the trailing dot.

To uninstall, use

    pip3 uninstall Styrene

from anywhere.
