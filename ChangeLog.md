0.3.0
-----

Styrene [v0.3.0](https://github.com/achadwick/styrene/releases/tag/v0.3.0)
has not yet been released.

* ChangeLog added.
* Postinst scripts built with `styrene --debug` now pause at the end.
* More flexible delete/nodelete.
  You can now use `delete = *` in configs and override what it matches
  sensibly with `nodelete`.
* Doc and examples updated.

0.2.0
-----

Styrene [v0.2.0](https://github.com/achadwick/styrene/releases/tag/v0.2.0)
was released on 2016-11-26.  

* Command-line flag to enable colours in the absence of a pty.
* Styrene must now be run from the native MINGW64 or MINGW32 shell.
* Fix for version parsing in local filenames.
* Drop dependency on pyalpm.
* Docs updates.

0.1.1
-----

Styrene [v0.1.1](https://github.com/achadwick/styrene/releases/tag/v0.1.1)
was released on 2016-11-25.

* Fix a silly typo that caused the wrong MSYS packages to be installed
  for MINGW32 bundles.
* Check dependencies at runtime (back here, Styrene expected to be run
  from the MSYS2 environment, so this wasn't a given from packaging).
* Script now installs as "styrene.py" to prevent shadowing.
* Point at the docs on rtd in the command line help.

0.1.0
-----

Styrene [v0.1.0](https://github.com/achadwick/styrene/releases/tag/v0.1.0)
was released on 2016-11-24.

* Initial release of Styrene.
