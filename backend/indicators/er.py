import pandas as pd
from .ta_utils import EMA

def calculate(data, N=20):
    # data: DataFrame，需包含 'HIGH', 'LOW', 'CLOSE' 列
    high = data['HIGH']
    low = data['LOW']
    close = data['CLOSE']
    bull_power = high - EMA(close, N)
    bear_power = low - EMA(close, N)
    return bull_power, bear_power
