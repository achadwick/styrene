# Styrene – a package bundler

[![Documentation Status](https://readthedocs.org/projects/styrene/badge/?version=latest)](http://styrene.readthedocs.io/en/latest/?badge=latest)

Styrene makes usable app bundles for Windows.
It repacks MSYS2 software into neat bundles that are nicer for your users,
and easier for you to distribute.
If a package containing your app is already available in MSYS2,
it can be bundled with Styrene.

## Quick start

1. Install [MSYS2](https://msys2.github.io/)
   from its download page, and upgrade it as described there.

2. Install Styrene’s dependencies from the *MSYS Shell* command line
   that came with MSYS2:

    ```sh
    pacman -S python3
    pacman -S zip
    pacman -S mingw-w64-x86_64-nsis    # "x86_64" → "i686" for 32 bit
    pacman -S mingw-w64-x86_64-gcc
    pacman -S mingw-w64-x86_64-binutils
    ```

3. Clone Styrene from its GitHub repository and try it out!

    ```sh
    pacman -S git
    git clone https://github.com/achadwick/styrene.git
    cd styrene
    ./styrene.sh gtk3-examples.cfg
    start .     # then run the installer .exe
    ```

4. [Read the docs](http://styrene.readthedocs.io) to find out more.

## Licenses

* [GPLv3](COPYING) for the tool itself.
* [CC0][cc0] for code templates and generated code inside bundles.

See the Styrene [licensing policy][pol] in the documentation
for details of why we make this split.

[cc0]: https://creativecommons.org/publicdomain/zero/1.0/
[pol]: docs/licenses.md
