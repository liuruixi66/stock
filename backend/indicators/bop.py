import pandas as pd
from .ta_utils import MA

def calculate(data, N=20):
    close = data['CLOSE']
    open_ = data['OPEN']
    high = data['HIGH']
    low = data['LOW']
    bop = MA((close - open_) / (high - low), N)
    return bop
