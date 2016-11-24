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

"""Launchers read from Desktop Entry files or input .cfg sections.

Ref: https://specifications.freedesktop.org/desktop-entry-spec/latest/

"""

from .utils import c_escape
from .utils import findexe
from .utils import nsis_escape
from .utils import boolify
from .utils import winsafe_filename
from . import consts

import re
import os
import configparser
import glob
import struct
import tempfile
import shutil
from textwrap import dedent
import subprocess
import xml.etree.ElementTree as ET

import logging
logger = logging.getLogger(__name__)


# Class defs:

class DesktopEntry:
    """Parsed .desktop file, or an equivalent from a bundle spec.

    """

    # Settings & parser consts:

    _SPLIT_CHAR = r";"
    _MIME_TYPE_REGEX = re.compile(r"^[^/]+/[^/]+$")
    _CMDLINE_TOKEN_RE = re.compile(r'''
        (?: " (?P<quoted> (?: \\. | [^\\"] )* ) "
          |   (?P<unquoted> [^\s\"]+ )
          |   (?P<whitespace> \s+ )
          |   (?P<end> $ )
        )
    ''', re.VERBOSE)

    # Python basics:

    def __init__(self, *args, **kwargs):
        """Construct a blank (rather useless) DesktopEntry."""
        super().__init__()
        self._basename = ""
        self._name = ""
        self._comment = ""
        self._exec = []      # raw Exec line
        self._cmdline = []    # parsed Exec line
        self._icon = ""
        self._mimetypes = []
        self._terminal = False
        self._extinfo_cache_for = None
        self._extinfo_cache = ([], [])

    def __repr__(self):
        return "<DesktopEntry %r>" % (self._basename,)

    # Construction:

    def update_from_desktop_file(self, fp):
        """Update a DesktopEntry from a .desktop file.

        :param fp: an open file-like object, or the path to a file.

        """
        close_needed = False
        section_name = "Desktop Entry"
        required_type = "Application".casefold()
        if isinstance(fp, str):
            fp = open(fp, "r")
            close_needed = True
        try:
            basename = os.path.basename(fp.name)
            conf = configparser.RawConfigParser()
            conf.read_file(fp)
            mapping = conf[section_name]
            type_ = mapping.get("Type", "").casefold()
            if type_ != required_type:
                logger.warning(
                    "%s: “[%s]” is of type “%s”. Needs to be “%s”.",
                    basename,
                    section_name,
                    type_,
                    required_type,
                )
            else:
                self.update(mapping, basename=basename)
        finally:
            if close_needed:
                fp.close()

    def update(self, mapping, basename=None):
        """Update a DesktopEntry from a mapping.

        :param mapping: a dict-like object.
        :param str basename: string to use as a replacement basename

        For launchers defined only in the config file, basename should
        normally be the name of the section (minus any filename extension).

        The checks are a bit laxer than update_from_desktop_file's,
        since any desktop entry listed in the bundle spec is assumed to
        be an application.

        Note that if mapping is a section proxy object from a
        configparser module, it should be from a RawConfigParser.
        Desktop file definitions contain their own `%`-style
        interpolations which configparser must not try to expand.

        """
        caseinsens_mapping = {}
        for key, value in mapping.items():
            key = key.casefold()
            caseinsens_mapping[key] = value
        if basename is not None:
            basename = str(basename)
            basename, ext = os.path.splitext(basename)
            basename = winsafe_filename(basename.strip())
            if basename == "":
                raise ValueError("DesktopEntry basename cannot be empty")
            self._basename = basename
        populate = [
            ("_name", "Name", str),
            ("_comment", "Comment", str),
            ("_icon", "Icon", str),
            ("_exec", "Exec", str),
            ("_cmdline", "Exec", self._tokenize_cmdline),
            ("_terminal", "Terminal", boolify),
            ("_mimetypes", "MimeType", self._parse_mimetypes),
        ]
        for attr, key, conv in populate:
            value = caseinsens_mapping.get(key.casefold())
            if value is None:
                continue
            value = str(value).strip()
            value = conv(value)
            setattr(self, attr, value)
        return self

    def is_valid(self):
        return all([
            self._basename, self._name,
            self._exec, self._cmdline,
        ])

    @classmethod
    def _tokenize_cmdline(cls, s):
        s = str(s).strip()
        cmd = []
        current = ""
        for m in cls._CMDLINE_TOKEN_RE.finditer(s):
            g = m.groupdict()
            quoted = g.get("quoted")
            unquoted = g.get("unquoted")
            if quoted:
                current += cls._unescape_string(quoted)
            if unquoted:
                current += unquoted
            if g.get("whitespace") is None and g.get("end") is None:
                continue
            cmd.append(current)
            current = ""
        return cmd

    @classmethod
    def _unescape_string(cls, s):
        p = re.compile(r'\\(.)')
        return p.replace((lambda m: m.group(1)), s)

    @classmethod
    def _parse_mimetypes(cls, s):
        s = str(s).strip()
        mimetypes = []
        for t in s.split(cls._SPLIT_CHAR):
            t = t.strip()
            if cls._MIME_TYPE_REGEX.match(t):
                mimetypes.append(t)
        return mimetypes

    # Actions:

    def install_icon(self, root, msystem):
        """Convert and install .ico icons.

        :param str root: Bundle root directory.
        :param consts.MSYSTEM msystem: The MSYSTEM to search.
        :returns: the icon basename minus extension, or None if failed
        :rtype: str

        """
        icon = self._icon
        if not icon:
            return None
        if os.path.isabs(icon):
            return None

        prefix = os.path.join(root, msystem.subdir)
        outdir = os.path.join(root, consts.ICO_FILE_SUBDIR)

        pngfile_infos = []
        for i in range(2, 33):
            match = None
            for theme in ["Adwaita", "hicolor"]:
                patt = "share/icons/{theme}/{s}x{s}/*/{icon}.png"
                patt = patt.format(
                    theme=theme,
                    s=(i * 8),
                    icon=icon,
                )
                patt = os.path.join(prefix, patt)
                for m in glob.glob(patt):
                    logger.debug("icon: using “%s”", m)
                    match = m
                    break
                if match:
                    break
            if match:
                pngfile_infos.append((i * 8, i * 8, match))

        if pngfile_infos:
            os.makedirs(outdir, exist_ok=True)
            ico_path = os.path.join(outdir, "%s.ico" % (icon,))
            write_ico_file(ico_path, pngfile_infos)
            if not os.path.isfile(ico_path):
                logger.error("Failed to create %r", ico_path)
            else:
                return icon

        return None

    def write_exe_launcher(self, root, bundle):
        """Compile and install a launcher .exe

        :param str root: Output folder path for the executable.
        :param .bundle.NativeBundle bundle: The bundle being built.

        """
        app_id = self.get_app_id(bundle)
        postinst_sh = os.path.join(consts.SCRIPTS_SUBDIR, "postinst.sh")

        exe_basename = self._basename + ".exe"
        final_exe_path = os.path.join(root, exe_basename)
        logger.info("Building launcher “%s”…", exe_basename)
        data_dir = os.path.join(
            os.path.dirname(__file__),
            consts.PACKAGE_DATA_SUBDIR,
        )

        # Does the launcher need to invoke bash?
        use_helper = True
        resolved_exe = ""
        logger.debug("%s: cmdline: %r", self._basename, self._cmdline)
        prefix = os.path.join(root, bundle.msystem.subdir)
        exe = self._cmdline[0]
        exe, args = self._resolve_exe(prefix)
        logger.debug(
            "%s: resolved exe: %r, args: %r",
            self._basename, exe, args,
        )
        if not self._terminal:
            if (exe is not None) and (exe.lower().endswith(".exe")):
                use_helper = False
                resolved_exe = exe

        if not use_helper:
            logger.info(
                "Launcher %s will directly invoke “%s”",
                self._basename,
                resolved_exe,
            )
        elif self._terminal:
            logger.info(
                "Launcher %s will use bash to invoke %r and then wait "
                "because %s specifies “Terminal: true”.",
                self._basename,
                self._cmdline,
                "%s.desktop" % (self._basename,),
            )
        else:
            logger.warning(
                "Launcher %s needs to use bash to launch %r "
                "despite %s being “Terminal: false”.",
                self._basename,
                self._cmdline,
                "%s.desktop" % (self._basename,),
            )
            logger.info(
                "It may be possible to override %s’s Exec line "
                "so that it launches a .exe for the main process. "
                "The user experience will be slightly better if you can.",
                self._basename,
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            logger.debug("tmpdir: %r", tmpdir)
            objects = []

            with open(os.path.join(tmpdir, "config.h"), "w") as fp:
                config_h = dedent("""
                    #ifndef HAVE_CONFIG_H
                    #define HAVE_CONFIG_H

                    #define LAUNCHER_POSTINST L"{postinst_sh}"
                    #define LAUNCHER_USE_HELPER {use_helper}

                    const BOOL LAUNCHER_USE_TERMINAL = {use_terminal};
                    LPCWSTR LAUNCHER_RESOLVED_EXE = L"{resolved_exe}";
                    LPCWSTR LAUNCHER_APP_ID = L"{app_id}";
                    LPCWSTR LAUNCHER_LOCATION_STATE_FILE = L"{state_file}";

                    const WCHAR *LAUNCHER_CMDLINE_TEMPLATE[] =
                """).format(
                    postinst_sh=c_escape(postinst_sh),
                    use_terminal=int(self._terminal),
                    use_helper=int(use_helper),
                    app_id=c_escape(app_id),
                    resolved_exe=c_escape(resolved_exe),
                    state_file=c_escape(consts.LAUNCHER_LOCATION_STATE_FILE),
                )

                config_h += "{\n"
                for s in self._cmdline:
                    config_h += 'L"%s",\n' % (c_escape(s),)
                config_h += "NULL\n};\n"

                config_h += dedent("""
                    #endif // HAVE_CONFIG_H
                """)
                print(config_h, file=fp)

            orig_c_path = os.path.join(data_dir, "launcherstub.c")
            c_basename = self._basename + ".c"
            c_path = os.path.join(tmpdir, c_basename)
            shutil.copy(orig_c_path, c_path)
            subprocess.check_call(
                ["gcc", "-municode", "-std=c11", "-c", c_basename],
                cwd=tmpdir,
            )
            o_basename = self._basename + ".o"
            o_path = os.path.join(tmpdir, o_basename)
            assert os.path.exists(o_path)
            objects.append(o_basename)

            if self._icon:
                ico_basename = "%s.ico" % (self._icon,)
                orig_ico_path = os.path.join(
                    root, consts.ICO_FILE_SUBDIR,
                    ico_basename,
                )
                if os.path.exists(orig_ico_path):
                    logger.debug("icon: %r" % (self._icon,))
                    ico_rc = "icon.rc"
                    ico_o = "icon.o"
                    ico_path = os.path.join(tmpdir, ico_basename)
                    shutil.copy(orig_ico_path, ico_path)
                    ico_rc_path = os.path.join(tmpdir, ico_rc)
                    with open(ico_rc_path, "w") as rc_fp:
                        print('1 ICON "%s"' % (ico_basename,), file=rc_fp)
                    try:
                        subprocess.check_call(
                            ["windres", ico_rc, ico_o],
                            cwd=tmpdir,
                        )
                    except:
                        logger.exception(
                            "Icon creation with windres failed",
                        )
                    else:
                        ico_o_path = os.path.join(tmpdir, ico_o)
                        if os.path.exists(ico_o_path):
                            objects.append(ico_o)

            link_cmd = ["gcc", "-municode", "-std=c11", "-mwindows", "-o"]
            link_cmd.append(exe_basename)
            link_cmd.extend(objects)
            subprocess.check_call(
                link_cmd,
                cwd=tmpdir,
            )
            exe_path = os.path.join(tmpdir, exe_basename)
            assert os.path.exists(exe_path)
            shutil.copy(exe_path, final_exe_path)
        assert os.path.exists(final_exe_path)

    def _resolve_exe(self, prefix):
        """Resolves the 1st element of self._cmdline to a Windows subpath.

        :params prefix: The POSIX style prefix root (with bin, share, ...)
        :returns: (cmd, args), as parsed.

        The return value is a pair (cmd, args) where cmd is a subpath
        relative to the parent of "prefix", and args is the args list.

        If cmd could not be found, (None, []) is returned.

        This function expects its prefix to be one of the usual MSYS2
        mingw32 or mingw64 folders, and that these will be deployed
        directly in the distributable's $INSTDIR.

        """
        args = list(self._cmdline)
        cmd = args.pop(0)
        cmd = findexe(cmd, prefix)
        if cmd is None:
            return (None, [])
        msystem_subdir = os.path.basename(prefix)
        cmd = msystem_subdir + "\\" + cmd
        return (cmd, args)

    def get_app_id(self, bundle):
        return "MSYS2.{bundle}.{launcher}.{ver}".format(
            bundle=bundle.stub_name,
            launcher=self._basename,
            ver=bundle.version,
        )

    def get_install_nsis(self, root, bundle):
        """Get NSIS Install config fragments."""

        app_id = self.get_app_id(bundle)

        substs = dict(
            sc_folder=nsis_escape(winsafe_filename(bundle.display_name)),
            sc_name=nsis_escape(winsafe_filename(self._name)),
            basename=nsis_escape(self._basename),
            msystem_subdir=nsis_escape(bundle.msystem.subdir),
            icon=nsis_escape(self._icon),
            icon_subdir=nsis_escape(consts.ICO_FILE_SUBDIR),
            comment=nsis_escape(self._comment),
            app_id=nsis_escape(app_id),
        )

        # Shortcut
        nsis = 'CreateShortcut '
        nsis += r'"$SMPROGRAMS\{sc_folder}\{sc_name}.lnk" '.format(**substs)
        nsis += r'"$INSTDIR\{basename}.exe" "" '.format(**substs)

        # Shortcut icon
        # was: nsis += r'"$INSTDIR\{icon_subdir}\{icon}.ico" '.format(**substs)
        nsis += r'"" '  # Can use the .exe icon now
        nsis += r'"" '  # icon index: just use the default

        nsis += r'SW_SHOWMINIMIZED '  # ignored: we're now launching a GUI app
        nsis += r'"" '    # hotkey
        nsis += r'"{comment}" '.format(**substs)
        nsis += "\n"

        return nsis

    def get_uninstall_nsis(self, root, bundle):
        """Get NSIS Uninstall config fragment."""
        return ""

    def get_postinst_sh_fragment(self, root, bundle):
        """Fetch a script fragment for postinst.sh"""
        app_id = self.get_app_id(bundle)
        sh_tmpl = dedent(r"""
            # Postinst fragment from {basename}
            win7appid="/{msystem_subdir}/bin/win7appid.exe"
            shortcut="$START_MENU_PROGRAMS/{sc_folder}/{sc_name}.lnk"
            echo "Setting appid for {sc_folder}/{sc_name}.lnk ..."
            if test "x$START_MENU_PROGRAMS" != "x"; then
                if ! test -f "$shortcut"; then
                    echo "warning: shortcut not installed: $shortcut"
                elif ! test -f "$win7appid"; then
                    echo "ERROR: missing binary: $win7appid"
                else
                    "$win7appid" "$shortcut" "{app_id}"
                fi
            fi
        """)
        sh_frag = sh_tmpl.format(
            basename=self._basename,
            sc_folder=winsafe_filename(bundle.display_name),
            sc_name=winsafe_filename(self._name),
            app_id=app_id,
            msystem_subdir=bundle.msystem.subdir,
        )
        return sh_frag

    def get_postinst_cmd_fragment(self, root, bundle):
        """Fetch a script fragment for postinst.cmd. Currently unused."""
        return ""

    def _get_extensions(self, root, bundle):
        """Gets the file name extensions this launcher can handle.

        :param str root: Bundle root directory.
        :param bundle.NativeBundle: The bundle tree to search.
        :returns: Two lists, ``(primary_extinfo, secondary_extinfo)``
        :rtype: tuple

        Either of the returned lists may be empty. The primary list
        should be considered the native file types for the app; the
        secondary list details files which it may also be able to open
        because they are derivative types of file.

        Each of the lists has elements ``(ext, desc)``, where ext is the
        filename extension without a leading dot, and desc is a
        human-readable description of the file type.

        """
        if not self._mimetypes:
            return ([], [])

        if self._extinfo_cache_for == (root, bundle):
            return self._extinfo_cache

        simple_glob_pattern_re = re.compile(r"^\*\.([a-zA-Z0-9]+)$")

        primary_exts = []
        secondary_exts = []
        prefix = os.path.join(root, bundle.msystem.subdir)
        ns = {
            "smi": "http://www.freedesktop.org/standards/shared-mime-info",
        }
        smi_file_patt = os.path.join(prefix, "share/mime/packages/*.xml")
        for smi_file_name in glob.glob(smi_file_patt):
            smi_docroot = ET.parse(smi_file_name)
            for t in smi_docroot.findall("smi:mime-type", ns):
                t_matched = False
                exts = None
                t_type = t.get("type", None)
                if t_type in self._mimetypes:
                    t_matched = True
                    exts = primary_exts
                else:
                    for mimetype in self._mimetypes:
                        p = ".//smi:sub-class-of[@type='%s']" % (mimetype,)
                        if t.findall(p, ns):
                            t_matched = True
                            exts = secondary_exts
                            break
                if not t_matched:
                    continue
                assert exts is not None
                desc = t_type
                for c in t.findall("smi:comment", ns):
                    if c.get("xml:lang") is None:  # FIXME: i18n generally
                        desc = c.text.strip()
                        break
                for g in t.findall("smi:glob", ns):
                    g_patt = g.get("pattern", "")
                    match = simple_glob_pattern_re.match(g_patt)
                    if not match:
                        continue
                    ext = match.group(1)
                    if ext not in exts:
                        exts.append((ext, desc))

        result = (primary_exts, secondary_exts)
        self._extinfo_cache_for = (root, bundle)
        self._extinfo_cache = result
        return result

    def get_file_assoc_nsis(self, root, bundle, ext_map):
        exts1, exts2 = self._get_extensions(root, bundle)
        nsis = ""
        for optflag, exts in [("", exts1), ("/o", exts2)]:
            for (ext, desc) in exts:
                if ext in ext_map:
                    continue
                ext_map[ext] = self

                frag = dedent(r"""
                    Section {optflag} "Open *.{ext} with {name}"
                        !insertmacro FileAssoc "{ext}" \
                            "{basename}.{ext}" \
                            "{desc}" \
                            "$INSTDIR\{basename}.exe,0" \
                            "Open with {name}" \
                            "$INSTDIR\{basename}.exe $\"%1$\""
                    SectionEnd
                """).format(
                    optflag=optflag,
                    ext=nsis_escape(ext),
                    name=nsis_escape(self._name),
                    basename=nsis_escape(self._basename),
                    desc=nsis_escape(desc),
                )
                nsis += frag
        return nsis

    def get_file_unassoc_nsis(self, root, bundle, ext_map):
        exts1, exts2 = self._get_extensions(root, bundle)
        exts = list(exts1) + list(exts2)
        nsis = "Section \"un.AssocFiles.{basename}\"\n".format(
            basename=nsis_escape(self._basename),
        )
        for (ext, desc) in exts:
            if ext_map.get(ext) is not self:
                continue
            nsis += dedent("""
                !insertmacro FileUnAssoc "{ext}" "{basename}.{ext}"
            """).format(
                ext=nsis_escape(ext),
                basename=nsis_escape(self._basename),
            )
        nsis += "SectionEnd\n\n"
        return nsis


# Helper funcs:

def write_ico_file(filename, pngfile_infos):
    """Concatenate PNG images into a .ico file.

    :param str filename: Output .ico file path, to be overwritten.
    :param list pngfile_infos: List of (w, h, pngpath) tuples.

    Very basic Windows icon file writer. We're using this hack because
    png2ico won't generate .ico files with 256x256 icons, and because
    Pillow isn't available for MSYS2's Cygwin-like environment.

    This code requires valid PNG file input, and trusts the sizes you
    give it. It will filter out images of the wrong size.

    Ref https://en.wikipedia.org/wiki/ICO_(file_format)#PNG_format

    """

    # Check that the images are all OK for an icon.
    entries = []
    for i, pngfile_info in enumerate(pngfile_infos):
        w, h, pngfile_path = pngfile_info
        if w != h:
            logger.warning("image #%d: ignored: not square", i)
            continue
        s = w
        if int(s//8.0)*8 != int(s):
            logger.warning("image #%d: ignored: size not multiple of 8", i)
            continue
        if s < 16:
            logger.warning("image #%d: ignored: < 16x16", i)
            continue
        if s > 256:
            logger.warning("image #%d: ignored: > 256x256", i)
            continue
        with open(pngfile_path, "rb") as png_fp:
            image_data = png_fp.read()
        assert len(image_data) > 0
        # The height and width fields are written as 0 to mean 256.
        if s == 256:
            s = 0
        entries.append((s, image_data))
    if not entries:
        raise RuntimeError("No valid images, ICO file not written")

    # Sort by image dimensions, largest first except for any 256x256 icon.
    entries.sort(reverse=True)

    # Write the ICO file
    with open(filename, "wb") as ico_fp:
        # ICONDIR
        icondir_fmt = "<HHH"
        icondir_size = struct.calcsize(icondir_fmt)
        assert(icondir_size) == 6
        icondir = struct.pack(
            icondir_fmt,
            0,  # H. Reserved.
            1,  # H. Icon (".ICO") format.
            len(entries),  # H. Number of entries.
        )
        ico_fp.write(icondir)
        # ICONDIRENTRY
        icondirentry_fmt = "<BBBBHHII"
        icondirentry_size = struct.calcsize(icondirentry_fmt)
        assert(icondirentry_size) == 16
        image_offset = icondir_size + (icondirentry_size * len(entries))
        for entry in entries:
            s, image_data = entry
            assert image_offset <= 0xffffffff
            image_size = len(image_data)
            assert image_size <= 0xffffffff
            icondirentry = struct.pack(
                icondirentry_fmt,
                s,  # B. Width, or 0 if that's 256.
                s,  # B. Height, or 0 if it's 256.
                0,  # B. Number of entries in palette, 0 if no palette.
                0,  # B. Reserved.
                0,  # H. Colour planes, either 0 or 1.
                32,  # H. Bits per pixel. Always 32 for PIL RGBA.
                image_size,    # H. Size of image data in bytes.
                image_offset,  # H. Offset of image data from start of file.
            )
            ico_fp.write(icondirentry)
            image_offset += len(image_data)
        # Image data, concatenated, as previously indexed
        for entry in entries:
            s, image_data = entry
            ico_fp.write(image_data)
