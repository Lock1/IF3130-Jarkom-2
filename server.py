import lib.arg, lib.conn
import lib.config

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


    def __valid_broadcast_req(self, data : "bytes") -> bool:
        # TODO : Proper checking
        return True


    def listen_for_clients(self):
        self.client_conn_list = []
        broadconn             = lib.conn.UDP_Conn("", self.port)
        waiting_client        = True

        while waiting_client:
            data, addr = broadconn.listen_single_datagram()
            if self.__valid_broadcast_req(data) and addr not in self.client_conn_list:
                self.client_conn_list.append(addr)

                print(f"[!] Client ({addr[0]}:{addr[1]}) found")
                prompt = input("[?] Listen more? (y/n) ")
                if prompt == "n":
                    waiting_client = False

        broadconn.close_connection()


    def send_response_data(self):
        self.conn = lib.conn.UDP_Conn(self.ip, self.port)
        for addr in self.client_conn_list:
            self.conn.send_bytes(b"hehe_response", addr)
        self.conn.close_connection()


if __name__ == '__main__':
    main = Server()
    print(f"Server started at port {main.port}...")
    print("Listening to broadcast address for clients.")
    main.listen_for_clients()
    main.send_response_data()
