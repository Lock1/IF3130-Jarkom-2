import lib.arg, lib.conn
import lib.config
from lib.segment import Segment
import math

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

        self.ip       = lib.config.SERVER_BIND_IP
        self.port     = args.port
        self.path     = args.path
        with open(self.path, "rb") as src:
            src.seek(0, 2)         # Seek to end of file
            filesize = src.tell()  # Get file size
        self.filesize      = filesize
        self.sizeperwindow = lib.config.TCP_WINDOW_SIZE * 32768
        self.segmentcount  = math.ceil(filesize / 32768)


    def __valid_syn_request(self, data : "Segment") -> bool:
        return data.get_flag().syn


    def listen_for_clients(self):
        self.client_conn_list = []
        broadconn             = lib.conn.UDP_Conn("", self.port)
        waiting_client        = True

        while waiting_client:
            addr, data, checksum_success = broadconn.listen_single_datagram()
            is_valid_syn_req             = self.__valid_syn_request(data)
            if is_valid_syn_req and addr not in self.client_conn_list and checksum_success:
                self.client_conn_list.append(addr)

                print(f"[!] Client ({addr[0]}:{addr[1]}) found")
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
        for client_addr in self.client_conn_list:
            print(f"[!] Sending SYN-ACK to {client_addr[0]}:{client_addr[1]}")
            handshake_success = self.three_way_handshake(client_addr)
            if not handshake_success:
                failed_handshake_addr.append(client_addr)

        for client in failed_handshake_addr:
            self.client_conn_list.remove(client)

        print("\n[!] Commencing file transfer...")
        for client_addr in self.client_conn_list:
            self.file_transfer(client_addr)
            # TODO : Maybe Three way handshake seq num != with data transfer


    def file_transfer(self, client_addr : tuple):
        sequence_base     = 0
        window_size       = lib.config.TCP_WINDOW_SIZE
        seq_window_bound  = min(sequence_base + window_size, self.segmentcount)

        with open(self.path, "rb") as src:
            # 32768 bytes max per segment

            # File transfer
            while sequence_base < self.segmentcount:
                # Sending segments within window
                for i in range(seq_window_bound - sequence_base):
                    data_segment = Segment()
                    src.seek(32768 * (sequence_base + i))
                    data_segment.set_payload(src.read(32768))
                    data_segment.set_header({"sequence" : sequence_base + i, "ack" : 0})
                    self.conn.send_data(data_segment, client_addr)
                    print(f"[!] Sending segment with sequence number {sequence_base}")

                for _ in range(seq_window_bound - sequence_base):
                    addr, resp, checksum_success = self.conn.listen_single_datagram()
                    # TODO : Add timeout
                    addr_str = f"{addr[0]}:{addr[1]}"
                    if checksum_success and addr == client_addr:
                        if resp.get_header()["ack"] == sequence_base:
                            sequence_base    += 1
                            seq_window_bound = min(sequence_base + window_size, self.segmentcount)
                            print(f"[!] [{addr_str}] ACK number {resp.get_header()['ack']}, new sequence base = {sequence_base}")
                        else:
                            print(f"[!] [{addr_str}] ACK number not match, ignoring segment")
                    elif not checksum_success:
                        print(f"[!] [{addr_str}] Checksum failed {addr[0]}:{addr[1]}")
                    elif addr != client_addr:
                        print(f"[!] [{addr_str}] Source address not match, ignoring segment")
                    else:
                        print(f"[!] [{addr_str}] Unknown error")
                    print(f"[S] [{addr_str}] Segment information :")
                    print(resp)

            print(f"\n[!] [{client_addr[0]}:{client_addr[1]}] File transfer completed, sending FIN to client...")
            data_segment = Segment()
            data_segment.set_flag(False, False, True)
            self.conn.send_data(data_segment, client_addr)






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
    print(f"[!] Server started at {main.ip}:{main.port}...")
    print(f"[!] Source file | {main.path} | {main.filesize} bytes")
    print("[!] Listening to broadcast address for clients.")
    main.listen_for_clients()

    print(f"\n{len(main.client_conn_list)} clients found:")
    for i, (ip, port) in enumerate(main.client_conn_list, start=1):
        print(f"{i}. {ip}:{port}")

    main.start_file_transfer()
