import pandas as pd
import numpy as np
from .ta_utils import MAX, MIN, REF

def calculate(data, N=20, PARAM=0.3):
    high = data['HIGH']
    low = data['LOW']
    close = data['CLOSE']
    price = (high + low) / 2
    price_ch = 2 * (price - MIN(low, N)) / (MAX(high, N) - MIN(low, N)) - 0.5
    price_ch = np.clip(price_ch, -0.999, 0.999)
    price_change = PARAM * price_ch + (1 - PARAM) * REF(price_ch, 1)
    fisher = 0.5 * REF(price_ch, 1) + 0.5 * np.log((1 + price_change) / (1 - price_change))
    return fisher
