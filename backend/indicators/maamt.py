def calculate(data, **params):
    # TODO: 实现 MAAMT 指标计算
    import pandas as pd
    from .ta_utils import MA
    N = params.get('N', 5)
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    if "VOLUME" not in data:
        raise KeyError("data 必须包含 'VOLUME' 列")
    volume = data["VOLUME"].astype(float)
    maamt = MA(volume, N)
    return maamt.fillna(0)
