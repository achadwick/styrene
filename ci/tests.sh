#!/usr/bin/env bash
# MSYS2 test commands for styrene in Appveyor.
# All rights waived: https://creativecommons.org/publicdomain/zero/1.0/

set -e

SCRIPT=`basename "$0"`
SCRIPTDIR=`dirname "$0"`
TOPDIR=`dirname "$SCRIPTDIR"`

cd "$TOPDIR"

. ci/env.sh

TEST_CFG_FILE="gtk3-examples.cfg"

logmsg "ci/tests.sh: installing styrene with pip3"
pip3 install .

tmpdir=/tmp/styrene.$$
mkdir -p $tmpdir

logmsg "ci/tests.sh: bundling from $TEST_CFG_FILE (debug mode)"
mkdir -p out/debug
styrene --colour=yes -o $tmpdir/debug --debug "$TEST_CFG_FILE"
mv -v $tmpdir/debug/*.{exe,zip} out/debug

logmsg "ci/tests.sh: bundling from $TEST_CFG_FILE (non-debug)"
mkdir -p out/nondebug
styrene --colour=yes -o $tmpdir/nondebug "$TEST_CFG_FILE"
mv -v $tmpdir/nondebug/*.{exe,zip} out/nondebug

logmsg "ci/tests.sh: all done"
