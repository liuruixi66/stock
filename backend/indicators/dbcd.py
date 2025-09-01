import pandas as pd
from .ta_utils import SMA, REF

def calculate(data, N=5, M=16, T=17):
    close = data['CLOSE']
    bias = (close - SMA(close, N, 1)) / SMA(close, N, 1) * 100
    bias_diff = bias - REF(bias, M)
    dbcd = SMA(bias_diff, T, 1)
    return dbcd
