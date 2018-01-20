#!/usr/bin/env bash
# Functions and environment checks.
# All rights waived: https://creativecommons.org/publicdomain/zero/1.0/

set -e

case "$MSYSTEM" in
    "MINGW64")
        PKG_PREFIX="mingw-w64-x86_64"
        ;;
    "MINGW32")
        PKG_PREFIX="mingw-w64-i686"
        ;;
    *)
        echo >&2 "This script must only be called from a MINGW64/32 login shell."
        exit 1
        ;;
esac


logmsg () {
    echo -en "\033[36m"
    echo -n "$@"
    echo -e "\033[0m"
}
