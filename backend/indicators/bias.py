import pandas as pd
from .ta_utils import MA

def calculate(data, N=6):
    close = data['CLOSE']
    bias = (close - MA(close, N)) / MA(close, N) * 100
    return bias
