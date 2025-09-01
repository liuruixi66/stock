import pandas as pd
import numpy as np
from .ta_utils import SMA, REF

def calculate(data, N=7):
    close = data['CLOSE']
    rmi = SMA(np.maximum(close - REF(close, 4), 0), N, 1) / SMA(abs(close - REF(close, 1)), N, 1) * 100
    return rmi
