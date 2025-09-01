import pandas as pd


def calculate(data, **params):
    N = params.get('N', 10)
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    for col in ["CLOSE", "OPEN"]:
        if col not in data:
            raise KeyError(f"data 必须包含 '{col}' 列")
    close = data["CLOSE"].astype(float)
    open_ = data["OPEN"].astype(float)
    num = (close - open_).rolling(window=N, min_periods=1).mean()
    den = (close - open_).abs().rolling(window=N, min_periods=1).mean().replace(0, 1)
    rvi = num / den * 100
    return rvi.fillna(0)
