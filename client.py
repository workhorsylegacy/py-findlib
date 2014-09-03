
import socket
import pickle

if __name__ == "__main__":
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(("localhost", 9000))
	data = {'request':'cache_file', 'file':'/home/matt/Projects/py-watchfs/client.py'}
	sock.sendall(pickle.dumps(data))
	result = pickle.loads(sock.recv(1024))
	print(result)
	sock.close()

