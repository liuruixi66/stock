def calculate(data, **params):
    # TODO: 实现 WR 指标计算
    import pandas as pd
    from .ta_utils import MAX, MIN
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    for col in ["HIGH", "LOW", "CLOSE"]:
        if col not in data:
            raise KeyError(f"data 必须包含 '{col}' 列")
    high = data["HIGH"].astype(float)
    low = data["LOW"].astype(float)
    close = data["CLOSE"].astype(float)
    wr = (MAX(high, 14) - close) / (MAX(high, 14) - MIN(low, 14)).replace(0, 1) * -100
    return wr.fillna(0)
