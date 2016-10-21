# Licensing

## Styrene itself

Unless otherwise noted, Styrene is free software
which is distributed under the terms of
the GNU [General Public License, version 3.0][gpl3].
See the file named COPYING that you got with Styrene
for the full legal terms and conditions.
The exceptions to this rule are as follows.

[gpl3]: https://www.gnu.org/licenses/gpl-3.0.en.html

## Code templates and generated code

The included source code for
any executable code that Styrene generates,
and any associated scripting,
is hereby gifted into the public domain
using a Creative Commons [CC0 1.0][cc0] Public Domain Dedication.
This covers all the extras that Styrene builds into your app bundle.
In other words, this exception lets you distribute or use the bundle
without any possible infingement against our licenses.

[cc0]: https://creativecommons.org/publicdomain/zero/1.0/

## MSVC runtime dependencies

Bundles that Styrene generates do not include [MSVCRT.DLL][msvcrt],
but application code compiled with MinGW-w64 will try to use it.
This is typically not an issue these days
because Windows normally ships with a version of this DLL.
You must examine your app’s license yourself carefully,
and decide whether the MSVCRT library’s license
allows you to use it with your code.

[msvcrt]: https://support.microsoft.com/en-us/kb/2977003
