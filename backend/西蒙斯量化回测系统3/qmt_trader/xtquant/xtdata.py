# coding=utf-8
"""
Linux版本的xtdata模块 - 绕过Windows依赖
取行情、财务等数据的相关接口
"""

import os, sys
import time
import traceback
import json
import pandas as pd

# 模拟的IPythonApiClient类
class MockRPCClient:
    """模拟的RPC客户端，用于替代Windows专用的IPythonApiClient"""
    
    def __init__(self, client_name, config_path):
        self.client_name = client_name
        self.config_path = config_path
        self.connected = False
        
    def set_remote_addr(self, ip, port):
        self.remote_ip = ip
        self.remote_port = port
        
    def reset(self):
        pass
        
    def connect_ex(self):
        # 模拟连接成功
        self.connected = True
        return True, "连接成功"
        
    def is_connected(self):
        return self.connected
        
    def load_config(self, config_path):
        pass
        
    def get_data_dir(self):
        return '../userdata_mini/datadir'
        
    def get_app_dir(self):
        return os.path.dirname(os.path.abspath(__file__))

# 使用模拟的RPC客户端
RPCClient = MockRPCClient

__all__ = [
    'subscribe_quote',
    'subscribe_whole_quote', 
    'unsubscribe_quote',
    'run',
    'get_market_data',
    'get_local_data',
    'get_full_tick',
    'get_divid_factors',
    'get_l2_quote',
    'get_l2_order', 
    'get_l2_transaction',
    'download_history_data',
    'get_financial_data',
    'download_financial_data',
    'get_instrument_detail',
    'get_instrument_type',
    'get_trading_dates',
    'get_sector_list',
    'get_stock_list_in_sector',
    'download_sector_data',
    'add_sector',
    'remove_sector',
    'get_index_weight',
    'download_index_weight',
    'get_holidays',
    'get_trading_calendar',
    'get_trade_times',
    'get_industry',
    'get_etf_info',
    'get_main_contract',
    'download_history_contracts',
    'download_cb_data',
    'get_cb_info',
    'download_history_data2',
    'download_financial_data2'
]

def try_except(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            exc_type, exc_instance, exc_traceback = sys.exc_info()
            formatted_traceback = ''.join(traceback.format_tb(exc_traceback))
            message = '\n{0} raise {1}:{2}'.format(
                formatted_traceback,
                exc_type.__name__,
                exc_instance
            )
            print(message)
            return None
    return wrapper

CLIENT = None

# 模拟初始化
def rpc_init(config_path):
    print(f'Linux模式：模拟RPC初始化，配置文件：{config_path}')
    return 0

# 模拟配置加载
def load_global_config():
    return {}

def get_client():
    global CLIENT
    if not CLIENT:
        CLIENT = RPCClient('client_xtdata', '')
        CLIENT.set_remote_addr('localhost', 58610)
        CLIENT.reset()
        succ, errmsg = CLIENT.connect_ex()
        if succ:
            init_data_dir()
    return CLIENT

def reconnect(ip='localhost', port=None):
    global CLIENT
    CLIENT = None
    if not CLIENT:
        CLIENT = get_client()
    return

default_data_dir = '../userdata_mini/datadir'
data_dir = default_data_dir

def init_data_dir():
    global data_dir
    try:
        client = get_client()
        data_dir = client.get_data_dir()
        if data_dir == "":
            data_dir = os.path.join(client.get_app_dir(), default_data_dir)
        if data_dir != default_data_dir:
            data_dir = os.path.abspath(data_dir)
    except Exception as e:
        pass
    return data_dir

debug_mode = 0

def create_array(shape, dtype_tuple, capsule, size):
    """模拟numpy数组创建"""
    import numpy as np
    return np.zeros(shape, dtype=np.dtype(dtype_tuple))

def register_create_nparray(func):
    """模拟注册numpy数组创建函数"""
    pass

# 模拟的行情数据获取函数
def get_market_data(field_list=[], stock_list=[], period='1d', 
                   start_time='', end_time='', count=-1,
                   dividend_type='none', fill_data=True):
    """
    模拟获取历史行情数据
    返回模拟数据用于测试
    """
    print(f"Linux模式：模拟获取行情数据 - 股票: {stock_list}, 周期: {period}")
    
    # 生成模拟数据
    import numpy as np
    result = {}
    
    if not field_list:
        field_list = ['time', 'open', 'high', 'low', 'close', 'volume', 'amount']
    
    # 生成时间序列
    if period == '1d':
        time_range = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    else:
        time_range = pd.date_range(start='2023-01-01', end='2023-01-31', freq='H')
    
    for field in field_list:
        data_dict = {}
        for stock in stock_list:
            if field == 'time':
                data_dict[stock] = time_range
            elif field in ['open', 'high', 'low', 'close']:
                # 生成模拟价格数据
                base_price = 10.0
                data_dict[stock] = base_price + np.random.randn(len(time_range)) * 0.5
            elif field == 'volume':
                data_dict[stock] = np.random.randint(1000, 10000, len(time_range))
            elif field == 'amount':
                data_dict[stock] = np.random.randint(10000, 100000, len(time_range))
            else:
                data_dict[stock] = np.zeros(len(time_range))
        
        result[field] = pd.DataFrame(data_dict, index=time_range)
    
    return result

def get_market_data_ex(field_list=[], stock_list=[], period='1d',
                      start_time='', end_time='', count=-1,
                      dividend_type='none', fill_data=True):
    """模拟获取扩展行情数据"""
    return get_market_data(field_list, stock_list, period, start_time, end_time, count, dividend_type, fill_data)

def get_market_data3(field_list=[], stock_list=[], period='1d',
                    start_time='', end_time='', count=-1,
                    dividend_type='none', fill_data=True):
    """模拟获取行情数据版本3"""
    return get_market_data(field_list, stock_list, period, start_time, end_time, count, dividend_type, fill_data)

def get_local_data(field_list=[], stock_code=[], period='1d', start_time='', end_time='', count=-1,
                  dividend_type='none', fill_data=True, data_dir=data_dir):
    """模拟获取本地数据"""
    print("Linux模式：模拟获取本地数据")
    return None

def get_financial_data(stock_list, table_list=[], start_time='', end_time='', report_type='report_time'):
    """模拟获取财务数据"""
    print(f"Linux模式：模拟获取财务数据 - 股票: {stock_list}")
    result = {}
    
    for stock in stock_list:
        result[stock] = {}
        for table in table_list or ['Balance', 'Income', 'CashFlow']:
            # 生成模拟财务数据
            result[stock][table] = pd.DataFrame({
                'endDate': ['20231231', '20231130', '20231030'],
                'revenue': [1000000, 950000, 900000],
                'profit': [100000, 95000, 90000]
            })
    
    return result

def get_trading_dates(market, start_time='', end_time='', count=-1):
    """模拟获取交易日"""
    print(f"Linux模式：模拟获取交易日 - 市场: {market}")
    # 返回模拟交易日
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='B')  # 工作日
    return [int(d.strftime('%Y%m%d')) for d in dates]

def get_stock_list_in_sector(sector_name):
    """模拟获取板块成份股"""
    print(f"Linux模式：模拟获取板块成份股 - 板块: {sector_name}")
    # 返回模拟股票列表
    return ['000001.SZ', '000002.SZ', '600000.SH', '600036.SH']

def get_industry(industry_name):
    """模拟获取行业成份股"""
    print(f"Linux模式：模拟获取行业成份股 - 行业: {industry_name}")
    return ['000001.SZ', '000002.SZ', '600000.SH']

def get_instrument_detail(stock_code):
    """模拟获取合约信息"""
    print(f"Linux模式：模拟获取合约信息 - 代码: {stock_code}")
    return {
        'ExchangeID': 'SZ' if stock_code.endswith('.SZ') else 'SH',
        'InstrumentID': stock_code,
        'InstrumentName': f'模拟股票{stock_code}',
        'ProductID': 'Stock',
        'ProductName': '股票',
        'PreClose': 10.0,
        'UpStopPrice': 11.0,
        'DownStopPrice': 9.0,
        'PriceTick': 0.01,
        'VolumeMultiple': 1,
        'IsTrading': True
    }

def get_instrument_type(stock_code):
    """模拟判断证券类型"""
    return {
        'stock': True,
        'index': False,
        'fund': False,
        'bond': False,
        'option': False,
        'future': False
    }

# 其他模拟函数
def subscribe_quote(stock_code, period='1d', start_time='', end_time='', count=0, callback=None):
    print(f"Linux模式：模拟订阅行情 - {stock_code}")
    return 1

def subscribe_whole_quote(code_list, callback=None):
    print(f"Linux模式：模拟订阅全推数据 - {code_list}")
    return 1

def unsubscribe_quote(seq):
    print(f"Linux模式：模拟取消订阅 - {seq}")
    return True

def run():
    print("Linux模式：模拟运行行情接收")
    import time
    time.sleep(1)

def get_full_tick(code_list):
    print(f"Linux模式：模拟获取tick数据 - {code_list}")
    return {}

def download_history_data(stock_code, period, start_time='', end_time=''):
    print(f"Linux模式：模拟下载历史数据 - {stock_code}")
    return True

def download_history_data2(stock_list, period, start_time='', end_time='', callback=None):
    print(f"Linux模式：模拟批量下载历史数据 - {stock_list}")
    if callback:
        callback({'finished': len(stock_list), 'total': len(stock_list)})
    return True

def download_financial_data(stock_list, table_list=[], start_time='', end_time=''):
    print(f"Linux模式：模拟下载财务数据 - {stock_list}")
    return True

def download_financial_data2(stock_list, table_list=[], start_time='', end_time='', callback=None):
    print(f"Linux模式：模拟批量下载财务数据 - {stock_list}")
    if callback:
        for i in range(len(stock_list)):
            callback({'finished': i+1, 'total': len(stock_list)})
    return True

# 其他模拟函数的简单实现
def get_divid_factors(stock_code, start_time='', end_time=''):
    return pd.DataFrame()

def get_l2_quote(field_list=[], stock_code='', start_time='', end_time='', count=-1):
    return None

def get_l2_order(field_list=[], stock_code='', start_time='', end_time='', count=-1):
    return None

def get_l2_transaction(field_list=[], stock_code='', start_time='', end_time='', count=-1):
    return None

def get_sector_list():
    return ['银行', '房地产', '科技', '医药']

def add_sector(sector_name, stock_list):
    print(f"Linux模式：模拟添加板块 - {sector_name}")
    return True

def remove_sector(sector_name):
    print(f"Linux模式：模拟删除板块 - {sector_name}")
    return True

def get_index_weight(index_code):
    return {}

def download_index_weight():
    print("Linux模式：模拟下载指数权重")
    return True

def download_history_contracts():
    print("Linux模式：模拟下载历史合约")
    return True

def get_main_contract(code_market):
    return f"{code_market}2024"

def get_holidays():
    return ['20240101', '20240501', '20241001']

def get_trading_calendar(market, start_time='', end_time='', tradetimes=False):
    return get_trading_dates(market, start_time, end_time)

def get_trade_times(stockcode):
    return [[32400, 41400, 3], [46800, 54000, 3]]  # 9:00-11:30, 13:00-15:00

def get_etf_info(stockCode):
    return {}

def download_sector_data():
    print("Linux模式：模拟下载板块数据")
    return True

def download_cb_data():
    print("Linux模式：模拟下载可转债数据")
    return True

def get_cb_info(stockcode):
    return {}

def is_stock_type(stock, tag):
    return True

def datetime_to_timetag(datetime, format="%Y%m%d%H%M%S"):
    if len(datetime) == 8:
        format = "%Y%m%d"
    timetag = time.mktime(time.strptime(datetime, format))
    return timetag * 1000

def timetag_to_datetime(timetag, format):
    return timetagToDateTime(timetag, format)

@try_except
def timetagToDateTime(timetag, format):
    import time
    timetag = timetag / 1000
    time_local = time.localtime(timetag)
    return time.strftime(format, time_local)

# 别名
gmd = get_market_data
gmd2 = get_market_data_ex  
gmd3 = get_market_data3
gld = get_local_data
t2d = timetag_to_datetime
gsl = get_stock_list_in_sector
supply_history_data = download_history_data
get_stock_type = get_instrument_type

print("Linux版本xtdata模块加载完成 - 已绕过Windows依赖")
