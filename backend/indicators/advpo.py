import pandas as pd


def calculate(data, N=14):
    close = data["CLOSE"]
    volume = data["VOLUME"]
    advpo = (close * volume).rolling(window=N, min_periods=1).mean()
    return advpo
