import pandas as pd

def calculate(data, N=20):
    # ADXR = (ADX + ADX.shift(N)) / 2
    if 'ADX' in data:
        adx = data['ADX']
    else:
        # 若无ADX列，可用CLOSE的变化近似
        adx = data['CLOSE'].diff().abs().rolling(window=N, min_periods=1).mean()
    adxr = (adx + adx.shift(N)) / 2
    return adxr
