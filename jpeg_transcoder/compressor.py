# compressor.py
import sys
import struct

from io_1 import parse_jpeg
from bitstream import BitReader, BitWriter
from huffman import parse_dht, decode_symbols, encode_symbols
from zigzag import zigzag_order, inverse_zigzag
from rle import encode_ac, decode_ac
from quantization import quantize_block, dequantize_block
from utils import SOI, EOI, APP0, DQT, DHT, SOS, ZIGZAG_ORDER

def build_scaled_qtables(orig_qtables_flat, quality):
    scaled = {}
    for tid, flat in orig_qtables_flat.items():
        mat = inverse_zigzag(flat)
        factor = (5000/quality) if quality < 50 else (200 - quality*2)
        new_mat = [
            [ max(1, min(255, int((mat[i][j]*factor + 50)/100)))
              for j in range(8) ]
            for i in range(8)
        ]
        scaled[tid] = new_mat
    return scaled

def rebuild_dqt_payload(scaled_qtables):
    payload = bytearray()
    for tid, mat in scaled_qtables.items():
        payload.append(tid & 0x0F)
        flat = [mat[i][j] for i in range(8) for j in range(8)]
        zz   = [flat[idx] for idx in ZIGZAG_ORDER]
        payload.extend(zz)
    return bytes(payload)

def build_segment(marker, payload):
    length = len(payload) + 2
    return b'\xFF' + bytes([marker]) + struct.pack(">H", length) + payload

def rebuild_jpeg(segments, frame_marker, frame_payload, scan_payload, scaled_qtables, new_scan, out_path):
    with open(out_path, "wb") as out:
        # 1) SOI
        out.write(b'\xFF' + bytes([SOI]))

        # 2) APPn / COM
        for m, p in segments:
            if (APP0 <= m <= 0xEF) or m == 0xFE:
                out.write(build_segment(m, p))

        # 3) New DQT
        out.write(build_segment(DQT, rebuild_dqt_payload(scaled_qtables)))

        # 4) Frame header (SOFx)
        out.write(build_segment(frame_marker, frame_payload))

        # 5) All DHT
        for m, p in segments:
            if m == DHT:
                out.write(build_segment(DHT, p))

        # 6) Any other markers before SOS
        for m, p in segments:
            if m < SOS and m not in (SOI, APP0, DQT, frame_marker, DHT):
                out.write(build_segment(m, p))

        # 7) SOS
        out.write(build_segment(SOS, scan_payload))

        # 8) Compressed scan data
        out.write(new_scan)

        # 9) EOI
        out.write(b'\xFF' + bytes([EOI]))


def compress(input_path, output_path, quality=50):
    # 1) Parse
    data = parse_jpeg(input_path)
    segments         = data["segments"]
    orig_qtables     = data["quant_tables"]
    scan_data        = data["scan_data"]
    scan_payload     = data["scan_header"]

    # 2) Locate frame header (first SOFx marker between 0xC0–0xCF, excluding DHT/SOS)
    frame_marker, frame_payload = next(
        (m, p) for (m, p) in segments
        if 0xC0 <= m <= 0xCF and m not in (DHT, SOS)
    )

    # 3) Parse DHT
    dc_tables = {}
    ac_tables = {}
    for m, p in segments:
        if m == DHT:
            dt, at = parse_dht(p)
            dc_tables.update(dt)
            ac_tables.update(at)

    # 4) Decode all blocks
    br = BitReader(scan_data)
    all_syms = []
    try:
        while True:
            all_syms.append(decode_symbols(br, dc_tables[0], ac_tables[0]))
    except EOFError:
        pass

    # 5) Scale Q-tables
    scaled_qtables = build_scaled_qtables(orig_qtables, quality)

    # 6) Re-encode scan
    bw = BitWriter()
    for syms in all_syms:
        coeffs = decode_ac(syms)
        qblk   = inverse_zigzag(coeffs)
        deq    = dequantize_block(qblk, inverse_zigzag(orig_qtables[0]))
        rq     = quantize_block(deq, scaled_qtables[0])
        zz     = zigzag_order(rq)
        new_syms = encode_ac(zz)
        encode_symbols(new_syms, dc_tables[0], ac_tables[0], bw)
    new_scan = bw.get_bytes()

    # 7) Write output
    rebuild_jpeg(segments, frame_marker, frame_payload, scan_payload,
                 scaled_qtables, new_scan, output_path)
    print(f"Compressed '{input_path}' → '{output_path}' (Q={quality})")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python compressor.py input.jpg output.jpg [quality]")
        sys.exit(1)
    inp, outp = sys.argv[1], sys.argv[2]
    q = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    compress(inp, outp, q)
