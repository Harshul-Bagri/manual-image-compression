# rle.py
# Run-length encoding and decoding for JPEG AC coefficients

def encode_ac(coeffs):
    """
    Run-length encode a list of 64 DCT coefficients (first is DC, rest AC).
    coeffs: list of 64 ints
    Returns: list of symbols, where each symbol is one of:
      - ("DC", dc_value)
      - (run, size, amplitude) for AC non-zero coefficients
      - ("ZRL", 0) for zero-run-length of 16 zeros
      - ("EOB", 0) to mark end of block when trailing zeros remain
    """
    if len(coeffs) != 64:
        raise ValueError("Input must be a list of 64 coefficients")
    out = []
    # DC coefficient
    dc = coeffs[0]
    out.append(("DC", dc))

    # AC coefficients
    run = 0
    for c in coeffs[1:]:
        if c == 0:
            run += 1
        else:
            # Emit ZRL symbols for runs > 15
            while run > 15:
                out.append(("ZRL", 0))
                run -= 16
            # Determine category size (number of bits to represent amplitude)
            size = c.bit_length() if c > 0 else (-c).bit_length()
            # Append (run, size, amplitude)
            out.append((run, size, c))
            run = 0

    # If trailing zeros remain, emit EOB
    if run > 0:
        out.append(("EOB", 0))

    return out


def decode_ac(symbols):
    """
    Decode a run-length–encoded symbol list back into 64 coefficients.
    symbols: list as produced by encode_ac
    Returns: list of 64 ints
    """
    coeffs = [0] * 64
    idx = 0

    # Process DC
    tag, dc_val = symbols[0]
    if tag != "DC":
        raise ValueError("First symbol must be DC")
    coeffs[0] = dc_val
    idx = 1

    # Process AC
    for sym in symbols[1:]:
        if sym[0] == "ZRL":
            # Zero Run Length of 16 zeros
            run = 16
            for i in range(run):
                if idx >= 64:
                    break
                coeffs[idx] = 0
                idx += 1
        elif sym[0] == "EOB":
            # End Of Block: fill remaining with zeros
            while idx < 64:
                coeffs[idx] = 0
                idx += 1
            break
        else:
            run, size, amp = sym
            # Insert 'run' zeros
            for i in range(run):
                if idx >= 64:
                    break
                coeffs[idx] = 0
                idx += 1
            # Insert the non-zero amplitude
            if idx < 64:
                coeffs[idx] = amp
                idx += 1

    # If we exit without EOB, pad any remaining coefficients with zeros
    while idx < 64:
        coeffs[idx] = 0
        idx += 1

    return coeffs
