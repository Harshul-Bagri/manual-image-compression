# zigzag.py
# Zig-zag reordering and inverse reordering for 8×8 blocks

from utils import ZIGZAG_ORDER

def zigzag_order(block):
    """
    Reorder an 8×8 block into a 1D list of 64 elements following the JPEG zig-zag pattern.
    block: 8×8 nested list (or list of lists)
    Returns: list of 64 ints/floats
    """
    if len(block) != 8 or any(len(row) != 8 for row in block):
        raise ValueError("Input must be an 8×8 block")
    # flatten row-major
    flat = [block[i][j] for i in range(8) for j in range(8)]
    # reorder
    return [flat[idx] for idx in ZIGZAG_ORDER]

def inverse_zigzag(arr):
    """
    Convert a 64-element 1D zig-zag list back into an 8×8 block.
    arr: list of 64 ints/floats
    Returns: 8×8 nested list
    """
    if len(arr) != 64:
        raise ValueError("Input must be a list of 64 elements")
    # place each element at its zig-zag index
    flat = [0] * 64
    for i, idx in enumerate(ZIGZAG_ORDER):
        flat[idx] = arr[i]
    # reshape into 8×8
    return [[flat[r * 8 + c] for c in range(8)] for r in range(8)]
