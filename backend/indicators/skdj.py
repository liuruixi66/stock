import pandas as pd
from .ta_utils import SMA, MA, REF, MIN, MAX

def calculate(data, N=60, M=5):
    close = data['CLOSE']
    high = data['HIGH']
    low = data['LOW']
    rsv = (close - MIN(low, N)) / (MAX(high, N) - MIN(low, N)) * 100
    mar_sv = SMA(rsv, 3, 1)
    k = SMA(mar_sv, 3, 1)
    d = MA(k, 3)
    return k, d
