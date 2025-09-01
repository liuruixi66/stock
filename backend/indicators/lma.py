import pandas as pd
from .ta_utils import MA

def calculate(data, N=20):
    low = data['LOW']
    lma = MA(low, N)
    return lma
