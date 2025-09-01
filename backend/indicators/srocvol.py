import pandas as pd


def calculate(data, N=14):
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    if "VOLUME" not in data:
        raise KeyError("data 必须包含 'VOLUME' 列")
    volume = data["VOLUME"].astype(float)
    if N is None or N < 1:
        N = 14
    srocvol = (volume - volume.shift(N)) / volume.shift(N).replace(0, 1) * 100
    srocvol = srocvol.rolling(window=N, min_periods=1).mean()
    return srocvol
