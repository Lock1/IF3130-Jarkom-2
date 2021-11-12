import socket
import lib.conn

connection = lib.conn.UDP_Conn("127.0.0.1", 5005)
connection.listen_single_datagram()
