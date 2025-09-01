import pandas as pd
from .ta_utils import EMA

def calculate(data, N=20, M=10):
    close = data['CLOSE']
    rsi = EMA(close, N)
    do = EMA(EMA(rsi, N), M)
    return do
