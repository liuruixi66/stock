def calculate(data, **params):
    import pandas as pd
    N = params.get('N', 24)
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    for col in ["CLOSE", "OPEN", "HIGH", "LOW", "VOLUME"]:
        if col not in data:
            raise KeyError(f"data 必须包含 '{col}' 列")
    close = data["CLOSE"].astype(float)
    open_ = data["OPEN"].astype(float)
    high = data["HIGH"].astype(float)
    low = data["LOW"].astype(float)
    volume = data["VOLUME"].astype(float)
    wvad = ((close - open_) / (high - low).replace(0, 1)) * volume
    wvad_sum = wvad.rolling(window=N, min_periods=1).sum()
    return wvad_sum.fillna(0)
