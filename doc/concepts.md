# Concepts and operation

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

<!-- TODO: expand this with a diagram -->
