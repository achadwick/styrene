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


// Consts {{{1

static const WCHAR LOCATION_STATE_FILE[] = LAUNCHER_LOCATION_STATE_FILE;
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
    FILE *fp = _wfopen(LOCATION_STATE_FILE, L"r, ccs=UTF-8");
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

    FILE *fp = _wfopen(LOCATION_STATE_FILE, L"w, ccs=UTF-8");
    if (! fp) {
        show_error_message_box(L"Cannot update location state file!");
        _exit(2);
    }
    size_t nwritten = fwrite(exe_dir, sizeof(WCHAR), wcslen(exe_dir), fp);
    if (ferror(fp) || (nwritten!=wcslen(exe_dir))) {
        fclose(fp);
        show_error_message_box(L"fwrite() failed");
        _wunlink(LOCATION_STATE_FILE);
        _exit(2);
    }
    fflush(fp);
    fclose(fp);
}


/*
 * Get the command line to use.
 * Returns a newly allocated command line, which must be free()d
 * after use.
 */

WCHAR *
get_command_line(PWSTR pCmdLine)
{
#if LAUNCHER_USE_HELPER > 0
    // The launcher has a complex enough command line that it needs the
    // helper bash script.
    WCHAR cmd_base[] = L"/usr/bin/bash --login "
        L"-c 'exec " LAUNCHER_HELPER_SCRIPT L" \"$@\"' --";
    int cmdlen = wcslen(cmd_base) + 1 /*space*/
               + wcslen(pCmdLine) + 1 /*NUL?*/;
    WCHAR *cmdline = malloc(cmdlen * sizeof(WCHAR));
    if (! cmdline) {
        show_error_message_box(L"malloc() failed.");
        _exit(4);
    }
    cmdline[0] = '\0';
    wcscat(cmdline, cmd_base);
    wcscat(cmdline, L" ");
    wcscat(cmdline, pCmdLine);
#else
    // We know that it's "simple", meaning no args (for now).
    // There may be "single arg" and "multi-arg" kinds of "simple" in
    // future. I guess we'll cat on a requoted __argv and __argc then.
    WCHAR *cmdline = malloc(sizeof(WCHAR) * (1+wcslen(LAUNCHER_RESOLVED_EXE)));
    if (! cmdline) {
        show_error_message_box(L"malloc() failed.");
        _exit(4);
    }
    cmdline[0] = '\0';
    wcscat(cmdline, LAUNCHER_RESOLVED_EXE);
    // no args yet.
#endif
    return cmdline;
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

    /*
    // In case we need to test that the args the exe sees are those the 
    // shell will get. Is passing through pCmdLine unquoted enough?
    */
    //for (int i=0; i < __argc; i++) {
    //    show_error_message_box(__wargv[i]);
    //}
    /*
    // Can't use CommandLineToArgvW() for this.
    // It's too weird and buggy.
    */

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
    si.lpTitle = LAUNCHER_APP_ID;
    // Unsure if that'll have any effect.
    // It's the process that bash launches that matters.
    // Maybe its exec is smart enough to inherit si like we do?
    // Update: seems it isn't. OK. But we *could* launch simple
    // cmdlines for real .exe files here ourselves, and that 
    // might allow some STARTF_TITLEISAPPID cleverness for prepackaged
    // stuff.

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
