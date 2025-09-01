import pandas as pd
from .ta_utils import MA

def calculate(data, N=6):
    close = data['CLOSE']
    bias36 = MA(close, 3) - MA(close, 6)
    mabias36 = MA(bias36, N)
    return bias36, mabias36
