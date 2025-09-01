import pandas as pd


def calculate(data, N=14):
    # 检查输入类型
    if not isinstance(data, pd.DataFrame):
        raise ValueError("输入必须为 pandas.DataFrame")
    if "CLOSE" not in data or "VOLUME" not in data:
        raise KeyError("data 必须包含 'CLOSE' 和 'VOLUME' 列")
    close = data["CLOSE"].astype(float)
    volume = data["VOLUME"].astype(float)
    # 检查 N 合法性
    if N is None or N < 1:
        N = 14
    amv = (close * volume).rolling(window=N, min_periods=1).mean()
    # 结果全为 NaN 时返回 0
    if amv.isnull().all():
        return pd.Series([0]*len(amv), index=amv.index)
    return amv.fillna(0)
