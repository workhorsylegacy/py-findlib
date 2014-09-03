

import socket
import pickle

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

	def _connect(self):
		# Connect to the server
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect(('localhost', 9000))

	def _disconnect(self):
		# Disconnect from the server
		self.sock.close()

if __name__ == '__main__':
	client = CacheFileChangeDateClient()

	r = client.has_file_changed('/home/matt/Projects/py-cache-file-change-dates/client.py')
	print(r)

	r = client.has_file_changed('/home/matt/Projects/py-cache-file-change-dates/server.py')
	print(r)


