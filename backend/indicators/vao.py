def calculate(data, **params):
    # TODO: 实现 VAO 指标计算
    import pandas as pd
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    for col in ["HIGH", "LOW", "CLOSE", "VOLUME"]:
        if col not in data:
            raise KeyError(f"data 必须包含 '{col}' 列")
    high = data["HIGH"].astype(float)
    low = data["LOW"].astype(float)
    close = data["CLOSE"].astype(float)
    volume = data["VOLUME"].astype(float)
    price_range = high + low + close
    price_range_shift = price_range.shift(1)
    vao = ((price_range - price_range_shift) * volume).rolling(window=34, min_periods=1).sum()
    return vao.fillna(0)
