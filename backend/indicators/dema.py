import pandas as pd
from .ta_utils import EMA

def calculate(data, N=60):
    close = data['CLOSE']
    ema = EMA(close, N)
    dema = 2 * ema - EMA(ema, N)
    return dema
