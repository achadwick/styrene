#!/usr/bin/bash
# Runs all the post_install scriptlets to adapt to a new install
# location.  This script is called directly by the launcher .exes, or
# indirectly by the installer .exe.

LOCATION_STATEFILE="%(state_file)s"
START_MENU_PROGRAMS=""

# If this script is invoked with an argument,
# it's being called indirectly from the NSIS installer.exe.
# The parameter is the runtime-specific value of NSIS's $SMPROGRAMS
# variable. Capture it for later.

if test "x$1" != "x"; then
    START_MENU_PROGRAMS=`cygpath -u "$1"`
fi

# Catch-all def in case the scriptlet doesn't define a post_install.
# It will be inherited each time by the subshell.
post_install () {
    return 0
}

# Run deferred install scriptlets in sub-shells.
echo "Running post_install setup scriptlets."
nfails=0
for d in /var/lib/pacman/local/?*-?*-?*; do
    if test -f "$d/install"; then
        b=`basename $d`
        p="$b"
        r=${p##*-}
        p=${p%%-*}   # template note: single percent
        v=${p##*-}
        p=${p%%-*}   # template note: single percent
        echo "Setting up for $b ..."
        if ! (source "$d/install" && post_install "$v-$r"); then
            echo "$b: post_install() failed"
            let nfails++
        fi
    fi
done
if test "x$nfails" != "x0"; then
    echo "Encountered $nfails failure(s)."
    echo "These can happen for trivial reasons, e.g. missing GNU install-info."
    echo "Please don't report them unless something is wrong elsewhere."
fi
echo "Post-install scripts done."

# If this script is run by a launcher .exe (i.e. the user unpacked a
# standalone zipfile and clicked on the shiny icon), the launcher itself
# will also update the location state file. It will write the runtime
# location to it so that it can detect changes on a future run. So this
# touch doesn't matter.
#
# Conversely, the installer will invoke this script via postinst.cmd
# when it runs its Install section, so we use touch to create an *empty*
# state file. The launcher executables know about this convention, and
# will assume that configuration was done once and for all time during
# installation.
#
# The empty-statefile convention means that C code doesn't have to worry
# about the encoding used when bash wrote stuff.

touch "$LOCATION_STATEFILE"

# Post-install fragments from the launchers follow...
%(launcher_sh_fragments)s
