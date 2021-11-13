import struct

class SegmentFlag:
    def __init__(self, flag):
        # Input : Tuple of 3 bool or integer
        if type(flag) == tuple:
            self.syn = flag[0]
            self.ack = flag[1]
            self.fin = flag[2]
        else:
            self.syn = bool(flag & 0b00000010)
            self.ack = bool(flag & 0b00010000)
            self.fin = bool(flag & 0b00000001)

    def get_flag_bytes(self) -> "bytes":
        result  = 0b00000000
        result |= 0b00000010 if self.syn else 0
        result |= 0b00010000 if self.ack else 0
        result |= 0b00000001 if self.fin else 0
        return struct.pack("B", result)





class Segment:
    def __init__(self):
        self.sequence = 0
        self.ack      = 0
        self.flag     = SegmentFlag((False, False, False))
        self.checksum = 0
        self.data     = b""

    def __str__(self):
        output = "-- Segment Information --\n"
        output += f"{'Sequence number':24} | {self.sequence}\n"
        output += f"{'Acknowledgement number':24} | {self.ack}\n"
        output += f"{'Flags':24} | [SYN {self.flag.syn}] [ACK {self.flag.ack}] [FIN {self.flag.fin}]\n"
        output += f"{'Checksum':24} | {hex(self.checksum)}\n"
        output += f"{'Valid checksum':24} | {self.valid_checksum()}\n"
        output += f"{'Data length':24} | {len(self.data)} bytes\n"
        return output

    def __calculate_checksum(self) -> int:
        checksum     = 0x0000
        checksum     = (checksum + self.sequence) & 0xFFFF
        checksum     = (checksum + self.ack)      & 0xFFFF
        flag_in_char = struct.unpack("B", self.flag.get_flag_bytes())[0]
        checksum     = (checksum + flag_in_char)  & 0xFFFF
        checksum     = (checksum + self.checksum) & 0xFFFF
        for i in range(0, len(self.data), 2):
            buffer         = self.data[i:i+2]
            if len(buffer) == 1:
                buffer += struct.pack("x")
            chunk         = struct.unpack("H", buffer)[0]
            checksum = (checksum + chunk) & 0xFFFF
        checksum = 0xFFFF - checksum
        return checksum


    def set_header(self, header : dict):
        self.sequence = header["sequence"]
        self.ack      = header["ack"]

    def set_payload(self, payload : "bytes"):
        self.data     = payload

    def set_flag(self, s : bool, a : bool, f : bool):
        self.flag     = SegmentFlag((s, a, f))

    def set_from_bytes(self, src : "bytes"):
        header_tuple  = struct.unpack("IIBxH", src[0:12])
        self.data     = src[12:]
        self.sequence = header_tuple[0]
        self.ack      = header_tuple[1]
        self.flag     = SegmentFlag(header_tuple[2])
        self.checksum = header_tuple[3]


    def get_bytes(self) -> "bytes":
        result        = b""
        result        += struct.pack("I", self.sequence) # Sequence number        : 4 bytes
        result        += struct.pack("I", self.ack)      # Acknowledgement number : 4 bytes
        result        += self.flag.get_flag_bytes()      # Flags                  : 1 byte
        result        += struct.pack("x")                # [empty] / Padding byte : 1 byte
        self.checksum = self.__calculate_checksum()
        result        += struct.pack("H", self.checksum) # Checksum               : 2 bytes
        result        += self.data                       # Data                   : 0-32768 bytes
        return result

    def get_flag(self) -> SegmentFlag:
        return self.flag

    def get_header(self) -> dict:
        return {"sequence" : self.sequence, "ack" : self.ack}

    def valid_checksum(self) -> bool:
        return self.__calculate_checksum() == 0x0000
