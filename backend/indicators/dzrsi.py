import pandas as pd
from .ta_utils import MA, STD, REF

def calculate(data, N=40, M=3, PARAM=2):
    close = data['CLOSE']
    rsi_middle = MA(close, N)
    rsi_upper = rsi_middle + PARAM * STD(close, N)
    rsi_lower = rsi_middle - PARAM * STD(close, N)
    rsi_ma = MA(close, M)
    return rsi_middle, rsi_upper, rsi_lower, rsi_ma
