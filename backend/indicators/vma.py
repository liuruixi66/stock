import pandas as pd
from .ta_utils import MA

def calculate(data, N=20):
    close = data['CLOSE']
    high = data['HIGH']
    low = data['LOW']
    open_ = data['OPEN']
    price = (high + low + open_ + close) / 4
    vma = MA(price, N)
    return vma
