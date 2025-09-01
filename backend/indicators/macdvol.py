def calculate(data, **params):
    import pandas as pd
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    if "VOLUME" not in data:
        raise KeyError("data 必须包含 'VOLUME' 列")
    volume = data["VOLUME"].astype(float)
    fast = params.get('fast', 12)
    slow = params.get('slow', 26)
    signal = params.get('signal', 9)
    ema_fast = volume.ewm(span=fast, adjust=False).mean()
    ema_slow = volume.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    macdvol = macd - macd_signal
    return macdvol.fillna(0)
