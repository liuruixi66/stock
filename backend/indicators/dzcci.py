import pandas as pd
from .ta_utils import MA, STD, REF

def calculate(data, N=40, M=3, PARAM=2):
    close = data['CLOSE']
    cci_middle = MA(close, N)
    cci_upper = cci_middle + PARAM * STD(close, N)
    cci_lower = cci_middle - PARAM * STD(close, N)
    cci_ma = MA(close, M)
    return cci_middle, cci_upper, cci_lower, cci_ma
