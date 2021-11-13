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


    def get_server(self):
        # TODO : Three way handshake
        data = Segment()
        data.set_payload(b"hoho")
        self.conn.send_data(data, (lib.config.SERVER_BIND_IP, 5005))
        # self.conn.send_data(b"hehe", ("", 5005))

    def wait_response(self):
        # TODO : File transfer
        print(self.conn.listen_single_datagram())





if __name__ == '__main__':
    main = Client()
    main.get_server()
    main.wait_response()
