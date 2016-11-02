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


"""Bundle specification, read from input .cfg files, writes main output.
"""

from .launchers import DesktopEntry
from .utils import str2key
from .utils import nsis_escape
from .utils import native_shell
from .utils import winsafe_filename
from . import consts

import os
import re
import subprocess
import sys
import glob
import shutil
from textwrap import dedent

import logging
logger = logging.getLogger(__name__)


# Class defs:

class NativeBundle:
    """Installable bundle for Win32 or Win64."""

    def __init__(self, spec, msystem):
        """Initializes a bundle from a specification."""
        super().__init__()
        self.spec = spec
        section = spec["bundle"]
        # Validate and canonicalize the target arch
        self.msystem = consts.MSYSTEM(msystem)
        # What to call generated files and directories
        self.stub_name = section.get("filename_stub", None)
        packages_raw = section.get("packages")
        packages_raw = packages_raw.strip().split()
        first_package_tmpl = packages_raw[0]
        if self.stub_name is None:
            self.stub_name = packages_raw[0].format(pkg_prefix="")
        if not re.match(r'^[\w+-]+$', self.stub_name):
            raise ValueError(str(
                    "Cannot use “{stub_name}” for naming things. "
                    "Please provide a [bundle]→filename_stub containing "
                    "letters, numbers, _ or - only."
                ).format(stub_name=self.stub_name),
            )
        self.stub_name += self.msystem.bundle_name_suffix
        # Extract package metadata
        substs = self.msystem.substs
        self.main_package = first_package_tmpl.format(**substs)
        metadata = self._get_package_metadata(self.main_package)
        logger.info("Got metadata for %r", self.main_package)
        self.metadata = metadata
        # Properties for templating
        version = section.get("version", metadata.get("version", "0"))
        major, minor = self._parse_version(version)
        self.version = version
        self.version_major = major
        self.version_minor = minor
        # For NSIS file generation
        self.icon = ""
        # Launchers
        self.launchers = []

    def _init_launchers(self, distroot):
        """Initializes the launcher specifications for this bundle.

        These come in two forms: .desktop files, or sections in the
        bundle specification file. Both are listed in the "launchers"
        key of the main [bundle] section.

        """
        spec = self.spec
        self.launchers = []
        bundle_section = spec["bundle"]
        launcher_names = bundle_section.get("launchers", "").strip().split()
        for launcher_name in launcher_names:
            logger.info("Loading launcher “%s”…", launcher_name)

            # Find .desktop files and cfg sections
            launcher_path = None
            if launcher_name.endswith(".desktop"):
                app_dirs = [
                    os.path.join(
                        distroot,
                        self.msystem.subdir,
                        "share",
                        "applications",
                    ),
                ]
                for app_dir in app_dirs:
                    p = os.path.join(app_dir, launcher_name)
                    if os.path.isfile(p):
                        logger.debug("Found %r", p)
                        launcher_path = p
                        break

            launcher_section = None
            if spec.has_section(launcher_name):
                launcher_section = dict(
                    spec.items(section=launcher_name, raw=True),
                )

            # Update from any found file, then any found overrides
            launcher = DesktopEntry()
            if launcher_path:
                launcher.update_from_desktop_file(launcher_path)
            if launcher_section:
                launcher.update(launcher_section, basename=launcher_name)

            if launcher.is_valid():
                self.launchers.append(launcher)
            else:
                logger.error(
                    "Can't find a complete launcher named “%s” "
                    "as either a config file section "
                    "or as a .desktop file in the bundle tree",
                    launcher_name,
                )
        logger.debug("New launchers: %r", self.launchers)

    def write_distributables(self, output_dir):
        """Create all distributable files for the bundle."""

        distroot = os.path.join(output_dir, self.stub_name)
        self._init_tree(distroot)

        self._cleanup(distroot)
        self._install_native_packages(distroot)
        self._init_launchers(distroot)
        self._install_icons(distroot)
        self._install_exe_launchers(distroot)
        self._install_packages(distroot, ["bash", "coreutils"])  # for postinst
        self._delete_surplus_files(distroot)  # including uneeded cygwin
        self._install_postinst_scripts(distroot)

        distfiles = []
        distfiles.extend(self._write_zip_distfile(distroot, output_dir))
        distfiles.extend(self._write_nsis_distfile(distroot, output_dir))
        return distfiles

    @property
    def display_name(self):
        s = self.spec["bundle"]
        d = s.get("display_name", None)
        if d:
            d = d.strip()
            if self.msystem != consts.MSYSTEM.MINGW64:
                d += " (w32)"
                # Win64 is the norm now, 32 bit is weird & old
        else:
            d = self.stub_name
        return d

    @property
    def description(self):
        s = self.spec["bundle"]
        d = self.display_name
        d = s.get("description", self.metadata.get("description", d))
        return d.strip()

    @property
    def url(self):
        s = self.spec["bundle"]
        u = "http://msys2.github.io"
        return s.get("url", self.metadata.get("url", u)).strip()

    @property
    def publisher(self):
        s = self.spec["bundle"]
        p = "MSYS2"
        if "packager" in self.metadata:
            p = self.metadata.get("packager", p)
            p = re.sub(r'\s*<[^@>]+@[^>]+>\s*', " ", p)  # strip email
        return s.get("publisher", p).strip()

    @staticmethod
    def _get_package_metadata(name):
        cmd = ["pacman", "--sync", "--info", name]
        try:
            info_str = subprocess.check_output(
                cmd,
                universal_newlines=True,
                env={"LANG": "C"},  # we specifically want the default
            )
        except:
            logger.critical("Failed to run “%s”", " ".join(cmd))
            sys.exit(2)
        metadata = {}
        current_header = None
        header_line_re = re.compile(r'^([a-z][a-z\040]*):\s(.*)$', re.I)
        for line in info_str.split("\n"):
            m = header_line_re.match(line)
            if m:
                current_header = str2key(m.group(1))
                line = m.group(2)
                metadata[current_header] = line
            else:
                assert current_header is not None
                new_value = "\n".join([metadata[current_header], line])
                metadata[current_header] = new_value
        return metadata

    @staticmethod
    def _parse_version(version):
        """Parses major and minor version numbers from a string."""
        components = re.findall(r'\d+', version)
        try:
            major = int(components[0])
        except IndexError:
            major = 0
        try:
            minor = int(components[1])
        except IndexError:
            minor = 0
        return (major, minor)

    def _init_tree(self, root):
        """Initialize a tree that can be installed to, then distributed.

        Internally, a bundle's tree is a heavily stripped-down MSYS2
        installation. It contains its own copy of the pacman database,
        but the cache that gets used is your own.

        Prepared bundle trees can be copied wherever you like, and used
        to launch their payload programs. The launcher scripts will do
        necessary postinst stuff before launching their payload.

        Normally these trees are packages in zipfiles or installers.

        """
        logger.info("Creating tree in “%s”…", root)
        for subpath in ["var/lib/pacman", "var/log", "tmp"]:
            os.makedirs(os.path.join(root, subpath), exist_ok=True)
        cmd = [
            "pacman", "--sync", "--refresh",
            "--quiet",
            "--root", root,
            "--noprogressbar",
        ]
        subprocess.check_call(cmd)

    def _install_packages(self, root, packages):
        """Helper: installs named packages into the tree."""
        logger.info("Installing %r in %r", packages, root)
        assert os.path.isdir(root)
        packages = list(packages)
        cmd = [
            "pacman", "--sync",
            "--quiet",
            "--root", ".",
            "--needed",
            "--noconfirm",
            "--noprogressbar",
            "--noscriptlet",  # postinst will do this
        ]
        cmd += packages
        logger.info("Running “%s”…", " ".join(cmd))
        subprocess.check_call(
            cmd,
            cwd=root,
        )

    def _install_postinst_scripts(self, root):
        """Installs specified post-install scripting for the bundle.

        The main post-install script, postinst.cmd, is used in both
        output formats. It adapts the install tree to a new install
        location by calling the post_install scriptlets deployed into
        place earlier by pacman.

        """
        scripts_dir = os.path.join(root, consts.SCRIPTS_SUBDIR)
        os.makedirs(scripts_dir, exist_ok=True)
        postinst_cmd = os.path.join(scripts_dir, consts.POSTINST_CMD_FILE)
        postinst_sh = os.path.join(scripts_dir, consts.POSTINST_SH_FILE)

        launcher_cmd_frags = ""
        launcher_sh_frags = ""
        for launcher in self.launchers:
            cfrag = launcher.get_postinst_cmd_fragment(root, self)
            sfrag = launcher.get_postinst_sh_fragment(root, self)
            launcher_cmd_frags += cfrag + "\n"
            launcher_sh_frags += sfrag + "\n"

        logger.info("Writing “%s”…", consts.POSTINST_CMD_FILE)
        data_dir = os.path.join(
            os.path.dirname(__file__),
            consts.PACKAGE_DATA_SUBDIR,
        )
        cmd_tmpl_path = os.path.join(data_dir, consts.POSTINST_CMD_FILE)
        with open(cmd_tmpl_path, "r") as fp:
            cmd_tmpl = fp.read()
        crlf = "\r\n"
        cmd = cmd_tmpl.format(
            scripts_subdir=consts.SCRIPTS_SUBDIR,
            msystem_subdir=self.msystem.subdir,
            launcher_cmd_fragments=launcher_cmd_frags,
            postinst_sh=consts.POSTINST_SH_FILE,
        )
        cmd = crlf.join(cmd.splitlines())
        with open(postinst_cmd, "w") as fp:
            print(cmd, end=crlf, file=fp)

        logger.info("Writing “%s”…", postinst_sh)
        sh_tmpl_path = os.path.join(data_dir, consts.POSTINST_SH_FILE)
        with open(sh_tmpl_path, "r") as fp:
            sh_tmpl = fp.read()
        cr = "\n"
        sh = sh_tmpl % dict(
            launcher_sh_fragments=launcher_sh_frags,
            state_file=consts.LAUNCHER_LOCATION_STATE_FILE,
        )
        with open(postinst_sh, "w") as fp:
            print(sh, end=cr, file=fp)

    def _install_native_packages(self, root):
        """Installs the packages in the bundle’s specification."""
        logger.info("Installing packages requested in the spec…")
        substs = self.msystem.substs
        packages = self.spec.get("bundle", "packages", fallback="")
        packages += " {pkg_prefix}win7appid"
        packages = packages.format(**substs)
        packages = packages.strip().split()
        self._install_packages(root, packages)

    def _install_icons(self, root):
        """Installs freedesktop icons specified in [bundle]→icons.

        This method converts PNG icons in the installed hicolor theme to
        an ICO file in the bundle root with PNG encoding for each size.

        """
        logger.info("Installing FreeDesktop icons…")
        converted = []
        for launcher in self.launchers:
            icon = launcher.install_icon(root, self.msystem)
            if not icon:
                continue
            if not self.icon:
                self.icon = icon
            converted.append(icon)
        return converted

    def _install_exe_launchers(self, root):
        """Install binary stub launchers"""
        logger.info("Installing .exe launchers…")
        for launcher in self.launchers:
            launcher.write_exe_launcher(root, self)

    def _cleanup(self, root):
        """Clean up any wrapper scripts etc. left by previous runs."""
        junk = [
            os.path.join(root, consts.LAUNCHER_LOCATION_STATE_FILE),
            os.path.join(root, consts.ICO_FILE_SUBDIR),
            os.path.join(root, consts.SCRIPTS_SUBDIR),
        ]
        junk.extend(glob.glob(os.path.join(root, "*.exe")))
        for path in junk:
            logger.debug("cleanup: removing “%s”", path)
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.unlink(path)

    def _search_path(self, root, exe_basename):
        """Gets win32 path elements for a native executable.

        The path returned is relative to the cygwin root. A .exe
        extension is appended if needed.

        """
        subdir = self.msystem.subdir
        search_paths = [
            (r'%s\bin' % (subdir,),
             os.path.join(root, subdir, "bin")),
        ]
        for win32_relpath, path in search_paths:
            for ext in [".exe", ""]:
                name = exe_basename + ext
                if os.path.isfile(os.path.join(path, name)):
                    return win32_relpath + '\\' + name
        return None

    def _delete_surplus_files(self, root):
        """Delete unwanted files from the bundle."""
        section = self.spec["bundle"]
        substs = self.msystem.substs

        nodelete_spec = section.get("nodelete", "")
        nodelete_patterns = nodelete_spec.format(**substs)
        nodelete_patterns = nodelete_spec.strip().split()
        nodelete_items = set()
        for patt in nodelete_patterns:
            for match in glob.glob(os.path.join(root, patt)):
                nodelete_items.add(match)
                # TODO: if it's a dir, exclude its descendents

        delete_spec = section.get("delete", "")
        delete_spec = delete_spec.format(**substs)
        delete_patterns = delete_spec.strip().split()
        for patt in delete_patterns:
            for item in glob.glob(os.path.join(root, patt)):
                if item in nodelete_items:
                    continue
                logger.debug("delete %r", item)
                try:
                    if os.path.isdir(item):
                        shutil.rmtree(item, ignore_errors=True, onerror=None)
                        # TODO: use a function that consults
                        # nodelete_items for exclusion.
                    elif os.path.isfile(item):
                        os.unlink(item)
                    else:
                        logger.warning(
                            "Filesystem entry “%s” has an unknown type",
                            item,
                        )
                except:
                    logger.exception("Failed to delete “%s”", item)

    def _write_zip_distfile(self, root, output_dir):
        """Package a frozen bundle as a standalone zipfile.

        :param str root: Frozen bundle location.
        :param str output_dir: Where to write the output zipfile.

        """
        output_file_basename = "{stub_name}-{version}-standalone.zip".format(
            stub_name=self.stub_name,
            version=self.metadata.get("version", "0"),
        )
        logger.info("Writing “%s”…", output_file_basename)
        output_file_path = os.path.join(output_dir, output_file_basename)
        cmd = ["zip", "-Xq9r", output_file_path, os.path.curdir]
        subprocess.check_call(
            cmd,
            cwd=root,
        )
        return [output_file_path]

    def _write_nsis_distfile(self, root, output_dir):
        """Package a frozen bundle as an NSIS installer executable.

        :param str root: Frozen bundle location.
        :param str output_dir: Where to write the output zipfile.

        """

        # Get the size
        bundle_size = 0
        for dir_path, subdirs, files in os.walk(root):
            for file_name in files:
                file_path = os.path.join(dir_path, file_name)
                bundle_size += os.path.getsize(file_path)
        bundle_size /= 1024   # to KiB
        bundle_size += 128   # uninstaller, plus a bit more for luck

        # Prepare substs for bundle.nsi
        installer_exe_name = "{stub_name}-{version}-installer.exe".format(
            stub_name=self.stub_name,
            version=self.version,
        )
        substs = {
            "stub_name": nsis_escape(self.stub_name),
            "regname": nsis_escape(self.stub_name),
            "msystem_subdir": nsis_escape(self.msystem.subdir),
            "bits": self.msystem.bits,
            "display_name": nsis_escape(self.display_name),
            "output_file_name": nsis_escape(installer_exe_name),
            "version_major": int(self.version_major),
            "version_minor": int(self.version_minor),
            "publisher": nsis_escape(self.publisher),
            "version": nsis_escape(self.version),
            "url": nsis_escape(self.url),
            "icon": nsis_escape(self.icon),
            "icons_subdir": nsis_escape(consts.ICO_FILE_SUBDIR),
            "description": nsis_escape(self.description),
            "scripts_subdir": nsis_escape(consts.SCRIPTS_SUBDIR),
            "icon_fragment": "",
            "launcher_install_fragments": "",
            "launcher_uninstall_fragments": "",
            "sc_folder": nsis_escape(winsafe_filename(self.display_name)),
            "bundle_size": int(round(bundle_size)),
        }

        # Conditional fragments
        if self.icon:
            frag = dedent("""
                Icon "%(stub_name)s\%(icons_subdir)s\%(icon)s.ico"
            """) % substs
            substs["icon_fragment"] = frag
        if self.launchers:
            ufrag = dedent(r"""
                RMDIR /r "$SMPROGRAMS\%(sc_folder)s"
            """) % substs
            ifrag = dedent(r"""
                RMDIR /r "$SMPROGRAMS\%(sc_folder)s"
                CreateDirectory "$SMPROGRAMS\%(sc_folder)s"
            """) % substs
            for launcher in self.launchers:
                ifrag += launcher.get_install_nsis(root, self)
                ufrag += launcher.get_uninstall_nsis(root, self)
            substs["launcher_install_fragments"] = ifrag
            substs["launcher_uninstall_fragments"] = ufrag

        # Load and subst the template file
        nsi_template_file = os.path.join(
            os.path.dirname(__file__),
            consts.PACKAGE_DATA_SUBDIR,
            "bundle.nsi",
        )
        with open(nsi_template_file, "r") as fp:
            nsis = fp.read()
        nsis = nsis % substs

        # Run makensis
        nsi_file_basename = "{stub_name}.nsi".format(**substs)
        logger.info("Writing “%s”…", nsi_file_basename)
        nsi_file_path = os.path.join(output_dir, nsi_file_basename)
        with open(nsi_file_path, "w") as fp:
            fp.write(nsis)
        native_shell(
            self.msystem,
            'makensis.exe -V3 "$1"', [nsi_file_path],
            cwd=output_dir,
        )
        installer_exe_path = os.path.join(output_dir, installer_exe_name)
        if not os.path.isfile(installer_exe_path):
            raise RuntimeError(
                "Missing output. "
                "Expected output file %r does not exist."
                % (installer_exe_path,),
            )

        return [installer_exe_path]
