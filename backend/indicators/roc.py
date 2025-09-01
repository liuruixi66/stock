import pandas as pd
from .ta_utils import REF

def calculate(data, N=100):
    close = data['CLOSE']
    roc = (close - REF(close, N)) / REF(close, N)
    return roc
