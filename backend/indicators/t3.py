import pandas as pd
from .ta_utils import EMA

def calculate(data, N=20, VA=0.5):
    close = data['CLOSE']
    T1 = EMA(close, N) * (1 + VA * EMA(EMA(close, N), N) * VA)
    T2 = EMA(T1, N) * (1 + VA) - EMA(EMA(T1, N), N) * VA
    T3 = EMA(T2, N) * (1 + VA) - EMA(EMA(T2, N), N) * VA
    return T3
