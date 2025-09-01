import pandas as pd
from .ta_utils import EMA, REF

def calculate(data, N=10):
    high = data['HIGH']
    low = data['LOW']
    h_l_ema = EMA(high - low, N)
    cv = (h_l_ema - REF(h_l_ema, N)) / REF(h_l_ema, N) * 100
    return cv
