import lib.arg, lib.conn
import lib.config
from lib.segment import Segment

class Server:
    def __init__(self):
        args = {
            "port" : (int, "Server port"),
            "path" : (str, "Source path"),
            "-m"   : (None, "Metadata"),
            "-p"   : (None, "Parallel")
        }
        parser = lib.arg.ArgParser("Server", args)
        args   = parser.get_parsed_args()

        self.ip   = lib.config.SERVER_BIND_IP
        self.port = args.port


    def __valid_syn_request(self, data : "Segment") -> bool:
        return data.get_flag().syn, data.get_header()["sequence"]


    def listen_for_clients(self):
        self.client_conn_list = []
        broadconn             = lib.conn.UDP_Conn("", self.port)
        waiting_client        = True

        while waiting_client:
            addr, data, checksum_success = broadconn.listen_single_datagram()
            is_valid_syn_req, seq_num    = self.__valid_syn_request(data)
            if is_valid_syn_req and (addr, seq_num) not in self.client_conn_list and checksum_success:
                self.client_conn_list.append((addr, seq_num))

                print(f"[!] Client ({addr[0]}:{addr[1]}) found, requesting sequence number = {seq_num}")
                prompt = input("[?] Listen more? (y/n) ")
                if prompt == "y":
                    waiting_client = True
                else:
                    waiting_client = False

        broadconn.close_connection()


    def start_file_transfer(self):
        print("\n[!] Initiating three way handshake with clients...")
        self.conn = lib.conn.UDP_Conn(self.ip, self.port)
        failed_handshake_addr = []
        for (client_addr, seq_num) in self.client_conn_list:
            print(f"[!] Sending SYN-ACK to {client_addr[0]}:{client_addr[1]}")
            handshake_success = self.three_way_handshake(client_addr)
            if not handshake_success:
                failed_handshake_addr.append((client_addr, seq_num))

        for client in failed_handshake_addr:
            self.client_conn_list.remove(client)

        print("\n[!] Commencing file transfer...")
        for (client_addr, seq_num) in self.client_conn_list:
            self.file_transfer(client_addr, seq_num)


    def file_transfer(self, client_addr : tuple, seq_num : int):
        # Unit for file transfering
        sequence_num  = 0
        sequence_base = 0
        sequence_max = 0
        window_size = 0
        request_num = 0


    def three_way_handshake(self, client_addr : (str, int)) -> bool:
        # TODO : Maybe queue + separate thread listener?
        # Assuming client already sending SYN request
        # 2. SYN + ACK server response
        synack_resp = Segment()
        synack_resp.set_flag(True, True, False)
        # TODO : Maybe set sequence number?
        self.conn.send_data(synack_resp, client_addr)

        # 3. Wait ACK response
        addr, resp, checksum_success = self.conn.listen_single_datagram()
        ack_flag = resp.get_flag()
        if addr == client_addr and ack_flag.ack and checksum_success:
            print(f"[!] Handshake success with {client_addr[0]}:{client_addr[1]}")
            return True
        else:
            print("[!] Invalid response : Client ACK handshake response invalid")
            print(f"[!] Handshake failed with {client_addr[0]}:{client_addr[1]}")
            return False





if __name__ == '__main__':
    main = Server()
    print(f"Server started at {main.ip}:{main.port}...")
    print("[!] Listening to broadcast address for clients.")
    main.listen_for_clients()

    print(f"\n{len(main.client_conn_list)} clients found:")
    for i, (ip, port) in enumerate(main.client_conn_list, start=1):
        print(f"{i}. {ip}:{port}")

    main.start_file_transfer()
