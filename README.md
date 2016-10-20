# ’Styrene – a package bundling tool

Styrene makes usable app bundles for Windows.
It repacks MSYS2 software into neat bundles that are nicer for your users,
and easier for you to distribute.
If a package containing your app is already available in MSYS2,
it can be bundled with Styrene.

[MSYS2][m2] is a large modern distribution of binary software for Windows.
Its contents are mostly ported from the free/Libré/Open Source software world.
It’s a very comprehensive platform, and stuff _mostly just works_ on it,
but it’s probably too developer-oriented for supporting ordinary users.
For one thing, it’s a law unto itself,
Software has to be deployed and run from its own special command line ☺

Styrene’s app bundles make the good stuff in MSYS2 available to
ordinary, non-technical users.
They contain all the dependencies necessary to get your app running,
plus the extra fluff and packing material that
makes sure everything looks nice and runs well.
Apps already using the [freedesktop.org][fdo] specifications
can be made to work nicely on your Windows users’ desktops
with only very minimal configuration.

## Features

* Simple INI-style configuration
* Creates installer executables and standalone zipfiles
* Users don't need to deploy MSYS2 to use your app
* Everything your app requires (other than msvcrt.dll) gets bundled 
* Post-installation scripting happens automatically
* Converts package versions, descriptions and other metadata fields
* Converts your app's FreeDesktop .desktop files to launchers
* Makes .EXE launchers with icons
* Installer makes start menu shortcuts
* Installer registers the bundle's uninstall.exe correctly
* Installed apps can normally be pinned to the taskbar

## Dependencies

Install [MSYS2][m2] first, and update it.
Their `msys2-x86_64-*.exe` installer is preferable,
since it can be used to generate both Win64 and Win32 bundles.

Then install the extra packages that Styrene needs.

    pacman -S mingw-w64-x86_64-nsis mingw-w64-x86_64-gcc \
              mingw-w64-x86_64-binutils
    pacman -S python3 zip

## Usage

The [example spec file][xcfg] creates a bundle of all the GTK3 demo apps.

    ./styrene.sh gtk3-examples.cfg

The distributable output files are eventually written into the current
working directory.  Run it with `--help` to see how you can use a
persistent output directory instead.

## How it works

Styrene makes a bundle tree containing a minimal MSYS2 installation
by installing required packages to it using _pacman_.
The tree includes _bash_ and a few other utilities
so that scripts can be executed later on.
These are needed because the packages are installed
without the usual post-installation configuration.

The post-install scriptlets from the packages
will be run automatically on the user's machine
when configuration is needed.

## Output types

### Installer executables

These are Nullsoft [NSIS][nsis] installers
which have filenames ending in `-installer.exe`.
When run, the installer acquires admin rights,
then installs the bundle into the appropriate “Program Files” folder.
The deferred post-install scriptlets
are run during this installation,
and the target folder is not expected to move afterwards.

These installers contain an `uninstall.exe`,
and registry glue to invoke it from “Add and Remove Programs”.
They'll also install start menu shortcuts
corresponding to the original `.desktop` files you listed.

### Standalone zipfiles

These can be unpacked onto a portable flash drive as a single folder,
allowing your users to take your program with them.
Your program is launched from a `.exe` file within the folder.

The post-install scriptlets may need to be run
each time the user runs a program
because drive letters or paths may have changed.
The launchers detect this automatically,
and re-run the scripts as needed.

## Licensing

Unless otherwise noted, Styrene is free software
which is distributed under the terms of
the GNU [General Public License, version 3.0][gpl3].
See the file named COPYING that you got with Styrene
for the full legal terms and conditions.
The exceptions to this rule are as follows.

The included source code for
any executable code that Styrene generates,
and any associated scripting,
is hereby gifted into the public domain
using a Creative Commons [CC0 1.0][cc0] Public Domain Dedication.
This covers all the extras that Styrene builds into your app bundle.
In other words, this exception lets you distribute or use the bundle
without any possible infingement against our licenses.

Bundles that Styrene generates do not include [MSVCRT.DLL][msvcrt].
This is typically not an issue these days
because Windows normally ships with a version of this DLL.
You must examine your app’s license yourself carefully,
and decide whether the MSVCRT library’s license
allows you to use it with your code.

[m2]: https://msys2.github.io/
[fdo]: https://www.freedesktop.org/wiki/
[nsis]: http://nsis.sourceforge.net/
[xcfg]: gtk3-examples.cfg
[cc0]: https://creativecommons.org/publicdomain/zero/1.0/
[gpl3]: COPYING
[msvcrt]: https://support.microsoft.com/en-us/kb/2977003
