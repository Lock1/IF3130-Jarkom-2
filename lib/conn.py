import socket
from . import config

class UDP_Conn:
    def __init__(self, ip : str, port : int):
        self.ip   = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


    def send_bytes(self, msg : "bytes", dest : (str, int)):
        # Sending bytes to destination
        # dest : (ip : str, port : int)
        self.sock.sendto(msg, dest)


    def listen_single_datagram(self) -> ("bytes", str):
        # Listening single datagram
        return self.sock.recvfrom(config.LISTEN_BUFFER_SIZE)


    def close_connection(self):
        self.sock.close()
