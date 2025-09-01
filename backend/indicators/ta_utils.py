import pandas as pd
import numpy as np

def MA(series, n):
    if n is None or n < 1:
        n = 1
    return series.rolling(window=n, min_periods=1).mean()

def EMA(series, n):
    if n is None or n < 1:
        n = 1
    return series.ewm(span=n, adjust=False).mean()

def SMA(series, n, m=1):
    # 常用SMA算法，m为权重，默认1
    if n is None or n < 1:
        n = 1
    sma = series.copy()
    for i in range(1, len(series)):
        sma.iloc[i] = (series.iloc[i] * m + sma.iloc[i-1] * (n - m)) / n
    return sma

def REF(series, n):
    if n is None or n < 1:
        n = 1
    return series.shift(n)

def SUM(series, n):
    if n is None or n < 1:
        n = 1
    return series.rolling(window=n, min_periods=1).sum()

def MAX(series, n):
    if n is None or n < 1:
        n = 1
    return series.rolling(window=n, min_periods=1).max()

def MIN(series, n):
    if n is None or n < 1:
        n = 1
    return series.rolling(window=n, min_periods=1).min()

def STD(series, n):
    if n is None or n < 1:
        n = 1
    return series.rolling(window=n, min_periods=1).std()

def CUMSUM(series):
    return series.cumsum()

def ABS(series):
    return series.abs()

def IF(cond, a, b):
    return np.where(cond, a, b)
