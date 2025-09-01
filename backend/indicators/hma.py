import pandas as pd
from .ta_utils import MA

def calculate(data, N=20):
    high = data['HIGH']
    hma = MA(high, N)
    return hma
