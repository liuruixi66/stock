def calculate(data, **params):
    import pandas as pd
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    if "CLOSE" not in data or "OPEN" not in data or "VOLUME" not in data:
        raise KeyError("data 必须包含 'CLOSE'、'OPEN'、'VOLUME' 列")
    close = data["CLOSE"].astype(float)
    open_ = data["OPEN"].astype(float)
    volume = data["VOLUME"].astype(float)
    # ADIO 常见公式：涨则加量，跌则减量
    adio = ((close > open_)*volume - (close < open_)*volume).cumsum()
    return adio.fillna(0)
