#!/usr/bin/env python3
# This file is dedicated into the public domain, CC0 v1.0.
# https://creativecommons.org/publicdomain/zero/1.0/

from distutils.core import setup
import os


if os.environ.get("MSYSTEM") != "MSYS":
    raise RuntimeError("This setup script must be run from the MSYS shell.")


setup(
    name="Styrene",
    version="0.1",
    description=(
        "Tool to make usable app bundles for regular Windows users "
        "out of MSYS2 binary packages"
    ),
    long_description="""

Styrene is a script that makes usable app bundles for Windows.

It repacks MSYS2 software into neat bundles that are nicer for your
users, and easier for you to distribute. If a package containing your
app is already available in MSYS2, it can be bundled with Styrene.
You can also bundle packages you build yourself.

Styrene operates by converting information in FreeDesktop.org ".desktop"
files into Windows launcher executables, start menu shortcuts, and file
associations. With very little extra effort, you get Windows integration
matching your app's integration into a free desktop like GNOME or KDE.

By default, styrene packs its bundles as .exe installers with all the
bells and whistles, and as bare-bones portable .zip files.

""",
    author="Andrew Chadwick",
    author_email="a.t.chadwick@gmail.com",
    url="https://github.com/achadwick/styrene",
    scripts=["scripts/styrene.py"],
    packages=["styrene"],
    package_data={'styrene': ['data/*']},
    classifiers=(
        ("License :: OSI Approved :: GNU General Public License v3 or "
         "later (GPLv3+)"),
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Desktop Environment",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
    ),
)
