#!/usr/bin/bash
# Desktop file launcher.
# This file is dedicated into the public domain, CC0 v1.0.
# https://creativecommons.org/publicdomain/zero/1.0/
#
# Template file: styrene/launcherstub.sh
# Installed as: $PREFIX/bin/$LAUNCHER_BASENAME.sh
#
# This script is the counterpart to launcherstub.c and the top-level
# launcher executables. It is invoked with any args passed to the
# executable.

# Settings are parsed from the desktop file.
##LAUNCHER_VARS##

# TODO: interpolate %u, %F etc.
# Can perhaps simplify by requiring LAUNCHER_EXEC to have only one.

if ! $LAUNCHER_USE_TERMINAL; then
    exec $LAUNCHER_EXEC
    exit 999  # hopefully never happens
else
    ( exec $LAUNCHER_EXEC )
    echo >&2 "Press return/enter to close this window."
    read _line
    exit 0
fi
