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


    def __valid_syn_request(self, data : "bytes") -> bool:
        syn_req  = Segment()
        syn_req.set_from_bytes(data)
        syn_flag = syn_req.get_flag()
        return syn_flag.syn


    def listen_for_clients(self):
        self.client_conn_list = []
        broadconn             = lib.conn.UDP_Conn("", self.port)
        waiting_client        = True

        while waiting_client:
            data, addr = broadconn.listen_single_datagram()
            if self.__valid_syn_request(data) and addr not in self.client_conn_list:
                self.client_conn_list.append(addr)

                print(f"[!] Client ({addr[0]}:{addr[1]}) found")
                prompt = input("[?] Listen more? (y/n) ")
                if prompt == "y":
                    waiting_client = True
                else:
                    waiting_client = False

        broadconn.close_connection()

    def start_file_transfer(self):
        self.conn = lib.conn.UDP_Conn(self.ip, self.port)
        for client_addr in self.client_conn_list:
            self.three_way_handshake(client_addr)

    def three_way_handshake(self, client_addr : (str, int)):
        # Assuming client already sending SYN request
        # 2. SYN + ACK server response
        synack_resp = Segment()
        synack_resp.set_flag(True, True, False)
        # TODO : Maybe set sequence number?
        self.conn.send_data(synack_resp, client_addr)

        # 3. Wait ACK response
        resp, addr = self.conn.listen_single_datagram()
        ack_resp = Segment()
        ack_resp.set_from_bytes(resp)
        ack_flag = ack_resp.get_flag()
        if addr == client_addr and ack_flag.ack:
            # TODO : Do something
            print(f"Handshake success with {client_addr}")
        else:
            print(f"Handshake failed with {client_addr}")






if __name__ == '__main__':
    main = Server()
    print(f"Server started at {main.ip}:{main.port}...")
    print("Listening to broadcast address for clients.")
    main.listen_for_clients()

    print(f"\n{len(main.client_conn_list)} clients found:")
    for i, (ip, port) in enumerate(main.client_conn_list, start=1):
        print(f"{i}. {ip}:{port}")

    print("\nCommencing file transfer...")
    main.start_file_transfer()
