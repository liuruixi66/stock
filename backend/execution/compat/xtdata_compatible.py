"""
XT数据模块兼容层 - 类型安全且现代化的实现
"""
import pandas as pd
import numpy as np
from typing import Optional
from typing import List
from typing import Dict
from typing import Any
from typing import Union
from typing import Callable
from datetime import datetime
from datetime import timedelta
import random

class XTDataCompatible:
    """XT数据模块的兼容实现 - 类型安全"""
    
    def __init__(self):
        self.connected = False
        self.session_id = None
        
    def connect(self, path: str = '', session_id: int = 0) -> bool:
        """连接数据源"""
        try:
            self.session_id = session_id
            self.connected = True
            print(f"✅ XT数据连接成功 (会话ID: {session_id})")
            return True
        except Exception as e:
            print(f"❌ XT数据连接失败: {e}")
            return False
    
    def disconnect(self) -> None:
        """断开连接"""
        self.connected = False
        self.session_id = None
        print("🔌 XT数据连接已断开")
    
    def download_history_data(self, stock_code: str, period: str = 'D', 
                            start_time: str = '', end_time: str = '',
                            dividend_type: str = 'none') -> pd.DataFrame:
        """下载历史数据 - 类型安全实现"""
        try:
            # 模拟历史数据
            if not start_time:
                start_time = '20200101'
            if not end_time:
                end_time = '20241231'
                
            # 生成日期范围
            start_date = pd.to_datetime(start_time, format='%Y%m%d')
            end_date = pd.to_datetime(end_time, format='%Y%m%d')
            
            # 根据周期生成数据
            if period == 'D':
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            elif period == 'W':
                date_range = pd.date_range(start=start_date, end=end_date, freq='W')
            elif period == 'M':
                date_range = pd.date_range(start=start_date, end=end_date, freq='M')
            else:
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # 生成模拟数据
            base_price = 10.0 + random.random() * 20  # 基础价格
            data_list = []
            
            for i, date in enumerate(date_range):
                # 模拟价格波动
                volatility = 0.02  # 2%波动率
                change = (random.random() - 0.5) * volatility * 2
                
                if i == 0:
                    open_price = base_price
                else:
                    open_price = data_list[-1]['close']
                
                high_price = open_price * (1 + abs(change) + random.random() * 0.01)
                low_price = open_price * (1 - abs(change) - random.random() * 0.01)
                close_price = open_price * (1 + change)
                volume = int(1000000 + random.random() * 5000000)  # 100万到600万成交量
                
                data_list.append({
                    'time': date.strftime('%Y%m%d'),
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': volume,
                    'amount': round(volume * close_price, 2)
                })
            
            df = pd.DataFrame(data_list)
            print(f"📊 生成 {stock_code} 历史数据: {len(df)} 条记录")
            return df
            
        except Exception as e:
            print(f"❌ 下载历史数据失败: {e}")
            return pd.DataFrame()
    
    def get_market_data(self, stock_list: List[str], period: str = '1d', 
                       count: int = -1, dividend_type: str = 'none', 
                       fill_data: bool = True) -> Dict[str, pd.DataFrame]:
        """获取多只股票的行情数据"""
        result = {}
        for stock in stock_list:
            try:
                df = self.download_history_data(stock, period)
                if not df.empty:
                    result[stock] = df
            except Exception as e:
                print(f"⚠️  获取 {stock} 数据失败: {e}")
                result[stock] = pd.DataFrame()
        
        return result
    
    def get_full_tick(self, stock_list: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取实时行情数据"""
        result = {}
        for stock in stock_list:
            result[stock] = {
                'lastPrice': round(10 + random.random() * 20, 2),
                'open': round(10 + random.random() * 20, 2),
                'high': round(10 + random.random() * 20, 2),
                'low': round(10 + random.random() * 20, 2),
                'volume': int(random.random() * 1000000),
                'amount': round(random.random() * 10000000, 2),
                'time': datetime.now().strftime('%Y%m%d %H:%M:%S')
            }
        return result
    
    def get_stock_list_in_sector(self, sector_name: str) -> List[str]:
        """获取板块内股票列表"""
        # 模拟返回一些股票代码
        mock_stocks = [
            '000001.SZ', '000002.SZ', '000063.SZ', '000568.SZ',
            '600000.SH', '600036.SH', '600519.SH', '600036.SH'
        ]
        return mock_stocks[:6]  # 返回前6只
    
    def subscribe_quote(self, stock_list: List[str], period: str = '',
                       start_time: str = '', end_time: str = '',
                       count: int = 0, callback: Optional[Callable] = None) -> int:
        """订阅行情数据"""
        print(f"📡 订阅 {len(stock_list)} 只股票行情")
        return 1  # 返回订阅ID
    
    def unsubscribe_quote(self, seq_id: int) -> bool:
        """取消订阅"""
        print(f"📡 取消订阅 (ID: {seq_id})")
        return True
    
    def run(self) -> None:
        """运行数据接收循环"""
        print("🔄 XT数据接收循环启动")
        
    def get_trading_dates(self, market: str = 'SH', count: int = -1) -> List[str]:
        """获取交易日历"""
        # 生成最近的交易日
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 最近一年
        
        trading_dates = []
        current_date = start_date
        
        while current_date <= end_date:
            # 排除周末
            if current_date.weekday() < 5:  # 0-6，周一到周五
                trading_dates.append(current_date.strftime('%Y%m%d'))
            current_date += timedelta(days=1)
        
        if count > 0:
            return trading_dates[-count:]
        return trading_dates
