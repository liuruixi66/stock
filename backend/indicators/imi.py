import pandas as pd
import numpy as np
from .ta_utils import REF, SUM

def calculate(data, N=14):
    close = data['CLOSE']
    open_ = data['OPEN']
    inc = SUM(pd.Series(np.where(close > open_, close - open_, 0), index=close.index), N)
    dec = SUM(pd.Series(np.where(open_ > close, open_ - close, 0), index=close.index), N)
    imi = inc / (inc + dec)
    return imi
