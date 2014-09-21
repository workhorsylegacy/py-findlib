#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2013-2014, Matthew Brennan Jones <matthew.brennan.jones@gmail.com>
# Py-findlib is for finding libraries and programs on most operating systems
# It uses a MIT style license
# It is hosted at: https://github.com/workhorsy/py-findlib
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.



import sys, os, re
import ast
import platform
import subprocess
from collections import namedtuple

import findlib_server

PY2 = sys.version_info[0] == 2

# Check if running on windows/os x
uname = platform.system().lower().strip()
is_windows = 'windows' in uname
is_osx = 'darwin' in  uname


def chomp(s):
	for sep in ['\r\n', '\n', '\r']:
		if s.endswith(sep):
			return s[:-len(sep)]

	return s

def before(s, n):
	i = s.find(n)
	if i == -1:
		return s
	else:
		return s[0 : i]

def before_last(s, n):
	i = s.rfind(n)
	if i == -1:
		return s
	else:
		return s[0 : i]

def after(s, n):
	i = s.find(n)
	if i == -1:
		return s
	else:
		return s[i+len(n) : ]

def between(s, l, r):
	return before(after(s, l), r)

def between_last(s, l, r):
	return before_last(after(s, l), r)


def _on_ok():
	pass

def _on_warn(message=None):
	pass

def _on_fail(message= None):
	pass

def _on_exit(message):
	pass

def _on_status(message):
	pass

def _ok_symbol():
	return 'ok'

def _warn_symbol():
	return 'warn'

def _fail_symbol():
	return 'fail'

class ProcessRunner(object):
	def __init__(self, command):
		if is_windows:
			# Remove starting ./
			if command.startswith('./'):
				command = command[2 :]
			# Replace ${BLAH} with %BLAH%
			command = command.replace('${', '%').replace('}', '%')

		self._command = command
		self._process = None
		self._return_code = None
		self._stdout = None
		self._stderr = None
		self._status = None

	def run(self):
		# Recursively expand all environmental variables
		env = {}
		for key, value in os.environ.items():
			env[key] = expand_envs(value)

		self._stdout = []
		self._stderr = []

		# Start the process and save the output
		self._process = subprocess.Popen(
			self._command, 
			stderr = subprocess.PIPE, 
			stdout = subprocess.PIPE, 
			shell = True, 
			env = env
		)

	def wait(self):
		# Wait for the process to actually exit
		self._process.wait()

		# Get the return code
		rc = self._process.returncode
		if hasattr(os, 'WIFEXITED') and os.WIFEXITED(rc):
			rc = os.WEXITSTATUS(rc)
		self._return_code = rc

		# Get strerr and stdout into byte strings
		self._stderr = b''.join(self._stderr)
		self._stdout = b''.join(self._stdout)

		# Convert strerr and stdout into unicode
		if PY2:
			self._stderr = unicode(self._stderr, 'UTF-8')
			self._stdout = unicode(self._stdout, 'UTF-8')
		else:
			self._stderr = str(self._stderr, 'UTF-8')
			self._stdout = str(self._stdout, 'UTF-8')

		# Chomp the terminating newline off the ends of output
		self._stdout = chomp(self._stdout)
		self._stderr = chomp(self._stderr)

		# :( Failure
		if self._return_code:
			self._status = _fail_symbol()
		else:
			# :\ Warning
			if len(self._stderr):
				self._status = _warn_symbol()
			# :) Success
			else:
				self._status = _ok_symbol()

	def get_is_done(self):
		# You have to poll a process to update the retval. Even if it has stopped already
		if self._process.returncode == None:
			self._process.poll()

		# Read the output from the buffer
		sout, serr = self._process.communicate()
		self._stdout.append(sout)
		self._stderr.append(serr)

		# Return true if there is a return code
		return self._process.returncode != None
	is_done = property(get_is_done)

	def get_is_success(self):
		self._require_wait()
		return self._status == _ok_symbol()
	is_success = property(get_is_success)

	def get_is_warning(self):
		self._require_wait()
		return self._status == _warn_symbol()
	is_warning = property(get_is_warning)

	def get_is_failure(self):
		self._require_wait()
		return self._status == _fail_symbol()
	is_failure = property(get_is_failure)

	def get_stderr(self):
		self._require_wait()
		return self._stderr
	stderr = property(get_stderr)

	def get_stdout(self):
		self._require_wait()
		return self._stdout
	stdout = property(get_stdout)

	def get_stdall(self):
		self._require_wait()
		return self._stdout + '\n' + self._stderr
	stdall = property(get_stdall)

	def _require_wait(self):
		if self._return_code == None:
			raise Exception("Wait needs to be called before any info on the process can be gotten.")

def run_print(command):
	_on_status("Running command")

	runner = ProcessRunner(command)
	runner.run()
	runner.is_done
	runner.wait()

	if runner.is_success or runner.is_warning:
		_on_ok()
		sys.stdout.write(command + '\n')
		sys.stdout.write(runner.stdall)
	elif runner.is_failure:
		_on_fail()
		sys.stdout.write(command + '\n')
		sys.stdout.write(runner.stdall)
		_on_exit('Failed to run command.')

def run_and_get_stdout(command):
	runner = ProcessRunner(command)
	runner.run()
	runner.is_done
	runner.wait()

	if runner.is_failure:
		return None
	else:
		return runner.stdout

def program_paths(*program_names):
	import glob
	paths = []
	exts = []
	if 'PATHEXT' in os.environ:
		exts = os.environ['PATHEXT'].split(os.pathsep)
	path = os.environ['PATH']

	# Each path
	for p in os.environ['PATH'].split(os.pathsep):
		# Each program name
		for program_name in program_names:
			full_name = os.path.join(p, program_name)
			full_names = glob.glob(full_name)

			# Each program name that exists in a path
			for name in full_names:
				# Save the path if it is executable
				if name and os.access(name, os.X_OK) and not os.path.isdir(name):
					paths.append(name)
				# Save the path if we found one with a common extension like .exe
				for e in exts:
					full_name_ext = name + e

					if os.access(full_name_ext, os.X_OK) and not os.path.isdir(full_name_ext):
						paths.append(full_name_ext)
	return paths

def expand_envs(string):
	while True:
		before = string
		string = os.path.expandvars(string)
		if before == string:
			return string

def is_safe_code(source_code):
	safe_nodes = (
		ast.Module, ast.Load, ast.Expr, ast.Attribute, ast.Name, 
		ast.Str, ast.Num, ast.BoolOp, 
		ast.Dict, ast.List, ast.Tuple, 
		ast.Store, ast.ListComp, ast.comprehension, 
		ast.Subscript, ast.Slice, ast.Index, 
		ast.BinOp, ast.UnaryOp, 
		ast.BitOr, ast.BitXor, ast.BitAnd, 
		ast.LShift, ast.RShift, 
		ast.Sub, ast.Add, ast.Div, ast.Mult, ast.Mod, ast.Pow, 
		ast.Eq, ast.NotEq, ast.And, ast.Or, ast.Not, 
		ast.Is, ast.IsNot, ast.In, ast.NotIn, 
		ast.Compare, ast.Gt, ast.GtE, ast.Lt, ast.LtE
	)

	# Make sure the code can be parsed
	tree = None
	try:
		tree = ast.parse(source_code)
	except SyntaxError:
		return False

	# Make sure each code node is in the white list
	for node in ast.walk(tree):
		if not isinstance(node, safe_nodes):
			print(type(node))
			return False

	return True

def version_string_to_tuple(version_string):
	# Get the version number
	Version = namedtuple('Version', 'major minor micro')
	major, minor, micro = 0, 0, 0
	try:
		version = version_string.split('.')
		major = int(version[0])
		minor = int(version[1])
		micro = int(version[2])
	except Exception as e:
		pass
	return Version(major, minor, micro)

def to_version_cb(version_str):
	black = {
		'AugAssign' : 'Operation with assignment', 
		'Assign' : 'Assignment', 
		'Lambda' : 'Lambda function', 
		'arguments' : 'Function argument', 
		'arg' : 'Argument', 
		'Param' : 'Function parameter', 
		'Call' : 'Function call', 
		'If' : 'If statement', 
		'While' : 'While loop', 
		'For' : 'For loop', 
		'Import' : 'Importing', 
		'ImportFrom' : 'Importing from', 
		'alias' : 'Aliase', 
		'ClassDef' : 'Class definition', 
		'Pass' : 'Pass statements', 
		'Assert' : 'Assert statement', 
		'Break' : 'Break statement', 
		'Continue' : 'Continue statement', 
		'Del' : 'Del statement', 
		'Delete' : 'Delete statement', 
		'ExceptHandler' : 'Exception handler', 
		'Raise' : 'Raise statement', 
		'Try' : 'Try block', 
		'TryExcept' : 'Try block', 
		'TryFinally' : 'Try finally block', 
		'Return' : 'Return statement', 
		'Yield' : 'Yield statement', 
		'With' : 'With statement', 
		'Global' : 'Global statement', 
		'Print' : 'Print statement', 
	}

	black_list = {}
	for k, v in black.items():
		if hasattr(ast, k):
			t = getattr(ast, k)
			black_list[t] = v

	# Make sure the code can be parsed
	tree = None
	parse_error = None
	try:
		tree = ast.parse(version_str)
	except SyntaxError as e:
		parse_error = str(e)
	if parse_error:
		_on_status('Building version string')
		_on_fail('Version string unparsable. "{0}", {1}'.format(version_str, parse_error))
		_on_exit('Fix version string and try again.')

	# Make sure each code node is not in the black list
	for node in ast.walk(tree):
		# Is in black list
		for k, v in black_list.items():
			if isinstance(node, k):
				_on_status('Building version string')
				_on_fail('{0} not allowed in version string. "{1}"'.format(v, version_str))
				_on_exit('Fix version string and try again.')

	code = "lambda ver: " + version_str
	version_cb = None
	# Make sure the code can be parsed into a lambda
	try:
		version_cb = eval(code, {})
		version_cb(version_string_to_tuple('(1, 9)'))
	except Exception as e:
		message = str(e).lstrip('global ')
		_on_status('Building version string')
		_on_fail('Invalid version string "{0}", {1}'.format(version_str, message))
		_on_exit('Fix version string and try again.')

	return version_cb

# Returns all the paths that libraries are installed in
def _get_all_library_paths():
	paths = ['/usr/lib', '/usr/local/lib',
			'/usr/include', '/usr/local/include']
	if not os.path.exists('/etc/ld.so.conf.d/'):
		return paths

	for file_name in os.listdir('/etc/ld.so.conf.d/'):
		f = open('/etc/ld.so.conf.d/' + file_name, 'r')
		for path in f.readlines():
			path = path.strip()
			if os.path.exists(path) and not path in paths:
				paths.append(path)

	return paths

def _get_best_match(names, desired):
	'''
	Will match files with this priority:
	1. Exact match
	2. Exact match different capitalization
	3. Matches start or end
	4. Matches start or end different capitalization
	'''

	# 1. Exact match
	for name in names:
		if name == desired:
			return name

	# 2. Exact match different capitalization
	for name in names:
		if name.lower() == desired.lower():
			return name

	# 3. Matches start or end
	for name in names:
		if name.startswith(desired) or name.endswith(desired):
			return name

	# 4. Matches start or end different capitalization
	for name in names:
		if name.lower().startswith(desired.lower()) or name.lower().endswith(desired.lower()):
			return name

	return None

def _get_matched_file_from_library_files(library_name, extension, library_files):
	'''
	Will match files with this priority:
	1. Exact match after last path separator
	2. Exact match different capitalization after last path separator
	3. Matches ending
	4. Matches ending with different capitalization
	'''
	library_name = library_name.lstrip('lib')

	# 1. Exact match after last path separator
	desired_name = '{0}{1}'.format(library_name, extension)
	for entry in library_files:
		file_name = os.path.basename(entry)
		if file_name == desired_name:
			return entry

	# 2. Exact match different capitalization after last path separator
	desired_name = '{0}{1}'.format(library_name, extension).lower()
	for entry in library_files:
		file_name = os.path.basename(entry).lower()
		if file_name == desired_name:
			return entry

	# 3. Matches ending
	desired_name = '{0}{1}'.format(library_name, extension)
	for entry in library_files:
		file_name = os.path.basename(entry)
		if file_name.endswith(desired_name):
			return entry

	# 4. Matches ending with different capitalization
	desired_name = '{0}{1}'.format(library_name, extension).lower()
	for entry in library_files:
		file_name = os.path.basename(entry).lower()
		if file_name.endswith(desired_name):
			return entry

	return None

# FIXME: Make it work with other packaging systems:
# http://en.wikipedia.org/wiki/List_of_software_package_management_systems
# Returns the full path of a library file or None
def _get_library_files(lib_name, version_str = None):
	files = []

	# Create a version_cb from the string
	version_cb = None
	if version_str:
		version_cb = to_version_cb(version_str)
	search_param = (version_str, lib_name)

	# If the query is cached, and none of the resulting files have 
	# changed, return the cache.
	cacher = None
	files = None
	try:
		cacher = findlib_server.CacheFileChangeDateClient()
		files = cacher.get_data(search_param)
		none_have_changed = True
		if files:
			for entry in files:
				response = cacher.has_file_changed(entry)
				has_changed = response['has_changed']
				if has_changed == True:
					none_have_changed = False

			if none_have_changed:
				return files
	except Exception as ex:
		pass

	# Try finding with dpkg
	if not files:
		files = _get_library_files_from_dpkg(lib_name, version_cb)

	# Try finding with rpm
	if not files:
		files = _get_library_files_from_rpm(lib_name, version_cb)

	# Try finding with pacman
	if not files:
		files = _get_library_files_from_pacman(lib_name, version_cb)

	# Try finding with slackware
	if not files:
		files = _get_library_files_from_slackware(lib_name, version_cb)

	# Try finding with portage
	if not files:
		files = _get_library_files_from_portage(lib_name, version_cb)

	# Try finding with pkg_info
	if not files:
		files = _get_library_files_from_pkg_info(lib_name, version_cb)

	# Try finding with ports
	if not files:
		files = _get_library_files_from_ports(lib_name, version_cb)

	# Try finding with pkg-config
	if not files:
		files = _get_library_files_from_pkg_config(lib_name, version_cb)
	
	# Try finding with the file system. But only if there is no version requirement.
	if not version_cb and not files:
		files = _get_library_files_from_fs(lib_name)

	# Save the file names in the cache
	if cacher and files:
		try:
			cacher.set_data(search_param, files)
		except Exception as ex:
			pass

	return files

def _get_library_files_from_pkg_config(lib_name, version_cb = None):
	matching_files = []
	lib_name = lib_name.lstrip('lib')

	# Just return if there is no pkg-config
	if not program_paths('pkg-config'):
		return matching_files

	# Find all packages that contain the name
	result = run_and_get_stdout("pkg-config --list-all | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name
		name = package.split()[0]

		# Skip this package if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Get the version, libdir, and includedir
		version = run_and_get_stdout("pkg-config --modversion {0}".format(name))
		libdir = run_and_get_stdout("pkg-config --variable=libdir {0}".format(name))
		includedir = run_and_get_stdout("pkg-config --variable=includedir {0}".format(name))
		if not version or not libdir or not includedir:
			continue
		version = version_string_to_tuple(version)

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get the library files in those directories
		for d in [libdir, includedir]:
			for root, dirs, files in os.walk(d):
				for entry in files:
					# Get the whole file name
					f = os.path.join(root, entry)

					# Save the file if the name is in the root
					if lib_name.lower() in root.lower():
						matching_files.append(f)
					# Save the file if the lib name is in the file
					elif 'lib' + lib_name.lower() in entry.lower():
						matching_files.append(f)

	return matching_files

def _get_library_files_from_ports(lib_name, version_cb = None):
	matching_files = []
	lib_name = lib_name.lstrip('lib')

	# Just return if there is no port
	if not program_paths('port'):
		return matching_files

	# Find all packages that contain the name
	result = run_and_get_stdout("port list | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name
		name = package.split()[0]

		# Skip if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Skip if not a devel package
		if not package.split()[2].startswith('devel/'):
			continue

		# Get the version
		version = package.split()[1].lstrip('@')
		if not version:
			continue
		version = version_string_to_tuple(version)

		# Skip if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get the files and skip if there are none
		library_files = run_and_get_stdout("port contents {0}".format(name))
		if not library_files:
			continue

		# Get the valid files
		for entry in library_files.split("\n"):
			entry = entry.strip()
			if os.path.isfile(entry):
				matching_files.append(entry)

	return matching_files

def _get_library_files_from_fs(lib_name):
	matching_files = []
	lib_name = lib_name.lstrip('lib')

	for path in _get_all_library_paths():
		for root, dirs, files in os.walk(path):
			for entry in files:
				# Get the whole file name
				f = os.path.join(root, entry)
				if lib_name in f and os.path.isfile(f):
					matching_files.append(f)

	return matching_files

def _get_library_files_from_pacman(lib_name, version_cb = None):
	matching_files = []
	lib_name = lib_name.lstrip('lib')

	# Just return if there is no pacman
	if not program_paths('pacman'):
		return matching_files

	# Find all packages that contain the name
	result = run_and_get_stdout("pacman -Sl | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# Get the best package name
	packages = [p.split()[1] for p in result.split("\n")]
	best_name = _get_best_match(packages, lib_name)
	if not best_name:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name
		name = package.split()[1]

		# Skip this package if it is not the best name
		if not best_name == name:
			continue

		# Skip this package if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Get the version
		version = package.split()[2]
		version = version.split('-')[0]
		version = version_string_to_tuple(version)

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get the library files
		result = run_and_get_stdout('pacman -Ql {0}'.format(name))
		if not result:
			continue

		# Save all the files
		for entry in result.split("\n"):
			entry = entry.split()[1]
			if os.path.isfile(entry):
				matching_files.append(entry)

	return matching_files

def _get_library_files_from_dpkg(lib_name, version_cb = None):
	matching_files = []

	# Just return if there is no dpkg
	if not program_paths('dpkg'):
		return matching_files

	# Find all packages that contain the name
	result = run_and_get_stdout("dpkg --list | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name and version
		name = before(package.split()[1], ':')
		version = between_last(package.split()[2], ':', '-')
		version = version_string_to_tuple(version)

		# Skip this package if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get all the files and directories
		result = run_and_get_stdout("dpkg -L {0}".format(name))
		if not result:
			continue

		# Save all the files
		library_entries = result.split("\n")
		for entry in library_entries:
			if os.path.isfile(entry):
				matching_files.append(entry)

	return matching_files

def _get_library_files_from_rpm(lib_name, version_cb = None):
	lib_name = lib_name.lstrip('lib')
	matching_files = []

	# Just return if there is no rpm
	if not program_paths('rpm'):
		return matching_files

	# Find all packages that contain the name
	result = run_and_get_stdout("rpm -qa | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name and version
		result = run_and_get_stdout("rpm -qi {0}".format(package))
		if not result:
			continue
		name = between(result, 'Name        : ', '\n')
		version = between(result, 'Version     : ', '\n')
		version = version_string_to_tuple(version)

		# Skip this package if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get all the files and directories
		result = run_and_get_stdout("rpm -ql {0}".format(package))
		if not result:
			continue

		# Save all the files
		library_entries = result.split("\n")
		for entry in library_entries:
			if os.path.isfile(entry):
				matching_files.append(entry)

	return matching_files

def _get_library_files_from_pkg_info(lib_name, version_cb = None):
	lib_name = lib_name.lstrip('lib')
	matching_files = []

	# Just return if there is not pkg_info
	if not program_paths('pkg_info'):
		return matching_files

	# Find all packages that contain the name
	result = run_and_get_stdout("pkg_info | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name and version
		name = package.split()[0]
		version = before(name.split('-')[-1], '_')
		version = version_string_to_tuple(version)

		# Skip this package if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Get all the files and directories
		result = run_and_get_stdout("pkg_info -L {0}".format(name))
		if not result:
			continue

		# Save all the files
		library_entries = result.split("\n")
		for entry in library_entries:
			if os.path.isfile(entry):
				matching_files.append(entry)

	return matching_files

def _get_library_files_from_slackware(lib_name, version_cb = None):
	matching_files = []
	lib_name = lib_name.lstrip('lib')

	# Just return if there is no package info
	if not os.path.isdir('/var/log/packages'):
		return matching_files

	# Get a list of all the installed packages
	result = run_and_get_stdout("ls /var/log/packages | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the metadata for this package
		result = run_and_get_stdout("cat /var/log/packages/{0}".format(package))

		# Get the name (Everything before the version number)
		name = []
		for n in package.split('-'):
			if re.match('^(\d|\.)+$', n):
				break
			name.append(n)
		name = str.join('-', name)

		# Get the version
		version = None
		for n in package.split('-'):
			if re.match('^(\d|\.)+$', n):
				version = n
				break
		version = version_string_to_tuple(version)

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Skip this package if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Get the files
		for entry in after(result, 'FILE LIST:').split("\n"):
			entry = '/' + entry
			if os.path.isfile(entry):
				matching_files.append(entry)

	return matching_files

def _get_library_files_from_portage(lib_name, version_cb = None):
	matching_files = []

	# Just return if there is not portage
	if not program_paths('qlist'):
		return matching_files

	# Find all the packages that contain the name
	result = run_and_get_stdout("qlist -C -I -v | grep -i {0}".format(lib_name))
	if not result:
		return matching_files

	# For each package
	for package in result.split("\n"):
		# Get the name (Everything before the version number)
		name = []
		for n in package.split('-'):
			if re.match('^(\d|\.)+$', n):
				break
			name.append(n)
		name = str.join('-', name)
		name = after(name, '/')

		# Get the version
		version = None
		for n in package.split('-'):
			if re.match('^(\d|\.)+$', n):
				version = n
				break
		version = version_string_to_tuple(version)

		# Skip this package if the version does not match
		if version_cb and not version_cb(version):
			continue

		# Skip this package if the library name is not in the package name
		if not lib_name.lower() in name.lower():
			continue

		# Get the files
		result = run_and_get_stdout("qlist -C {0}".format(name))
		if not result:
			continue

		for entry in result.split("\n"):
			if os.path.isfile(entry):
				matching_files.append(entry)

	return matching_files

def get_header_file(header_name, version_str = None):
	library_files = _get_library_files(header_name, version_str)
	header_file = _get_matched_file_from_library_files(header_name, '.h', library_files)
	return header_file

def get_static_library(lib_name, version_str = None):
	library_files = _get_library_files(lib_name, version_str)
	static_file = _get_matched_file_from_library_files(lib_name, '.a', library_files)
	return static_file

def get_shared_library(lib_name, version_str = None):
	extension = None
	if is_osx:
		extension = '.dylib'
	elif is_windows:
		extension = '.dll'
	else:
		extension = '.so'

	library_files = _get_library_files(lib_name, version_str)
	shared_file = _get_matched_file_from_library_files(lib_name, extension, library_files)
	return shared_file

def header_path(header_name):
	retval = None

	# Get any paths that contain the library name
	paths = []
	include_paths = [
		"/usr/include", 
		"/usr/local/include"
	]
	for include_path in include_paths:
		for root, dirs, files in os.walk(include_path):
			for file_name in files:
				complete_name = os.path.join(root, file_name)
				if complete_name.endswith(header_name):
					paths.append(complete_name)

	# Of those paths, get the ones that match the architecture
	for path in paths:
		if 'lib' + CPU.bits in path or CPU.arch in path:
			retval = path

	# If none were matched specifically from the architecture
	# Use the first
	if retval == None and paths:
		retval = paths[0]

	# Make sure a header file was found
	if not retval or not os.path.exists(retval):
		raise Exception("Header file not found: '" + header_name + "'")

	i = retval.rfind('/') + 1
	return retval[:i]

def header_paths(header_names):
	paths = []
	for header_name in header_names:
		paths.append(header_path(header_name))

	return paths

def include_path(header_name):
	return '-I' + header_path(header_name)

def include_paths(header_names):
	paths = []
	for header_name in header_names:
		paths.append(include_path(header_name))
	return str.join(' ', paths)

def static_or_shared_library_path(lib_name):
	path = get_static_library(lib_name)
	if path:
		return path

	path = get_shared_library(lib_name)
	if path:
		return path

	raise Exception("Static/Shared library not found: '" + lib_name + "'")




