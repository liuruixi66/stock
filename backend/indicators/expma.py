import pandas as pd
from .ta_utils import EMA

def calculate(data, N1=12, N2=50):
    close = data['CLOSE']
    ema1 = EMA(close, N1)
    ema2 = EMA(close, N2)
    return ema1, ema2
