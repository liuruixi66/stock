import pandas as pd
from .ta_utils import MA

def calculate(data, N=40, M=20):
    close = data['CLOSE']
    osc = close - MA(close, N)
    oscma = MA(osc, M)
    return osc, oscma
