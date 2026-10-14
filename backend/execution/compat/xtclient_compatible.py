"""
XT客户端模块兼容层 - 类型安全的交易客户端实现
"""
import pandas as pd
from typing import Optional
from typing import List
from typing import Dict
from typing import Any
from typing import Union
from typing import Callable
from datetime import datetime
import time
import random

class XTClientCompatible:
    """XT交易客户端的兼容实现 - 类型安全"""
    
    def __init__(self, path: str = '', session_id: int = 0):
        self.path = path
        self.session_id = session_id
        self.connected = False
        self.account_id = ""
        self.total_asset = 100000.0  # 默认10万资金
        self.available_cash = 100000.0
        self.market_value = 0.0
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.orders: List[Dict[str, Any]] = []
        self.trades: List[Dict[str, Any]] = []
        
    def connect(self) -> bool:
        """连接交易服务器"""
        try:
            self.connected = True
            print(f"✅ XT交易客户端连接成功 (会话ID: {self.session_id})")
            return True
        except Exception as e:
            print(f"❌ XT交易客户端连接失败: {e}")
            return False
    
    def disconnect(self) -> None:
        """断开连接"""
        self.connected = False
        print("🔌 XT交易客户端连接已断开")
    
    def get_account_info(self, account_id: str = "") -> Dict[str, Any]:
        """获取账户信息 - 类型安全"""
        return {
            'account_id': account_id or self.account_id,
            'total_asset': self.total_asset,
            'available_cash': self.available_cash,
            'market_value': self.market_value,
            'frozen_cash': 0.0,
            'total_profit': self.total_asset - 100000.0,
            'profit_ratio': (self.total_asset - 100000.0) / 100000.0 * 100
        }
    
    def get_stock_position(self, account_id: str = "") -> List[Dict[str, Any]]:
        """获取股票持仓 - 类型安全"""
        position_list = []
        for stock_code, position in self.positions.items():
            position_list.append({
                'account_id': account_id or self.account_id,
                'stock_code': stock_code,
                'volume': position['volume'],
                'can_use_volume': position['can_use_volume'],
                'avg_price': position['avg_price'],
                'market_value': position['market_value'],
                'profit_loss': position['profit_loss'],
                'profit_loss_ratio': position['profit_loss_ratio']
            })
        return position_list
    
    def get_orders(self, account_id: str = "") -> List[Dict[str, Any]]:
        """获取委托订单 - 类型安全"""
        return [order.copy() for order in self.orders]
    
    def get_trades(self, account_id: str = "") -> List[Dict[str, Any]]:
        """获取成交记录 - 类型安全"""
        return [trade.copy() for trade in self.trades]
    
    def order_stock(self, account_id: str, stock_code: str, order_type: int,
                   order_volume: int, price_type: int, price: float = 0.0,
                   strategy_name: str = "", order_remark: str = "") -> Dict[str, Any]:
        """股票下单 - 类型安全"""
        try:
            # 生成订单ID
            order_id = f"ORDER_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
            
            # 模拟市价
            if price <= 0.0:
                price = round(10 + random.random() * 20, 2)
            
            # 计算订单金额
            order_amount = order_volume * price
            
            # 检查资金充足性（买入时）
            if order_type == 1:  # 买入
                if order_amount > self.available_cash:
                    return {
                        'order_id': '',
                        'error_code': -1,
                        'error_msg': '资金不足'
                    }
                self.available_cash -= order_amount
            
            # 创建订单记录
            order = {
                'order_id': order_id,
                'account_id': account_id,
                'stock_code': stock_code,
                'order_type': order_type,  # 1=买入, 2=卖出
                'order_volume': order_volume,
                'price_type': price_type,
                'price': price,
                'order_time': datetime.now().strftime('%Y%m%d %H:%M:%S'),
                'strategy_name': strategy_name,
                'order_remark': order_remark,
                'status': 'filled',  # 模拟立即成交
                'filled_volume': order_volume,
                'filled_amount': order_amount
            }
            
            self.orders.append(order)
            
            # 创建成交记录
            trade = {
                'trade_id': f"TRADE_{order_id}",
                'order_id': order_id,
                'account_id': account_id,
                'stock_code': stock_code,
                'trade_type': order_type,
                'trade_volume': order_volume,
                'trade_price': price,
                'trade_amount': order_amount,
                'trade_time': datetime.now().strftime('%Y%m%d %H:%M:%S')
            }
            
            self.trades.append(trade)
            
            # 更新持仓
            self._update_position(stock_code, order_type, order_volume, price)
            
            print(f"📋 订单执行成功: {stock_code} {'买入' if order_type == 1 else '卖出'} {order_volume}股 @ {price}元")
            
            return {
                'order_id': order_id,
                'error_code': 0,
                'error_msg': ''
            }
            
        except Exception as e:
            return {
                'order_id': '',
                'error_code': -1,
                'error_msg': str(e)
            }
    
    def _update_position(self, stock_code: str, order_type: int, 
                        volume: int, price: float) -> None:
        """更新持仓信息"""
        if stock_code not in self.positions:
            self.positions[stock_code] = {
                'volume': 0,
                'can_use_volume': 0,
                'avg_price': 0.0,
                'market_value': 0.0,
                'profit_loss': 0.0,
                'profit_loss_ratio': 0.0
            }
        
        position = self.positions[stock_code]
        
        if order_type == 1:  # 买入
            # 计算新的平均成本
            total_volume = position['volume'] + volume
            total_amount = position['volume'] * position['avg_price'] + volume * price
            new_avg_price = total_amount / total_volume if total_volume > 0 else 0
            
            position['volume'] = total_volume
            position['can_use_volume'] = total_volume
            position['avg_price'] = new_avg_price
            
        elif order_type == 2:  # 卖出
            position['volume'] -= volume
            position['can_use_volume'] -= volume
            
            # 释放资金
            self.available_cash += volume * price
            
            # 如果全部卖出，清除持仓
            if position['volume'] <= 0:
                del self.positions[stock_code]
                return
        
        # 更新市值和盈亏（使用当前价格模拟）
        current_price = price * (1 + (random.random() - 0.5) * 0.02)  # 模拟价格波动
        position['market_value'] = position['volume'] * current_price
        position['profit_loss'] = (current_price - position['avg_price']) * position['volume']
        position['profit_loss_ratio'] = (current_price - position['avg_price']) / position['avg_price'] * 100 if position['avg_price'] > 0 else 0
        
        # 更新总资产
        self.market_value = sum(pos['market_value'] for pos in self.positions.values())
        self.total_asset = self.available_cash + self.market_value
    
    def cancel_order(self, order_id: str, account_id: str = "") -> Dict[str, Any]:
        """撤销订单"""
        for order in self.orders:
            if order['order_id'] == order_id:
                order['status'] = 'cancelled'
                print(f"📋 订单已撤销: {order_id}")
                return {'error_code': 0, 'error_msg': ''}
        
        return {'error_code': -1, 'error_msg': '订单不存在'}
    
    def subscribe_account(self, account_id: str, callback: Optional[Callable] = None) -> int:
        """订阅账户变动"""
        print(f"📡 订阅账户变动: {account_id}")
        return 1  # 返回订阅ID
    
    def unsubscribe_account(self, seq_id: int) -> bool:
        """取消账户订阅"""
        print(f"📡 取消账户订阅 (ID: {seq_id})")
        return True
    
    def run(self) -> None:
        """运行客户端循环"""
        print("🔄 XT交易客户端循环启动")
    
    def get_last_account_data(self) -> pd.DataFrame:
        """获取最新账户数据 - 返回DataFrame格式"""
        account_info = self.get_account_info()
        
        data = {
            '时间': [datetime.now().strftime('%Y%m%d')],
            '总资产': [account_info['total_asset']],
            '股票市值': [account_info['market_value']],
            '可用金额': [account_info['available_cash']],
            '当日盈亏': [account_info['total_profit']],
            '当日盈亏比': [account_info['profit_ratio']],
            '持仓盈亏': [account_info['total_profit']],
            '收益': [account_info['profit_ratio']]
        }
        
        return pd.DataFrame(data)
