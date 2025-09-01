import pandas as pd
from .ta_utils import EMA, MA, MAX, MIN

def calculate(data, N1=20, N2=20, N3=20):
    high = data['HIGH']
    low = data['LOW']
    close = data['CLOSE']
    m = (MAX(high, N1) + MIN(low, N1)) / 2
    d = close - m
    ds = EMA(EMA(d, N2), N2)
    dhl = EMA(EMA(MAX(high, N1) - MIN(low, N1), N2), N2)
    smi = 100 * ds / dhl
    smima = MA(smi, N3)
    return smi, smima
