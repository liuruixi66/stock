def calculate(data, **params):
    # TODO: 实现 RSIV 指标计算
    import pandas as pd
    from .ta_utils import SMA
    N = params.get('N', 14)  # Default value for N
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    for col in ["CLOSE", "OPEN"]:
        if col not in data:
            raise KeyError(f"data 必须包含 '{col}' 列")
    close = data["CLOSE"].astype(float)
    open_ = data["OPEN"].astype(float)
    diff = close - open_
    up = diff.where(diff > 0, 0)
    down = -diff.where(diff < 0, 0)
    rsiv = SMA(up, N, 1) / (SMA(up, N, 1) + SMA(down, N, 1)).replace(0, 1) * 100
    return rsiv.fillna(0)
