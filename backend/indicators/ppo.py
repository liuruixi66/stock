import pandas as pd
from .ta_utils import EMA

def calculate(data, N1=12, N2=26, N3=9):
    close = data['CLOSE']
    ppo = (EMA(close, N1) - EMA(close, N2)) / EMA(close, N2)
    ppo_signal = EMA(ppo, N3)
    return ppo, ppo_signal
