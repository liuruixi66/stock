import pandas as pd

def dea(close: pd.Series, short: int = 12, long: int = 26, m: int = 9) -> pd.Series:
    ema_short = close.ewm(span=short, adjust=False).mean()
    ema_long = close.ewm(span=long, adjust=False).mean()
    dif = ema_short - ema_long
    dea = dif.ewm(span=m, adjust=False).mean()
    return dea

# 用法: dea(df['close'])
