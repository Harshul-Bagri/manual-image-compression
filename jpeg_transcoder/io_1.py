# io_1.py
# JPEG parsing and writing routines (renamed from io.py)

import struct
from utils import SOI, EOI, APP0, DQT, SOF0, DHT, SOS

def parse_jpeg(path):
    """
    Parses a JPEG file into segments and extracts key components:
      - segments: list of (marker, payload) tuples
      - quant_tables: dict of table_id -> 64-entry list (zigzag order)
      - huff_tables: dict of marker (0xC4) -> raw DHT payload
      - frame_header: the SOF0 payload
      - scan_header: the SOS payload
      - scan_data: raw compressed scan bytes (with stuffed 0x00s still in place)
    """
    data = open(path, "rb").read()
    # verify SOI
    assert data[0:2] == b'\xFF\xD8', "Not a valid JPEG (missing SOI)"
    ptr = 2
    segments = []
    quant_tables = {}
    huff_tables = {}
    frame_header = None
    scan_header = None
    scan_data = bytearray()

    while ptr < len(data):
        byte = data[ptr]
        # If not at a marker, we're in scan data
        if byte != 0xFF:
            # All bytes until next marker are scan data
            scan_data.append(byte)
            ptr += 1
            continue

        # Found marker prefix 0xFF
        marker = data[ptr+1]
        ptr += 2

        # EOI has no length/payload
        if marker == EOI:
            segments.append((marker, b""))
            break

        # Read segment length (includes the two length bytes)
        length = struct.unpack_from(">H", data, ptr)[0]
        ptr += 2
        payload = data[ptr:ptr + length - 2]
        ptr += length - 2

        segments.append((marker, payload))

        # Handle DQT: extract quantization tables
        if marker == DQT:
            i = 0
            while i < len(payload):
                pq_tq = payload[i]; i += 1
                pq = pq_tq >> 4        # precision (0=8bit,1=16bit)
                tq = pq_tq & 0x0F      # table identifier
                entry_size = 2 if pq else 1
                count = 64 * entry_size
                raw = payload[i:i+count]
                i += count
                # convert to list of ints
                if pq:
                    # 16-bit big-endian entries
                    table = [(raw[j] << 8) | raw[j+1] for j in range(0, count, 2)]
                else:
                    table = list(raw)
                quant_tables[tq] = table

        # Collect DHT payloads for Huffman parsing later
        elif marker == DHT:
            # store raw DHT payload
            huff_tables.setdefault(DHT, []).append(payload)

        # Save frame header (SOF0) and scan header (SOS)
        elif marker == SOF0:
            frame_header = payload
        elif marker == SOS:
            scan_header = payload

    return {
        "segments":       segments,
        "quant_tables":   quant_tables,
        "huff_tables":    huff_tables,
        "frame_header":   frame_header,
        "scan_header":    scan_header,
        "scan_data":      bytes(scan_data),
    }

def write_jpeg(path, segments, scan_bytes):
    """
    Writes out a new JPEG file:
      - segments: list of (marker, payload) up to and including SOS
      - scan_bytes: raw compressed scan data bytes to follow SOS
    Automatically appends EOI.
    """
    with open(path, "wb") as out:
        # Start Of Image
        out.write(b'\xFF' + bytes([SOI]))

        for marker, payload in segments:
            # Write marker prefix + code
            out.write(b'\xFF' + bytes([marker]))

            if marker == EOI:
                # End Of Image has no payload
                continue

            if marker == SOS:
                # SOS payload: write length & payload, then write scan data
                out.write(struct.pack(">H", len(payload) + 2))
                out.write(payload)
                out.write(scan_bytes)
            else:
                # Other segments: length includes the two length bytes
                out.write(struct.pack(">H", len(payload) + 2))
                out.write(payload)

        # Finally, ensure EOI
        out.write(b'\xFF' + bytes([EOI]))
