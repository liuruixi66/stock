import numpy as np
import pandas as pd

from .ta_utils import REF, ABS, SUM, MA


def calculate(data, N=20):
    high = data["HIGH"]
    low = data["LOW"]
    close = data["CLOSE"]
    open_ = data["OPEN"]
    a = ABS(high - REF(close, 1))
    b = ABS(low - REF(close, 1))
    c = ABS(high - REF(low, 1))
    d = ABS(REF(close, 1) - REF(open_, 1))
    k = np.maximum(a, b)
    m = np.maximum(high - low, N)
    r1 = a + 0.5 * b + 0.25 * d
    r2 = b + 0.5 * a + 0.25 * d
    r3 = c + 0.25 * d
    r4 = np.where((a >= b) & (a >= c), r1, r2)
    r = np.where((c >= a) & (c >= b), r3, r4)
    si = 50 * (close - REF(close, 1) + (REF(close, 1) - REF(open_, 1)) + 0.5 * (close - open_)) / r * k / m
    asi = np.cumsum(si)
    asima = MA(asi, N)
    return asi, asima
