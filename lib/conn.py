import socket
import fcntl
import struct
import ipaddress
from . import config
from .segment import Segment



class UDP_Conn:
    def __init__(self, ip : str, port : int, auto_ifname : str = None, send_broadcast : bool = False, listen_broadcast : bool = False):
        self.ip   = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        if send_broadcast:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        if config.AUTO_CONFIG_IP:
            self.__auto_config_ip(auto_ifname)
        else:
            self.broadcast_addr = lib.config.SERVER_BROADCAST_IP

        if listen_broadcast:
            self.sock.bind(("", port))
        else:
            self.sock.bind((self.ip, port))

    def __try_common_ifname(self) -> ("str", "str"):
        common_ifname   = [b"eth0", b"enp0s3", b"lo"]
        sock_fd         = self.sock.fileno()
        request_code    = 0x8915
        selected_ifname = None
        ipv4_address    = None

        for name in common_ifname:
            try:
                ipv4_address    = fcntl.ioctl(sock_fd, request_code, struct.pack("256s", name[:15]))[20:24]
                selected_ifname = name
                break
            except OSError:
                print(f"[!] Interface {name} not found")

        if selected_ifname is not None:
            return selected_ifname, ipv4_address
        else:
            print(f"[!] Error, no interface found")
            exit(-1)

    def __auto_config_ip(self, ifname : bytes):
        # Main reference
        # https://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-from-nic-in-python

        # Get IPv4 from interface name
        # First argument, file descriptor
        sock_fd             = self.sock.fileno()

        # Second argument, Request code SIOCGIFADDR for getting ip address
        request_code        = 0x8915

        # Third argument, interface name.
        #   C string 15 char + 1 null terminator <=> 15 char in alphanumeric python string
        #   using struct for converting python string to C string
        c_ifname            = struct.pack("256s", ifname[:15])

        # Get IPv4 address with UNIX ioctl(), only slice IPv4 return value
        try:
            ipv4_address         = fcntl.ioctl(sock_fd, request_code, c_ifname)[20:24]
        except OSError:
            print(f"[!] Warning, interface {ifname.decode(encoding='ascii')} not found, trying common interface name...")
            ifname, ipv4_address = self.__try_common_ifname()
            c_ifname             = struct.pack("256s", ifname[:15])
            print(f"[!] Using interface {ifname.decode(encoding='ascii')}...")


        # Convert IPv4 address bytes to IPv4 address string
        self.ip             = socket.inet_ntoa(ipv4_address)


        # Get IPv4 subnet mask from interface name
        # Using same first and third argument, retrieve subnet mask
        request_code        = 0x891b    # SIOCGIFNETMASK request

        subnet_mask         = fcntl.ioctl(sock_fd, request_code, c_ifname)[20:24]
        self.subnet_mask    = socket.inet_ntoa(subnet_mask)
        self.broadcast_addr = str(ipaddress.IPv4Network(self.ip + "/" + self.subnet_mask, False).broadcast_address)



    def get_ipv4(self) -> str:
        return self.ip


    def get_broadcast_addr(self) -> str:
        return self.broadcast_addr


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
