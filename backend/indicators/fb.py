import numpy as np
import pandas as pd
from .ta_utils import MA, REF, ABS

def calculate(data, N=20):
    close = data['CLOSE']
    high = data['HIGH']
    low = data['LOW']
    tr = pd.Series(np.maximum.reduce([high - low, ABS(high - REF(close, 1)), ABS(low - REF(close, 1))]), index=high.index)
    atr = MA(tr, N)
    middle = MA(close, N)
    upper1 = middle + 1.618 * atr
    upper2 = middle + 2.618 * atr
    upper3 = middle + 4.236 * atr
    lower1 = middle - 1.618 * atr
    lower2 = middle - 2.618 * atr
    lower3 = middle - 4.236 * atr
    return upper1, upper2, upper3, lower1, lower2, lower3, middle
