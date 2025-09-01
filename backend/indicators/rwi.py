import pandas as pd
import numpy as np
from .ta_utils import REF, ABS, MA, MAX

def calculate(data, N=14):
    high = data['HIGH']
    low = data['LOW']
    close = data['CLOSE']
    tr = pd.Series(np.maximum.reduce([ABS(high - low), ABS(high - REF(close, 1)), ABS(REF(close, 1) - low)]), index=high.index)
    atr = MA(tr, N)
    rwih = (high - REF(low, 1)) / (atr * np.sqrt(N))
    rwil = (REF(high, 1) - low) / (atr * np.sqrt(N))
    return rwih, rwil
