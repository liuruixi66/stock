import pandas as pd
from .ta_utils import EMA, REF, ABS

def calculate(data, N1=25, N2=13):
    close = data['CLOSE']
    tsi = EMA(EMA(close - REF(close, 1), N1), N2) / EMA(EMA(ABS(close - REF(close, 1)), N1), N2) * 100
    return tsi
