import lib.arg, lib.conn
import lib.config

args = {
    "port" : (int, "Client port"),
    "path" : (str, "Destination path"),
    "-m"   : (None, "Metadata"),
    "-p"   : (None, "Parallel")
}

parser = lib.arg.ArgParser("Client", args)
args   = parser.get_parsed_args()

client_ip   = lib.config.CLIENT_BIND_IP
client_port = args.port

connection = lib.conn.UDP_Conn(client_ip, client_port)
connection.send_bytes(b"hehe", (lib.config.SERVER_BIND_IP, 5005))
