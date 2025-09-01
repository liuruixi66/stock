import pandas as pd
from .ta_utils import EMA, REF

def calculate(data, N=20):
    close = data['CLOSE']
    triple_ema = EMA(EMA(EMA(close, N), N), N)
    trix = (triple_ema - REF(triple_ema, 1)) / REF(triple_ema, 1)
    return trix
