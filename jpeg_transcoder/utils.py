# utils.py
# JPEG utility constants and helper data structures

# JPEG marker codes (marker byte values, without the 0xFF prefix)
SOI  = 0xD8  # Start Of Image
EOI  = 0xD9  # End Of Image
APP0 = 0xE0  # JFIF APP0 segment
DQT  = 0xDB  # Define Quantization Table
SOF0 = 0xC0  # Start Of Frame (Baseline DCT)
DHT  = 0xC4  # Define Huffman Table
SOS  = 0xDA  # Start Of Scan

# Zig-zag scan order for an 8×8 block (maps 2D→1D index)
ZIGZAG_ORDER = [
     0,  1,  5,  6, 14, 15, 27, 28,
     2,  4,  7, 13, 16, 26, 29, 42,
     3,  8, 12, 17, 25, 30, 41, 43,
     9, 11, 18, 24, 31, 40, 44, 53,
    10, 19, 23, 32, 39, 45, 52, 54,
    20, 22, 33, 38, 46, 51, 55, 60,
    21, 34, 37, 47, 50, 56, 59, 61,
    35, 36, 48, 49, 57, 58, 62, 63,
]
