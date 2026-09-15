import pandas as pd

def resample_to_period(df, period='D', price_col='close'):
    """按周期聚合行情，并保留每个周期最后一个交易日的记录。

    ``price_col`` 是兼容旧调用的参数，目前聚合规则对所有列统一取末值；
    调用方应确保输入包含可转换为日期的 ``date`` 列。
    """
    df = df.sort_values('date')
    df['date'] = pd.to_datetime(df['date'])
    # 取每周期最后一个交易日数据
    df_period = df.set_index('date').resample(period).last().dropna().reset_index()
    return df_period

def calculate_kdj(high, low, close, n=9):
    """
    计算KDJ指标
    参数:
        high: 最高价序列
        low: 最低价序列  
        close: 收盘价序列
        n: 计算周期，默认9
    返回:
        包含K、D、J值的字典

    数据不足一个完整周期时返回全 50 的占位序列；每个周期最高价等于
    最低价时同样将 RSV 设为 50，以避免除零并保持指标中性。
    """
    high = pd.Series(high)
    low = pd.Series(low)
    close = pd.Series(close)
    
    if len(close) < n:
        # 数据量不足，返回默认值
        return {
            'k': [50] * len(close),
            'd': [50] * len(close),
            'j': [50] * len(close)
        }
    
    # 先计算 RSV，再用平滑递推得到 K、D，J 是 K/D 的派生值。
    rsv = []
    for i in range(len(close)):
        if i < n - 1:
            rsv.append(50)  # 前n-1个点设为50
        else:
            period_high = high[i-n+1:i+1].max()
            period_low = low[i-n+1:i+1].min()
            if period_high == period_low:
                rsv.append(50)
            else:
                rsv_val = (close[i] - period_low) / (period_high - period_low) * 100
                rsv.append(rsv_val)
    
    # 计算K、D、J
    k_values = []
    d_values = []
    j_values = []
    
    k_prev = 50
    d_prev = 50
    
    for rsv_val in rsv:
        k_val = 2/3 * k_prev + 1/3 * rsv_val
        d_val = 2/3 * d_prev + 1/3 * k_val
        j_val = 3 * k_val - 2 * d_val
        
        k_values.append(round(k_val, 2))
        d_values.append(round(d_val, 2))
        j_values.append(round(j_val, 2))
        
        k_prev = k_val
        d_prev = d_val
    
    return {
        'k': k_values,
        'd': d_values,
        'j': j_values
    }

# indicator_utils.py 只负责数据分割和周期转换，具体指标计算请在 indicators/ 下实现
