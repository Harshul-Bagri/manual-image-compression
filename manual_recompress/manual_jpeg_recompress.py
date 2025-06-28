# manual_jpeg_recompress.py
# Simplified JPEG “recompression” using Pillow for I/O and your own DCT/quantization

import sys
import math
import numpy as np
from PIL import Image

# Standard 8×8 luminance quantization table
STD_LUMA_Q = np.array([
    [16,11,10,16,24,40,51,61],
    [12,12,14,19,26,58,60,55],
    [14,13,16,24,40,57,69,56],
    [14,17,22,29,51,87,80,62],
    [18,22,37,56,68,109,103,77],
    [24,35,55,64,81,104,113,92],
    [49,64,78,87,103,121,120,101],
    [72,92,95,98,112,100,103,99],
])

def build_q_table(std_table, quality):
    """Scale a standard quant table for a given JPEG quality factor."""
    q = max(1, min(100, quality))
    if q < 50:
        scale = 5000 / q
    else:
        scale = 200 - q * 2
    qt = np.floor((std_table * scale + 50) / 100).astype(int)
    qt[qt < 1] = 1
    qt[qt > 255] = 255
    return qt

# Precompute 8×8 DCT basis
_COS = np.array([
    [math.cos((2*x + 1) * u * math.pi / 16) for x in range(8)]
    for u in range(8)
])

def dct2(block):
    """Perform 2D DCT on an 8×8 block (level-shifted)."""
    # apply normalization factors
    cu = np.array([1/math.sqrt(2) if u == 0 else 1 for u in range(8)])
    cv = np.array([1/math.sqrt(2) if v == 0 else 1 for v in range(8)])
    return 0.25 * (cu[:, None] * (_COS @ block @ _COS.T) * cv[None, :])

def idct2(coef):
    """Perform inverse 2D DCT on an 8×8 block of coefficients."""
    cu = np.array([1/math.sqrt(2) if u == 0 else 1 for u in range(8)])
    cv = np.array([1/math.sqrt(2) if v == 0 else 1 for v in range(8)])
    return 0.25 * (_COS.T @ (cu[:, None] * coef * cv[None, :]) @ _COS)

def process_channel(channel, q_table):
    """
    Apply blockwise DCT → quantize → dequantize → iDCT to one channel.
    channel: 2D numpy array (float)
    q_table: 8×8 numpy array (int)
    """
    h, w = channel.shape
    # pad dimensions to multiples of 8
    H = (h + 7) // 8 * 8
    W = (w + 7) // 8 * 8
    padded = np.zeros((H, W), dtype=float)
    padded[:h, :w] = channel

    out = np.zeros_like(padded)
    for by in range(0, H, 8):
        for bx in range(0, W, 8):
            block = padded[by:by+8, bx:bx+8] - 128.0
            C = dct2(block)
            Q = np.round(C / q_table).astype(int)
            C2 = Q * q_table
            block_rec = idct2(C2) + 128.0
            out[by:by+8, bx:bx+8] = block_rec

    # crop to original and clip to [0,255]
    out = out[:h, :w]
    return np.clip(out, 0, 255).astype(np.uint8)

def main():
    if len(sys.argv) != 4:
        print("Usage: python manual_jpeg_recompress.py input.jpg output.jpg quality")
        sys.exit(1)

    input_path, output_path, quality = sys.argv[1], sys.argv[2], int(sys.argv[3])

    # 1) Load and convert to YCbCr
    img = Image.open(input_path).convert("YCbCr")
    Y, Cb, Cr = (np.array(ch, dtype=float) for ch in img.split())

    # 2) Build quantization table
    qY = build_q_table(STD_LUMA_Q, quality)
    # Optionally, define and use a separate STD_CHROMA_Q for Cb/Cr

    # 3) Process each channel
    Y_rec  = process_channel(Y,  qY)
    Cb_rec = process_channel(Cb, qY)
    Cr_rec = process_channel(Cr, qY)

    # 4) Merge, convert to RGB, and save via Pillow
    img_rec = Image.merge("YCbCr", (
        Image.fromarray(Y_rec,  "L"),
        Image.fromarray(Cb_rec, "L"),
        Image.fromarray(Cr_rec, "L")
    )).convert("RGB")
    img_rec.save(output_path, "JPEG", quality=quality)
    print(f"Saved recompressed JPEG to '{output_path}' at quality={quality}")

if __name__ == "__main__":
    main()
