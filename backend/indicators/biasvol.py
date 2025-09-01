def calculate(data, **params):
    # TODO: 实现 BIASVOL 指标计算
    import pandas as pd
    from .ta_utils import MA
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    if "VOLUME" not in data:
        raise KeyError("data 必须包含 'VOLUME' 列")
    volume = data["VOLUME"].astype(float)
    biasvol = (volume - MA(volume, 6)) / MA(volume, 6).replace(0, 1) * 100
    return biasvol.fillna(0)
