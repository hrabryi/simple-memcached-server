# simple-memcached-server
Key-value storage server.

This is implementation of memcached protocol with storing data in SQLite.
Default TCP address and port is: 127.0.0.1:11211

To run server use command:  $ python main.py database.sqlite

Storage commands
------------------

To store new key-value data client sends a command line which looks like this:

set \<key> \<value> \<exptime> \<bytes> \r\n"

Retrieval command:
------------------

The retrieval command "get" operate like this:

get \<key>*\r\n

- <key>* means one or more key strings separated by whitespace.

After this command, the client expects zero or more items, each of
which is received as a text line followed by a data block. After all
the items have been transmitted, the server sends the string

"END\r\n"

to indicate the end of response.

Each item sent by the server looks like this:

VALUE \<key> \<flags> \<bytes> \r\n
\<data block>\r\n

- \<key> is the key for the item being sent

- \<value> is the flags value set by the storage command

- \<bytes> is the length of the data block to follow, *not* including
  its delimiting \r\n

- \<data block> is the data for this item.

If some of the keys appearing in a retrieval request are not sent back
by the server in the item list this means that the server does not
hold items with such keys (because they were never stored, or stored
but deleted to make space for more items, or expired, or explicitly
deleted by a client).

Deletion
--------

The command "delete" allows for explicit deletion of items:

delete \<key> \r\n

- \<key> is the key of the item the client wishes the server to delete

The response line to this command can be one of:

- "DELETED\r\n" to indicate success

- "NOT_FOUND\r\n" to indicate that the item with this key was not
  found.

Exit
----
Use "quit" command to close the session.