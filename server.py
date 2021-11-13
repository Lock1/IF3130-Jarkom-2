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
                if prompt == "y":
                    waiting_client = True
                else:
                    waiting_client = False

        broadconn.close_connection()


    def send_response_data(self):
        self.conn = lib.conn.UDP_Conn(self.ip, self.port)
        data = Segment()
        data.set_payload(b"hehe_response")
        for addr in self.client_conn_list:
            self.conn.send_data(data, addr)
        self.conn.close_connection()





if __name__ == '__main__':
    main = Server()
    print(f"Server started at port {main.port}...")
    print("Listening to broadcast address for clients.")
    main.listen_for_clients()

    print(f"\n{len(main.client_conn_list)} clients found:")
    for i, (ip, port) in enumerate(main.client_conn_list, start=1):
        print(f"{i}. {ip}:{port}")

    print("\nCommencing file transfer...")
    main.send_response_data()
