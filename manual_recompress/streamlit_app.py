# streamlit_app.py
# Streamlit frontend for manual_jpeg_recompress.py functionality

import streamlit as st
import math
import numpy as np
from PIL import Image
import io
import sys

# ─── DCT / Quantization Helpers ─────────────────────────────────────────────

# Standard 8×8 luminance quant table
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
    cu = np.array([1/math.sqrt(2) if u == 0 else 1 for u in range(8)])
    cv = np.array([1/math.sqrt(2) if v == 0 else 1 for v in range(8)])
    return 0.25 * (cu[:,None] * (_COS @ block @ _COS.T) * cv[None,:])

def idct2(coef):
    """Perform inverse 2D DCT on an 8×8 block of coefficients."""
    cu = np.array([1/math.sqrt(2) if u == 0 else 1 for u in range(8)])
    cv = np.array([1/math.sqrt(2) if v == 0 else 1 for v in range(8)])
    return 0.25 * (_COS.T @ (cu[:,None] * coef * cv[None,:]) @ _COS)

def process_channel(channel, q_table):
    """
    Apply blockwise DCT → quantize → dequantize → iDCT to one channel.
    channel: 2D numpy array (float)
    q_table: 8×8 numpy array (int)
    """
    h, w = channel.shape
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

    return np.clip(out[:h, :w], 0, 255).astype(np.uint8)

# ─── Streamlit UI ───────────────────────────────────────────────────────────

st.title("🎨 Manual Image Recompressor")

st.write("""
Upload an image, choose a quality factor (1–100), and download your recompressed image.  
All DCT/quantization is done by hand.
""")

uploaded = st.file_uploader("Choose an image", type=["jpg","jpeg"])
quality  = st.slider("Quality", 1, 100, 50)

if uploaded:
    # Load and convert to YCbCr
    img = Image.open(uploaded).convert("YCbCr")
    Y, Cb, Cr = [np.array(ch, dtype=float) for ch in img.split()]

    if st.button("Compress!"):
        # Build quant table
        qY = build_q_table(STD_LUMA_Q, quality)

        # Process each channel
        Y2  = process_channel(Y,  qY)
        Cb2 = process_channel(Cb, qY)
        Cr2 = process_channel(Cr, qY)

        # Reconstruct and save to in-memory buffer
        out_img = Image.merge("YCbCr", (
            Image.fromarray(Y2,  "L"),
            Image.fromarray(Cb2, "L"),
            Image.fromarray(Cr2, "L")
        )).convert("RGB")

        buf = io.BytesIO()
        out_img.save(buf, format="JPEG", quality=quality)
        buf.seek(0)

        st.image(out_img, caption=f"Compressed @ Q={quality}", use_column_width=True)
        st.download_button(
            "Download recompressed image",
            data=buf,
            file_name=f"recompressed_q{quality}.jpg",
            mime="image/jpeg"
        )
