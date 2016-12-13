Bundle configuration language
=============================

Styrene's specification language for bundles is a `.INI`_-style format.
The config files are read with Python's `configparser`_ module,
and can be written with a standard text editor.

Section names and keys are case-insensitive.
Values may be split over several lines.

.. rubric:: See also

* :doc:`cmdline`,
* :doc:`concepts`.

Main bundle specification
-------------------------

    ::

        [bundle]
        packages = ...
        filemname_stub = ...

This section defines how to create the bundle,
and allows you to override settings which would otherwise
be set to default values or values parsed from the packages
you install.

packages
........

    ::

        packages = {pkg_prefix}gedit

This key lists the packages to install into the bundle,
separated by spaces.
Pacman will find their dependencies from
your MSYS2 installation's configured repositories,
and will use and update its pacman cache.

The substitution code ``{pkg_prefix}`` is
expanded either ``mingw-w64-x86_64-`` or ``mingw-w64-i686-``.

The first item in the ``packages`` list is called the *primary package*.
The primary package is used for lots of default values for the bundle,
on the assumption that you're bundling a single interesting piece of
software.

assume_installed
................

    ::

        assume_installed = {pkg_prefix}python3 {pkg_prefix}ncurses

This key lists packages that ``pacman`` should assume are installed.
It has the same syntax as ``packages``, and the same subtititions apply.

Install assumptions are a partial workaround for
MSYS2’s unfortunate preference for
full-fat packages with every aspect of a lib or a program thrown in.
This choice tends to lead to wide dependency cascades which
are fine for developer environments, but bad for lean bundling.
The ``assume_installed`` key can be used to avoid installation of
particularly large sub-dependencies which your app doesn't need.

Styrene provides another workaround in the form of the ``delete`` key,
but using that requires a deeper knowledge of your bundle's system.

filename_stub
.............

    ::

        filename_stub = gtk3-examples

This string is used for the first part of generated installer or archive
filenames.  It will be suffixed with the version, an architecture spec
like "-w64" or "-w32", and the appropriate filename extension.

Characters other than alphanumerics, underscores, or hyphens are not
allowed.

By default, the template string in the primary package's name is used,
with ``{pkg_prefix}`` set to the empty string.


display_name
............

    ::

        display_name = GTK3 Examples

This key defines the *display name* for the bundle.
You should almost always set it,
and it must be unique to the software bundle being created.

The display name is used to refer to the bundle
in the Add/Remove Programs dialog,
and in the Start menu.
It's basically the human-readable form of ``filename_stub``.

The suffix " (w32)" will be appended for Win32 bundles,
but not for Win64 ones.
64-bit Windows is the norm these days, 32-bit is the exception.

Default: the value of ``filename_stub``.

description
...........

    ::

        description = GTK3’s test and demo apps

Provides a short, human-readable description of the bundle.
This is used in the Add/Remove Programs dialog.

If this isn't set, the description of the primary package is used.

version
.......

    ::

        version = 3.20.4

Overrides the version string. You almost never need to set this.

The version appears in installer and zipfile names,
in the Add/Remove Programs dialog, and elsewhere.
Some of these places expect a major and minor revision to be parseable
from the start of the version string. Styrene uses the first two
substrings that look like decimal numbers for these cases, and will
default them to a zero if the string doesn't contain those fields.

By default, the version string of the primary package is used.

url
...

    ::

        url = http://example.org/

The home page URL for the backage being built.

By default, this is set to the URL property of the primary package.

launchers
.........
    ::

        launchers =
            gtk3-demo.desktop
            gtk3-widget-factory.desktop
            gtk3-icon-browser.desktop
            gtk3-demo-event-axes

This key lists the launchers which should be installed,
seprataed by whitespace.
Launchers are how your users will start your bundled app(s).
Entries in this section should name a desktop file,
or name an equivalent *launcher section* (see below).

Desktop files are searched for in the installation tree,
and then parsed for their `[Desktop Entry]` sections.
The keys can then be overridden - see the section below.

These .desktop files are the typical way in which a FreeDesktop
application is started on a POSIX/Linux desktop machine.
See the `Desktop Entry Specification`_ for details.
Styrene reads a subset of this format, and from the information
contained there creates:

* Multi-resolution icon files in .ico format
* Native WinXX ``.exe`` launchers the root of the bundle
* Start menu ``.lnk`` entries

Launchers can be defined entirely within a Styrene config file,
which is useful if you need launchers with special Exec lines
for debugging your app in a terminal or something similar.

delete
......
    ::

        delete =
            mingw*/share/gtk-doc
            mingw*/lib/*.a
            mingw*/share/doc
            mingw*/share/info
            mingw*/share/man

This key provides a space-separated list of glob patterns,
which will be resolved relative to the bundle root.
File matches will be deleted,
and folder matches will be deleted recursively.

nodelete
........
    ::

        nodelete =
            mingw*/bin/*.dll
            mingw*/bin/gtk3-demo.exe
            mingw*/bin/xmlcatalog.exe

This key provides a space-separated list of glob patterns,
which will be resolved relative to the bundle root.
Its matched files and folders will be retained,
even if they have been matched by ``delete``.

Glob patterns
-------------

The special characters used by ``delete`` and ``nodelete`` are:

==========  =========================================================
Pattern     Matches…
==========  =========================================================
``*``       any sequence of characters other than ``/``
``?``       any single character
``[abc]``   any single character in the list (``a``, ``b``, or ``c``)
``[!abc]``  any character *not* listed
``**``      any files and/or zero or more subdirectories
==========  =========================================================

If a ``**`` is followed by a ``/``,
then it matches only a sequence of subdirectories.

Styrene use Python’s `glob module`_ for this type of path matching.

Launcher definitions
--------------------

You can add sections which are named after your ``.desktop`` launchers
to override fields which are otherwise parsed from the installed bundle.
Sections defined here can define complete launchers too,
even if there is no corresponding file on disk.

    ::

        [gtk3-demo-event-axes]
        name = ...
        comment = ...

All launchers need to be listed
in the main ``[bundle]``'s ``launchers`` key.
Launcher definitions will not be used unless they define a ``name`` and
an ``exec`` line. Everything else is optional.

name
....
    ::

        name = Event Axes

Provides a display name for the launcher, or overrides an existing name.
This should be unique amongst all launchers belonging to this app: it
will be turned into the name of a .lnk shortcut file installed in the
start menu.

The file name of the lanucher itself is derived from the .desktop file
name, or the name of the launcher section, and cannot be changed.

comment
.......
    ::

        comment = Test fancy input events

A short, human-readable explanation of what the launcher is or does.
This is only used in installed start menu shortcuts.

icon
....
    ::

        icon = input-tablet

This is the name of the icon to make for the launcher.
When Styrene seees that a launcher has an icon,
it generates a single .ico file in the bundle's ``_icons`` folder.
These icons are compiled into the launcher .exe,
and referred to by any .lnk shortcuts installed in the Start menu.

Styrene only knows how to build these from PNG icons
installed in ``$PREFIX/share/icons/{Adwaita,default}``.
It also trusts that the size is what is claimed by the directory structure.
However, unlike ``png2ico`` which we could have used,
Styrene's generated icons contain a 256x256 PNG icon.

exec
....
    ::

        exec = gtk3-demo --run=event_axes

The program to execute, possibly with arguments.
This key has the syntax defined in the `Desktop Entry Specification`,
and the same semantics to the extent we can make it work under Windows.

Styrene follows these rules whan making its ``.exe`` launchers:

1. Styrene looks up the program in
   what will be the bundle's ``$PREFIX\bin`` after deployment

2. If the program is a .exe,
   the binary launcher will try to call it directly
   with `CreateProcessW()`_, having done any argument expansion needed.

3. More complex command lines are passed to the MSYS2 bash.

Using *CreateProcessW()* directly on an executable
makes the user experience nicer.
Apps will be pinnable
(they will be assigned the same appid as start menu .lnk shortcuts),
and Styrene will hide any CMD window associated with the app sensibly.

Styrene launchers respect the following field codes:

%f
    A single file name.

%F
    A list of file names,
    each of which will be passed as a separate argument.

%u
    Treated as %f by styrene.

%U
    Treated as %F by styrene.

terminal
........
    ::

        terminal = true

If this boolean value is set to true,
it forces the launcher to invoke the command via bash
in a visible CMD window.
The user will be asked to press return when the command has exited.

mimetype
........
    ::

        mimetype = image/openraster;image/png;

This key is a list of MIME types the launcher can open.
Styrene converts this into a list of Windows file name extensions,
and offers the user a choice about whether to associate your launcher
with those extensions during installation.

This normally requires the ``shared-mime-info`` package to be
installed in the bundle tree.
When Styrene creates an installer, it consults all the XML files
in ``mingw*/share/mime/packages/*.xml`` to discover which extensions
the types map to.
.. _.INI: https://en.wikipedia.org/wiki/INI_file
.. _configparser: https://docs.python.org/3/library/configparser.html
.. _Desktop Entry Specification: https://specifications.freedesktop.org/desktop-entry-spec/latest/
.. _CreateProcessW(): https://msdn.microsoft.com/en-us/library/windows/desktop/ms682425(v=vs.85).aspx
.. _glob module: https://docs.python.org/3/library/glob.html
