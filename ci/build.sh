#!/usr/bin/env bash
# MSYS2 build for styrene in Appveyor.
# All rights waived: https://creativecommons.org/publicdomain/zero/1.0/

set -e

SCRIPT=`basename "$0"`
SCRIPTDIR=`dirname "$0"`
TOPDIR=`dirname "$SCRIPTDIR"`

cd "$TOPDIR"

. ci/env.sh

logmsg "ci/build.sh: cleaning up..."
python3 setup.py clean --all

logmsg "ci/build.sh: building Styrene..."
python3 setup.py build

logmsg "ci/build.sh: building Styrene as a wheel..."
pip3 wheel .
mkdir -p out
mv *.whl out/

logmsg "ci/build.sh: all done"
