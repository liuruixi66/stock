def calculate(data, **params):
    # TODO: 实现 VRAMT 指标计算
    import pandas as pd
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    if "VOLUME" not in data:
        raise KeyError("data 必须包含 'VOLUME' 列")
    volume = data["VOLUME"].astype(float)
    vramt = volume.rolling(window=20, min_periods=1).sum()
    return vramt.fillna(0)
