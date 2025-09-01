import pandas as pd
import numpy as np
from .ta_utils import MAX, MIN

def calculate(data, N=20):
    high = data['HIGH']
    low = data['LOW']
    high_len = high.rolling(window=N).apply(lambda x: N - (np.argmax(x[::-1])), raw=True)
    low_len = low.rolling(window=N).apply(lambda x: N - (np.argmin(x[::-1])), raw=True)
    arron_up = (N - high_len) / N * 100
    arron_down = (N - low_len) / N * 100
    arron_os = arron_up - arron_down
    return arron_up, arron_down, arron_os
