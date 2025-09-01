import numpy as np
import pandas as pd

from .ta_utils import MA, REF


def calculate(data, N=20):
    close = data["CLOSE"]
    high = data["HIGH"]
    low = data["LOW"]
    import pandas as pd
    prev_close = close.shift(1)
    trh = high.where(close > prev_close, prev_close)
    trl = low.where(close < prev_close, prev_close)
    wad = ((close - trh) + (close - trl)).cumsum()
    wadma = MA(wad, N)
    return wad, wadma
