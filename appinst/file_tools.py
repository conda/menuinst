# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.


"""
These are tools used to modify files at install time. Alternatively, these tools
can be used any time after the install is complete to refresh the files, such as if
the install dir is moved and rpaths need to be changed.
"""

import sys
import os
import glob
import re
import subprocess


def fix_easy_install_script(filename, verbose=0, dryrun=False):
    if os.path.islink(filename):
        return

    # Update any broken python scripts to use the current python executable.
    # Note that on OS X, scripts may reference a python executable that is not
    # all lowercase.
    file = open(filename, "r")
    script_exec_line = file.readline()
    if script_exec_line[:2] == "#!":
        executable = script_exec_line[2:].split()[0]
        executable_lower = executable.lower()
        executable_stripped = executable_lower.strip(os.sep)
        executable_split = executable_stripped.split(os.sep)
        if not os.path.exists(executable) and \
            executable_split[-1].startswith('python'):
            script_exec_line = "#!%s%s" % (sys.executable, os.linesep)
            file_contents = script_exec_line + file.read()
            file.close()

            if dryrun:
                print 'Overwriting "%s" with content:\n%s\n\n' % (filename,
                    file_contents)
            else:
                file = open(filename, "w")
                file.write(file_contents)
                if verbose > 0:
                    print "\tUpdated %s" % filename

    file.close()

    return


def fix_easy_install_scripts_in_directory(path, verbose=0, dryrun=False):
     if not os.path.exists(path):
         raise ValueError("path does not exist: '%s'", path)
     for filename in os.listdir(path):
         file_path = os.path.join(path, filename)
         try:
             fix_easy_install_script(file_path, verbose, dryrun)
         except OSError, ex:
             print >> stderr, 'error fixing path to python in file: %s' % file_path

     return


def fix_easy_install_scripts_from_tar(listing_file_path, untarred_dir):
    """ Give a file containing the results of running 'tar -tzf tarfile',
        fix the paths for all of the files. This is to be used when a tar
        file is untarred in / or some other dir where not every python
        script should have its python execuable line overridden
    """
    file = open(listing_file_path)
    for line in file.readlines():
        if line.startswith('bin/'):
            filename = os.path.join(untarred_dir, line.rstrip())
            if not os.path.isdir(filename):
                fix_easy_install_script(filename)

    return


def recompile_pyc_files():
    import compileall
    site_packages_dir = os.path.join(os.path.dirname(os.__file__), 'site-packages')
    print "INFO: recompiling all python modules"
    compileall.compile_dir(site_packages_dir, force=True, quiet=True)

    return


def _chrpath_list(filename):
    try:
        import chrpath
        chrpath_exe = os.path.join( os.path.dirname( chrpath.__file__ ), "chrpath" )
    except ImportError:
        print >> sys.stderr, "ERROR: chrpath egg is not installed, you may need to add " \
              "%s to your LD_LIBRARY_PATH" % new_rpath
        sys.exit(1)

    #
    # Get the current RPATH
    #
    stdin, stdout, stderr = os.popen3( "%s -l %s" % (chrpath_exe, filename))
    output = stdout.read()
    if( not( stdout.close() is None ) ) :
        stdin.close()
        stderr.close()
        return None

    stdin.close()
    stderr.close()

    return re.split( ": RPATH=", output )[-1].strip()


def _chrpath_replace(filename, new_rpath):
    try:
        import chrpath
        chrpath_exe = os.path.join( os.path.dirname( chrpath.__file__ ), "chrpath" )
    except ImportError:
        print >> sys.stderr, "ERROR: chrpath egg is not installed, you may need to add " \
              "%s to your LD_LIBRARY_PATH" % new_rpath
        sys.exit(1)

    retcode = subprocess.call([chrpath_exe, '-r', new_rpath, filename], stdout=open('/dev/null'))
    if( retcode != 0 ) :
        print >> sys.stderr, "Error: could not change RPATH in: %s" % filename
        return False

    return True


def relocate_rpath(libdir, new_path, old_path, verbose=0):
    #
    # Walk to the libdir and replace the placeholder LD_RUN_PATH (/xxxxxxxxx/...)
    # with the new_rpath
    #
    for so in glob.glob( os.path.join( libdir, "*" ) ) :

        orig_rpath = _chrpath_list(so)
        if orig_rpath is None:
            continue

        match = re.search( ".*(%s).*" % old_path.replace('/', '\\/'), orig_rpath )

        if match is None:
            if verbose > 0:
                print >> sys.stderr, "Warning: %s does not contain '%s' as part of its RPATH" %\
                    (so, old_path)
            continue

        start, end = match.span(1)
        new_rpath = orig_rpath[:start] + new_path + orig_rpath[end:]

        _chrpath_replace(so, new_rpath)

    return


def change_rpath(libdir, new_rpath):
    """ Iterates through all the shared libraries in 'libdir', replacing
        the rpath with 'new_rpath'
    """
    #
    # Walk to the libdir and replace the placeholder LD_RUN_PATH (/xxxxxxxxx/...)
    # with the new_rpath
    #
    for so in glob.glob( os.path.join( libdir, "*.so" ) ) :

        orig_rpath = _chrpath_list(so)
        if orig_rpath is None:
            continue

        totallen = len( orig_rpath )

        #
        # Check for a placeholder
        #
        match = re.search( "/[x/]+", orig_rpath )

        if( match is None ) :
            print >> sys.stderr, "Error: %s has no placeholder for RPATH additions." % so
            continue

        (start, end) = match.span(0)
        orig_placeholder = orig_rpath[start:end]
        span = end - start

        #
        # Add a path sep and the remainder of the placeholder string if placeholder
        # is longer than the lib dir being inserted
        #
        if( span > len(new_rpath) ) :
            rpath_insert = new_rpath + os.pathsep
            rpstart = len( rpath_insert ) - 1
            for i in range( rpstart, span ) :
                rpath_insert += orig_placeholder[i - rpstart]
        else :
            rpath_insert = new_rpath

        #
        # Replace the placeholder with the new rpath
        #
        new_rpath = ""
        span_range = range( start, end+1 )
        for i in range( len( orig_rpath ) ) :
            if( i in span_range ) :
                new_rpath += rpath_insert[i - start]
            else :
                new_rpath += orig_rpath[i]

        #
        # Check that the new rpath fits in the space
        #
        if( len( new_rpath ) > totallen ) :
            print >> sys.stderr,"New RPATH: %s is too long for space allocated in library: %s!" %\
                  (new_rpath, so)
            continue

        _chrpath_replace(so, new_rpath)


    return

