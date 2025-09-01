import pandas as pd
from .ta_utils import REF, MIN, MAX

def calculate(data, N=100):
    close = data['CLOSE']
    price = (close - REF(close, N)) / REF(close, N)
    pos = (price - MIN(price, N)) / (MAX(price, N) - MIN(price, N))
    return pos
