def calculate(data, **params):
    import pandas as pd
    fast = params.get('fast', 3)
    slow = params.get('slow', 10)
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    for col in ["HIGH", "LOW", "CLOSE", "VOLUME"]:
        if col not in data:
            raise KeyError(f"data 必须包含 '{col}' 列")
    high = data["HIGH"].astype(float)
    low = data["LOW"].astype(float)
    close = data["CLOSE"].astype(float)
    volume = data["VOLUME"].astype(float)
    ad = ((close - low) - (high - close)) / (high - low).replace(0, 1) * volume
    ad_cum = ad.cumsum()
    adosc = ad_cum.ewm(span=fast, adjust=False).mean() - ad_cum.ewm(span=slow, adjust=False).mean()
    return adosc.fillna(0)
