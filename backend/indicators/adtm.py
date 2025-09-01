import pandas as pd
from .ta_utils import REF, MAX, SUM, IF

def calculate(data, N=20):
    import pandas as pd
    open_ = data['OPEN']
    high = data['HIGH']
    low = data['LOW']
    dtm = pd.Series([high[i] - open_[i] if high[i] > open_[i] else 0 for i in range(len(high))])
    dbm = pd.Series([open_[i] - low[i] if open_[i] > low[i] else 0 for i in range(len(low))])
    stm = SUM(dtm, N)
    sbm = SUM(dbm, N)
    dtm_sum = dtm.rolling(window=N, min_periods=1).sum()
    dbm_sum = dbm.rolling(window=N, min_periods=1).sum()
    adtm = (dtm_sum - dbm_sum) / dtm_sum
    return adtm
