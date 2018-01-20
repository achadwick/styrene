#!/usr/bin/env bash
# Install dependencies for building and testing Styrene.
# All rights waived: https://creativecommons.org/publicdomain/zero/1.0/

set -e

SCRIPT=`basename "$0"`
SCRIPTDIR=`dirname "$0"`
TOPDIR=`dirname "$SCRIPTDIR"`

cd "$TOPDIR"

. ci/env.sh

PACMAN_SYNC="pacman -S --noconfirm --needed --noprogressbar"

logmsg "ci/installdeps.sh: installing MSYS2 packages required by Styrene..."
$PACMAN_SYNC \
    ${PKG_PREFIX}-nsis \
    ${PKG_PREFIX}-gcc \
    ${PKG_PREFIX}-binutils \
    ${PKG_PREFIX}-python3 \
    ${PKG_PREFIX}-python3-pip \
    zip

logmsg "ci/installdeps.sh: installing Python packages for this AppVeyor build..."
pip3 install wheel

logmsg "ci/installdeps.sh: all done."


