import numpy as np
import pandas as pd
from .ta_utils import SMA, REF

def calculate(data, N=14):
    close = data['CLOSE']
    import pandas as pd
    diff = close.diff()
    gain = diff.where(diff > 0, 0)
    loss = -diff.where(diff < 0, 0)
    avg_gain = gain.rolling(window=N, min_periods=1).mean()
    avg_loss = loss.rolling(window=N, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
