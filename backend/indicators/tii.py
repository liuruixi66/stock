import numpy as np
import pandas as pd
from .ta_utils import MA, REF, IF, SUM, EMA

def calculate(data, N1=40, N2=9):
    close = data['CLOSE']
    M = int(N1/2)+1
    close_ma = MA(close, N1)
    CLOSE = data['CLOSE']
    tii = np.zeros(len(CLOSE))
    for i in range(N1, len(CLOSE)):
        tii[i] = (CLOSE[i] - CLOSE[i-N1]) / CLOSE[i-N1] * 100
    tii_series = pd.Series(tii, index=data.index)
    # 如果后续有 rolling 操作，需用 tii_series 而不是 numpy
    return tii_series
    tii_signal = EMA(tii, N2)
    return tii, tii_signal
