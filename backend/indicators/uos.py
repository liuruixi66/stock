def calculate(data, N1=7, N2=14, N3=28):
    # UOS (Ultimate Oscillator) 指标实现
    import pandas as pd
    high = data['HIGH']
    low = data['LOW']
    close = data['CLOSE']
    prev_close = close.shift(1)
    bp = close - pd.concat([low, prev_close], axis=1).min(axis=1)
    tr = pd.concat([high, prev_close], axis=1).max(axis=1) - pd.concat([low, prev_close], axis=1).min(axis=1)
    avg1 = bp.rolling(window=N1, min_periods=1).sum() / tr.rolling(window=N1, min_periods=1).sum()
    avg2 = bp.rolling(window=N2, min_periods=1).sum() / tr.rolling(window=N2, min_periods=1).sum()
    avg3 = bp.rolling(window=N3, min_periods=1).sum() / tr.rolling(window=N3, min_periods=1).sum()
    uos = 100 * (4 * avg1 + 2 * avg2 + avg3) / (4 + 2 + 1)
    return uos
