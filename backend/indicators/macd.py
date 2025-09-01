import pandas as pd
from .ta_utils import EMA

def calculate(data, short=12, long=26, signal=9):
    # 兼容大小写列名
    if 'CLOSE' in data.columns:
        close = data['CLOSE']
    elif 'close' in data.columns:
        close = data['close']
    else:
        raise ValueError(f"找不到收盘价列，可用列: {list(data.columns)}")
    
    dif = EMA(close, short) - EMA(close, long)
    dea = EMA(dif, signal)
    macd = (dif - dea) * 2  # 标准MACD柱状图计算公式
    return dif, dea, macd
