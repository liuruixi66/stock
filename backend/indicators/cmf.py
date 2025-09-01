def calculate(data, **params):
    # TODO: 实现 CMF 指标计算
    import pandas as pd
    N = params.get('N', 20)
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    for col in ["HIGH", "LOW", "CLOSE", "VOLUME"]:
        if col not in data:
            raise KeyError(f"data 必须包含 '{col}' 列")
    high = data["HIGH"].astype(float)
    low = data["LOW"].astype(float)
    close = data["CLOSE"].astype(float)
    volume = data["VOLUME"].astype(float)
    mfv = ((close - low) - (high - close)) / (high - low).replace(0, 1) * volume
    cmf = mfv.rolling(window=N, min_periods=1).sum() / volume.rolling(window=N, min_periods=1).sum().replace(0, 1)
    return cmf.fillna(0)
