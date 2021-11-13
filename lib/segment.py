import struct

# Segment part sizes :
#   Sequence = 4 bytes
#   Acknowledgement = 4 bytes
#   Flags = 1 byte
#   Checksum = 2 bytes
#   Data = 32768 bytes
#   Total : 2**16 = 65536 bytes

class SegmentFlag:
    def __init__(self, flag_tuple : (bool, bool, bool)):
        self.syn = flag_tuple[0]
        self.ack = flag_tuple[1]
        self.fin = flag_tuple[2]



class Segment:
    def __init__(self):
        self.sequence = None
        self.ack      = None
        self.flag     = None
        self.checksum = None
        self.data     = None

    def __calculate_checksum(self):
        # TODO : Add
        self.checksum = ""

    def set_header(self, header : dict):
        self.sequence = header["sequence"]
        self.ack      = header["ack"]
        # Auto checksum (?)

    def set_payload(self, payload : "bytes"):
        self.data     = payload

    def get_bytes(self) -> "bytes":
        result = self.data

        return result


    def set_flag(self, s, a, f):
        self.flag = SegmentFlag((s, a, f))

    def get_flag(self) -> (bool, bool, bool):
        # TODO : Test endianness
        syn_flag = self.flag & 0b00000010
        ack_flag = self.flag & 0b00010000
        fin_flag = self.flag & 0b00000001
        return SegmentFlag((syn_flag, ack_flag, fin_flag))

    def valid_checksum(self) -> bool:
        pass
