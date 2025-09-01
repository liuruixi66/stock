import pandas as pd
from .ta_utils import MIN, MAX, SMA, MA

def calculate(data, N=40, M=3):
    # 兼容大小写列名
    if 'CLOSE' in data.columns:
        close = data['CLOSE']
        high = data['HIGH']
        low = data['LOW']
    elif 'close' in data.columns:
        close = data['close']
        high = data['high']
        low = data['low']
    else:
        raise ValueError(f"找不到OHLC列，可用列: {list(data.columns)}")
    
    low_n = MIN(low, N)
    high_n = MAX(high, N)
    rsv = (close - low_n) / (high_n - low_n) * 100
    mar_sv = SMA(rsv, 3, 1)
    k = SMA(mar_sv, 3, 1)
    d = MA(k, 3)
    return k, d

def kdj(df: pd.DataFrame, n: int = 9, k_period: int = 3, d_period: int = 3):
    # 自动适配字段名
    low_col = 'LOW' if 'LOW' in df.columns else 'low'
    high_col = 'HIGH' if 'HIGH' in df.columns else 'high'
    close_col = 'CLOSE' if 'CLOSE' in df.columns else 'close'
    low_min = df[low_col].rolling(window=n, min_periods=1).min()
    high_max = df[high_col].rolling(window=n, min_periods=1).max()
    rsv = (df[close_col] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=k_period-1, adjust=False).mean()
    d = k.ewm(com=d_period-1, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j

# 用法: k, d, j = kdj(df)
