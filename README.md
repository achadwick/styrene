# Styrene – a package bundler

[![Documentation](https://readthedocs.org/projects/styrene/badge/?version=latest)](http://styrene.readthedocs.io/en/latest/?badge=latest)
[![Appveyor Build status](https://ci.appveyor.com/api/projects/status/dxspflkulv60uv97?svg=true)](https://ci.appveyor.com/project/achadwick/styrene)
[![Tea-CI Build status](https://tea-ci.org/api/badges/achadwick/styrene/status.svg)](https://tea-ci.org/achadwick/styrene)

Styrene makes usable app bundles for Windows.
It repacks MSYS2 software into neat bundles that are nicer for your users,
and easier for you to distribute.
If a package containing your app is already available in MSYS2,
it can be bundled with Styrene.
You can also bundle packages you build yourself.

## Quick start

1. Install [MSYS2](https://msys2.github.io/)
   from its download page, and upgrade it as described there.

2. Install Styrene’s dependencies from the *MSYS Shell* command line
   that came with MSYS2:

   ```sh
   pacman -S --needed zip \
     mingw-w64-x86_64-python3 \
     mingw-w64-x86_64-gcc mingw-w64-x86_64-nsis mingw-w64-x86_64-binutils \
     mingw-w64-i686-python3 \
     mingw-w64-i686-gcc mingw-w64-i686-nsis mingw-w64-i686-binutils
   ```

   And the ones for fetching and installing too:

   ```sh
   pacman -S --needed git
   pacman -S mingw-w64-i686-python3-pip mingw-w64-i686-python3-pip
   ```

3. Clone Styrene from its GitHub repository and install it

   ```sh
   git clone https://github.com/achadwick/styrene.git
   cd styrene
   pip3 install .
   ```

4. Try it out with the demo config file!

   ```sh
   styrene ./gtk3-examples.cfg
   start .     # then try running one of the installer .exe files
   ```

5. [Read the docs](http://styrene.readthedocs.io) to find out more.

## Contributing

This project has a [Code of Conduct][ccc] for its contributors.
By participating in this project, you agree to abide by its terms.

## Licenses

Styrene’s code is licensed as follows:

* [GPLv3](COPYING) or later for the tool itself.
* [CC0][cc0] for code templates and generated code inside bundles.

See the Styrene [licensing policy][pol] in the documentation
for details of why we make this split.

Other licenses:

* The CoC text is licensed as [CC BY 4.0][ccby40].

[cc0]: https://creativecommons.org/publicdomain/zero/1.0/
[pol]: docs/licenses.md
[ccc]: CODE_OF_CONDUCT.md
[ccby40]: https://creativecommons.org/licenses/by/4.0/
