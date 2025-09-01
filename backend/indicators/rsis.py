def calculate(data, **params):
    # TODO: 实现 RSIS 指标计算
    pass
    import pandas as pd
    from .ta_utils import SMA
    N = params.get('N', 14)
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    if "CLOSE" not in data:
        raise KeyError("data 必须包含 'CLOSE' 列")
    close = data["CLOSE"].astype(float)
    diff = close.diff()
    up = diff.where(diff > 0, 0)
    down = -diff.where(diff < 0, 0)
    rsis = SMA(up, N, 1) / (SMA(up, N, 1) + SMA(down, N, 1)).replace(0, 1) * 100
    return rsis.fillna(0)
