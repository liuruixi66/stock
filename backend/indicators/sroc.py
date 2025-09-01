import pandas as pd
from .ta_utils import EMA, REF

def calculate(data, N=13, M=21):
    close = data['CLOSE']
    emap = EMA(close, N)
    sroc = (emap - REF(emap, M)) / REF(emap, M)
    return sroc
