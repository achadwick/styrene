@ECHO off

REM Runs all the post_install scriptlets using MSYS2 bash.
REM Usage: postinst.cmd SMPROGRAMS
REM This script should only be called by the installer .exe.

REM This file is dedicated into the public domain, CC0 v1.0.
REM https://creativecommons.org/publicdomain/zero/1.0/

SETLOCAL

CD %~dp0
CD ..
PATH "%cd%\usr\bin"
SET MSYSTEM=MSYS2
usr\bin\bash --login -c ". /{scripts_subdir}/{postinst_sh} \"$@\"" -- %*

REM Post-install fragments from the launchers follow...
{launcher_cmd_fragments}
