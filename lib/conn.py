import socket
from . import config
from .segment import Segment

class UDP_Conn:
    def __init__(self, ip : str, port : int):
        self.ip   = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.bind((ip, port))


    def send_data(self, msg : "Segment", dest : (str, int)):
        # Sending bytes to destination
        # dest : (ip : str, port : int)
        self.sock.sendto(msg.get_bytes(), dest)


    def set_listen_timeout(self, timeout : float):
        self.sock.settimeout(timeout)


    def listen_single_datagram(self) -> ("Segment", str):
        # Listening single datagram
        resp, addr      = self.sock.recvfrom(config.LISTEN_BUFFER_SIZE)
        data            = Segment()
        data.set_from_bytes(resp)
        checksum_result = data.valid_checksum()
        return addr, data, checksum_result


    def close_socket(self):
        self.sock.close()
