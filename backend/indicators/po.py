import pandas as pd
from .ta_utils import EMA

def calculate(data):
    close = data['CLOSE']
    ema_short = EMA(close, 9)
    ema_long = EMA(close, 26)
    po = (ema_short - ema_long) / ema_long * 100
    return po
