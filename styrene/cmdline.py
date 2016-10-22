# Copyright © 2016 Andrew Chadwick.
#
# This file is part of ’Styrene.
#
# ’Styrene is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# ’Styrene is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ’Styrene.  If not, see <http://www.gnu.org/licenses/>.


"""Launching from the command line."""

from .bundle import NativeBundle
from . import consts

import optparse
import configparser
import sys
import os.path
import os
import tempfile
import shutil
from textwrap import dedent
import logging

logger = logging.getLogger(__name__)


# Top-level commands:

def process_spec_file(spec, options):
    """Prepare the bundle as specified in the spec."""
    msystems = []
    if options.win64:
        msystems.append(consts.MSYSTEM.MINGW64)
    if options.win32:
        msystems.append(consts.MSYSTEM.MINGW32)
    if not msystems:
        logger.warn("Nothing to do")
    for msystem in msystems:
        bundle = NativeBundle(spec, msystem)
        output_dir = options.output_dir
        if not output_dir:
            output_dir = os.getcwd()
            with tempfile.TemporaryDirectory() as tmp_dir:
                for distfile in bundle.write_distributables(tmp_dir):
                    distfile_final = os.path.join(
                        output_dir,
                        os.path.basename(distfile),
                    )
                    shutil.copy(distfile, distfile_final)
        else:
            bundle.write_distributables(output_dir)


# Startup:

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    # Parse command line args
    parser = optparse.OptionParser(
        usage="%prog [options] spec1.cfg ...",
        description=dedent("""
            Creates distributable installers and portable zipfiles
            by bundling together MSYS2 packages.
        """).strip(),
        epilog=dedent("""
            Normally a temp directory is used for building,
            and the output distributables are then copied
            into the current directory.
            The temp dir is normally deleted after processing.

            Specifying --output-dir changes this behaviour:
            no temp directory will be made.
            The output dir will be created if it doesn't exist,
            and all output will be retained there, not copied out.
            The temporary bundle tree is kept too,
            for inspection and testing.
        """).strip(),
    )
    parser.add_option(
        "-q", "--quiet",
        help="log errors and warnings only",
        action="store_const",
        const=logging.WARNING,
        dest="loglevel",
    )
    parser.add_option(
        "-v", "--verbose",
        help="log detailed information about processing (default)",
        action="store_const",
        const=logging.INFO,
        dest="loglevel",
        default=logging.INFO,
    )
    parser.add_option(
        "--debug",
        help="log lengthy debugging information",
        action="store_const",
        const=logging.debug,
        dest="loglevel",
    )
    parser.add_option(
        "-o", "--output-dir",
        help="where to store output, created if needed",
        metavar="DIR",
        default=None,
    )
    parser.add_option(
        "--no-win64",
        help="Don't build 64-bit native bundles.",
        action="store_false",
        default=True,
        dest="win64",
    )
    parser.add_option(
        "--no-win32",
        help="Don't build 32-bit native bundles.",
        action="store_false",
        default=True,
        dest="win32",
    )
    options, args = parser.parse_args(sys.argv[1:])
    if not len(args):
        parser.print_help()
        sys.exit(1)

    # Initialize logging
    root_logger = logging.getLogger()
    root_logger.setLevel(options.loglevel)

    # Process bundles
    for spec_file in args:
        try:
            spec = configparser.SafeConfigParser()
            spec.read(spec_file)
        except:
            logger.exception("Failed to load bundle spec file “%s”", spec_file)
            sys.exit(2)
        process_spec_file(spec, options)
