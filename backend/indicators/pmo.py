import pandas as pd
from .ta_utils import MA, REF

def calculate(data, N1=10, N2=30, N3=20):
    close = data['CLOSE']
    if N1 is None or N1 <= 0:
        N1 = 1
    if N2 is None or N2 <= 0:
        N2 = 1
    if N3 is None or N3 <= 0:
        N3 = 1
    roc = (close - REF(close, 1)) / REF(close, 1) * 100
    roc_ma = MA(roc, 2 / N1)
    roc_ma10 = roc_ma * 10
    pmo = MA(roc_ma10, 2 / N2)
    pmo_signal = MA(pmo, 2 / (N3 + 1))
    return pmo, pmo_signal
