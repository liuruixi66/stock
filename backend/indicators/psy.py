import pandas as pd
import numpy as np
from .ta_utils import REF

def calculate(data, N=12):
    close = data['CLOSE']
    psy = np.where(close > REF(close, 1), 1, 0)
    psy = pd.Series(psy).rolling(window=N).mean() * 100
    return psy
