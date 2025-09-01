import pandas as pd
from .ta_utils import MA

def calculate(data, N1=20, N2=20):
    high = data['HIGH']
    low = data['LOW']
    hma = MA(high, N1)
    lma = MA(low, N2)
    return hma, lma
