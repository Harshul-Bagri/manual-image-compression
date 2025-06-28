# dct.py
# Forward & inverse 2D DCT for 8×8 blocks

import math

# Precompute cosine values for performance
COS = [[math.cos((2 * x + 1) * u * math.pi / 16) for x in range(8)] for u in range(8)]

def forward_dct(block):
    """
    Perform the 8×8 forward DCT on a block of pixel values (level-shifted by -128).
    block: 8×8 list of ints or floats
    Returns: 8×8 list of floats (DCT coefficients)
    """
    F = [[0.0] * 8 for _ in range(8)]
    for u in range(8):
        for v in range(8):
            cu = 1 / math.sqrt(2) if u == 0 else 1
            cv = 1 / math.sqrt(2) if v == 0 else 1
            s = 0.0
            for x in range(8):
                for y in range(8):
                    s += block[x][y] * COS[u][x] * COS[v][y]
            F[u][v] = 0.25 * cu * cv * s
    return F

def inverse_dct(F):
    """
    Perform the 8×8 inverse DCT to reconstruct pixel values.
    F: 8×8 list of floats (DCT coefficients)
    Returns: 8×8 list of floats (reconstructed block, still level-shifted)
    """
    block = [[0.0] * 8 for _ in range(8)]
    for x in range(8):
        for y in range(8):
            s = 0.0
            for u in range(8):
                for v in range(8):
                    cu = 1 / math.sqrt(2) if u == 0 else 1
                    cv = 1 / math.sqrt(2) if v == 0 else 1
                    s += cu * cv * F[u][v] * COS[u][x] * COS[v][y]
            block[x][y] = 0.25 * s
    return block
