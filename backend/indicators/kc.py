import pandas as pd
import numpy as np
from .ta_utils import MAX, MIN, ABS, REF, MA, EMA

def calculate(data, N=14, K=2):
    high = data['HIGH']
    low = data['LOW']
    close = data['CLOSE']
    typical = (high + low + close) / 3
    ma = typical.rolling(window=N, min_periods=1).mean()
    tr = (high - low).rolling(window=N, min_periods=1).mean()
    upper = ma + K * tr
    lower = ma - K * tr
    middle = ma
    return upper, lower, middle
