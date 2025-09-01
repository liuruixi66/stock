import pandas as pd
import numpy as np
from .ta_utils import REF, MAX, MA

def calculate(data, N=20):
    high = data['HIGH']
    low = data['LOW']
    close = data['CLOSE']
    open_ = data['OPEN']
    if N is None or N <= 0:
        N = 1
    a = abs(high - REF(close, 1))
    b = abs(low - REF(close, 1))
    c = abs(high - REF(low, 1))
    d = abs(REF(close, 1) - REF(open_, 1))
    k = MAX(a, b)
    m = MAX(high - low, N)
    r1 = a + 0.5 * b + 0.25 * d
    r2 = b + 0.5 * a + 0.25 * d
    r3 = c + 0.25 * d
    r4 = np.where((a >= b) & (a >= c), r1, r2)
    r = np.where((c >= a) & (c >= b), r3, r4)
    si = 50 * (close - REF(close, 1) + (REF(close, 1) - REF(open_, 1)) + 0.5 * (close - open_)) / r * k / m
    return si
