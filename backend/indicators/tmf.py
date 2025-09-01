import pandas as pd

def calculate(data, **params):
    N = params.get('N', 21)
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    for col in ["HIGH", "LOW", "CLOSE", "VOLUME"]:
        if col not in data:
            raise KeyError(f"data 必须包含 '{col}' 列")
    high = data["HIGH"].astype(float)
    low = data["LOW"].astype(float)
    close = data["CLOSE"].astype(float)
    volume = data["VOLUME"].astype(float)
    mf = ((close - low) - (high - close)) / (high - low).replace(0, 1) * volume
    tmf = mf.rolling(window=N, min_periods=1).sum() / volume.rolling(window=N, min_periods=1).sum().replace(0, 1)
    return tmf.fillna(0)
