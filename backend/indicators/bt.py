import pandas as pd


def calculate(data, N=14):
    close = data['CLOSE']
    bt = close.rolling(window=N, min_periods=1).std()
    return bt
