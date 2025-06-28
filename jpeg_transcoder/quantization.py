# quantization.py
# Standard JPEG quantization tables plus scaling & (de)quantization functions

# Standard luminance quantization table (8×8)
STD_LUMA_Q = [
    [16, 11, 10, 16, 24,  40,  51,  61],
    [12, 12, 14, 19, 26,  58,  60,  55],
    [14, 13, 16, 24, 40,  57,  69,  56],
    [14, 17, 22, 29, 51,  87,  80,  62],
    [18, 22, 37, 56, 68, 109, 103,  77],
    [24, 35, 55, 64, 81, 104, 113,  92],
    [49, 64, 78, 87,103, 121, 120, 101],
    [72, 92, 95, 98,112, 100, 103,  99],
]

# Standard chrominance quantization table (8×8)
STD_CHROMA_Q = [
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
]

def scale_table(table, quality):
    """
    Scale a standard quantization table for the given quality factor (1-100).
    quality: integer between 1 (lowest quality, highest compression)
             and 100 (highest quality, lowest compression).
    Returns a new 8×8 table of integers between 1 and 255.
    """
    if quality < 1:
        quality = 1
    if quality > 100:
        quality = 100

    # JPEG quality scaling formula
    if quality < 50:
        factor = 5000 / quality
    else:
        factor = 200 - quality * 2

    new_table = []
    for row in table:
        new_row = []
        for v in row:
            q = int((v * factor + 50) / 100)
            # Clamp to valid range [1,255]
            q = max(1, min(q, 255))
            new_row.append(q)
        new_table.append(new_row)

    return new_table

def quantize_block(block, q_table):
    """
    Quantize an 8×8 block of DCT coefficients.
    block: 8×8 list (or nested list) of floats (DCT values).
    q_table: 8×8 list of ints (quantization table).
    Returns: 8×8 list of ints.
    """
    return [
        [int(round(block[i][j] / q_table[i][j])) for j in range(8)]
        for i in range(8)
    ]

def dequantize_block(q_block, q_table):
    """
    Dequantize an 8×8 block of quantized DCT coefficients.
    q_block: 8×8 list of ints.
    q_table: 8×8 list of ints (quantization table used).
    Returns: 8×8 list of floats.
    """
    return [
        [q_block[i][j] * q_table[i][j] for j in range(8)]
        for i in range(8)
    ]
