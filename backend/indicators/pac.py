import pandas as pd
from .ta_utils import SMA

def calculate(data, N1=20, N2=20):
    high = data['HIGH']
    low = data['LOW']
    upper = SMA(high, N1, 1)
    lower = SMA(low, N2, 1)
    return upper, lower
