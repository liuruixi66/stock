import pandas as pd
from .ta_utils import MA

def calculate(data, N=20):
    close = data['CLOSE']
    close_ma = MA(close, N)
    tma = MA(close_ma, N)
    return tma
