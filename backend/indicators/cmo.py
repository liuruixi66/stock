import pandas as pd
import numpy as np
from .ta_utils import REF, SUM

def calculate(data, N=20):
    close = data['CLOSE']
    su = SUM(np.maximum(close - REF(close, 1), 0), N)
    sd = SUM(np.maximum(REF(close, 1) - close, 0), N)
    cmo = (su - sd) / (su + sd) * 100
    return cmo
