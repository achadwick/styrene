# Concepts and operation

Styrene operates by converting information in
FreeDesktop.org “.desktop” files into
Windows launcher executables, start menu shortcuts,
and file associations.
With very little extra effort,
you get Windows integration matching your app's integration into
a free desktop like GNOME or KDE.

## The bundle tree

Styrene initially makes a _bundle tree_
containing a minimal MSYS2 installation.
It does this by installing required packages to it using _pacman_.
The tree includes _bash_ and a few other utilities
so that scripts can be executed later on.
These are needed because the packages are installed
without the usual post-installation configuration.

The post-install scriptlets from the packages
will be run automatically on the user's machine
when configuration is needed.

Styrene also writes launcher executables, support scripts,
and .ico icons into the bundle tree.

The bundle tree is then repacked into .exe installers and
portable .zip files which you can distribute
alongside your app's source code.

<!-- TODO: expand this with a diagram -->
