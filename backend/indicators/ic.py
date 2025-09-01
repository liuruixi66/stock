import pandas as pd
from .ta_utils import MAX, MIN, REF

def calculate(data, N1=9, N2=26, N3=52):
    high = data['HIGH']
    low = data['LOW']
    ts = (MAX(high, N1) + MIN(low, N1)) / 2
    ks = (MAX(high, N2) + MIN(low, N2)) / 2
    span_a = (ts + ks) / 2
    span_b = (MAX(high, N3) + MIN(low, N3)) / 2
    return ts, ks, span_a, span_b
