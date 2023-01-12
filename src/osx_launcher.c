/*
 * Written by Jaime Rodriguez-Guerra, 2022 Nov
 *
 * A small C program to launch shell scripts on macOS.
 * This allows us to work nicely with the permission system
 * and other security issues in macOS.
 *
 * It expects an executable file next to itself, suffixed
 * with `-script`. The file is execv'd and passed argv[1:].
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syslimits.h>
#include <sys/wait.h>
#include <unistd.h>
#include <mach-o/dyld.h>

int main(int argc, char **argv) {
    int status;
    pid_t pid;

    // 1. Get path to shell script; should be next to the compiled binary
    // Allocate the string buffer and ask _NSGetExecutablePath()
    // to fill it with the executable path
    uint32_t bufsize = PATH_MAX;
    char scriptPath[PATH_MAX + 1];
    if (_NSGetExecutablePath(scriptPath, &bufsize) != 0) {
        fprintf(stderr, "ERROR: Could not find executable path.");
        return 127;
    }
    // the path to the script is the same path + "-script"; 7 characters
    const char suffix[] = "-script";
    strcat(scriptPath, suffix);

    // 2. Build arguments vector from argv, skipping argv[0]
    char* args[argc + 2];
    args[0] = scriptPath;
    for(int i = 0; i <= argc; i++) {
        if (i > 0) {
            args[i] = argv[i];
        }
    }

    // 3. Fork process
    pid = fork();
    if (pid == 0) {
        // This is the child process.  Execute the shell command.
        execv(scriptPath, args);
        _exit(127); // This should never be reached.
    }
    else if (pid < 0) {
        // The fork failed.  Report failure.
        status = EXIT_FAILURE;
    }
    else {
        // This is the parent process.  Wait for the child to complete.
        if (waitpid(pid, &status, 0) != pid) {
            // waitpid failed
            status = EXIT_FAILURE;
        }
        else {
            if (WIFEXITED(status)) {
                // program terminated normally
                status = WEXITSTATUS(status);
                if (status == 127) {
                    fprintf(stderr, "ERROR: Could not run or find '%s'\n", scriptPath);
                }
            }
            else {
                status = EXIT_FAILURE;
            }
        }
    }
    return status;
}
