import pandas as pd
from .ta_utils import EMA

def calculate(data, N1=20, N2=100):
    close = data['CLOSE']
    zlmacd = (2 * EMA(close, N1) - EMA(EMA(close, N1), N1)) - (2 * EMA(close, N2) - EMA(EMA(close, N2), N2))
    return zlmacd
