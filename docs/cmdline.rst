Command line usage
==================

.. note:: Currently Styrene is not an installable package,
   although it would be trivial to make a ``setup.py``.
   The current way to run it for testing purposes
   is through the ``styrene.sh`` script bundled with the source.

Styrene creates distributable installers and portable zipfiles
by bundling together MSYS2 packages.

Usage
-----
1. ::

    ./styrene.sh --help

2. ::

    ./styrene.sh [options] spec1.cfg ...

The first form shows the usage message,
and gives a terse explanation of what the options do.
Normally you run Styrene with a configuration file
which tells it what packages to install into your bundle.

Options
-------

-h, --help  Show the help message,
            and exit immediately with a return code of zero.
-q, --quiet           Log errors and warnings only.
-v, --verbose         Log detailed information about processing (default).
--debug               Log lengthy debugging information.
-o DIR, --output-dir=DIR   Where to store output.
                           The folder ``DIR`` will be created if needed.
--no-win64            Don't build 64-bit native bundles.
--no-win32            Don't build 32-bit native bundles.
-p DIR, --pkg-dir=DIR   Preferentially use package files from ``DIR``.

Normally a temp directory is used for building,
and the output distributables are then copied into the current directory.
The temp dir is normally deleted after processing.
Specifying ``--output-dir`` changes this behaviour:
no temp directory will be made.

The output dir will be created if it doesn't exist,
and all output will be retained there, not copied out.
The temporary bundle tree is kept too, for inspection and testing.

Not counting any retained bundle trees, styrene generates two kinds of
bundle files for distribution: installer executables, amd standalone
zipfiles. See :doc:`output` for details.

Required parameters
-------------------

Styrene requires at least one config file to process.
Each config file defines
the list of packages to install into the bundle,
and what launchers to create in it.
It also allows you to delete unused files from your bundle
in order to keep its file size down.

See :doc:`bundleconf` for details of the format.

Examples
--------
::

     ./styrene.sh gtk3-examples.cfg

This processes the standard test file in the normal way.
It'll eventually write four output files
into the current working directory,
with names like ``gtk3-examples-w64-3.22.1-1-standalone.zip``
or ``gtk3-examples-w32-3.22.1-1-installer.exe``.


::

     ./styrene.sh --debug gtk3-examples.cfg

This shows debugging output: highly detailed explanations of each step.
It's normally too verbose to be useful
except when trying to diagnose a fault.

::

     ./styrene.sh --output-dir=/tmp/test1 gtk3-examples.cfg

This makes Styrene write all its output
into a folder of your choice.
If you do this, the temporary bundle trees it uses to build the
installers and zipfiles are retained.
This allows you to examine the contents and run the launchers
from inside the working tree.
This is a good way to test some aspects of your bundle
without installing it.

::

    ./styrene.sh --no-win32 gtk3-examples.cfg

If you don't want to build outputs for a particular architecture,
you can do that too.

::

     ./styrene.sh --pkg-dir=path/to/my/builds my-package.cfg

If you routinely `build your own`_ packages,
you can tell Styrene to look in specific folders for packages
you explicitly name in the config file.
Note that you must explicitly name the packages,
or they won't be installed.
They won't be pulled in as dependencies,
but they can be used to _satisfy_ dependencies of other packages
if you list them explicitly.

Styrene will only install the most recent version of the packages
you name.

.. _build your own: https://sourceforge.net/p/msys2/wiki/Contributing%20to%20MSYS2/
