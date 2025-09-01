import pandas as pd
from .ta_utils import EMA

def calculate(df, n=20):
    # 计算EMA指标，n为周期
    close = df['CLOSE']
    ema = EMA(close, n)
    return ema