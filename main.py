import socket
import sys
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)

"""Key-value storage server
This is implementation of memcached protocol with storing data in SQLite.
Default TCP address and port is: 127.0.0.1:11211
To run server use command:  $ python main.py database.sqlite
"""


class Cache(dict):
    """
    Cache class that used dictionary. Initial values initialize from sqlite db.
    """

    def __init__(self):
        kwargs = self._get_init_values_from_db()
        super(Cache, self).__init__(**kwargs)

    def _get_init_values_from_db(self):
        """
        Get k,v from database and return dictionary.
        :return: dict
        """
        conn = sqlite3.connect('database.sqlite')
        with conn:
            data = conn.execute('SELECT key, value, exptime, bytes  FROM cache;')
            all_rows = data.fetchall()
        return {key: {'value': value, 'exptime': exptime, 'bytes': bytes} for key, value, exptime, bytes in all_rows}


def _update_db(command, key, value=None, exptime=None, bytes_length=None):
    """
    Update(create) or delete database record.
    :return: None
    """
    conn = sqlite3.connect(db_file_name)
    conn.isolation_level = None  # autocommit mode
    with conn:
        if command == "set":
            # Create or update value
            conn.execute(f"""INSERT INTO cache VALUES ('{key}', '{value}', {exptime}, {bytes_length})
                        ON CONFLICT (key)
                        DO UPDATE SET value='{value}', exptime={exptime}, bytes={bytes_length} WHERE key='{key}';""")
        elif command == "delete":
            conn.execute(f"DELETE FROM cache WHERE key='{key}';")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        logging.info("Wrong amount of arguments. Expected DB filename")
    db_file_name = sys.argv[1]

    TCP_IP = '127.0.0.1'
    TCP_PORT = 11211
    BUFFER_SIZE = 10240

    #  Initialize DB if not exist
    conn = sqlite3.connect(db_file_name)
    with conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS cache (
                            key char(250) PRIMARY KEY NOT NULL,
                            value char(250) NOT NULL,
                            exptime INT NULL,
                            bytes INT NULL);""")

    # Server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((TCP_IP, TCP_PORT))
    cache = Cache()
    logging.info(f"Listening {TCP_IP}:{TCP_PORT}...")
    # Listen for incoming connections
    server_socket.listen(5)  # Number of connections
    while True:
        #  Waiting for connection
        (client_socket, address) = server_socket.accept()
        try:
            while True:
                #  Waiting for data
                data = client_socket.recv(BUFFER_SIZE).decode('utf-8')
                if data.split()[0] == "quit":
                    logging.error('Connection closed by user')
                    client_socket.close()
                    break
                elif len(data.split()) < 2 or len(data.split()) > 6:
                    client_socket.send("CLIENT_ERROR Unexpected amount of params\r\n".encode('utf-8'))
                    logging.error(f"CLIENT_ERROR Unexpected amount of params: {data}")
                else:
                    command = data.split()[0]
                    key = data.split()[1]
                    if command == "get":
                        try:
                            response = []
                            keys = data.split()[1:]
                            for key in keys:
                                value = cache[key]['value']
                                bytes_length = cache[key]['bytes']
                                response.append(f"VALUE {key} {value} {bytes_length}\n")
                            response.append("END\r\n")
                            client_socket.send("".join(response).encode('utf-8'))
                        except KeyError:
                            client_socket.send("END\r\n".encode('utf-8'))
                            logging.error(f"No such key in cache {key}")
                            pass
                    elif command == "set":
                        try:
                            value, exptime, bytes_length = data.split()[2:5]
                            cache[key] = {'value': value, 'exptime': exptime, 'bytes': bytes_length}
                            client_socket.send("STORED\r\n".encode('utf-8'))
                            _update_db(command, key, value, exptime, bytes_length)
                        except ValueError:
                            client_socket.send(
                                "CLIENT_ERROR Required params is missed. See documentation.\r\n".encode('utf-8'))
                    elif command == "delete":
                        try:
                            print("Delete command")
                            del cache[key]
                            client_socket.send("DELETED\r\n".encode('utf-8'))
                            logging.info(f"key={key} successfully deleted.")
                            print("delete key from DB")
                            _update_db(command, key)
                        except KeyError:
                            client_socket.send("NOT_FOUND\r\n".encode('utf-8'))
                            logging.error(f"Key to delete {key} not found.")
                    else:
                        # Unsupported command
                        client_socket.send("ERROR\r\n".encode('utf-8'))
                        logging.error(f"Unsupported command {command}.")
        except ConnectionResetError:
            continue
