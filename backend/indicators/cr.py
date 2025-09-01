import pandas as pd
from .ta_utils import MAX, MIN, SUM, REF

def calculate(data, N=20):
    print(f'cr参数N={N}')
    close = data['CLOSE']
    high = data['HIGH']
    low = data['LOW']
    # 参数保护，避免 window=0 报错
    if N is None or N < 1:
        N = 20
    typ = (high + low + close) / 3
    h = MAX(high - REF(typ, 1), 0)
    l = MAX(REF(typ, 1) - low, 0)
    up = SUM(h, N)
    down = SUM(l, N)
    cr = up / down * 100
    cr = cr.fillna(0)  # 防止 inf 或 nan
    return cr
