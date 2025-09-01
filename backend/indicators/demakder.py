import pandas as pd
import numpy as np
from .ta_utils import REF, MA

def calculate(data, N=20):
    high = data['HIGH']
    low = data['LOW']
    demax = high - REF(high, 1)
    demax = pd.Series(np.where(demax > 0, demax, 0), index=high.index)
    demin = REF(low, 1) - low
    demin = pd.Series(np.where(demin > 0, demin, 0), index=low.index)
    demaker = MA(demax, N) / (MA(demax, N) + MA(demin, N))
    return demaker
