# NSIS installer template, processed by bundle.py

!define UNINST_KEY \
    "Software\Microsoft\Windows\CurrentVersion\Uninstall\%(regname)s"

Name "%(display_name)s"
OutFile "%(output_file_name)s"
InstallDir "$PROGRAMFILES%(bits)s\%(stub_name)s"

RequestExecutionLevel admin

Page Directory
Page InstFiles

%(icon_fragment)s

Section "Install"
    setOutPath $INSTDIR
    SetShellVarContext all

    # Bit brutal, but it makes upgrades cleaner.
    RMDIR /r "$INSTDIR"

    file /r %(stub_name)s\*.*
    writeUninstaller "$INSTDIR\uninstall.exe"

    # Uninstall registry information
    WriteRegStr HKLM "${UNINST_KEY}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "${UNINST_KEY}" "DisplayName" "%(display_name)s"
    WriteRegStr HKLM "${UNINST_KEY}" "UninstallString" \
        "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "${UNINST_KEY}" "QuietUninstallString" \
        "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "${UNINST_KEY}" "DisplayIcon" \
        "$\"$INSTDIR\%(icons_subdir)s\%(icon)s.ico$\""
    WriteRegStr HKLM "${UNINST_KEY}" "Publisher" "%(publisher)s"
    # WriteRegStr HKLM "${UNINST_KEY}" "HelpLink" "%(url)s"
    # WriteRegStr HKLM "${UNINST_KEY}" "URLUpdateInfo" "%(url)s"
    WriteRegStr HKLM "${UNINST_KEY}" "URLInfoAbout" "%(url)s"
    WriteRegStr HKLM "${UNINST_KEY}" "DisplayVersion" "%(version)s"
    WriteRegDWORD HKLM "${UNINST_KEY}" "VersionMajor" %(version_major)s
    WriteRegDWORD HKLM "${UNINST_KEY}" "VersionMinor" %(version_minor)s
    WriteRegDWORD HKLM "${UNINST_KEY}" "NoModify" 1
    WriteRegDWORD HKLM "${UNINST_KEY}" "NoRepair" 1
    WriteRegDWORD HKLM "${UNINST_KEY}" "EstimatedSize" "%(bundle_size)d"
    WriteRegStr HKLM "${UNINST_KEY}" "Comments" "%(description)s"

    # Install shortcuts etc.

    %(launcher_install_fragments)s

    # Run post_install scriptlets.
    # These must take place after the shortcut installation.

    ExecWait '"$INSTDIR\%(scripts_subdir)s\postinst.cmd" "$SMPROGRAMS"'
SectionEnd

Section "Uninstall"
    SetShellVarContext all
    DeleteRegKey HKLM "${UNINST_KEY}"
    RMDIR /r "$INSTDIR"
    %(launcher_uninstall_fragments)s
SectionEnd
