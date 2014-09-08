py-findlib
==========

Find libraries and programs in python


Finding libraries
-----

    import findlib

    # Find a shared library
    libs = findlib.get_shared_library('libpcre', 'ver.major == 8')
    print(libs)

    # Find a static library
    libs = findlib.get_static_library('libpcre', 'ver.major == 8')
    print(libs)

    # Find a header file
    libs = findlib.get_header_file('libpcre', 'ver.major == 8')
    print(libs)


Running programs
-----
    # Print to stdout
    findlib.run_print('uptime')

    # Or return stdout to variable
    result = findlib.run_and_get_stdout('uptime')
    print(result)


Finding program paths
-----
    # Find the full path of gcc
    result = findlib.program_paths('gcc')
    print(result)


Expanding environmental variables
-----
    # Recursively expand an environmental variable
    result = findlib.expand_envs('$PATH')
    print(result)


Bugs and Corrections
-----

Please report a Bug if you suspect any of this information is wrong.


