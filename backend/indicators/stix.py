def calculate(data, **params):
    import pandas as pd
    N = params.get('N', 10)
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    if "CLOSE" not in data:
        raise KeyError("data 必须包含 'CLOSE' 列")
    close = data["CLOSE"].astype(float)
    # STIX 常见公式：N日均线与N日前均线之差
    stix = close.rolling(window=N, min_periods=1).mean() - close.shift(N).rolling(window=N, min_periods=1).mean()
    return stix.fillna(0)
