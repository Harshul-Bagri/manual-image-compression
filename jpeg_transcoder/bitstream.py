# bitstream.py
# Handles bit-level I/O for JPEG scan data with 0xFF–0x00 byte-stuffing

class BitReader:
    """
    Reads bits from a JPEG scan data byte stream, handling 0xFF-0x00 byte stuffing.
    """
    def __init__(self, data: bytes):
        self.data = data
        self.bytepos = 0  # Index of next byte to read
        self.bitpos = 0   # Bit position within current byte (0-7)

    def read_bit(self) -> int:
        if self.bytepos >= len(self.data):
            raise EOFError("No more data to read bits from.")
        byte = self.data[self.bytepos]
        # Extract the bit at the current position
        bit = (byte >> (7 - self.bitpos)) & 1
        self.bitpos += 1
        if self.bitpos == 8:
            # Finished reading this byte
            self.bitpos = 0
            self.bytepos += 1
            # Skip stuffed 0x00 following any 0xFF byte
            if byte == 0xFF and self.bytepos < len(self.data) and self.data[self.bytepos] == 0x00:
                self.bytepos += 1
        return bit

    def read_bits(self, n: int) -> int:
        """
        Read n bits and return as an integer (most-significant-bit first).
        """
        value = 0
        for _ in range(n):
            value = (value << 1) | self.read_bit()
        return value


class BitWriter:
    """
    Writes bits into a byte stream, applying 0xFF-0x00 byte stuffing as needed.
    """
    def __init__(self):
        self.buffer = bytearray()
        self.curr_byte = 0
        self.bitpos = 0  # Number of bits currently in curr_byte (0-7)

    def write_bit(self, bit: int):
        """
        Write a single bit (0 or 1).
        """
        self.curr_byte = (self.curr_byte << 1) | (bit & 1)
        self.bitpos += 1
        if self.bitpos == 8:
            self._flush_curr_byte()

    def write_bits(self, n: int, value: int):
        """
        Write n bits from 'value', most-significant-bit first.
        """
        for shift in range(n - 1, -1, -1):
            self.write_bit((value >> shift) & 1)

    def _flush_curr_byte(self):
        """
        Flush the current byte to the buffer, handling 0xFF stuffing.
        """
        byte = self.curr_byte & 0xFF
        self.buffer.append(byte)
        if byte == 0xFF:
            # After any 0xFF in the payload, JPEG requires a 0x00 stuffing byte
            self.buffer.append(0x00)
        self.curr_byte = 0
        self.bitpos = 0

    def flush(self):
        """
        Flush remaining bits by padding with zeros to form a full byte.
        """
        if self.bitpos > 0:
            self.curr_byte <<= (8 - self.bitpos)
            self._flush_curr_byte()

    def get_bytes(self) -> bytes:
        """
        Finalize and return the byte stream.
        """
        self.flush()
        return bytes(self.buffer)
