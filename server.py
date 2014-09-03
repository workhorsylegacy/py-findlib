
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
		self.cache = {}

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

class WatchFSServer(Server):
	def on_client_connect(self, conn, message):
		# The request is for the cache file
		if message['request'] == 'cache_file':
			has_changed = self.has_file_changed(message['file'])
			conn.sendall(pickle.dumps({'status':'ok', 'has_changed':has_changed}))
		# Unknown request
		else:
			conn.sendall(pickle.dumps({'status':'fail', 'message':'Unknown request: {0}'.format(message['request'])}))

	def has_file_changed(self, name):
		# Return true if the file does not exist
		if not os.path.isfile(os.path.abspath(name)):
			print("not a file: '{0}'".format(name))
			return True

		# Get the modify time from the cache
		cached_time = 0
		if name in self.cache:
			cached_time = self.cache[name]

		# Get the modify time from the file system
		fs_time = os.path.getmtime(name)

		print("fs_time:{0}, cached_time:{1}".format(fs_time, cached_time))
		# Return true if the file system has a newer date than the cache
		if fs_time > cached_time:
			self.cache[name] = fs_time
			return True

		return False

if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	server = WatchFSServer('0.0.0.0', 9000)
	try:
		logging.info('Listening')
		server.start()
	except:
		logging.exception('Unexpected exception')
	finally:
		logging.info('Shutting down')
	logging.info('All done')


