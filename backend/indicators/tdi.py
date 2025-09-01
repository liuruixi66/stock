import pandas as pd
from .ta_utils import EMA

def calculate(data, N2=10, N3=20, N4=30):
    rsi = EMA(data['CLOSE'], N2)
    rsi_price_line = EMA(rsi, N2)
    rsi_signal_line = EMA(rsi, N3)
    rsi_market_line = EMA(rsi, N4)
    return rsi_price_line, rsi_signal_line, rsi_market_line
