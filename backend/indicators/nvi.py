def calculate(data, **params):
    import pandas as pd
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    for col in ["CLOSE", "VOLUME"]:
        if col not in data:
            raise KeyError(f"data 必须包含 '{col}' 列")
    close = data["CLOSE"].astype(float)
    volume = data["VOLUME"].astype(float)
    nvi = pd.Series(1000, index=data.index)
    for i in range(1, len(data)):
        if volume.iloc[i] < volume.iloc[i-1]:
            nvi.iloc[i] = nvi.iloc[i-1] + (close.iloc[i] - close.iloc[i-1]) / close.iloc[i-1] * nvi.iloc[i-1]
        else:
            nvi.iloc[i] = nvi.iloc[i-1]
    return nvi.fillna(0)
