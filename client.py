import lib.arg, lib.conn
import lib.config
from lib.segment import Segment

class Client:
    def __init__(self):
        args = {
            "port" : (int, "Client port"),
            "path" : (str, "Destination path"),
            "-m"   : (None, "Metadata"),
            "-p"   : (None, "Parallel")
        }
        parser = lib.arg.ArgParser("Client", args)
        args   = parser.get_parsed_args()

        self.ip   = lib.config.CLIENT_BIND_IP
        self.port = args.port
        self.conn = lib.conn.UDP_Conn(self.ip, self.port)


    def three_way_handshake(self):
        # 1. SYN to server
        server_broadcast_addr = (lib.config.SERVER_BROADCAST_IP, lib.config.SERVER_LISTEN_PORT)
        print(f"Client started at {self.ip}:{self.port}")
        print("[!] Initiating three way handshake...")
        print(f"[!] Sending broadcast SYN request to port {server_broadcast_addr[1]}")
        syn_req = Segment()
        syn_req.set_flag(True, False, False)
        self.conn.send_data(syn_req, server_broadcast_addr)

        # 2. Waiting SYN + ACK from server
        resp, server_addr = self.conn.listen_single_datagram()
        resp_seg          = Segment()
        resp_seg.set_from_bytes(resp)
        if not resp_seg.valid_checksum():
            # TODO : Maybe add something?
            print("Failed checksum")
            exit(1)
        print(f"[S] Getting response from {server_addr[0]}:{server_addr[1]}")
        print(resp_seg)

        resp_flag = resp_seg.get_flag()
        if resp_flag.syn and resp_flag.ack:
            resp_head = resp_seg.get_header()
            # TODO : Do something

            # 3. Sending ACK to server
            ack_req = Segment()
            ack_req.set_flag(False, True, False)
            self.conn.send_data(ack_req, server_addr)
        else:
            # TODO : Do something?
            print("Handshake failed")
            exit(1)


    def listen_file_transfer(self):
        # TODO : Add
        pass

    # def get_metadata
    # TODO : Extra, bonus metadata request



if __name__ == '__main__':
    main = Client()
    main.three_way_handshake()
    print("handshake success")
