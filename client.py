

from cache_file_change_date import *


if __name__ == '__main__':
	client = CacheFileChangeDateClient()

	r = client.has_file_changed('/home/matt/Projects/py-cache-file-change-dates/client.py')
	print(r)

	r = client.has_file_changed('/home/matt/Projects/py-cache-file-change-dates/cache_file_change_date.py')
	print(r)


