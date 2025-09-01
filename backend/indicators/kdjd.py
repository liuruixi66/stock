import pandas as pd
from .ta_utils import REF, MIN, MAX, SMA

def calculate(data, N=20, M=60):
    close = data['CLOSE']
    high = data['HIGH']
    low = data['LOW']
    low_n = MIN(low, N)
    high_n = MAX(high, N)
    stochastics = (close - low_n) / (high_n - low_n) * 100
    stochastics_low = MIN(stochastics, M)
    stochastics_high = MAX(stochastics, M)
    stochastics_double = (stochastics - stochastics_low) / (stochastics_high - stochastics_low) * 100
    K = SMA(stochastics_double, 3, 1)
    D = SMA(K, 3, 1)
    return K, D
