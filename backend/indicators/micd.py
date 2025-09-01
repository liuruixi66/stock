import pandas as pd
from .ta_utils import MA, REF, SMA

def calculate(data, N=20, N1=10, N2=20, M=10):
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    if "CLOSE" not in data:
        raise KeyError("data 必须包含 'CLOSE' 列")
    close = data['CLOSE'].astype(float)
    mi = close - close.shift(1)
    mtmma = SMA(mi, N, 1)
    dif = MA(mtmma.shift(1), N1) - MA(mtmma.shift(1), N2)
    micd = SMA(dif, M, 1)
    if micd.isnull().all():
        return pd.Series([0]*len(micd), index=micd.index)
    return micd.fillna(0)
