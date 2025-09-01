"""
交易信号库 - 专门处理买入和卖出信号
作者: 系统集成
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import json

# 交易信号常量定义
SIGNAL_CODES = {
    'golden_cross': 0,          # 金叉
    'death_cross': 1,           # 死叉
    'holder_reduce': 2,         # 股东减持信号
    'holder_add': 3,            # 股东增持信号
    'holder_dividend': 4,       # 股东分红信号
    'violation_letter': 5,      # 违规问询函信号
    'new_listing': 6,           # 新上市
    'beijing_exchange': 7,      # 北交所
    'main_board': 8,            # 沪深主板
    'st': 9,                    # ST
    'star_st': 10,              # *ST
    'suspension': 11,           # 停牌
    'science_board': 12,        # 科创板
    'growth_board': 13,         # 创业板
    'delisting': 14,            # 退市
    'buy_signal': 15,           # 买入信号
    'sell_signal': 16           # 卖出信号
}

# 导入技术指标
try:
    from indicators import ma, dif, dea, macd, kdj
except ImportError:
    import indicators.ma as ma
    import indicators.dif as dif
    import indicators.dea as dea  
    import indicators.macd as macd
    import indicators.kdj as kdj

class SignalLibrary:
    """交易信号库类"""
    
    def __init__(self, initial_balance: float = 100000.0):
        self.signal_history: List[Dict[str, Any]] = []
        self.initial_balance = initial_balance  # 初始资金
        self.current_balance = initial_balance  # 当前余额
        self.positions: Dict[str, Dict] = {}  # 持仓信息 {股票代码: {shares: 股数, avg_price: 平均成本}}
        self.commission_rate = 0.0003  # 手续费率 0.03%
        self.min_commission = 5.0  # 最小手续费 5元
        self.stamp_tax_rate = 0.001  # 印花税率 0.1% (仅卖出收取)
    
    def calculate_commission(self, amount: float) -> float:
        """计算手续费"""
        commission = amount * self.commission_rate
        return max(commission, self.min_commission)
    
    def calculate_stamp_tax(self, amount: float) -> float:
        """计算印花税（仅卖出时收取）"""
        return amount * self.stamp_tax_rate
    
    def execute_buy_trade(self, stock_code: str, price: float, shares: int, trade_date: str) -> Dict[str, Any]:
        """执行买入交易"""
        try:
            total_amount = price * shares
            commission = self.calculate_commission(total_amount)
            total_cost = total_amount + commission
            
            if total_cost > self.current_balance:
                # 资金不足，按可用资金计算最大可买股数
                available_for_stock = self.current_balance - self.min_commission
                if available_for_stock <= 0:
                    return {'success': False, 'reason': '资金不足，无法买入'}
                
                max_shares = int(available_for_stock / (price * (1 + self.commission_rate)))
                if max_shares <= 0:
                    return {'success': False, 'reason': '资金不足，无法买入'}
                
                shares = max_shares
                total_amount = price * shares
                commission = self.calculate_commission(total_amount)
                total_cost = total_amount + commission
            
            # 更新余额
            self.current_balance -= total_cost
            
            # 更新持仓
            if stock_code in self.positions:
                old_shares = self.positions[stock_code]['shares']
                old_cost = self.positions[stock_code]['avg_price'] * old_shares
                new_total_shares = old_shares + shares
                new_avg_price = (old_cost + total_amount) / new_total_shares
                self.positions[stock_code] = {
                    'shares': new_total_shares,
                    'avg_price': new_avg_price
                }
            else:
                self.positions[stock_code] = {
                    'shares': shares,
                    'avg_price': price
                }
            
            return {
                'success': True,
                'action': 'buy',
                'stock_code': stock_code,
                'price': price,
                'shares': shares,
                'total_amount': total_amount,
                'commission': commission,
                'stamp_tax': 0,
                'total_cost': total_cost,
                'balance_after': self.current_balance,
                'position_shares': self.positions[stock_code]['shares'],
                'position_avg_price': self.positions[stock_code]['avg_price'],
                'trade_date': trade_date
            }
            
        except Exception as e:
            return {'success': False, 'reason': f'买入交易执行失败: {e}'}
    
    def execute_sell_trade(self, stock_code: str, price: float, shares: int, trade_date: str) -> Dict[str, Any]:
        """执行卖出交易"""
        try:
            if stock_code not in self.positions:
                return {'success': False, 'reason': '无持仓，无法卖出'}
            
            current_shares = self.positions[stock_code]['shares']
            if shares > current_shares:
                shares = current_shares  # 最多卖出全部持仓
            
            if shares <= 0:
                return {'success': False, 'reason': '无足够持仓卖出'}
            
            total_amount = price * shares
            commission = self.calculate_commission(total_amount)
            stamp_tax = self.calculate_stamp_tax(total_amount)
            total_fees = commission + stamp_tax
            net_amount = total_amount - total_fees
            
            # 更新余额
            self.current_balance += net_amount
            
            # 更新持仓
            remaining_shares = current_shares - shares
            if remaining_shares <= 0:
                del self.positions[stock_code]
                position_shares = 0
                position_avg_price = 0
            else:
                self.positions[stock_code]['shares'] = remaining_shares
                position_shares = remaining_shares
                position_avg_price = self.positions[stock_code]['avg_price']
            
            # 计算盈亏
            cost_price = self.positions.get(stock_code, {}).get('avg_price', price) if stock_code in self.positions else self.positions.get(stock_code, {}).get('avg_price', price)
            if stock_code not in self.positions:
                # 已全部卖出，从历史记录中获取成本价
                for record in reversed(self.signal_history):
                    if record.get('stock_code') == stock_code and record.get('action') == 'buy':
                        cost_price = record.get('position_avg_price', price)
                        break
            
            profit_loss = (price - cost_price) * shares - total_fees
            
            return {
                'success': True,
                'action': 'sell',
                'stock_code': stock_code,
                'price': price,
                'shares': shares,
                'total_amount': total_amount,
                'commission': commission,
                'stamp_tax': stamp_tax,
                'total_cost': total_fees,
                'net_amount': net_amount,
                'balance_after': self.current_balance,
                'position_shares': position_shares,
                'position_avg_price': position_avg_price,
                'cost_price': cost_price,
                'profit_loss': profit_loss,
                'trade_date': trade_date
            }
            
        except Exception as e:
            return {'success': False, 'reason': f'卖出交易执行失败: {e}'}

    def generate_buy_signal(self, stock_code: str, df: pd.DataFrame, 
                          signal_type: str = 'basic', **kwargs) -> pd.Series:
        """
        生成买入信号
        
        Args:
            stock_code: 股票代码
            df: 股票数据DataFrame
            signal_type: 信号类型 ('basic', 'macd_golden', 'ma_bullish', 'smart')
            **kwargs: 其他参数
            
        Returns:
            pd.Series: 买入信号序列，买入时为15，其他时候为None
        """
        try:
            if signal_type == 'basic':
                return self._basic_buy_signal(stock_code, df, **kwargs)
            elif signal_type == 'macd_golden':
                return self._macd_golden_buy_signal(stock_code, df, **kwargs)
            elif signal_type == 'ma_bullish':
                return self._ma_bullish_buy_signal(stock_code, df, **kwargs)
            elif signal_type == 'smart':
                return self._smart_buy_signal(stock_code, df, **kwargs)
            else:
                return pd.Series([None] * len(df), index=df.index)
                
        except Exception as e:
            print(f"生成买入信号失败 ({stock_code}): {e}")
            return pd.Series([None] * len(df), index=df.index)
    
    def generate_sell_signal(self, stock_code: str, df: pd.DataFrame, 
                           signal_type: str = 'basic', **kwargs) -> pd.Series:
        """
        生成卖出信号
        
        Args:
            stock_code: 股票代码
            df: 股票数据DataFrame
            signal_type: 信号类型 ('basic', 'macd_death', 'ma_bearish', 'smart')
            **kwargs: 其他参数
            
        Returns:
            pd.Series: 卖出信号序列，卖出时为16，其他时候为None
        """
        try:
            if signal_type == 'basic':
                return self._basic_sell_signal(stock_code, df, **kwargs)
            elif signal_type == 'macd_death':
                return self._macd_death_sell_signal(stock_code, df, **kwargs)
            elif signal_type == 'ma_bearish':
                return self._ma_bearish_sell_signal(stock_code, df, **kwargs)
            elif signal_type == 'smart':
                return self._smart_sell_signal(stock_code, df, **kwargs)
            else:
                return pd.Series([None] * len(df), index=df.index)
                
        except Exception as e:
            print(f"生成卖出信号失败 ({stock_code}): {e}")
            return pd.Series([None] * len(df), index=df.index)
    
    def _basic_buy_signal(self, stock_code: str, df: pd.DataFrame, **kwargs) -> pd.Series:
        """基础买入信号 - 基于价格突破"""
        threshold = kwargs.get('price_threshold', 0.05)  # 5%涨幅突破
        
        if 'CLOSE' not in df.columns:
            return pd.Series([None] * len(df), index=df.index)
        
        # 计算价格涨幅
        price_change = df['CLOSE'].pct_change()
        buy_condition = price_change > threshold
        
        signals = buy_condition.apply(lambda x: SIGNAL_CODES['buy_signal'] if x else None)
        
        # 记录信号
        for idx, signal in signals.items():
            if signal == SIGNAL_CODES['buy_signal']:
                self._record_signal(stock_code, 'buy', 'basic', df.loc[idx], idx)
        
        return signals
    
    def _basic_sell_signal(self, stock_code: str, df: pd.DataFrame, **kwargs) -> pd.Series:
        """基础卖出信号 - 基于价格跌破"""
        threshold = kwargs.get('price_threshold', -0.05)  # 5%跌幅跌破
        
        if 'CLOSE' not in df.columns:
            return pd.Series([None] * len(df), index=df.index)
        
        # 计算价格跌幅
        price_change = df['CLOSE'].pct_change()
        sell_condition = price_change < threshold
        
        signals = sell_condition.apply(lambda x: SIGNAL_CODES['sell_signal'] if x else None)
        
        # 记录信号
        for idx, signal in signals.items():
            if signal == SIGNAL_CODES['sell_signal']:
                self._record_signal(stock_code, 'sell', 'basic', df.loc[idx], idx)
        
        return signals
    
    def _macd_golden_buy_signal(self, stock_code: str, df: pd.DataFrame, **kwargs) -> pd.Series:
        """MACD金叉买入信号"""
        macd_n = kwargs.get('macd_n', 9)
        
        if 'CLOSE' not in df.columns:
            return pd.Series([None] * len(df), index=df.index)
        
        # 计算MACD
        macd_result = macd.calculate(df, signal=macd_n)
        dif_val = macd_result[0]
        dea_val = macd_result[1]
        
        # MACD金叉：DIF上穿DEA
        golden_cross = ((dif_val.shift(1) <= dea_val.shift(1)) & (dif_val > dea_val))
        
        signals = golden_cross.apply(lambda x: SIGNAL_CODES['buy_signal'] if x else None)
        
        # 记录信号
        for idx, signal in signals.items():
            if signal == SIGNAL_CODES['buy_signal']:
                self._record_signal(stock_code, 'buy', 'macd_golden', df.loc[idx], idx)
        
        return signals
    
    def _macd_death_sell_signal(self, stock_code: str, df: pd.DataFrame, **kwargs) -> pd.Series:
        """MACD死叉卖出信号"""
        macd_n = kwargs.get('macd_n', 9)
        
        if 'CLOSE' not in df.columns:
            return pd.Series([None] * len(df), index=df.index)
        
        # 计算MACD
        macd_result = macd.calculate(df, signal=macd_n)
        dif_val = macd_result[0]
        dea_val = macd_result[1]
        
        # MACD死叉：DIF下穿DEA
        death_cross = ((dif_val.shift(1) >= dea_val.shift(1)) & (dif_val < dea_val))
        
        signals = death_cross.apply(lambda x: SIGNAL_CODES['sell_signal'] if x else None)
        
        # 记录信号
        for idx, signal in signals.items():
            if signal == SIGNAL_CODES['sell_signal']:
                self._record_signal(stock_code, 'sell', 'macd_death', df.loc[idx], idx)
        
        return signals
    
    def _ma_bullish_buy_signal(self, stock_code: str, df: pd.DataFrame, **kwargs) -> pd.Series:
        """均线多头买入信号"""
        short_ma = kwargs.get('short_ma', 5)
        long_ma = kwargs.get('long_ma', 20)
        
        if 'CLOSE' not in df.columns:
            return pd.Series([None] * len(df), index=df.index)
        
        # 计算均线
        ma_short = df['CLOSE'].rolling(window=short_ma).mean()
        ma_long = df['CLOSE'].rolling(window=long_ma).mean()
        
        # 短期均线上穿长期均线
        bullish_cross = ((ma_short.shift(1) <= ma_long.shift(1)) & (ma_short > ma_long))
        
        signals = bullish_cross.apply(lambda x: SIGNAL_CODES['buy_signal'] if x else None)
        
        # 记录信号
        for idx, signal in signals.items():
            if signal == SIGNAL_CODES['buy_signal']:
                self._record_signal(stock_code, 'buy', 'ma_bullish', df.loc[idx], idx)
        
        return signals
    
    def _ma_bearish_sell_signal(self, stock_code: str, df: pd.DataFrame, **kwargs) -> pd.Series:
        """均线空头卖出信号"""
        short_ma = kwargs.get('short_ma', 5)
        long_ma = kwargs.get('long_ma', 20)
        
        if 'CLOSE' not in df.columns:
            return pd.Series([None] * len(df), index=df.index)
        
        # 计算均线
        ma_short = df['CLOSE'].rolling(window=short_ma).mean()
        ma_long = df['CLOSE'].rolling(window=long_ma).mean()
        
        # 短期均线下穿长期均线
        bearish_cross = ((ma_short.shift(1) >= ma_long.shift(1)) & (ma_short < ma_long))
        
        signals = bearish_cross.apply(lambda x: SIGNAL_CODES['sell_signal'] if x else None)
        
        # 记录信号
        for idx, signal in signals.items():
            if signal == SIGNAL_CODES['sell_signal']:
                self._record_signal(stock_code, 'sell', 'ma_bearish', df.loc[idx], idx)
        
        return signals
    
    def _smart_buy_signal(self, stock_code: str, df: pd.DataFrame, **kwargs) -> pd.Series:
        """智能买入信号 - 多指标组合"""
        try:
            if 'CLOSE' not in df.columns:
                return pd.Series([None] * len(df), index=df.index)
            
            # MACD金叉
            macd_result = macd.calculate(df, signal=kwargs.get('macd_n', 9))
            dif_val = macd_result[0]
            dea_val = macd_result[1]
            macd_golden = ((dif_val.shift(1) <= dea_val.shift(1)) & (dif_val > dea_val))
            
            # MA多头排列
            ma5 = df['CLOSE'].rolling(window=5).mean()
            ma10 = df['CLOSE'].rolling(window=10).mean()
            ma_bullish = ma5 > ma10
            
            # 成交量放大
            volume_ma = df['VOLUME'].rolling(window=5).mean() if 'VOLUME' in df.columns else pd.Series([1] * len(df))
            volume_surge = df['VOLUME'] > volume_ma * 1.5 if 'VOLUME' in df.columns else pd.Series([True] * len(df))
            
            # 综合条件
            buy_condition = macd_golden & ma_bullish & volume_surge
            
            signals = buy_condition.apply(lambda x: SIGNAL_CODES['buy_signal'] if x else None)
            
            # 记录信号
            for idx, signal in signals.items():
                if signal == SIGNAL_CODES['buy_signal']:
                    self._record_signal(stock_code, 'buy', 'smart', df.loc[idx], idx)
            
            return signals
            
        except Exception as e:
            print(f"智能买入信号计算失败: {e}")
            return pd.Series([None] * len(df), index=df.index)
    
    def _smart_sell_signal(self, stock_code: str, df: pd.DataFrame, **kwargs) -> pd.Series:
        """智能卖出信号 - 多指标组合"""
        try:
            if 'CLOSE' not in df.columns:
                return pd.Series([None] * len(df), index=df.index)
            
            # MACD死叉
            macd_result = macd.calculate(df, signal=kwargs.get('macd_n', 9))
            dif_val = macd_result[0]
            dea_val = macd_result[1]
            macd_death = ((dif_val.shift(1) >= dea_val.shift(1)) & (dif_val < dea_val))
            
            # MA空头排列
            ma5 = df['CLOSE'].rolling(window=5).mean()
            ma10 = df['CLOSE'].rolling(window=10).mean()
            ma_bearish = ma5 < ma10
            
            # 价格跌破支撑
            support_level = df['CLOSE'].rolling(window=20).min()
            price_breakdown = df['CLOSE'] < support_level * 0.98
            
            # 综合条件
            sell_condition = macd_death & ma_bearish & price_breakdown
            
            signals = sell_condition.apply(lambda x: SIGNAL_CODES['sell_signal'] if x else None)
            
            # 记录信号
            for idx, signal in signals.items():
                if signal == SIGNAL_CODES['sell_signal']:
                    self._record_signal(stock_code, 'sell', 'smart', df.loc[idx], idx)
            
            return signals
            
        except Exception as e:
            print(f"智能卖出信号计算失败: {e}")
            return pd.Series([None] * len(df), index=df.index)
    
    def _record_signal(self, stock_code: str, action: str, signal_type: str, 
                      data_row: pd.Series, timestamp: Any, trade_result: Optional[Dict[str, Any]] = None) -> None:
        """记录信号到历史记录"""
        try:
            # 基础信号记录
            signal_record = {
                'timestamp': datetime.now().isoformat(),
                'trade_date': str(timestamp),
                'stock_code': stock_code,
                'action': action,  # 'buy' or 'sell'
                'signal_type': signal_type,
                'signal_code': SIGNAL_CODES['buy_signal'] if action == 'buy' else SIGNAL_CODES['sell_signal'],
                'price': float(data_row.get('CLOSE', 0)),
                'volume': float(data_row.get('VOLUME', 0)) if 'VOLUME' in data_row else 0,
            }
            
            # 如果有交易结果，添加交易详细信息
            if trade_result and trade_result.get('success'):
                signal_record.update({
                    'shares': trade_result.get('shares', 0),
                    'total_amount': trade_result.get('total_amount', 0),
                    'commission': trade_result.get('commission', 0),
                    'stamp_tax': trade_result.get('stamp_tax', 0),
                    'total_cost': trade_result.get('total_cost', 0),
                    'net_amount': trade_result.get('net_amount', 0),
                    'balance_after': trade_result.get('balance_after', 0),
                    'position_shares': trade_result.get('position_shares', 0),
                    'position_avg_price': trade_result.get('position_avg_price', 0),
                })
                
                # 卖出特有信息
                if action == 'sell':
                    signal_record.update({
                        'cost_price': trade_result.get('cost_price', 0),
                        'profit_loss': trade_result.get('profit_loss', 0),
                    })
            else:
                # 模拟交易（用于测试）
                default_shares = 100  # 默认100股
                price = signal_record['price']
                
                if action == 'buy':
                    trade_result = self.execute_buy_trade(stock_code, price, default_shares, str(timestamp))
                else:
                    trade_result = self.execute_sell_trade(stock_code, price, default_shares, str(timestamp))
                
                if trade_result.get('success'):
                    signal_record.update({
                        'shares': trade_result.get('shares', 0),
                        'total_amount': trade_result.get('total_amount', 0),
                        'commission': trade_result.get('commission', 0),
                        'stamp_tax': trade_result.get('stamp_tax', 0),
                        'total_cost': trade_result.get('total_cost', 0),
                        'net_amount': trade_result.get('net_amount', 0),
                        'balance_after': trade_result.get('balance_after', 0),
                        'position_shares': trade_result.get('position_shares', 0),
                        'position_avg_price': trade_result.get('position_avg_price', 0),
                    })
                    
                    if action == 'sell':
                        signal_record.update({
                            'cost_price': trade_result.get('cost_price', 0),
                            'profit_loss': trade_result.get('profit_loss', 0),
                        })
            
            # 添加原始数据
            signal_record['data'] = data_row.to_dict()
            
            self.signal_history.append(signal_record)
            
        except Exception as e:
            print(f"记录信号失败: {e}")
    
    def get_account_summary(self) -> Dict[str, Any]:
        """获取账户摘要"""
        total_value = self.current_balance
        total_cost = 0
        total_profit_loss = 0
        
        # 计算持仓市值（需要当前价格，这里用平均成本价估算）
        for stock_code, position in self.positions.items():
            position_value = position['shares'] * position['avg_price']
            total_value += position_value
            total_cost += position_value
        
        # 统计已实现盈亏
        for record in self.signal_history:
            if record.get('action') == 'sell' and 'profit_loss' in record:
                total_profit_loss += record['profit_loss']
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.current_balance,
            'total_value': total_value,
            'total_profit_loss': total_profit_loss,
            'return_rate': (total_value - self.initial_balance) / self.initial_balance * 100,
            'positions': dict(self.positions),
            'total_trades': len(self.signal_history)
        }
    
    def get_trading_summary(self, stock_code: Optional[str] = None) -> Dict[str, Any]:
        """获取交易摘要"""
        history = self.signal_history
        if stock_code:
            history = [h for h in history if h.get('stock_code') == stock_code]
        
        buy_trades = [h for h in history if h.get('action') == 'buy']
        sell_trades = [h for h in history if h.get('action') == 'sell']
        
        total_buy_amount = sum(h.get('total_amount', 0) for h in buy_trades)
        total_sell_amount = sum(h.get('total_amount', 0) for h in sell_trades)
        total_commission = sum(h.get('commission', 0) for h in history)
        total_stamp_tax = sum(h.get('stamp_tax', 0) for h in history)
        total_profit_loss = sum(h.get('profit_loss', 0) for h in sell_trades)
        
        return {
            'stock_code': stock_code or 'ALL',
            'total_trades': len(history),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_buy_amount': total_buy_amount,
            'total_sell_amount': total_sell_amount,
            'total_commission': total_commission,
            'total_stamp_tax': total_stamp_tax,
            'total_fees': total_commission + total_stamp_tax,
            'total_profit_loss': total_profit_loss,
            'profit_rate': (total_profit_loss / total_buy_amount * 100) if total_buy_amount > 0 else 0
        }

    def get_signal_history(self, stock_code: Optional[str] = None, 
                          action: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取信号历史记录"""
        history = self.signal_history
        
        if stock_code:
            history = [s for s in history if s['stock_code'] == stock_code]
        
        if action:
            history = [s for s in history if s['action'] == action]
        
        return history
    
    def clear_signal_history(self) -> None:
        """清空信号历史记录"""
        self.signal_history.clear()
    
    def export_signal_history(self, filepath: str) -> None:
        """导出信号历史记录到文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.signal_history, f, ensure_ascii=False, indent=2)
            print(f"信号历史记录已导出到: {filepath}")
        except Exception as e:
            print(f"导出信号历史记录失败: {e}")
    
    def import_signal_history(self, filepath: str) -> None:
        """从文件导入信号历史记录"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.signal_history = json.load(f)
            print(f"信号历史记录已从 {filepath} 导入")
        except Exception as e:
            print(f"导入信号历史记录失败: {e}")

# 全局信号库实例
signal_library = SignalLibrary()

# 便捷函数
def generate_buy_signal(stock_code: str, df: pd.DataFrame, signal_type: str = 'basic', **kwargs) -> pd.Series:
    """生成买入信号的便捷函数"""
    return signal_library.generate_buy_signal(stock_code, df, signal_type, **kwargs)

def generate_sell_signal(stock_code: str, df: pd.DataFrame, signal_type: str = 'basic', **kwargs) -> pd.Series:
    """生成卖出信号的便捷函数"""
    return signal_library.generate_sell_signal(stock_code, df, signal_type, **kwargs)

def get_signal_history(stock_code: Optional[str] = None, action: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取信号历史的便捷函数"""
    return signal_library.get_signal_history(stock_code, action)

if __name__ == '__main__':
    # 测试信号库
    print("📈 交易信号库测试")
    
    # 创建更真实的测试数据 - 模拟股价走势
    import numpy as np
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    
    # 创建有趋势的价格数据
    base_price = 20.0
    trend = np.linspace(0, 5, 100)  # 上升趋势
    noise = np.random.randn(100) * 0.3
    prices = base_price + trend + noise
    
    # 确保价格为正值
    prices = np.maximum(prices, 1.0)
    
    # 创建有变化的成交量
    volumes = np.random.randint(5000, 20000, 100)
    
    # 模拟更真实的OHLC数据
    test_df = pd.DataFrame({
        'date': dates,
        'OPEN': prices * (1 + np.random.randn(100) * 0.01),
        'HIGH': prices * (1 + np.abs(np.random.randn(100) * 0.02)),
        'LOW': prices * (1 - np.abs(np.random.randn(100) * 0.02)),
        'CLOSE': prices,
        'VOLUME': volumes
    })
    
    print(f"测试数据: {len(test_df)}条记录")
    print(f"价格范围: {test_df['CLOSE'].min():.2f} - {test_df['CLOSE'].max():.2f}")
    
    # 测试基础买入信号（降低阈值）
    print("\n测试基础买入信号...")
    buy_signals_basic = generate_buy_signal('000001', test_df, 'basic', price_threshold=0.02)  # 2%阈值
    print(f"基础买入信号: {buy_signals_basic.notna().sum()}个")
    
    # 测试MACD买入信号
    print("\n测试MACD买入信号...")
    buy_signals_macd = generate_buy_signal('000001', test_df, 'macd_golden')
    print(f"MACD买入信号: {buy_signals_macd.notna().sum()}个")
    
    # 测试均线买入信号
    print("\n测试均线买入信号...")
    buy_signals_ma = generate_buy_signal('000001', test_df, 'ma_bullish', short_ma=5, long_ma=10)
    print(f"均线买入信号: {buy_signals_ma.notna().sum()}个")
    
    # 测试卖出信号
    print("\n测试卖出信号...")
    sell_signals_basic = generate_sell_signal('000001', test_df, 'basic', price_threshold=-0.02)  # -2%阈值
    sell_signals_macd = generate_sell_signal('000001', test_df, 'macd_death')
    sell_signals_ma = generate_sell_signal('000001', test_df, 'ma_bearish', short_ma=5, long_ma=10)
    
    print(f"基础卖出信号: {sell_signals_basic.notna().sum()}个")
    print(f"MACD卖出信号: {sell_signals_macd.notna().sum()}个")
    print(f"均线卖出信号: {sell_signals_ma.notna().sum()}个")
    
    # 查看信号历史
    history = get_signal_history('000001')
    print(f"\n📊 信号历史记录: {len(history)}条")
    
    if history:
        print("\n🕒 最近的交易详情:")
        for record in history[-5:]:
            action = "买入" if record['action'] == 'buy' else "卖出"
            trade_date = record.get('trade_date', 'N/A')
            price = record.get('price', 0)
            shares = record.get('shares', 0)
            commission = record.get('commission', 0)
            stamp_tax = record.get('stamp_tax', 0)
            balance = record.get('balance_after', 0)
            signal_type = record.get('signal_type', 'unknown')
            
            print(f"  📅 {trade_date} - {action} ({signal_type})")
            print(f"     💰 价格: ¥{price:.2f} | 数量: {shares}股 | 金额: ¥{price * shares:.2f}")
            print(f"     💸 手续费: ¥{commission:.2f} | 印花税: ¥{stamp_tax:.2f}")
            print(f"     💳 余额: ¥{balance:.2f}")
            
            if record['action'] == 'sell' and 'profit_loss' in record:
                profit_loss = record['profit_loss']
                profit_text = f"盈利 ¥{profit_loss:.2f}" if profit_loss > 0 else f"亏损 ¥{abs(profit_loss):.2f}"
                print(f"     📈 {profit_text}")
            print()
    
    # 账户摘要
    account_summary = signal_library.get_account_summary()
    print(f"💼 账户摘要:")
    print(f"   初始资金: ¥{account_summary['initial_balance']:,.2f}")
    print(f"   当前余额: ¥{account_summary['current_balance']:,.2f}")
    print(f"   总资产: ¥{account_summary['total_value']:,.2f}")
    print(f"   总盈亏: ¥{account_summary['total_profit_loss']:,.2f}")
    print(f"   收益率: {account_summary['return_rate']:+.2f}%")
    print(f"   总交易数: {account_summary['total_trades']}笔")
    
    # 持仓信息
    if account_summary['positions']:
        print(f"\n📈 当前持仓:")
        for stock_code, position in account_summary['positions'].items():
            market_value = position['shares'] * position['avg_price']
            print(f"   {stock_code}: {position['shares']}股 @ ¥{position['avg_price']:.2f} (市值: ¥{market_value:.2f})")
    
    # 交易摘要
    trading_summary = signal_library.get_trading_summary('000001')
    print(f"\n📊 交易摘要 (000001):")
    print(f"   总交易数: {trading_summary['total_trades']}笔")
    print(f"   买入: {trading_summary['buy_trades']}笔 (¥{trading_summary['total_buy_amount']:,.2f})")
    print(f"   卖出: {trading_summary['sell_trades']}笔 (¥{trading_summary['total_sell_amount']:,.2f})")
    print(f"   总手续费: ¥{trading_summary['total_commission']:,.2f}")
    print(f"   总印花税: ¥{trading_summary['total_stamp_tax']:,.2f}")
    print(f"   净盈亏: ¥{trading_summary['total_profit_loss']:,.2f}")
    print(f"   盈利率: {trading_summary['profit_rate']:+.2f}%")
    
    # 显示一些技术指标数据用于调试
    print(f"\n🔍 调试信息:")
    print(f"价格变化率范围: {test_df['CLOSE'].pct_change().min():.3f} - {test_df['CLOSE'].pct_change().max():.3f}")
    
    # 计算MA5和MA10
    ma5 = test_df['CLOSE'].rolling(window=5).mean()
    ma10 = test_df['CLOSE'].rolling(window=10).mean()
    ma_cross_up = ((ma5.shift(1) <= ma10.shift(1)) & (ma5 > ma10)).sum()
    ma_cross_down = ((ma5.shift(1) >= ma10.shift(1)) & (ma5 < ma10)).sum()
    print(f"MA5上穿MA10次数: {ma_cross_up}")
    print(f"MA5下穿MA10次数: {ma_cross_down}")
