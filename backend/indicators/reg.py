import pandas as pd
import numpy as np
from .ta_utils import REF, MA

def calculate(data, N=40):
    close = data['CLOSE']
    if N is None or N <= 0:
        N = 1
    CLOSE = data['CLOSE']
    reg = np.full(len(CLOSE), np.nan)
    x = np.arange(N)
    for i in range(N-1, len(CLOSE)):
        y = CLOSE[i-N+1:i+1].values
        if len(y) == N:
            A = np.vstack([x, np.ones(len(x))]).T
            m, c = np.linalg.lstsq(A, y, rcond=None)[0]
            reg[i] = m * x[-1] + c
    return pd.Series(reg, index=data.index)
