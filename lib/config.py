# Config file
AUTO_CONFIG_IP        = True         # Will override BIND_IP configuration
CLIENT_INTERFACE_NAME = b"eth0"
SERVER_INTERFACE_NAME = b"eth0"

CLIENT_BIND_IP        = "127.0.0.1"
SERVER_BIND_IP        = "127.0.0.1"
CLIENT_SEND_PORT      = 5005         # Target port for sending segment
SERVER_BROADCAST_IP   = ""

LISTEN_BUFFER_SIZE    = 2**16
TCP_WINDOW_SIZE       = 5

SERVER_TRANSFER_ACK_TIMEOUT = 0.1    # Unit : second


# Bonus
SEND_METADATA         = True
USE_PARALLEL          = True
