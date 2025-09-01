import pandas as pd
from .ta_utils import MA, REF

def calculate(data):
    close = data['CLOSE']
    roc_ma1 = MA(close - REF(close, 10), 10)
    roc_ma2 = MA(close - REF(close, 15), 10)
    roc_ma3 = MA(close - REF(close, 20), 10)
    roc_ma4 = MA(close - REF(close, 30), 10)
    kst_ind = roc_ma1 + roc_ma2 * 2 + roc_ma3 * 3 + roc_ma4 * 4
    kst = MA(kst_ind, 9)
    return kst
