import pandas as pd

def calculate(df, n=20):
    # BOLL指标，n为周期
    close = df['CLOSE']
    mid = close.rolling(window=n, min_periods=1).mean()
    std = close.rolling(window=n, min_periods=1).std()
    upper = mid + 2 * std
    lower = mid - 2 * std
    return mid  # 这里只返回中轨，实际可返回 (mid, upper, lower)
