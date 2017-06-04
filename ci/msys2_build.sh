#!/usr/bin/env bash
# MSYS2 build and test commands for styrene in Appveyor.
# All rights waived: https://creativecommons.org/publicdomain/zero/1.0/
#
#: Usage:
#:   $ ci/msys2_build.sh [OPTIONS] [CFG FILE]
#:
#: Options:
#:   installdeps Install dependencies Styrene requires
#:   install     Install Styrene using pip3, for testing.
#:   demo        Run Styrene with the test file (gtk3-examples.cfg).
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

PACMAN_SYNC="pacman -S --noconfirm --needed --noprogressbar"
DEMO_CFG_FILE="gtk3-examples.cfg"
DEMO_OUTPUT_DIR="$SCRIPTDIR/out"

install_dependencies() {
    echo "BASH: Installing packages required by Styrene"
    $PACMAN_SYNC \
        ${PKG_PREFIX}-nsis \
        ${PKG_PREFIX}-gcc \
        ${PKG_PREFIX}-binutils \
        ${PKG_PREFIX}-python3 \
        ${PKG_PREFIX}-python3-pip \
        zip
}              

install_styrene() {
    echo "BASH: Installing Styrene from source."
    cd "$TOPDIR"
    pip3 install .
}

run_styrene_demo() {
    cd "$TOPDIR"
    tmpdir="/tmp/styrenedemo.$$"
    TEMP=/tmp styrene --colour=yes "$DEMO_CFG_FILE"
}

# Command line processing

case "$1" in
    installdeps)
        install_dependencies
        ;;
    install)
        install_styrene
        ;;
    demo)
        run_styrene_demo
        ;;
    *)
        echo >&2 "usage: $SCRIPT {installdeps|install|demo}"
        exit 2
        ;;
esac
