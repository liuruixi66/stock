import pandas as pd
from .ta_utils import MA

def calculate(data, N1=10, N2=50):
    close = data['CLOSE']
    dma = MA(close, N1) - MA(close, N2)
    ama = MA(dma, N1)
    return dma, ama
