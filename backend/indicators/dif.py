import pandas as pd

def dif(close: pd.Series, short: int = 12, long: int = 26) -> pd.Series:
    ema_short = close.ewm(span=short, adjust=False).mean()
    ema_long = close.ewm(span=long, adjust=False).mean()
    return ema_short - ema_long

# 用法: dif(df['close'])
