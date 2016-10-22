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
    pacman -S --needed zip python3 \
      mingw-w64-x86_64-gcc mingw-w64-x86_64-nsis mingw-w64-x86_64-binutils \
      mingw-w64-i686-gcc mingw-w64-i686-nsis mingw-w64-i686-binutils
    ```

3. Clone Styrene from its GitHub repository and try it out!

    ```sh
    pacman -S --needed git
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
