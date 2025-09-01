import pandas as pd
from .ta_utils import MA, REF, SMA

def calculate(data, M=40, N1=20, N2=40):
    close = data['CLOSE']
    rc = close / REF(close, M)
    arc1 = SMA(REF(rc, 1), M, 1)
    dif = MA(REF(arc1, 1), N1) - MA(REF(arc1, 1), N2)
    rccd = SMA(dif, M, 1)
    return rccd
