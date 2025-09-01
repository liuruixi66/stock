import pandas as pd
from .ta_utils import SMA, REF, MAX, MIN

def calculate(data):
    close = data['CLOSE']
    open_ = data['OPEN']
    high = data['HIGH']
    low = data['LOW']
    ha_open = SMA(close, 2, 1).shift(1)
    ha_close = (open_ + close + high + low) / 4
    ha_high = pd.concat([ha_open, ha_close, high, low], axis=1).max(axis=1)
    ha_low = pd.concat([ha_open, ha_close, high, low], axis=1).min(axis=1)
    return ha_open, ha_close, ha_high, ha_low
