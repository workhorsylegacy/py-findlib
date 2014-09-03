#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2014, Matthew Brennan Jones <matthew.brennan.jones@gmail.com>
# Py-cache-file-change-dates is a server that monitors if files have changed.
# It uses a MIT style license
# It is hosted at: https://github.com/workhorsy/py-cache-file-change-dates
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

import os, sys
import socket
import pickle
import logging

class Server(object):
	def __init__(self, hostname, port):
		self.logger = logging.getLogger('server')
		self.hostname = hostname
		self.port = port

	def start(self):
		self.logger.debug('listening')
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind((self.hostname, self.port))
		self.socket.listen(1)

		while True:
			conn, address = self.socket.accept()
			self.logger.debug('Got connection')
			self.fire_on_client_connect(conn, address)

	def fire_on_client_connect(self, conn, address):
		logging.basicConfig(level=logging.DEBUG)
		logger = logging.getLogger("process-{0}".format(address))
		try:
			logger.debug("Connected %r at %r", conn, address)
			raw_message = b''
			while True:
				# Read the next chunk
				chunk = conn.recv(1024)

				# The chunk is blank, so there is no more message
				if chunk == b'':
					logger.debug('Socket closed remotely')
					break

				# Add the chunk to the message
				raw_message += chunk

				# The chunk is max size, there may be more message to read
				if len(chunk) == 1024:
					continue

				# Unpickle the message
				message = pickle.loads(raw_message)
				logger.debug("Received message %r", message)

				# Fire the client connect event
				self.on_client_connect(conn, message)
				logger.debug('Sent message')
		except:
			logger.exception('Problem handling request')
		finally:
			logger.debug('Closing socket')
			conn.close()

	def on_client_connect(self, conn, message):
		raise NotImplementedError('The on_client_connect method should be overridden in a child class.')

class CacheFileChangeDateServer(Server):
	def __init__(self, hostname, port):
		super(CacheFileChangeDateServer, self).__init__(hostname, port)
		self.cached_times = {}
		self.cached_data = {}

	def on_client_connect(self, conn, message):
		# cache file request
		if message['request'] == 'cache_file':
			has_changed = self._has_file_changed(message['file'])
			conn.sendall(pickle.dumps({'status':'ok', 'has_changed':has_changed, 'file':message['file']}))
		# set data request
		elif message['request'] == 'set_data':
			key = message['key']
			value = message['value']
			self.cached_data[key] = value
			conn.sendall(pickle.dumps({'status':'ok', 'key':key}))
		# get data request
		elif message['request'] == 'get_data':
			key = message['key']
			value = None
			if key in self.cached_data:
				value = self.cached_data[key]
			conn.sendall(pickle.dumps({'status':'ok', 'key':key, 'value':value}))
		# Unknown request
		else:
			conn.sendall(pickle.dumps({'status':'fail', 'message':'Unknown request: {0}'.format(message['request'])}))

	def _has_file_changed(self, name):
		# Return true if the file does not exist
		if not os.path.isfile(os.path.abspath(name)):
			print("not a file: '{0}'".format(name))
			return None

		# Get the modify time from the cache
		cached_time = 0
		if name in self.cached_times:
			cached_time = self.cached_times[name]

		# Get the modify time from the file system
		fs_time = os.path.getmtime(name)

		print("fs_time:{0}, cached_time:{1}".format(fs_time, cached_time))
		# Return true if the file system has a newer date than the cache
		if fs_time > cached_time:
			self.cached_times[name] = fs_time
			return True

		return False

class CacheFileChangeDateClient(object):
	def has_file_changed(self, file_name):
		self._connect()

		# Send a request to cache a file change date
		data = {'request':'cache_file', 'file':file_name}
		data = pickle.dumps(data)
		self.sock.sendall(data)

		# Get the response that says if it has changed or not since the last check
		result = pickle.loads(self.sock.recv(1024))

		self._disconnect()

		return result

	def set_data(self, key, value):
		self._connect()

		# 
		data = {'request':'set_data', 'key':key, 'value':value}
		data = pickle.dumps(data)
		self.sock.sendall(data)

		# 
		result = pickle.loads(self.sock.recv(10240))

		self._disconnect()

		return result

	def get_data(self, key):
		self._connect()

		# 
		message = {'request':'get_data', 'key':key}
		message = pickle.dumps(message)
		self.sock.sendall(message)

		# 
		result = pickle.loads(self.sock.recv(10240))

		self._disconnect()

		return result['value']

	def _connect(self):
		# Connect to the server
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect(('localhost', 9000))

	def _disconnect(self):
		# Disconnect from the server
		self.sock.close()

if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	server = CacheFileChangeDateServer('0.0.0.0', 9000)
	try:
		logging.info('Listening')
		server.start()
	except:
		logging.exception('Unexpected exception')
	finally:
		logging.info('Shutting down')
	logging.info('All done')



