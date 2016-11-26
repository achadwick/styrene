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
from .utils import winsafe_filename
from . import consts

import os
import re
import subprocess
import sys
import glob
import shutil
import functools
from textwrap import dedent

import logging
logger = logging.getLogger(__name__)


# Consts:

RUNTIME_DEPENDENCIES = {
    consts.MSYSTEM.MINGW64: [
        "mingw-w64-x86_64-gcc",
        "mingw-w64-x86_64-nsis",
        "mingw-w64-x86_64-binutils",
    ],
    consts.MSYSTEM.MINGW32: [
        "mingw-w64-i686-gcc",
        "mingw-w64-i686-nsis",
        "mingw-w64-i686-binutils",
    ],
}


# Class defs:

class SpecificationError (Exception):
    """An error with the bundle specification."""
    pass


class NativeBundle:
    """Installable bundle for Win32 or Win64."""

    _SECTION_NAME = "bundle"

    def __init__(self, spec):
        """Initializes a bundle from a specification."""
        super().__init__()
        self.spec = spec
        #: The target architecture, prefixes etc.
        self.msystem = consts.MSYSTEM.from_environ()
        #: Collected metadata, only useful after package installation.
        self.metadata = {}
        self.icon = ""
        self.launchers = []

    def check_runtime_dependencies(self):
        deps = RUNTIME_DEPENDENCIES.get(self.msystem)
        assert deps is not None, "Runtime dependencies not defined?"
        missing = []
        for pkg in deps:
            try:
                subprocess.check_output(
                    ["pacman", "-Qi", pkg],
                    stderr=subprocess.STDOUT,
                )
            except subprocess.CalledProcessError:
                missing.append(pkg)
                logger.warning("Package %s is not installed.", pkg)
        if missing:
            cmdline = "pacman -S %s" % (" ".join(missing),)
            logger.info(
                "Please run “%s” to install the missing packages",
                cmdline,
            )
            raise RuntimeError("Missing dependencies, cannot proceed")

    @property
    def _section(self):
        """The main configuration section."""
        if not self.spec.has_section(self._SECTION_NAME):
            raise SpecificationError(
                "Missing [%s] section.",
                self._SECTION_NAME,
            )
        return self.spec[self._SECTION_NAME]

    def _init_launchers(self, distroot):
        """Initializes the launcher specifications for this bundle.

        These come in two forms: .desktop files, or sections in the
        bundle specification file. Both are listed in the "launchers"
        key of the main [bundle] section.

        """
        spec = self.spec
        self.launchers = []
        launcher_names = self._section.get("launchers", "").strip().split()
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

    def write_distributables(self, output_dir, options):
        """Create all distributable files for the bundle."""

        distroot = os.path.join(output_dir, self.stub_name)
        self._init_tree(distroot)

        self._cleanup(distroot)
        self._install_native_packages(distroot, pkgdirs=options.pkgdirs)
        self._init_metadata(distroot)
        self._init_launchers(distroot)
        self._install_icons(distroot)
        self._install_exe_launchers(distroot)
        self._install_packages(distroot, ["bash", "coreutils"])  # for postinst
        self._delete_surplus_files(distroot)  # including uneeded cygwin
        self._install_postinst_scripts(distroot)

        distfiles = []
        if options.build_exe:
            distfiles.extend(self._write_nsis_distfile(distroot, output_dir))
        if options.build_zip:
            distfiles.extend(self._write_zip_distfile(distroot, output_dir))
        return distfiles

    @property
    def version(self):
        """The bundle's version string.

        The version string is normally derived from the primary
        package's version.  It can be overridden in [bundle]→version.

        As such, the value may only be meaningful after bundle metadata
        has been collected from the installed packages.

        """
        return self._section.get("version", self.metadata.get("version", "0"))

    @property
    def stub_name(self):
        """What to call generated files and directories.

        This will be derived from the first package's name if necessary.
        A suffix reflecting the target architecture will be appended.

        """
        stub = self._section.get("filename_stub")
        if not stub:
            packages_raw = self._section.get("packages")
            if not packages_raw:
                raise SpecificationError(
                    "No definition of [%s]→packages "
                    "when trying to derive the bundle’s stub_name",
                    self._SECTION_NAME,
                )
            packages_raw = packages_raw.strip().split()
            stub = packages_raw[0].format(pkg_prefix="")
        if not re.match(r'^[\w+-]+$', stub):
            tmpl = str(
                "Cannot use “{stub_name}” for naming things. "
                "Please define a [bundle]→filename_stub containing "
                "letters, numbers, _ or - only."
            )
            raise ValueError(tmpl.format(stub_name=stub))
        stub += self.msystem.bundle_name_suffix
        return stub

    @property
    def packages(self):
        """The list of packages to install."""
        packages_raw = self._section.get("packages")
        if not packages_raw:
            raise SpecificationError(
                "No definition of [%s]→packages",
                self._SECTION_NAME,
            )
        packages_raw = packages_raw.strip()
        substs = self.msystem.substs
        packages_raw = packages_raw.format(**substs)
        return packages_raw.split()

    @property
    def display_name(self):
        """The name to display when referring to the bundle.

        This property is normally derived from the primary packages's
        entry in the install tree's package database.

        It can be overridden in [bundle]→display name.

        """
        d = self._section.get("display_name", None)
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
        """Textual description of the bundle.

        This property is normally derived from the primary packages's
        entry in the install tree's package database.

        It can be overridden in [bundle]→description.

        """
        s = self._section
        d = self.display_name
        d = s.get("description", self.metadata.get("description", d))
        return d.strip()

    @property
    def url(self):
        """Home page URL for the bundle.

        This property is normally derived from the primary packages's
        entry in the install tree's package database.

        It can be overridden in [bundle]→url.

        """
        s = self._section
        u = "http://msys2.github.io"
        return s.get("url", self.metadata.get("url", u)).strip()

    @property
    def publisher(self):
        """Package publisher.

        This property is normally derived from the primary packages's
        entry in the install tree's package database.

        It can be overridden in [bundle]→publisher.

        """
        s = self._section
        p = "MSYS2"
        if "packager" in self.metadata:
            p = self.metadata.get("packager", p)
            p = re.sub(r'\s*<[^@>]+@[^>]+>\s*', " ", p)  # strip email
        return s.get("publisher", p).strip()

    def _init_metadata(self, root):
        """Update self.metadata from the first listed package."""
        main_package = self.packages[0]
        metadata = self._get_package_metadata(main_package, root)
        logger.debug("Got metadata for “%s”: %r", main_package, metadata)
        self.metadata.update(metadata)

    @staticmethod
    def _get_package_metadata(name, root):
        """Get details about a package from the db of installed packages."""
        cmd = [
            "pacman", "--query",
            "--info", name,
            "--root", root,
        ]
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

    def _install_packages(self, root, packages, pkgdirs=()):
        """Helper: installs named packages into the tree."""
        packages = list(packages)
        logger.info("Installing %r into “%s”", packages, root)
        assert os.path.isdir(root)

        cmd_common = [
            "--root", root,
            "--needed",
            "--noconfirm",
            "--noprogressbar",
            "--noscriptlet",  # postinst will do this
        ]

        # Divide the list of package names into ones that can be added
        # from files in the pkgdirs, and ones which must be synced from
        # the online repositories. In both cases, styrene assumes you
        # want the most recent available version.

        local_packages = set()
        local_package_paths = set()
        remaining_packages = set()
        filename_re_tmpl = r'''
            ^ {name}
            - (?P<version> [^-]+ - \d+ )
            - any
            [.]pkg[.]tar
            (?: [.](?:gz|xz) )?
            $
        '''
        keyobj = functools.cmp_to_key(self._vercmp)
        for pkg_name in packages:
            filename_re = filename_re_tmpl.format(
                name=re.escape(pkg_name),
            )
            filename_re = re.compile(filename_re, re.X | re.I)
            matches = []
            for pkgdir in pkgdirs:
                for entry in os.listdir(pkgdir):
                    m = filename_re.match(entry)
                    if not m:
                        continue
                    version = m.groupdict()["version"]
                    matchinfo = (version, os.path.join(pkgdir, entry))
                    matches.append(matchinfo)
                    logger.debug(
                        "Found %s version %s in “%s”",
                        pkg_name, version, pkgdir,
                    )
            if matches:
                matches.sort(key=lambda vp: (keyobj(vp[0]), vp[1]))
                most_recent_match = matches[-1]
                _, package_path = most_recent_match
                logger.info("Using “%s” for %s", package_path, pkg_name)
                local_package_paths.add(package_path)
                local_packages.add(pkg_name)
            else:
                remaining_packages.add(pkg_name)

        if local_package_paths:
            cmd = ["pacman", "--upgrade"]
            cmd += cmd_common
            cmd += list(local_package_paths)
            logger.debug("Running “%s”…", " ".join(cmd))
            subprocess.check_call(cmd)

        if remaining_packages:
            cmd = ["pacman", "--sync", "--quiet"]
            cmd += cmd_common
            cmd += list(remaining_packages)
            if local_packages:
                cmd += ["--ignore", ",".join(local_packages)]
            logger.debug("Running “%s”…", " ".join(cmd))
            subprocess.check_call(cmd)

    @staticmethod
    def _vercmp(v1, v2):
        """Compares package version strings."""
        # Ugly way of doing this, but necessary if this is to run
        # with the native MINGW64 and 32 Pythons.
        v1 = str(v1)
        v2 = str(v2)
        sign_str = subprocess.check_output(["vercmp", v1, v2])
        sign_str = sign_str.strip()
        return int(sign_str)

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
        with open(cmd_tmpl_path, "r", encoding="utf-8") as fp:
            cmd_tmpl = fp.read()
        crlf = "\r\n"
        cmd = cmd_tmpl.format(
            scripts_subdir=consts.SCRIPTS_SUBDIR,
            msystem_subdir=self.msystem.subdir,
            launcher_cmd_fragments=launcher_cmd_frags,
            postinst_sh=consts.POSTINST_SH_FILE,
        )
        cmd = crlf.join(cmd.splitlines())
        with open(postinst_cmd, "w", encoding="utf-8") as fp:
            print(cmd, end=crlf, file=fp)

        logger.info("Writing “%s”…", postinst_sh)
        sh_tmpl_path = os.path.join(data_dir, consts.POSTINST_SH_FILE)
        with open(sh_tmpl_path, "r", encoding="utf-8") as fp:
            sh_tmpl = fp.read()
        cr = "\n"
        sh = sh_tmpl % dict(
            launcher_sh_fragments=launcher_sh_frags,
            state_file=consts.LAUNCHER_LOCATION_STATE_FILE,
        )
        with open(postinst_sh, "w", encoding="utf-8") as fp:
            print(sh, end=cr, file=fp)

    def _install_native_packages(self, root, pkgdirs):
        """Installs the packages in the bundle’s specification.

        The win7appid binary for the target architecture is installed
        too, because the post-install scripting will need it for
        associating launcher shortcuts with launcher binaries and any
        spawned cmd windows.

        """
        logger.info("Installing packages requested in the spec…")
        substs = self.msystem.substs
        packages = list(self.packages)
        packages.append("{pkg_prefix}win7appid".format(**substs))
        self._install_packages(root, packages, pkgdirs=pkgdirs)

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
        section = self._section
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
                        if not os.access(item, os.W_OK):  # native winXX sem
                            os.chmod(item, 0o600)
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
        major, minor = self._parse_version(self.version)
        substs = {
            "stub_name": nsis_escape(self.stub_name),
            "regname": nsis_escape(self.stub_name),
            "msystem_subdir": nsis_escape(self.msystem.subdir),
            "bits": self.msystem.bits,
            "display_name": nsis_escape(self.display_name),
            "output_file_name": nsis_escape(installer_exe_name),
            "version_major": int(major),
            "version_minor": int(minor),
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
            "launcher_assoc_fragments": "",
            "launcher_unassoc_fragments": "",
            "sc_folder": nsis_escape(winsafe_filename(self.display_name)),
            "bundle_size": int(round(bundle_size)),
        }

        # Conditional fragments

        if self.icon:
            frag = dedent("""
                Icon "%(stub_name)s\%(icons_subdir)s\%(icon)s.ico"
                UninstallIcon "%(stub_name)s\%(icons_subdir)s\%(icon)s.ico"
            """) % substs
            substs["icon_fragment"] = frag

        if self.launchers:

            # Shortcuts
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

            # File associations
            # Only one per extension even if lots of launchers claim it.
            ifrag = ""
            ufrag = ""
            ext_map = {}
            for launcher in self.launchers:
                ifrag += launcher.get_file_assoc_nsis(root, self, ext_map)
            for launcher in self.launchers:
                ufrag += launcher.get_file_unassoc_nsis(root, self, ext_map)
            if ext_map:
                ifrag += dedent("""
                    Section "Update filename associations"
                        SectionIn RO
                        !insertmacro UpdateFileAssocs
                    SectionEnd
                """)
                ufrag += dedent("""
                    Section "un.Update filename associations"
                        SectionIn RO
                        !insertmacro UpdateFileAssocs
                    SectionEnd
                """)
            substs["launcher_assoc_fragments"] = ifrag
            substs["launcher_unassoc_fragments"] = ufrag

        # Load and subst the template file
        nsi_template_file = os.path.join(
            os.path.dirname(__file__),
            consts.PACKAGE_DATA_SUBDIR,
            "bundle.nsi",
        )
        with open(nsi_template_file, "r", encoding="utf-8") as fp:
            nsis = fp.read()
        nsis = nsis % substs

        # Run makensis with a suitable config and includes

        nsi_file_basename = "{stub_name}.nsi".format(**substs)
        logger.info("Writing “%s”…", nsi_file_basename)
        nsi_file_path = os.path.join(output_dir, nsi_file_basename)
        with open(nsi_file_path, "w", encoding="utf-8") as fp:
            fp.write(nsis)

        nsh_file_basenames = ["assoc.nsh"]
        for nsh_file_basename in nsh_file_basenames:
            logger.info("Copying “%s”…", nsh_file_basename)
            nsh_src_file_path = os.path.join(
                os.path.dirname(__file__),
                consts.PACKAGE_DATA_SUBDIR,
                nsh_file_basename,
            )
            nsh_targ_file_path = os.path.join(output_dir, nsh_file_basename)
            shutil.copy(nsh_src_file_path, nsh_targ_file_path)

        subprocess.check_call(
            ["makensis.exe", "-V3", "-INPUTCHARSET", "UTF8", nsi_file_path],
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
