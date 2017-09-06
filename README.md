py-findlib
==========

 &nbsp;
 
 &nbsp;


:warning: :warning: :warning: :warning: :warning: :warning: :warning: :warning:
:warning: :warning: :warning: :warning: :warning: :warning: :warning: :warning:
:warning: :warning: :warning: :warning: :warning: :warning: :warning: :warning:

:warning: :warning: :warning: :warning: :warning: :warning: :warning: :warning:
:warning: :warning: :warning: :warning: :warning: :warning: :warning: :warning:
:warning: :warning: :warning: :warning: :warning: :warning: :warning: :warning:

!!! WARNING !!!
=========

As of September 2017, this project is deprecated.


 
 :warning: :warning: :warning: :warning: :warning: :warning: :warning: :warning:
 :warning: :warning: :warning: :warning: :warning: :warning: :warning: :warning:
 :warning: :warning: :warning: :warning: :warning: :warning: :warning: :warning:

:warning: :warning: :warning: :warning: :warning: :warning: :warning: :warning:
:warning: :warning: :warning: :warning: :warning: :warning: :warning: :warning:
:warning: :warning: :warning: :warning: :warning: :warning: :warning: :warning:
 
 &nbsp;
 
 &nbsp;
 
 &nbsp;
 
 &nbsp;

A module for finding programs and libraries with Python 2 & 3

1. Works on BeOS, BSD, Cygwin, Linux, OS X, Solaris, and  Windows.
2. Finds libraries with dpkg, rpm, pacman, slack packages, portage, pkg_info, mac ports, pkg-config, and the file system.
3. Finds shared libraries, static libraries, and header files.
4. Finds program paths.
5. Recursively expands environmental variables.
6. Runs commands and gets output.


Finding libraries
-----
    from findlib import findlib

    # Find a shared library
    libs = findlib.get_shared_library('libpcre', 'ver >= (8, 31)')
    print(libs)

    # Find a static library
    libs = findlib.get_static_library('libpcre', 'ver.major == 8')
    print(libs)

    # Find a header file
    libs = findlib.get_header_file('libpcre', 'ver.major == 8')
    print(libs)


Running programs
-----
    from findlib import findlib

    # Print to stdout
    findlib.run_print('uptime')

    # Or return stdout to variable
    result = findlib.run_and_get_stdout('uptime')
    print(result)


Finding program paths
-----
    from findlib import findlib

    # Find the full path of gcc
    result = findlib.program_paths('gcc')
    print(result)


Expanding environmental variables
-----
    from findlib import findlib

    # Recursively expand an environmental variable
    result = findlib.expand_envs('$PATH')
    print(result)


Bugs and Corrections
-----

Please report a Bug if you suspect any of this information is wrong.


