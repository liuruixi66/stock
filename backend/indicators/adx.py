import pandas as pd
import numpy as np
from .ta_utils import REF, ABS, SUM

def calculate(data, N1=14):
    high = data['HIGH']
    low = data['LOW']
    close = data['CLOSE']
    max_high = ABS(high - REF(high, 1))
    max_low = ABS(REF(low, 1) - low)
    xpdm = pd.Series(np.where(max_high > max_low, high - REF(high, 1), 0), index=high.index)
    pdm = SUM(xpdm, N1)
    xndm = pd.Series(np.where(max_low > max_high, REF(low, 1) - low, 0), index=low.index)
    ndm = SUM(xndm, N1)
    tr = pd.Series(np.maximum.reduce([ABS(high - low), ABS(high - close), ABS(low - close)]), index=high.index)
    tr_sum = SUM(tr, N1)
    di_pos = pdm / tr_sum
    di_neg = ndm / tr_sum
    return di_pos, di_neg
