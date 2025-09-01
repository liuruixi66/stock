import pandas as pd
from .ta_utils import EMA

def calculate(data, N=20):
    close = data['CLOSE']
    tema = 3 * EMA(close, N) - 3 * EMA(EMA(close, N), N) + EMA(EMA(EMA(close, N), N), N)
    return tema
