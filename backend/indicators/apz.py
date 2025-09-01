import pandas as pd
from .ta_utils import EMA

def calculate(data, N=10, M=20, PARAM=2):
    high = data['HIGH']
    low = data['LOW']
    close = data['CLOSE']
    vol = EMA(EMA(high - low, N), N)
    upper = EMA(EMA(close, M), M) + PARAM * vol
    lower = EMA(EMA(close, M), M) - PARAM * vol
    return upper, lower
