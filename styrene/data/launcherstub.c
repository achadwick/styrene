/*
 * Launcher stub - calls a bash script with its args, without a window.
 * Sometimes they're launched directly, if the command line is simple
 * enough for Windows.
 * One of these is compiled with an icon for each converted .desktop file.
 *
 * This source code, and any executable code generated from it,
 * is dedicated into the public domain, CC0 v1.0
 * https://creativecommons.org/publicdomain/zero/1.0/
 * In other words, feel free to redistribute the launcher .exes under
 * your own license ☺
 */

#ifndef UNICODE
#define UNICODE
#endif

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <Shellapi.h>
#include <stdio.h>
#include <wchar.h>
#include <stdlib.h>
#include "config.h"


// Consts {{{1

static const WCHAR BASH_RELPATH[] = L"usr\\bin\\bash.exe";

static const WCHAR CYGWIN_STYLE_MSYSTEM[] = L"MSYS2";
static const WCHAR CYGWIN_STYLE_BIN_SUBPATH[] = L"\\usr\\bin";

#if defined(_WIN64)
static const WCHAR NATIVE_MSYSTEM[] = L"MINGW64";
static const WCHAR NATIVE_BIN_SUBPATH[] = L"\\mingw64\\bin";
#elif defined(_WIN32)
static const WCHAR NATIVE_MSYSTEM[] = L"MINGW32";
static const WCHAR NATIVE_BIN_SUBPATH[] = L"\\mingw32\\bin";
#else
#error "_WIN64 or _WIN32 is required." 
#endif

 
// Environment init {{{1


BOOL
init_cygwin_style_env (const WCHAR *exe_dir)
{
    if (! SetEnvironmentVariableW(L"MSYSTEM", CYGWIN_STYLE_MSYSTEM)) {
        printf("SetEnvironmentVariableW() failed.\n");
        return FALSE;
    }
    /* Probably better to use the user's HOME
    if (! SetEnvironmentVariableW(L"HOME", L"/")) {
        printf("SetEnvironmentVariableW() failed.\n");
        return FALSE;
    }
    */

    int len = wcslen(exe_dir) + wcslen(CYGWIN_STYLE_BIN_SUBPATH) + 1;
    WCHAR *newpath = malloc(len * sizeof(WCHAR));
    if (! newpath) {
        printf("malloc() failed.\n");
        return FALSE;
    }
    newpath[0] = L'\0';
    wcscat(newpath, exe_dir);
    wcscat(newpath, CYGWIN_STYLE_BIN_SUBPATH);
    if (! SetEnvironmentVariableW(L"PATH", newpath)) {
        printf("SetEnvironmentVariableW() failed.\n");
        return FALSE;
    }
    free(newpath);

    return TRUE;
}


BOOL
init_native_env (const WCHAR *exe_dir)
{
    if (! SetEnvironmentVariableW(L"MSYSTEM", NATIVE_MSYSTEM)) {
        printf("SetEnvironmentVariableW() failed.\n");
        return FALSE;
    }

    /* Probably better to use the user's HOME
    if (! SetEnvironmentVariableW(L"HOME", L"/")) {
        printf("SetEnvironmentVariableW() failed.\n");
        return FALSE;
    }
    */

    int len = wcslen(exe_dir) + wcslen(CYGWIN_STYLE_BIN_SUBPATH)
        + 1   // semicolon
        + wcslen(exe_dir) + wcslen(NATIVE_BIN_SUBPATH)
        + 1   // NUL
        ;
    WCHAR *newpath = malloc(len * sizeof(WCHAR));
    if (! newpath) {
        printf("malloc() failed.\n");
        return FALSE;
    }
    newpath[0] = L'\0';
    wcscat(newpath, exe_dir);
    wcscat(newpath, NATIVE_BIN_SUBPATH);
    wcscat(newpath, L";");
    wcscat(newpath, exe_dir);
    wcscat(newpath, CYGWIN_STYLE_BIN_SUBPATH);
    if (! SetEnvironmentVariableW(L"PATH", newpath)) {
        printf("SetEnvironmentVariableW() failed.\n");
        return FALSE;
    }
    free(newpath);

    return TRUE;
}


// Utility funcs {{{1

void
show_error_message_box (LPCTSTR msg)
{
    MessageBox(NULL, msg, L"Error", MB_ICONERROR|MB_OK);
}


// Main code flow {{{1


/*
 * True if the location of the bundle has not changed since the last
 * time the the postinst.cmd script ran.
 */

BOOL
bundle_is_configured(const WCHAR *exe_dir)
{
    BOOL configured = TRUE;
    FILE *fp = _wfopen(LAUNCHER_LOCATION_STATE_FILE, L"r, ccs=UTF-8");
    if (! fp) {
        configured = FALSE;
    }
    else {
        // Read a path from the file
        WCHAR read_buf[MAX_PATH + 1];
        ZeroMemory(&read_buf, sizeof(read_buf));
        size_t nread = fread(read_buf, sizeof(WCHAR), MAX_PATH, fp);
        if (ferror(fp)) {
            show_error_message_box(L"fread() failed.");
            fclose(fp);
            _exit(2);
        }
        if (! feof(fp)) {
            show_error_message_box(L"fread() not at EOF, "
                                   L"path name in file is too long.");
            fclose(fp);
            _exit(2);
        }
        if (nread > MAX_PATH) {
            show_error_message_box(L"fread() read too much data");
            fclose(fp);
            _exit(2);
        }

        // Append a NUL character for wcscmp().
        read_buf[nread] = L'\0';

        if ((nread > 0) && (wcscmp(read_buf, exe_dir) != 0)) {
            configured = FALSE;
        }

        // NOTE: an empty state file means "accept this config".
        //
        // This covers the case when the installer exe created the state
        // file without having to worry about the encoding its shell was
        // using back then.

        fclose(fp);
    }
    return configured;
}


void
run_postinst_configuration_script(const WCHAR *exe_dir)
{
    // Run the post-install configuration script in an MSYS environment.
    // This configures all the packages which were installed earlier to
    // run correctly with the current path to the bundle.

    if (! init_cygwin_style_env(exe_dir)) {
        show_error_message_box(L"Cannot set up Cygwin-style environment.");
        _exit(2);
    }

    STARTUPINFO si;
    PROCESS_INFORMATION pi;

    ZeroMemory(&si, sizeof(si));
    ZeroMemory(&pi, sizeof(pi));
    GetStartupInfo(&si);

    si.wShowWindow = SW_NORMAL;
    si.lpTitle = LAUNCHER_POSTINST;

    if (! CreateProcessW(
        BASH_RELPATH,
        L"/usr/bin/bash --login " LAUNCHER_POSTINST,
        NULL, NULL,   /* process and thread attrs */
        TRUE,   /* don't inherit handles (stdout, stderr etc.) */
        0,    /* Process creation flags */
        NULL,   /* Use parent's environment block... */
        NULL,    /* ... and starting dir. */
        &si,
        &pi)
    ) {
        show_error_message_box(L"Unable to launch bash.exe");
        _exit(2);
    }

    // Wait till bash exits before continuing.

    WaitForSingleObject(pi.hProcess, INFINITE);

    // Record where the config was last run.

    FILE *fp = _wfopen(LAUNCHER_LOCATION_STATE_FILE, L"w, ccs=UTF-8");
    if (! fp) {
        show_error_message_box(L"Cannot update location state file!");
        _exit(2);
    }
    size_t nwritten = fwrite(exe_dir, sizeof(WCHAR), wcslen(exe_dir), fp);
    if (ferror(fp) || (nwritten!=wcslen(exe_dir))) {
        fclose(fp);
        show_error_message_box(L"fwrite() failed");
        _wunlink(LAUNCHER_LOCATION_STATE_FILE);
        _exit(2);
    }
    fflush(fp);
    fclose(fp);
}


/*
 * Quote a filename argument for CreateProcessW().
 * The return value is a newly-allocated zero-WCHAR-terminated
 * string which must be freed after use.
 */

WCHAR *
new_quoted_filename (WCHAR *s)
{
    int rlen = 0;
    BOOL contains_spaces = FALSE;
    for (int i=0; i<wcslen(s); ++i) {
        if (s[i] == L'"') {
            show_error_message_box(
                L"Filename parameter contains double quotes. What the hell."
                // Aren't they forbidden in Windows file names?
            );
            _exit(2);
        }
        else if (s[i] == L'\040' /* space */) {
            contains_spaces = TRUE;
        }
        rlen++;
    }

    if (contains_spaces) {
        rlen += 2;
    }
    rlen += 1;
    int rbytes = rlen * sizeof(WCHAR);
    WCHAR *r = malloc(rbytes);
    if (! r) {
        show_error_message_box(L"malloc() failed.");
        _exit(4);
    }
    ZeroMemory(r, rbytes);

    if (contains_spaces) {
        wcscat(r, L"\"");
    }
    wcscat(r, s);
    if (contains_spaces) {
        wcscat(r, L"\"");
    }

    return r;
}




/*
 * Expand a single template argument token, if needed.
 * The result may be the template argument, or NULL,
 * or a newly allocated string which will need to be free()d after use.
 */

WCHAR *
expand_arg_token (WCHAR *tmpl_arg)
{
    WCHAR *result = tmpl_arg;

    if ((wcscmp(tmpl_arg, L"%f")==0) || (wcscmp(tmpl_arg, L"%u")==0)) {
        result = NULL;
        if (__argc > 1) {
            result = new_quoted_filename(__wargv[1]);
        }
    }
    else if ((wcscmp(tmpl_arg, L"%F")==0) || (wcscmp(tmpl_arg, L"%U")==0)) {
        result = NULL;
        for (int i = 1; i < __argc; ++i) {
            WCHAR *filename = new_quoted_filename(__wargv[i]);

            int result_len = 0;
            if (i > 1) {
                result_len += wcslen(result);
                result_len += 1; // space
            }
            result_len += wcslen(filename);
            result_len += 1;  // trailing NULL

            result = realloc(result, result_len * sizeof(WCHAR));
            if (! result) {
                show_error_message_box(L"realloc() failed.");
                _exit(4);
            }
            if (i == 1) {
                result[0] = L'\000';
            }
            else {
                wcscat(result, L"\040");  // space
            }
            wcscat(result, filename);
            free(filename);
        }
    }

    return result;
}


/*
 * Get the command line to use.
 * Returns a newly allocated command line, which must be free()d
 * after use.
 */

WCHAR *
get_command_line(PWSTR pCmdLine)
{
    WCHAR *helper_cmd_prefix = NULL;
    if (LAUNCHER_USE_TERMINAL) {
        helper_cmd_prefix = L"/usr/bin/bash --login -c '"
            L"echo \"Running $1...\"; \"$@\";"
            L"echo \"$1 exited with status $?.\";"
            L"echo \"Press return to close this window.\";"
            L"read"
            L"' --";
    }
    else {
        helper_cmd_prefix = L"/usr/bin/bash --login -c "
            L"'exec \"$@\"' "
            L"--";
    }

    int cmd_len = 0;
    WCHAR *cmd = NULL;
    WCHAR *cmd_prefix = NULL;
    WCHAR **tmpl_arg = (WCHAR **) LAUNCHER_CMDLINE_TEMPLATE;

    if (LAUNCHER_USE_HELPER) {
        cmd_prefix = helper_cmd_prefix;
    }
    else {
        cmd_prefix = (WCHAR *) LAUNCHER_RESOLVED_EXE;
        tmpl_arg ++;
    }
    cmd_len = wcslen(cmd_prefix) + 1 + MAX_PATH;  // avoid some realloc()s...

    cmd = malloc(cmd_len * sizeof(WCHAR));
    if (! cmd) {
        show_error_message_box(L"malloc() failed.");
        _exit(4);
    }

    cmd[0] = L'\000';
    wcscat(cmd, cmd_prefix);

    // Concatenate the remaining args' individual expansions,
    // separated by spaces.
    while (*tmpl_arg != NULL) {
        WCHAR *arg = expand_arg_token(*tmpl_arg);
        if (arg != NULL) {
            int new_cmd_len = wcslen(cmd) + 1 + wcslen(arg);
            if (new_cmd_len > cmd_len) {
                cmd_len = new_cmd_len;
                cmd = realloc(cmd, cmd_len * sizeof(WCHAR));
                if (! cmd) {
                    show_error_message_box(L"realloc() failed.");
                    _exit(4);
                }
            }
            wcscat(cmd, L" ");
            wcscat(cmd, arg);
            if (arg != *tmpl_arg) {
                free(arg);
            }
        }
        tmpl_arg ++;
    }

    return cmd;
}


/*
 * Graphical entry function.
 */

int WINAPI
wWinMain (HINSTANCE hInstance, HINSTANCE hPrevInstance,
          PWSTR pCmdLine, int nCmdShow)
{
    // Change to the directory containing this launcher.

    WCHAR exe_dir[MAX_PATH + 1];
    ZeroMemory(&exe_dir, sizeof(exe_dir));
    exe_dir[0] = L'\0';
    if (! GetModuleFileNameW(NULL, exe_dir, MAX_PATH)) {
        show_error_message_box(L"GetModuleFileNameW() failed.");
        return 1;
    }
    WCHAR *backslash_ptr = wcsrchr(exe_dir, L'\\');
    if (! backslash_ptr) {
        show_error_message_box(
            L"GetModuleFileNameW() did not return "
            L"a backslash-separated path."
        );
        return 1;
    }
    *backslash_ptr = L'\0';
    if (! SetCurrentDirectoryW(exe_dir)) {
        show_error_message_box(L"SetCurrentDirectoryW() failed.");
        return 2;
    }

    // Adapt the installation to a new runtime location, if needed.

    BOOL configured = bundle_is_configured(exe_dir);
    if (! configured) {
        run_postinst_configuration_script(exe_dir);
    }

    // Next subprocess starts the MinGW-compiled native Win32/Win64
    // software defined in the .desktop file corresponding to this
    // launcher. First set up the environment.

    if (! init_native_env(exe_dir)) {
        show_error_message_box(L"Cannot set up native WinAPI environment.");
        return 3;
    }

    // Launch our canned shell command in as hidden as way as possible.
    // Try and reuse as much as we can of this process's startup info,
    // although bash is free to do its own thing in launching the
    // .desktop file's target.

    STARTUPINFO si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    ZeroMemory(&pi, sizeof(pi));

    DWORD create_flags = 0;
    GetStartupInfo(&si);
    if (! LAUNCHER_USE_TERMINAL) {
        si.wShowWindow = SW_HIDE;
        create_flags = DETACHED_PROCESS;
    }
    else {
        si.wShowWindow = SW_NORMAL;
        create_flags = 0;
    }
    si.dwFlags = STARTF_TITLEISAPPID
        | STARTF_FORCEONFEEDBACK 
        | STARTF_USESHOWWINDOW;
    si.lpTitle = (LPWSTR) LAUNCHER_APP_ID;
    // STARTF_TITLEISAPPID doesn't have have any effect if bash is
    // to be launched, but it provides a more GNOME-like experience if
    // the thing being launched is a native .exe.

    WCHAR *cmdline = get_command_line(pCmdLine);
    if (! CreateProcessW(
        (LAUNCHER_USE_HELPER ? BASH_RELPATH : LAUNCHER_RESOLVED_EXE),
        cmdline,
        NULL, NULL,   /* process and thread attrs */
        TRUE,   /* inherit handles (stdout, stderr etc.) */
        create_flags,
        NULL,
        NULL,
        &si,
        &pi)
    ) {
        show_error_message_box(L"Unable to create process");
        return 99;
    }
    free(cmdline);

    return 0;
}

// Compiling with -mwindows allows a *windows* application to work
// without creating a console window.  However using the MinGW-w64 libs'
// exec() functions or the ones from <process.h> still creates a window.
// Gonna have to go full WinAPI here, via CreateProcess().
