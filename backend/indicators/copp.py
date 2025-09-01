import pandas as pd

def calculate(data, N1=11, N2=14, N3=10, M=10):
    close = data['CLOSE']
    rc1 = (close - close.shift(N1)) / close.shift(N1)
    rc2 = (close - close.shift(N2)) / close.shift(N2)
    rc = 100 * (rc1 + rc2)
    copp = rc.rolling(window=M, min_periods=1).mean()
    return copp
