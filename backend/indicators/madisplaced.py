import pandas as pd
from .ta_utils import MA, REF

def calculate(data, N=20, M=10):
    close = data['CLOSE']
    ma_close = MA(close, N)
    madisplaced = REF(ma_close, M)
    return madisplaced
