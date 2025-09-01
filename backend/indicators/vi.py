import pandas as pd
import numpy as np
from .ta_utils import REF, ABS, SUM

def calculate(data, N=40):
    high = data['HIGH']
    low = data['LOW']
    close = data['CLOSE']
    vmp = ABS(high - REF(low, 1))
    vmn = ABS(low - REF(high, 1))
    tr = pd.Series(np.maximum.reduce([ABS(high - low), ABS(low - REF(close, 1)), ABS(high - REF(close, 1))]), index=high.index)
    sumpos = SUM(vmp, N)
    sumneg = SUM(vmn, N)
    trsum = SUM(tr, N)
    vi_pos = sumpos / trsum
    vi_neg = sumneg / trsum
    return vi_pos, vi_neg
