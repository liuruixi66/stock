import pandas as pd


def calculate(data, N=14):
    close = data["CLOSE"]
    volume = data["VOLUME"]
    advr = (close.diff() * volume).rolling(window=N, min_periods=1).mean()
    return advr
