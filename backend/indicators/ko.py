def calculate(data, **params):
    # TODO: 实现 KO 指标计算
    pass
    import pandas as pd
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    if "CLOSE" not in data:
        raise KeyError("data 必须包含 'CLOSE' 列")
    close = data["CLOSE"].astype(float)
    ko = close.ewm(span=params.get('fast', 10), adjust=False).mean() - close.ewm(span=params.get('slow', 20), adjust=False).mean()
    return ko.fillna(0)
