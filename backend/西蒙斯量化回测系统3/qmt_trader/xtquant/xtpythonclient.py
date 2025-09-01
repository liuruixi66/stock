# coding=utf-8
"""
Linux版本的xtpythonclient模块 - 绕过Windows依赖
模拟QMT交易客户端功能
"""

import pandas as pd
import time
import threading
from typing import Dict, List, Any, Optional, Callable

# 模拟常量
XTP_POSITION_DIRECTION_LONG = 1
XTP_POSITION_DIRECTION_SHORT = 2
XTP_POSITION_EFFECT_OPEN = 1
XTP_POSITION_EFFECT_CLOSE = 2
XTP_SIDE_BUY = 1
XTP_SIDE_SELL = 2

class MockXTPythonClient:
    """模拟的QMT Python客户端"""
    
    def __init__(self, client_id: int = 1, config_path: str = ""):
        self.client_id = client_id
        self.config_path = config_path
        self.connected = False
        self.accounts = {}
        self.positions = {}
        self.orders = {}
        self.trades = {}
        self.callbacks = {}
        
    def set_client_config(self, config: Dict):
        """设置客户端配置"""
        print(f"Linux模式：设置客户端配置 - {config}")
        
    def connect(self, ip: str = "localhost", port: int = 6001, timeout: int = 10):
        """连接服务器"""
        print(f"Linux模式：模拟连接服务器 - {ip}:{port}")
        self.connected = True
        return True
        
    def disconnect(self):
        """断开连接"""
        print("Linux模式：模拟断开连接")
        self.connected = False
        
    def is_connected(self):
        """检查连接状态"""
        return self.connected
        
    def login(self, user_id: str, password: str, software_key: str = ""):
        """登录"""
        print(f"Linux模式：模拟登录 - 用户: {user_id}")
        return True
        
    def logout(self):
        """登出"""
        print("Linux模式：模拟登出")
        return True
        
    def register_callback(self, callback_type: str, callback_func: Callable):
        """注册回调函数"""
        print(f"Linux模式：注册回调 - {callback_type}")
        self.callbacks[callback_type] = callback_func
        
    def query_asset(self, account_id: str = ""):
        """查询资金"""
        print(f"Linux模式：模拟查询资金 - 账户: {account_id}")
        return {
            'account_id': account_id or 'mock_account',
            'total_asset': 1000000.0,
            'buying_power': 900000.0,
            'security_asset': 100000.0,
            'fund_buy_amount': 0.0,
            'fund_sell_amount': 0.0,
            'withholding_amount': 0.0
        }
        
    def query_stock_asset(self, account_id: str = ""):
        """查询股票资产"""
        print(f"Linux模式：模拟查询股票资产 - 账户: {account_id}")
        return [
            {
                'account_id': account_id or 'mock_account',
                'stock_code': '000001.SZ',
                'stock_name': '平安银行',
                'current_amount': 1000,
                'can_use_amount': 1000,
                'avg_price': 10.5,
                'market_value': 10500.0,
                'profit': 500.0
            }
        ]
        
    def query_orders(self, account_id: str = ""):
        """查询委托"""
        print(f"Linux模式：模拟查询委托 - 账户: {account_id}")
        return []
        
    def query_trades(self, account_id: str = ""):
        """查询成交"""
        print(f"Linux模式：模拟查询成交 - 账户: {account_id}")
        return []
        
    def order_stock(self, account_id: str, stock_code: str, order_type: int, 
                   order_volume: int, price_type: int, price: float = 0.0,
                   strategy_name: str = "", order_remark: str = ""):
        """股票下单"""
        print(f"Linux模式：模拟股票下单 - {stock_code}, 数量: {order_volume}, 价格: {price}")
        
        order_id = f"mock_order_{int(time.time())}"
        order_info = {
            'order_id': order_id,
            'account_id': account_id,
            'stock_code': stock_code,
            'order_type': order_type,
            'order_volume': order_volume,
            'price': price,
            'order_time': time.time(),
            'order_status': 1  # 已报
        }
        
        self.orders[order_id] = order_info
        
        # 模拟立即成交
        if self.callbacks.get('on_order_trade'):
            trade_info = {
                'order_id': order_id,
                'trade_id': f"mock_trade_{int(time.time())}",
                'stock_code': stock_code,
                'trade_volume': order_volume,
                'trade_price': price,
                'trade_time': time.time()
            }
            self.trades[trade_info['trade_id']] = trade_info
            # 异步调用回调
            threading.Thread(target=self.callbacks['on_order_trade'], args=(trade_info,)).start()
            
        return order_id
        
    def cancel_order(self, account_id: str, order_id: str):
        """撤单"""
        print(f"Linux模式：模拟撤单 - 订单: {order_id}")
        if order_id in self.orders:
            self.orders[order_id]['order_status'] = 5  # 已撤
        return True
        
    def order_stock_async(self, account_id: str, stock_code: str, order_type: int,
                         order_volume: int, price_type: int, price: float = 0.0,
                         strategy_name: str = "", order_remark: str = ""):
        """异步股票下单"""
        return self.order_stock(account_id, stock_code, order_type, order_volume, 
                               price_type, price, strategy_name, order_remark)
        
    def query_stock_orders(self, account_id: str = "", stock_code: str = ""):
        """查询指定股票委托"""
        orders = []
        for order_id, order in self.orders.items():
            if (not account_id or order['account_id'] == account_id) and \
               (not stock_code or order['stock_code'] == stock_code):
                orders.append(order)
        return orders
        
    def query_stock_trades(self, account_id: str = "", stock_code: str = ""):
        """查询指定股票成交"""
        trades = []
        for trade_id, trade in self.trades.items():
            if not stock_code or trade['stock_code'] == stock_code:
                trades.append(trade)
        return trades

# 创建默认实例
default_client = MockXTPythonClient()

# 模拟模块级别的函数
def create_trader_api(client_id: int = 1, config_path: str = ""):
    """创建交易API"""
    print(f"Linux模式：创建模拟交易API - ID: {client_id}")
    return MockXTPythonClient(client_id, config_path)

def get_version():
    """获取版本"""
    return "Linux Mock Version 1.0.0"

# 导出类和函数
__all__ = [
    'MockXTPythonClient',
    'create_trader_api', 
    'get_version',
    'XTP_POSITION_DIRECTION_LONG',
    'XTP_POSITION_DIRECTION_SHORT',
    'XTP_POSITION_EFFECT_OPEN',
    'XTP_POSITION_EFFECT_CLOSE',
    'XTP_SIDE_BUY',
    'XTP_SIDE_SELL'
]

print("Linux版本xtpythonclient模块加载完成 - 已绕过Windows依赖")
