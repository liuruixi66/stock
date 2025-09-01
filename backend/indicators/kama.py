import pandas as pd
from .ta_utils import REF, ABS, SUM

def calculate(data, N=10, N1=2, N2=30):
    close = data['CLOSE']
    direction = close - REF(close, N)
    volatility = SUM(ABS(close - REF(close, 1)), N)
    er = direction / volatility
    fast = 2 / (N1 + 1)
    slow = 2 / (N2 + 1)
    smooth = er * (fast - slow) + slow
    cof = smooth * smooth
    kama = cof * close + (1 - cof) * REF(close, 1)
    return kama
