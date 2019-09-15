import unittest
import socket


class Test_service(unittest.TestCase):

    def setUp(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(('127.0.0.1', 11211))

    def tearDown(self):
        self.client_socket.close()

    def test_get(self):
        # Set value
        self.client_socket.send("set test_key test_value 100 200".encode('utf-8'))
        self.assertEqual(self.client_socket.recv(1024).decode('utf-8'), "STORED\r\n")

        # Get value
        self.client_socket.send("get test_key".encode('utf-8'))
        self.assertEqual(self.client_socket.recv(1024).decode('utf-8'), "VALUE test_key test_value 200\nEND\r\n")

        # Get value from not existing key
        self.client_socket.send("get key_not_exist".encode('utf-8'))
        self.assertEqual(self.client_socket.recv(1024).decode('utf-8'), "END\r\n")

        # Delete not existing key
        self.client_socket.send("delete key_not_exist".encode('utf-8'))
        self.assertEqual(self.client_socket.recv(1024).decode('utf-8'), "NOT_FOUND\r\n")

        # Delete existing key
        self.client_socket.send("delete test_key".encode('utf-8'))
        self.assertEqual(self.client_socket.recv(1024).decode('utf-8'), "DELETED\r\n")

        #  Get value of deleted key
        self.client_socket.send("get test_key".encode('utf-8'))
        self.assertEqual(self.client_socket.recv(1024).decode('utf-8'), "END\r\n")

    def test_params_missed(self):
        # Set value
        self.client_socket.send("clear".encode('utf-8'))
        self.assertEqual(self.client_socket.recv(1024).decode('utf-8'), "CLIENT_ERROR Unexpected amount of params\r\n")

    def test_set_with_missed_params(self):
        # Set value
        self.client_socket.send("set test_key test_value".encode('utf-8'))
        self.assertEqual(self.client_socket.recv(1024).decode('utf-8'),
                         "CLIENT_ERROR Required params is missed. See documentation.\r\n")

    def test_unsupported_command(self):
        # Set value
        self.client_socket.send('incr test_key new_value'.encode('utf-8'))
        self.assertEqual(self.client_socket.recv(1024).decode('utf-8'), 'ERROR\r\n')
