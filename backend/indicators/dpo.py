import pandas as pd
from .ta_utils import MA, EMA, REF

def calculate(data, N=20):
    # data: DataFrame，需包含 'CLOSE' 列
    close = data['CLOSE']
    ma_close = MA(close, N)
    dpo = close - REF(ma_close, int(N/2)+1)
    return dpo
