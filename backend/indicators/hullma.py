import pandas as pd
import numpy as np
from .ta_utils import EMA

def calculate(data, N=20, N2=80):
    close = data['CLOSE']
    x = 2 * EMA(close, int(N/2)) - EMA(close, N)
    hullma = EMA(x, int(np.sqrt(N)))
    return hullma
