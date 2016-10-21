# Supported output formats

## Installer executables

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

## Standalone zipfiles

These can be unpacked onto a portable flash drive as a single folder,
allowing your users to take your program with them.
Your program is launched from a `.exe` file within the folder.

The post-install scriptlets may need to be run
each time the user runs a program
because drive letters or paths may have changed.
The launchers detect this automatically,
and re-run the scripts as needed.

[nsis]: http://nsis.sourceforge.net/
