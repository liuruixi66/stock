import pandas as pd
from .ta_utils import MAX, MIN

def calculate(data, N=20):
    high = data['HIGH']
    low = data['LOW']
    upper = MAX(high, N)
    lower = MIN(low, N)
    middle = (upper + lower) / 2
    return upper, lower, middle
