import pandas as pd
import numpy as np
from .ta_utils import REF, ABS, MAX, SUM

def calculate(data, N=40):
    high = data['HIGH']
    low = data['LOW']
    hl = high + low
    high_abs = ABS(high - REF(high, 1))
    low_abs = ABS(low - REF(low, 1))
    dmz = pd.Series(np.where(hl > REF(hl, 1), np.maximum(high_abs, low_abs), 0), index=hl.index)
    dmf = pd.Series(np.where(hl < REF(hl, 1), np.maximum(high_abs, low_abs), 0), index=hl.index)
    diz = SUM(dmz, N) / (SUM(dmz, N) + SUM(dmf, N))
    dif = SUM(dmf, N) / (SUM(dmz, N) + SUM(dmf, N))
    ddi = diz - dif
    return ddi
