import pandas as pd
from .ta_utils import MA

def calculate(data, N=60):
    close = data['CLOSE']
    high = data['HIGH']
    low = data['LOW']
    clv = (2 * close - low - high) / (high - low)
    clvma = MA(clv, N)
    return clv, clvma
