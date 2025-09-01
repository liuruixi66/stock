import pandas as pd
from .ta_utils import MA

def calculate(data):
    close = data['CLOSE']
    bbi = (MA(close, 3) + MA(close, 6) + MA(close, 12) + MA(close, 24)) / 4
    return bbi
