import pandas as pd
from .ta_utils import REF

def calculate(data, N=60):
    close = data['CLOSE']
    mtm = close - REF(close, N)
    return mtm
