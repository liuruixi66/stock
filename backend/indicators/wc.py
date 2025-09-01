import pandas as pd
from .ta_utils import EMA

def calculate(data, N1=20, N2=40):
    high = data['HIGH']
    low = data['LOW']
    close = data['CLOSE']
    wc = (high + low + 2 * close) / 4
    ema1 = EMA(wc, N1)
    ema2 = EMA(wc, N2)
    return ema1, ema2
