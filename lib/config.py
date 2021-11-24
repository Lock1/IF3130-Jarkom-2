# Config file
# Tested on WSL2 with Ubuntu 20.04 and Virtualbox Ubuntu 20.04
AUTO_CONFIG_IP        = True       # Will override BIND_IP and BROADCAST_IP configuration

# If AUTO_CONFIG_IP True, change INTERFACE_NAME value
CLIENT_INTERFACE_NAME = b"eth0"
SERVER_INTERFACE_NAME = b"eth0"
# Else, edit BIND_IP
CLIENT_BIND_IP        = "localhost"
SERVER_BIND_IP        = "localhost"


CLIENT_SEND_PORT      = 5005         # Target port for sending segment
SERVER_BROADCAST_IP   = ""           # Target IP for client broadcast

LISTEN_BUFFER_SIZE    = 2**16
TCP_WINDOW_SIZE       = 5

SERVER_TRANSFER_ACK_TIMEOUT = 0.1    # Unit : second


# Bonus
SEND_METADATA         = True
USE_PARALLEL          = True
