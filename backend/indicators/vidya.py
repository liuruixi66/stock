import pandas as pd
from .ta_utils import REF, ABS, SUM

def calculate(data, N=10):
    close = data['CLOSE']
    vi = ABS(close - REF(close, N)) / SUM(ABS(close - REF(close, 1)), N)
    vidya = vi * close + (1 - vi) * REF(close, 1)
    return vidya
