import pandas as pd
from .ta_utils import MA

def calculate(data, N=25, PARAM=0.05):
    close = data['CLOSE']
    mac = MA(close, N)
    upper = mac * (1 + PARAM)
    lower = mac * (1 - PARAM)
    return upper, lower, mac
