import pandas as pd
from .ta_utils import EMA

def calculate(data, N1=10, N2=30):
    close = data['CLOSE']
    high = data['HIGH']
    low = data['LOW']
    typ = (close + high + low) / 3
    typma1 = EMA(typ, N1)
    typma2 = EMA(typ, N2)
    return typma1, typma2
