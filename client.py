import lib.arg, lib.conn
import lib.config
from lib.segment import Segment

class Client:
    def __init__(self):
        args = {
            "port" : (int, "Client port"),
            "path" : (str, "Destination path"),
            "-m"   : (None, "Metadata"),
            "-p"   : (None, "Parallel"),
            "-f"   : (None, "Show full segment information")
        }
        parser = lib.arg.ArgParser("Client", args)
        args   = parser.get_parsed_args()

        self.ip                    = lib.config.CLIENT_BIND_IP
        self.port                  = args.port
        self.conn                  = lib.conn.UDP_Conn(self.ip, self.port)
        self.path                  = args.path
        self.verbose_segment_print = args.f

    def __output_segment_info(self, addr : (str, int), data : "Segment"):
        if self.verbose_segment_print:
            addr_str = f"{addr[0]}:{addr[1]}"
            print(f"[S] [{addr_str}] Segment information :")
            print(data)

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
        print("[!] Waiting for response...")
        server_addr, resp, checksum_success = self.conn.listen_single_datagram()
        if not checksum_success:
            # TODO : Maybe add something?
            print("[!] Checksum failed")
            exit(1)
        print(f"[S] Getting response from {server_addr[0]}:{server_addr[1]}")
        self.__output_segment_info(server_addr, resp)

        resp_flag = resp.get_flag()
        if resp_flag.syn and resp_flag.ack:
            resp_head = resp.get_header()
            # TODO : Do something

            # 3. Sending ACK to server
            ack_req = Segment()
            ack_req.set_flag(False, True, False)
            self.conn.send_data(ack_req, server_addr)
            self.server_addr = server_addr
            print(f"\n[!] Handshake with {server_addr[0]}:{server_addr[1]} success")
        else:
            print("\n[!] Invalid response : Server SYN-ACK handshake response invalid")
            print(f"[!] Handshake with {server_addr[0]}:{server_addr[1]} failed")
            print(f"[!] Exiting...")
            exit(1)


    def listen_file_transfer(self):
        print("[!] Starting file transfer...")
        with open(self.path, "wb") as dst:
            request_number = 0
            end_of_file    = False
            while not end_of_file:
                addr, resp, checksum_success = self.conn.listen_single_datagram()
                addr_str = f"{addr[0]}:{addr[1]}"
                if addr == self.server_addr and checksum_success:
                    segment_seq_number = resp.get_header()["sequence"]
                    if segment_seq_number == request_number:
                        print(f"[!] [{addr_str}] Sequence number match with Rn, sending Ack number {request_number}...")
                        dst.write(resp.get_payload())
                        ack_resp = Segment()
                        ack_resp.set_header({"sequence" : 0, "ack" : request_number})
                        self.conn.send_data(ack_resp, self.server_addr)
                        request_number += 1

                    elif resp.get_flag().fin:
                        end_of_file = True
                        print(f"[!] [{addr_str}] FIN flag, stopping transfer...")

                    else:
                        print(f"[!] [{addr_str}] Sequence number not equal with Rn ({segment_seq_number} =/= {request_number}), ignoring...")

                elif not checksum_success:
                    print(f"[!] [{addr_str}] Checksum failed, ignoring segment")

                self.__output_segment_info(addr, resp)
        self.conn.close_socket()
    # def get_metadata
    # TODO : Extra, bonus metadata request



if __name__ == '__main__':
    main = Client()
    main.three_way_handshake()
    main.listen_file_transfer()
