import socket
import fcntl
import struct
from . import config
from .segment import Segment

class UDP_Conn:
    def __init__(self, ip : str, port : int, auto_ifname : str = None):
        self.ip   = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        if config.AUTO_CONFIG_IP:
            self.__auto_config_ip(auto_ifname)
        self.sock.bind((self.ip, port))


    def __auto_config_ip(self, ifname : str):
        # Main reference
        # https://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-from-nic-in-python

        # First argument, file descriptor
        sock_fd      = self.sock.fileno()

        # Second argument, Request code SIOCGIFADDR for getting ip address
        request_code = 0x8915

        # Third argument, interface name.
        #   C string 15 char + 1 null terminator <=> 15 char in alphanumeric python string
        #   using struct for converting python string to C string
        c_ifname     = struct.pack("256s", ifname[:15])

        # Get IPv4 address with UNIX ioctl(), only slice IPv4 return value
        ipv4_address = fcntl.ioctl(sock_fd, request_code, c_ifname)[20:24]

        # Convert IPv4 address bytes to IPv4 address string
        self.ip      = socket.inet_ntoa(ipv4_address)


    def get_ipv4(self) -> str:
        return self.ip


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
