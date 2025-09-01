def calculate(data, **params):
    # TODO: 实现 EMV 指标计算
    pass
    import pandas as pd
    from .ta_utils import MA
    N = params.get('N', 14)
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    for col in ["HIGH", "LOW", "VOLUME"]:
        if col not in data:
            raise KeyError(f"data 必须包含 '{col}' 列")
    high = data["HIGH"].astype(float)
    low = data["LOW"].astype(float)
    volume = data["VOLUME"].astype(float)
    emv = ((high + low)/2 - ((high + low)/2).shift(1)) * (high - low) / volume.replace(0, 1)
    emv_ma = MA(emv, N)
    return emv_ma.fillna(0)
