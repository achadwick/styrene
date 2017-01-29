# Getting started

Styrene runs in MSYS2 and uses the tools it provides to do its job.
The commands below should be run from its MSYS2 shell.

## Install dependencies

You will need some extra packages to make Styrene work.

1. Install [MSYS2][m2] first, and update it.
   Their `msys2-x86_64-*.exe` installer is preferable,
   since it can be used to generate both Win64 and Win32 bundles.

2. Then install the extra packages that Styrene needs.

    ```sh
    pacman -S zip
    pacman -S mingw-w64-{i686,x86_64}-python3
    pacman -S mingw-w64-{i686,x86_64}-nsis
    pacman -S mingw-w64-{i686,x86_64}-gcc
    pacman -S mingw-w64-{i686,x86_64}-binutils
    ```

[m2]: https://msys2.github.io/

## Download Styrene

```sh
pacman -S git
git clone https://github.com/achadwick/styrene.git
```

## Trying it out

Styrene includes a little launcher script which allows you to test it
from inside the clone you just made.
It also includes an [example spec file][xcfg]
which creates a bundle of all the GTK3 demo apps.

```sh
cd styrene
./styrene.sh gtk3-examples.cfg
```

The distributable output files are eventually written
into the current working directory.
Run Styrene with `--help` to see how you can use a
persistent output directory instead.

[xcfg]: https://github.com/achadwick/styrene/blib/master/gtk3-examples.cfg
