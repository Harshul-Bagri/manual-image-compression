# huffman.py
# JPEG Huffman table parsing, encode & decode routines

from bitstream import BitReader, BitWriter

class HuffmanTable:
    """
    Represents one Huffman table (DC or AC).
    Builds code ↔ symbol mappings from JPEG DHT payload.
    """
    def __init__(self, lengths, symbols):
        """
        lengths: list of 16 ints, number of codes of length 1..16
        symbols: flat list of symbol values in order
        """
        self.codes = {}      # symbol -> (code, length)
        self.decode_map = {} # (code << (16-length)) -> (symbol, length)
        code = 0
        p = 0
        # JPEG spec: assign increasing code values per length
        for bitlen, count in enumerate(lengths, start=1):
            for i in range(count):
                sym = symbols[p]
                self.codes[sym] = (code, bitlen)
                # left-align bits into a 16-bit buffer for easy decode
                self.decode_map[(code << (16 - bitlen))] = (sym, bitlen)
                code += 1
                p += 1
            code <<= 1

    def encode(self, symbol):
        """
        Return (code, length) for given symbol.
        """
        return self.codes[symbol]

    def decode(self, bitreader):
        """
        Read bits until a matching code is found.
        Returns the symbol.
        """
        code = 0
        for length in range(1, 17):
            bit = bitreader.read_bit()
            code = (code << 1) | bit
            # align to 16 bits
            lookup = code << (16 - length)
            if lookup in self.decode_map:
                sym, _ = self.decode_map[lookup]
                return sym
        raise ValueError("Invalid Huffman code")


def parse_dht(payload):
    """
    Parse one or more DHT tables from a JPEG DQT payload.
    Returns two dicts: dc_tables and ac_tables mapping table_id -> HuffmanTable.
    """
    dc_tables = {}
    ac_tables = {}
    i = 0
    while i < len(payload):
        tc_th = payload[i]
        i += 1
        table_class = (tc_th >> 4)  # 0 = DC, 1 = AC
        table_id    = (tc_th & 0x0F)
        # next 16 bytes: code lengths count[1..16]
        lengths = list(payload[i:i+16])
        i += 16
        total_syms = sum(lengths)
        symbols = list(payload[i:i+total_syms])
        i += total_syms
        table = HuffmanTable(lengths, symbols)
        if table_class == 0:
            dc_tables[table_id] = table
        else:
            ac_tables[table_id] = table
    return dc_tables, ac_tables


def encode_coefficient(value, bitwriter):
    """
    Write amplitude bits for a value (positive or negative).
    JPEG uses the 'category' bit representation:
      - For positive val: binary as is.
      - For negative val: inverted bits of magnitude-1.
    """
    if value == 0:
        return 0  # no bits
    size = value.bit_length()
    if value < 0:
        # two's complement style: invert bits of (abs(value))
        em = (1 << size) + value - 1
        bitwriter.write_bits(size, em)
    else:
        bitwriter.write_bits(size, value)
    return size


def encode_symbols(symbols, dc_table, ac_table, bitwriter):
    """
    symbols: list of tuples from rle.encode_ac, e.g.:
      [("DC", dc_value),
       (run, size, amp), ...,
       ("EOB", 0)]
    dc_table: HuffmanTable for DC
    ac_table: HuffmanTable for AC
    bitwriter: BitWriter instance
    """
    # DC
    tag, dc_val = symbols[0]
    assert tag == "DC"
    prev_size = dc_val.bit_length() if dc_val != 0 else 0
    # lookup Huffman code by category = size
    code, length = dc_table.encode(prev_size)
    bitwriter.write_bits(length, code)
    # write amplitude bits
    encode_coefficient(dc_val, bitwriter)

    # AC
    for sym in symbols[1:]:
        if sym[0] == "ZRL":
            # symbol 0xF0
            code, length = ac_table.encode(0xF0)
            bitwriter.write_bits(length, code)
        elif sym[0] == "EOB":
            # symbol 0x00
            code, length = ac_table.encode(0x00)
            bitwriter.write_bits(length, code)
            break
        else:
            run, size, amp = sym
            tag_byte = (run << 4) | size
            code, length = ac_table.encode(tag_byte)
            bitwriter.write_bits(length, code)
            encode_coefficient(amp, bitwriter)


def decode_symbols(bitreader, dc_table, ac_table):
    """
    Read one MCU's worth of symbols (DC + 63 AC) from bitreader.
    Returns list of tuples like in encode_symbols.
    """
    symbols = []
    # DC: decode category
    cat = dc_table.decode(bitreader)
    # read amplitude bits
    amplitude = 0
    if cat > 0:
        amplitude = bitreader.read_bits(cat)
        # if MSB is 0, value is negative
        if amplitude < (1 << (cat-1)):
            amplitude -= (1 << cat) - 1
    symbols.append(("DC", amplitude))

    # AC coefficients
    count = 1
    while count < 64:
        rs = ac_table.decode(bitreader)
        if rs == 0x00:
            symbols.append(("EOB", 0))
            break
        if rs == 0xF0:
            symbols.append(("ZRL", 0))
            count += 16
        else:
            run = rs >> 4
            size = rs & 0x0F
            amp = 0
            if size > 0:
                bits = bitreader.read_bits(size)
                if bits < (1 << (size-1)):
                    bits -= (1 << size) - 1
                amp = bits
            symbols.append((run, size, amp))
            count += run + 1
    return symbols
