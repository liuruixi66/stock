def calculate(data, **params):
    import pandas as pd
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    for col in ["CLOSE", "VOLUME"]:
        if col not in data:
            raise KeyError(f"data 必须包含 '{col}' 列")
    close = data["CLOSE"].astype(float)
    volume = data["VOLUME"].astype(float)
    pvt = pd.Series(0, index=data.index)
    for i in range(1, len(data)):
        pvt.iloc[i] = pvt.iloc[i-1] + (close.iloc[i] - close.iloc[i-1]) / close.iloc[i-1] * volume.iloc[i]
    return pvt.fillna(0)
