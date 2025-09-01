import pandas as pd
from .ta_utils import MA

def calculate(data, N=5):
    close = data['CLOSE']
    ma = MA(close, N)
    return ma
