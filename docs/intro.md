# Introduction

## What Styrene does

Styrene makes usable app bundles for Windows.
It repacks MSYS2 software into neat bundles that are nicer for your users,
and easier for you to distribute.
If a package containing your app is already available in MSYS2,
it can be bundled with Styrene.
You can also bundle packages you build yourself.

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

[m2]: https://msys2.github.io/
[fdo]: https://www.freedesktop.org/wiki/

## Feature list

* Simple INI-style configuration
* Creates installer executables and standalone zipfiles
* Users don't need to deploy MSYS2 to use your app
* Everything your app requires (other than msvcrt.dll) gets bundled 
* Post-installation scripting happens automatically
* Converts package versions, descriptions and other metadata fields
* Converts your app's FreeDesktop .desktop files to launchers
* Makes .EXE launchers with icons
* Optionally installs default file associations
* Installer makes start menu shortcuts
* Installer registers the bundle's uninstall.exe correctly
* Installed apps can normally be pinned to the taskbar

## Contributing

It’s early days yet. However if this project takes off,
it will grow with respect and inclusivity.

Please note that this project is released with a
[Contributor Code of Conduct][ccc]. By participating in this project,
you agree to abide by its terms.

[ccc]: https://github.com/achadwick/styrene/blob/master/CODE_OF_CONDUCT.md
