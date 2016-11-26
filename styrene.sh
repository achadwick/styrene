#!/bin/sh
# Start the bundler locally, for testing.

PACKAGE=styrene
BASH=/usr/bin/bash.exe
PYTHON=python3

set -e
export PYTHONPATH=.

if test "x$MSYSTEM" = "xMSYS"; then
    echo >&2 "+++ MSYS shell detected, building all native architectures."
    for s in MINGW64 MINGW32; do
        echo >&2 "+++ Running $PACKAGE in a $s login shell..."
        cmd="$PYTHON $PACKAGE"' "$@"'
        MSYSTEM=$s \
        CHERE_INVOKING=1 \
            "$BASH" --login -c "$cmd" -- "$@"
    done
else
    echo >&2 "+++ Running $PACKAGE directly..."
    $PYTHON $PACKAGE "$@"
fi
