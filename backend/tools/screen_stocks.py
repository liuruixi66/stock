"""Legacy screening CLI. Run with python -m tools.screen_stocks."""

import os
import json
import pandas as pd
from config.paths import BASE_DIR
from strategies import compare

def main():
    import sys, json, os
    # 支持前端传递参数：指标、条件、时间区间、数据路径
    indicator_names = os.environ.get('INDICATORS')
    if indicator_names:
        try:
            indicator_names = json.loads(indicator_names)
        except:
            indicator_names = indicator_names.split(',')
    else:
        indicator_names = []
    conditions_str = os.environ.get('CONDITIONS')
    if conditions_str:
        conditions = json.loads(conditions_str)
        # 支持前端传递比较表达式，如 {'OPEN': {'op': '>', 'value': 10}}
        for k, v in conditions.items():
            if isinstance(v, dict) and 'op' in v and 'value' in v:
                op = v['op']
                val = v['value']
                if op == '>':
                    conditions[k] = lambda x, val=val: compare.greater(x, val)
                elif op == '<':
                    conditions[k] = lambda x, val=val: compare.less(x, val)
                elif op == '>=':
                    conditions[k] = lambda x, val=val: compare.greater_equal(x, val)
                elif op == '<=':
                    conditions[k] = lambda x, val=val: compare.less_equal(x, val)
                elif op == '=':
                    conditions[k] = lambda x, val=val: compare.equal(x, val)
                else:
                    conditions[k] = lambda x: True
            elif isinstance(v, str):
                conditions[k] = eval(f'lambda x: {v}')
    else:
        conditions = {}
    start_date = os.environ.get('START_DATE')
    end_date = os.environ.get('END_DATE')
    extra = {}
    if start_date:
        extra['start_date'] = start_date
    if end_date:
        extra['end_date'] = end_date
    # 数据库配置
    mysql_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '9',
        'database': 'stock',
        'table': 'quotes',
        'charset': 'utf8mb4'
    }
    print(f'MySQL配置: {mysql_config}')
    print(f'指标: {indicator_names}')
    print(f'条件: {conditions_str}')
    print(f'时间区间: {extra}')
    # 读取数据库数据
    df = get_mysql_df(
        host=mysql_config['host'],
        user=mysql_config['user'],
        password=mysql_config['password'],
        database=mysql_config['database'],
        table=mysql_config['table'],
        charset=mysql_config['charset']
    )
    df = df.rename(columns={
        'price': 'CLOSE',
        'close': 'CLOSE',
        'open': 'OPEN',
        'high': 'HIGH',
        'low': 'LOW',
        'volume': 'VOLUME',
        'amount': 'AMOUNT',     # 成交额
        'turnover': 'AMOUNT',   # 成交额别名
        'avg_price': 'AVG_PRICE',  # 日成交均价
        'change_rate': 'CHANGE_RATE',  # 涨幅
        'pct_change': 'CHANGE_RATE',   # 涨幅别名
        'volume_ratio': 'VOLUME_RATIO',  # 量比
        'turnover_rate': 'TURNOVER_RATE',  # 换手率
        'total_share': 'TOTAL_SHARE'   # 流通股本
    })
    
    # 计算衍生字段（如果原始数据没有的话）
    if 'AVG_PRICE' not in df.columns and 'AMOUNT' in df.columns and 'VOLUME' in df.columns:
        # 日成交均价 = 成交额 / 成交量
        volume_nonzero = df['VOLUME'].replace(0, 1)
        df['AVG_PRICE'] = df['AMOUNT'] / volume_nonzero
    
    if 'CHANGE_RATE' not in df.columns and 'CLOSE' in df.columns:
        # 计算涨幅
        prev_close = df['CLOSE'].shift(1)
        df['CHANGE_RATE'] = ((df['CLOSE'] - prev_close) / prev_close * 100).fillna(0)
    
    if 'VOLUME_RATIO' not in df.columns and 'VOLUME' in df.columns:
        # 计算量比
        avg_volume_5 = df['VOLUME'].rolling(window=5).mean()
        df['VOLUME_RATIO'] = (df['VOLUME'] / avg_volume_5).fillna(1)
    
    if 'AMOUNT' not in df.columns and 'CLOSE' in df.columns and 'VOLUME' in df.columns:
        # 计算成交额
        df['AMOUNT'] = df['CLOSE'] * df['VOLUME']
    
    if 'TURNOVER_RATE' not in df.columns and 'VOLUME' in df.columns and 'TOTAL_SHARE' in df.columns:
        # 计算换手率
        df['TURNOVER_RATE'] = (df['VOLUME'] / df['TOTAL_SHARE'] * 100).fillna(0)
    # 合并所有比较结果到 DataFrame
    compare_results = {}
    for field, cond_func in conditions.items():
        if field in df.columns:
            compare_results[f'{field}_compare_result'] = df[field].apply(cond_func)
    
    # 合并比较结果到 df
    for col, result in compare_results.items():
        df[col] = result
    
    # 应用筛选条件
    if compare_results:
        # 获取所有比较结果列
        condition_columns = list(compare_results.keys())
        # 创建布尔索引：所有条件都为True的行
        if condition_columns:
            mask = df[condition_columns[0]]
            for col in condition_columns[1:]:
                mask = mask & df[col]
            df_filtered = df[mask]
        else:
            df_filtered = df.copy()
    else:
        df_filtered = df.copy()
    
    # 输出所有字段比较结果到前端（控制台）
    if compare_results:
        print('所有字段比较结果（筛选后）:')
        print(df_filtered[[col for col in compare_results.keys() if col in df_filtered.columns]])
    
    log_path = BASE_DIR / 'filter_stocks_result.log'
    df_filtered.to_csv(log_path, index=False, encoding='utf-8')
    print(f'筛选结果已保存到: {log_path}')


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    from research.screening import get_mysql_df
    main()
