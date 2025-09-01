import pandas as pd
import numpy as np
from .ta_utils import REF, ABS, MA, MIN, MAX

def calculate(data, N=14):
    import pandas as pd
    high = data['HIGH']
    low = data['LOW']
    close = data['CLOSE']
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=N, min_periods=1).mean()
    middle = MA(close, N)
    upper1 = MIN(low, int(N/2)) + atr * 3
    lower1 = MAX(high, int(N/2)) - atr * 3
    return atr, middle, upper1, lower1
