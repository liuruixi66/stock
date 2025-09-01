import numpy as np
import pandas as pd
from .ta_utils import REF

def calculate(data, N=20):
    close = data['CLOSE']
    weights = np.arange(N, 0, -1)
    wma = close.rolling(window=N).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    return wma
