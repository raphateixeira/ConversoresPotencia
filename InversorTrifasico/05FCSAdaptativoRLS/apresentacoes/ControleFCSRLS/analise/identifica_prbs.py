"""PRBS de 9 bits (mesma do firmware VSI02): +1/-1, periodo 511."""
import numpy as np


def prbs(tap, n=511, semente=0x1FF):
    r, saida = semente, []
    for _ in range(n):
        bit = ((r >> 8) ^ (r >> tap)) & 1
        r = ((r << 1) | bit) & 0x1FF
        saida.append(1.0 if r & 1 else -1.0)
    return np.array(saida)
