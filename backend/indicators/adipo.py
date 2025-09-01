import pandas as pd


def calculate(data, N=14):
    high = data["HIGH"]
    low = data["LOW"]
    close = data["CLOSE"]
    prev_close = close.shift(1)
    adipo = (
        (high - prev_close) - (low - prev_close)
    ).rolling(window=N, min_periods=1).mean()
    return adipo
