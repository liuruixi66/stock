import pandas as pd
from .ta_utils import MA, ABS

def calculate(data, N=14):
    high = data['HIGH']
    low = data['LOW']
    close = data['CLOSE']
    tp = (high + low + close) / 3
    ma_tp = MA(tp, N)
    md = MA(ABS(tp - ma_tp), N)
    cci = (tp - ma_tp) / (0.015 * md)
    return cci
