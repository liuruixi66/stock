import pandas as pd


def calculate(data, N=14):
    close = data["CLOSE"]
    mcl = close.rolling(window=N, min_periods=1).mean()
    return mcl
