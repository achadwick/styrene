#!/usr/bin/env bash
# MSYS2 build and test commands for styrene.
# All rights waived: https://creativecommons.org/publicdomain/zero/1.0/
#
#: Usage:
#:   $ msys2_build.sh [OPTIONS] [CFG FILE]
#:
#: Options:
#:   installdeps    Install dependencies Styrene requires
#:   install        Install Styrene-git via it PKGBUILD file
#:   run            Run Styrene for testing.
#:   copy           Copy Styrene output to project folder
#
# This script was initially designed to be called by AppVeyor or Tea-CI.
# However it's clean enough to run from an interactive shell. It expects
# to be called with MSYSTEM="MINGW{64,32}", i.e. from an MSYS2 "native"
# shell.

set -e

SCRIPT=`basename "$0"`
SCRIPTDIR=`dirname "$0"`
TOPDIR=`dirname "$SCRIPTDIR"`

cd "$TOPDIR"

case "$MSYSTEM" in
    "MINGW64")
        PKG_PREFIX="mingw-w64-x86_64"
        MINGW_INSTALLS="mingw64"
        ;;
    "MINGW32")
        PKG_PREFIX="mingw-w64-i686"
        MINGW_INSTALLS="mingw32"
        ;;
    *)
        echo >&2 "$SCRIPT must only be called from a MINGW64/32 login shell."
        exit 1
        ;;
esac
export MINGW_INSTALLS

# For more information on how to use pacman visit:
# https://www.archlinux.org/pacman/pacman.8.html or
# use "man pacman" in your terminal if the package is installed.
PACMAN_SYNC="pacman -S --noconfirm --needed --noprogressbar"

STYRENE_PKGBUILD_URI="https://raw.githubusercontent.com/Alexpux/MINGW-packages/master/mingw-w64-styrene-git/PKGBUILD"

CFG_FILE="gtk3-examples.cfg"
OUTPUT_DIR="/tmp/output.styrene"
TARGET_DIR="${TOPDIR}${OUTPUT_DIR}"

install_dependencies() {
    echo "BASH: Installing packages required by Styrene"
    $PACMAN_SYNC \
        ${PKG_PREFIX}-nsis \
        ${PKG_PREFIX}-gcc \
        ${PKG_PREFIX}-binutils \
        ${PKG_PREFIX}-python3 \
        zip
}              

install_pkgbuild(){
    echo "BASH: Installing Styrene from source."
    BUILD_DIR="/tmp/build.styrene.$$"
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    curl --remote-name "$STYRENE_PKGBUILD_URI"
    MSYSTEM="MSYS2" bash --login -c "cd $BUILD_DIR && makepkg-mingw -f"
    ls -la *.pkg.tar.xz
    pacman -U --noconfirm *.pkg.tar.xz
    cd $TOPDIR
    rm -rf "$BUILD_DIR"
}

# This will run styrene from within the git folder.
run_styrene(){
    styrene --colour=yes --output=$OUTPUT_DIR $CFG_FILE
}    

copy_builds(){
    # FIXME: Workaround due to styrene erroring out for not setting it.
    # Causes errors with pacman which styrene uses.
    rm -f $TARGET_DIR
    mkdir -p $TARGET_DIR
    echo "BASH: Copying installer to ${TARGET_DIR}"
    cp -a $OUTPUT_DIR/*-installer.exe "${TARGET_DIR}"
    echo "BASH: Copying zip file to ${TARGET_DIR}"
    cp -a $OUTPUT_DIR/*-standalone.zip "${TARGET_DIR}"
    echo "BASH: All Files Copied"
}

# Command line processing

case "$1" in
    installdeps)
        install_dependencies
        ;;
    pkgbuild)
        install_pkgbuild
        ;;
    run)
        run_styrene
        ;;
    copy)
        copy_builds
        ;;
    *)
        echo >&2 "usage: $SCRIPT {installdeps|install|pkgbuild|run|copy}"
        exit 2
        ;;
esac
