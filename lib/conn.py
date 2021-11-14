import socket
from . import config
from .segment import Segment

class UDP_Conn:
    def __init__(self, ip : str, port : int):
        self.ip   = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


    def send_data(self, msg : "Segment", dest : (str, int)):
        # Sending bytes to destination
        # dest : (ip : str, port : int)
        self.sock.sendto(msg.get_bytes(), dest)


    def listen_single_datagram(self) -> ("Segment", str):
        # Listening single datagram
        resp, addr      = self.sock.recvfrom(config.LISTEN_BUFFER_SIZE)
        data            = Segment()
        data.set_from_bytes(resp)
        checksum_result = data.valid_checksum()
        return addr, data, checksum_result


    def close_connection(self):
        self.sock.close()
