import logging

def	setup_logging():
	logging.basicConfig(
		level=logging.DEBUG,
		format='%(levelname)s - %(message)s'
	)

LOCAL_HOST = '127.0.0.1'
BUFFER_SIZE = 4096
MAX_READ = 10 * 1024 * 1024
TIMEOUT_INT = 30.0
PORT = 8080
