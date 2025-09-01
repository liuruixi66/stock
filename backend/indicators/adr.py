def calculate(data, **params):
    # TODO: 实现 ADR 指标计算
    import pandas as pd
    from .ta_utils import REF
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    for col in ["HIGH", "LOW"]:
        if col not in data:
            raise KeyError(f"data 必须包含 '{col}' 列")
    high = data["HIGH"].astype(float)
    low = data["LOW"].astype(float)
    adr = (high - low) / REF(high - low, 1).replace(0, 1)
    return adr.fillna(0)
