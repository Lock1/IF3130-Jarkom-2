import struct
# Struct format used:
#   B -> Unsigned char  (1 byte)
#   H -> Unsigned short (x86, 2 bytes)
#   I -> Unsigned int   (x86, 4 bytes)
#   x -> 1 byte padding

# Constant
SYN_FLAG = 0b00000010
ACK_FLAG = 0b00010000
FIN_FLAG = 0b00000001

class SegmentFlag:
    def __init__(self, flag):
        self.syn = bool(flag & SYN_FLAG)
        self.ack = bool(flag & ACK_FLAG)
        self.fin = bool(flag & FIN_FLAG)

    def get_flag_bytes(self) -> "bytes":
        result  = 0b00000000
        result |= SYN_FLAG if self.syn else 0
        result |= ACK_FLAG if self.ack else 0
        result |= FIN_FLAG if self.fin else 0
        return struct.pack("B", result)





class Segment:
    def __init__(self):
        self.sequence = 0
        self.ack      = 0
        self.flag     = SegmentFlag(0b00000000)
        self.checksum = 0
        self.data     = b""

    def __str__(self):
        output = "-- Segment Information --\n"
        output += f"{'Sequence number':24} | {self.sequence}\n"
        output += f"{'Acknowledgement number':24} | {self.ack}\n"
        output += f"{'Flags':24} | [SYN {self.flag.syn}] [ACK {self.flag.ack}] [FIN {self.flag.fin}]\n"
        output += f"{'Checksum':24} | {hex(self.checksum)}\n"
        output += f"{'Valid checksum':24} | {self.valid_checksum()}\n"
        output += f"{'Data length':24} | {len(self.data)} bytes"
        return output

    def __calculate_checksum(self) -> int:
        checksum      = 0x0000
        # Mask and shift 4 bytes unsigned integer to 2 bytes / 16 bit integer
        seq_upper     = (self.sequence & 0xFFFF0000) >> 16
        seq_lower     = (self.sequence & 0x0000FFFF)
        ack_upper     = (self.ack      & 0xFFFF0000) >> 16
        ack_lower     = (self.ack      & 0x0000FFFF)

        checksum      = (checksum + seq_upper + seq_lower) & 0xFFFF
        checksum      = (checksum + ack_upper + ack_lower) & 0xFFFF
        flag_in_char  = struct.unpack("B", self.flag.get_flag_bytes())[0]
        checksum      = (checksum + flag_in_char)          & 0xFFFF
        checksum      = (checksum + self.checksum)         & 0xFFFF

        # Sum all 16-bit chunks of data
        for i in range(0, len(self.data), 2):
            buffer         = self.data[i:i+2]
            if len(buffer) == 1:
                buffer += struct.pack("x")
            chunk    = struct.unpack("H", buffer)[0]
            checksum = (checksum + chunk) & 0xFFFF

        checksum = 0xFFFF - checksum    # Unsigned 16-bit bitwise not
        return checksum


    def set_header(self, header : dict):
        self.sequence = header["sequence"]
        self.ack      = header["ack"]

    def set_payload(self, payload : "bytes"):
        self.data     = payload

    def set_flag(self, flag_list : list):
        flag_res = 0b00000000
        for flag in flag_list:
            flag_res |= flag
        self.flag     = SegmentFlag(flag_res)

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

    def get_payload(self) -> "bytes":
        return self.data

    def valid_checksum(self) -> bool:
        # Sum everything and bitwise not
        # Everything else except checksum + checksum = 0xFFFF
        # 0xFFFF bitwise not = 0x0000
        return self.__calculate_checksum() == 0x0000
