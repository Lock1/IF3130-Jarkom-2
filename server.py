import lib.arg, lib.conn
import lib.config
from lib.segment import Segment
import lib.segment as segment
import math
import time
import socket
import threading



class Server:
    def __init__(self):
        args = {
            "port" : (int, "Server port"),
            "path" : (str, "Source path"),
            "-f"   : (None, "Show segment information"),
            "-d"   : (None, "Show full payload in hexadecimal")
        }
        parser = lib.arg.ArgParser("Server", args)
        args   = parser.get_parsed_args()

        self.ip       = lib.config.SERVER_BIND_IP
        self.port     = args.port
        self.path     = args.path
        with open(self.path, "rb") as src:
            src.seek(0, 2)         # Seek to end of file
            filesize = src.tell()  # Get file size
        self.filesize              = filesize
        self.window_size           = lib.config.TCP_WINDOW_SIZE
        self.segmentcount          = math.ceil(filesize / 32768)
        self.verbose_segment_print = args.f
        self.show_payload          = args.d
        self.send_metadata         = lib.config.SEND_METADATA
        self.parallel_mode         = lib.config.USE_PARALLEL
        self.ack_timeout           = lib.config.SERVER_TRANSFER_ACK_TIMEOUT
        if self.send_metadata:
            self.__get_metadata_from_file()
        self.conn                  = lib.conn.UDP_Conn(
            self.ip,
            self.port,
            auto_ifname=lib.config.SERVER_INTERFACE_NAME,
            listen_broadcast=True
            )
        self.ip                    = self.conn.get_ipv4()

    def __output_segment_info(self, addr : (str, int), data : "Segment"):
        if self.verbose_segment_print:
            addr_str = f"{addr[0]}:{addr[1]}"
            print(f"[S] [{addr_str}] Segment information :")
            print(data)

        if self.show_payload:
            print(f"[S] [{addr_str}] Payload in hexadecimal")
            print(binascii.hexlify(data.get_payload(), " "))

        if self.verbose_segment_print or self.show_payload:
            print("")

    def __valid_syn_request(self, data : "Segment") -> bool:
        return data.get_flag().syn

    def __send_metadata(self, client_addr : (str, int)):
        metadata = Segment()
        payload  = bytes(self.filename, 'ascii') + b"\x04" + bytes(self.file_ext, 'ascii')
        metadata.set_payload(payload)
        self.conn.send_data(metadata, client_addr)

    def __get_metadata_from_file(self):
        self.filename = self.path[self.path.rfind("/") + 1:self.path.rfind(".")]
        self.file_ext = self.path[self.path.rfind("."):]

    def __parallel_packet_queue_listener(self):
        while True:
            addr, data, checksum_success = self.conn.listen_single_datagram()
            if checksum_success:
                if self.__valid_syn_request(data):
                    self.syn_request_queue.append((addr, data, checksum_success))
                elif addr in self.packet_queue:
                    self.packet_queue[addr].append((addr, data, checksum_success))
                else:
                    self.packet_queue[addr] = [(addr, data, checksum_success)]
            else:
                print(f"[!] [Listener] [{addr[0]}:{addr[1]}] Checksum error")

    def __parallel_listen_syn_request(self):
        if self.syn_request_queue:   # If queue is not empty
            return self.syn_request_queue.pop(0)
        else:
            return None, None, False

    def __parallel_client_listener(self):
        self.client_conn_list = []
        while True:
            addr, data, checksum_success = self.__parallel_listen_syn_request()

            if checksum_success and addr not in self.client_conn_list and self.__valid_syn_request(data):
                print("\n[!] Initiating three way handshake with clients...")
                try:
                    handshake_success = self.three_way_handshake(addr)
                    if handshake_success:
                        self.client_conn_list.append(addr)
                        thread = threading.Thread(target=self.file_transfer, args=(addr,))
                        thread.start()
                except socket.timeout:
                    print(f"[!] [{addr[0]}:{addr[1]}] Handshake failed, connection timeout")
            elif addr in self.client_conn_list:
                print(f"[!] Client ({addr[0]}:{addr[1]}) already in list")

    def __fetch_data_from_addr(self, addr : (str, int)) -> ("Tuple addr", "Segment", "Checksum_result"):
        if self.parallel_mode:
            timeout = time.time() + self.ack_timeout
            # Blocking loop
            while addr not in self.packet_queue or not self.packet_queue[addr]:
                if time.time() >= timeout:
                    raise socket.timeout()

            return self.packet_queue[addr].pop(0)
        else:
            return self.conn.listen_single_datagram()



    def listen_for_clients(self):
        if self.parallel_mode:
            self.packet_queue      = {}          # Dictionary with client address as key and queue as value
            self.syn_request_queue = []
            packet_listener_thread = threading.Thread(target=self.__parallel_packet_queue_listener, args=())
            packet_listener_thread.start()
            self.__parallel_client_listener()
        else:
            self.client_conn_list = []
            waiting_client        = True

            while waiting_client:
                addr, data, checksum_success = self.conn.listen_single_datagram()
                if self.__valid_syn_request(data) and addr not in self.client_conn_list and checksum_success:
                    self.client_conn_list.append(addr)

                    print(f"[!] Client ({addr[0]}:{addr[1]}) found")
                    prompt = input("[?] Listen more? (y/n) ")
                    if prompt == "y":
                        waiting_client = True
                    else:
                        waiting_client = False
                elif addr in self.client_conn_list:
                    print(f"[!] Client ({addr[0]}:{addr[1]}) already in list")


    def start_file_transfer(self):
        print("\n[!] Initiating three way handshake with clients...")
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



    def file_transfer(self, client_addr : tuple):
        if self.send_metadata:
            self.__send_metadata(client_addr)
        sequence_base     = 0
        window_size       = self.window_size
        seq_window_bound  = min(sequence_base + window_size, self.segmentcount)

        # 32768 bytes max per segment
        with open(self.path, "rb") as src:

            # File transfer
            iter_count = 1
            while sequence_base < self.segmentcount:
                # Sending segments within window
                if not self.parallel_mode:
                    print(f"\n[!] [{client_addr[0]}:{client_addr[1]}] Transfer iteration = {iter_count}")
                for i in range(seq_window_bound - sequence_base):
                    data_segment = Segment()
                    src.seek(32768 * (sequence_base + i))
                    data_segment.set_payload(src.read(32768))
                    data_segment.set_header({"sequence" : sequence_base + i, "ack" : 0})
                    self.conn.send_data(data_segment, client_addr)
                    print(f"[!] [{client_addr[0]}:{client_addr[1]}] Sending segment with sequence number {sequence_base + i}")

                for _ in range(seq_window_bound - sequence_base):
                    try:
                        addr, resp, checksum_success = self.__fetch_data_from_addr(client_addr)

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
                            self.__output_segment_info(addr, resp)
                    except socket.timeout:
                        print(f"[!] [{client_addr[0]}:{client_addr[1]}] ACK number {sequence_base} response time out")
                        print(f"[!] [{client_addr[0]}:{client_addr[1]}] Retrying transfer from {sequence_base} to {seq_window_bound - 1}...")
                        break

                iter_count += 1

            # Tearing down connection
            print(f"\n[!] [{client_addr[0]}:{client_addr[1]}] File transfer completed, sending FIN to client...\n")
            data_segment = Segment()
            data_segment.set_flag([segment.FIN_FLAG])
            self.conn.send_data(data_segment, client_addr)

            # Waiting ACK response
            addr, resp, checksum_success = self.__fetch_data_from_addr(client_addr)
            if resp.get_flag().ack:
                print(f"\n[!] [{client_addr[0]}:{client_addr[1]}] Connection closed\n")
            else:
                print(f"\n[!] [{client_addr[0]}:{client_addr[1]}] Invalid ACK segment\n")
                self.__output_segment_info(resp)


    def three_way_handshake(self, client_addr : (str, int)) -> bool:
        # TODO : Maybe queue + separate thread listener?
        # Assuming client already sending SYN request
        # 2. SYN + ACK server response
        synack_resp = Segment()
        synack_resp.set_flag([segment.SYN_FLAG, segment.ACK_FLAG])
        # TODO : Maybe set sequence number?
        self.conn.send_data(synack_resp, client_addr)

        # 3. Wait ACK response
        addr, resp, checksum_success = self.__fetch_data_from_addr(client_addr)
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

    if not main.parallel_mode:
        print(f"\n{len(main.client_conn_list)} clients found:")
        for i, (ip, port) in enumerate(main.client_conn_list, start=1):
            print(f"{i}. {ip}:{port}")

        main.start_file_transfer()
