import pandas as pd

def calculate_ma(series, window=5):
    """
    计算移动平均线
    
    Args:
        series: 价格序列（pandas Series）
        window: 均线周期
    
    Returns:
        pandas Series: 移动平均线序列
    """
    return series.rolling(window=window, min_periods=1).mean()

def get_ma_on_date(df, target_date, window=5, price_col='close'):
    """
    选定日期，往前取window个有效交易日，计算MA。
    df: 包含'date'和价格字段的DataFrame
    target_date: 目标日期字符串，如'2025-07-31'
    window: 均线周期
    price_col: 价格字段名，默认'close'
    返回: MA值
    """
    df = df.sort_values('date')
    df = df[df['date'] <= target_date]
    df_window = df.tail(window)
    return df_window[price_col].mean()


def add_ma_column(df, window=5, price_col='close', ma_col=None):
    """
    批量为所有交易日添加MA列。
    df: 包含'date'和价格字段的DataFrame
    window: 均线周期
    price_col: 价格字段名，默认'close'
    ma_col: MA列名，默认'MA{window}'
    返回: 新DataFrame，含MA列
    """
    if ma_col is None:
        ma_col = f'MA{window}'
    df = df.sort_values('date')
    df[ma_col] = df[price_col].rolling(window=window).mean()
    return df

# 示例用法：
# df = pd.read_csv('xxx.csv')
# ma5 = get_ma_on_date(df, '2025-07-31', window=5)
# df = add_ma_column(df, window=5)
