# NSIS installer template, processed by bundle.py.
# This file is dedicated into the public domain, CC0 v1.0.
# https://creativecommons.org/publicdomain/zero/1.0/

!include "assoc.nsh"

!define UNINST_KEY \
    "Software\Microsoft\Windows\CurrentVersion\Uninstall\%(regname)s"

Name "%(display_name)s"
OutFile "%(output_file_name)s"
InstallDir "$PROGRAMFILES%(bits)s\%(stub_name)s"
InstallDirRegKey HKLM "Software\%(regname)s" "Install_Dir"
RequestExecutionLevel admin
SetCompressor bzip2

; Icons

%(icon_fragment)s

; Pages

Page directory
Page components
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles


; Installer sections

Section "Install %(display_name)s" SecBundleTree
    SetOutPath $INSTDIR
    SetShellVarContext all
    SectionIn RO

    ; Bit brutal, but it makes upgrades cleaner.
    RMDIR /r "$INSTDIR"

    ; Install the bundle tree
    File /r %(stub_name)s\*.*

    ; Uninstall registry information
    WriteRegStr HKLM "${UNINST_KEY}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "${UNINST_KEY}" "DisplayName" "%(display_name)s"
    WriteRegStr HKLM "${UNINST_KEY}" "UninstallString" \
        "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "${UNINST_KEY}" "QuietUninstallString" \
        "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "${UNINST_KEY}" "DisplayIcon" \
        "$\"$INSTDIR\%(icons_subdir)s\%(icon)s.ico$\""
    WriteRegStr HKLM "${UNINST_KEY}" "Publisher" "%(publisher)s"
    WriteRegStr HKLM "${UNINST_KEY}" "URLInfoAbout" "%(url)s"
    WriteRegStr HKLM "${UNINST_KEY}" "DisplayVersion" "%(version)s"
    WriteRegDWORD HKLM "${UNINST_KEY}" "VersionMajor" %(version_major)s
    WriteRegDWORD HKLM "${UNINST_KEY}" "VersionMinor" %(version_minor)s
    WriteRegDWORD HKLM "${UNINST_KEY}" "NoModify" 1
    WriteRegDWORD HKLM "${UNINST_KEY}" "NoRepair" 1
    WriteRegDWORD HKLM "${UNINST_KEY}" "EstimatedSize" "%(bundle_size)d"
    WriteRegStr HKLM "${UNINST_KEY}" "Comments" "%(description)s"

    ; The uninstaller itself
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; Write the install path into the registry
    WriteRegStr HKLM "Software\%(regname)s" "Install_Dir" "$INSTDIR"
SectionEnd

Section "Install shortcuts" SecShortcuts
    setOutPath $INSTDIR
    SetShellVarContext all
    %(launcher_install_fragments)s
SectionEnd

%(launcher_assoc_fragments)s

Section "Run post-install script" SecPostInst
    setOutPath $INSTDIR
    SetShellVarContext all
    SectionIn RO
    ExecWait '"$INSTDIR\%(scripts_subdir)s\postinst.cmd" "$SMPROGRAMS"'
SectionEnd

; Uninstall sections

Section "un.InstallBundleTree"
    SetShellVarContext all
    SectionIn RO
    DeleteRegKey HKLM "${UNINST_KEY}"
    DeleteRegKey HKLM "Software\%(regname)s"
    RMDIR /r "$INSTDIR"
SectionEnd

%(launcher_unassoc_fragments)s

Section "un.InstallShortcuts"
    setOutPath $INSTDIR
    SetShellVarContext all
    SectionIn RO
    %(launcher_uninstall_fragments)s
SectionEnd
