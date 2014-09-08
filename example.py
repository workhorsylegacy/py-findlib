

import findlib


print('Looking for libpcre shared library ...')
libs = findlib.get_shared_library('libpcre', 'ver >= (8, 31)')
print('    {0}'.format(libs))

print('Looking for libpcre static library ...')
libs = findlib.get_static_library('libpcre', 'ver.major == 8')
print('    {0}'.format(libs))

print('Looking for libpcre header file ...')
libs = findlib.get_header_file('libpcre', 'ver.major == 8')
print('    {0}'.format(libs))


# Print to stdout
findlib.run_print('uptime')

# Or return stdout to variable
result = findlib.run_and_get_stdout('uptime')
print(result)

# Find the full path of gcc
result = findlib.program_paths('gcc')
print(result)


# Recursively expand an environmental variable
result = findlib.expand_envs('$PATH')
print(result)





