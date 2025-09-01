def calculate(data, **params):
    import pandas as pd
    # 假定 data 包含 ADV（上涨家数）、DECL（下跌家数）、UVOL（上涨成交量）、DVOL（下跌成交量）
    for col in ["ADV", "DECL", "UVOL", "DVOL"]:
        if col not in data:
            raise KeyError(f"data 必须包含 '{col}' 列")
    adv = data["ADV"].astype(float)
    decl = data["DECL"].astype(float)
    uvol = data["UVOL"].astype(float)
    dvol = data["DVOL"].astype(float)
    trin = (adv / decl).replace([float('inf'), -float('inf')], 0) / (uvol / dvol).replace([float('inf'), -float('inf')], 0)
    return trin.fillna(0)
