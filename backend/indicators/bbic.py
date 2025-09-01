import pandas as pd

def calculate(df, n=20):
    # BBIC指标简单实现，n为周期
    close = df['CLOSE']
    bbic = close.rolling(window=n, min_periods=1).mean() / close
    return bbic
