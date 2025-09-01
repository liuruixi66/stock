import pandas as pd
from .ta_utils import SUM

def calculate(data, N=20):
    high = data['HIGH']
    open_ = data['OPEN']
    low = data['LOW']
    close = data['CLOSE']
    ar = SUM(high - open_, N) / SUM(open_ - low, N) * 100
    br = SUM(high - close.shift(1), N) / SUM(close.shift(1) - low, N) * 100
    return ar, br
