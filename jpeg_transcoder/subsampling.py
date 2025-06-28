# subsampling.py
# 4:2:0 chroma subsampling and upsampling for JPEG compression

import numpy as np

def subsample_420(C):
    """
    Perform 4:2:0 subsampling on a chroma channel.
    C: 2D numpy array of shape (H, W)
    Returns: subsampled 2D array of shape (H//2, W//2)
    """
    h, w = C.shape
    if h % 2 != 0 or w % 2 != 0:
        raise ValueError("Image dimensions must be even for 4:2:0 subsampling")
    # reshape into blocks of 2×2, then average
    C2 = C.reshape(h//2, 2, w//2, 2).mean(axis=(1, 3)).astype(int)
    return C2

def upsample_420(C2):
    """
    Perform 4:2:0 upsampling on a subsampled chroma channel.
    C2: 2D numpy array of shape (H2, W2)
    Returns: upsampled 2D array of shape (H2*2, W2*2)
    """
    # repeat rows and columns
    return np.repeat(np.repeat(C2, 2, axis=0), 2, axis=1)
