"""
重塑的西蒙斯量化回测系统 - 类型安全且跨平台兼容
"""
import os
import sys
import platform
import pandas as pd
import numpy as np
import math
import json
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import logging

# 导入系统适配器
from system_adapter import system_adapter, trading_modules
# 导入信号库
from signal_library import SIGNAL_CODES, generate_buy_signal, generate_sell_signal

class XMSQuantBacktraderRemastered:
    """重塑的西蒙斯量化回测系统 - 现代化且类型安全"""
    
    def __init__(self, trader_tool: str = 'ths', data_api: str = 'dfcf', 
                 data_type: str = 'D', stock_list: Optional[List[str]] = None,
                 start_date: str = '20200101', end_date: str = '20241231',
                 total_cash: float = 100000.0, st_name: str = '量化回测策略'):
        
        # 基础配置
        self.trader_tool = trader_tool
        self.data_api = data_api
        self.data_type = data_type
        self.stock_list = stock_list or []
        self.start_date = start_date
        self.end_date = end_date
        self.total_cash = total_cash
        self.st_name = st_name
        
        # 系统信息
        self.system_info = {
            'platform': platform.system(),
            'python_version': sys.version,
            'trading_platform': trading_modules['platform']
        }
        
        # 交易模块
        self.xtdata = trading_modules['xtdata']
        self.xt_client_class = trading_modules['XTPythonClient']
        self.xt_client: Optional[Any] = None
        
        # 数据存储
        self.hist_data: Union[pd.DataFrame, Dict[str, pd.DataFrame]] = pd.DataFrame()
        self.account_data: pd.DataFrame = pd.DataFrame()
        self.position_data: List[Dict[str, Any]] = []
        self.trade_records: List[Dict[str, Any]] = []
        
        # 日志配置
        self.logger = self._setup_logger()
        
        # 初始化
        self._initialize()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(f'XMSQuant_{self.st_name}')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize(self) -> None:
        """初始化回测系统"""
        try:
            self.logger.info(f"🚀 初始化西蒙斯量化回测系统")
            self.logger.info(f"📊 交易工具: {self.trader_tool}")
            self.logger.info(f"📡 数据源: {self.data_api}")
            self.logger.info(f"⏰ 回测周期: {self.start_date} - {self.end_date}")
            self.logger.info(f"💰 初始资金: {self.total_cash:,.2f}元")
            self.logger.info(f"🖥️  运行平台: {self.system_info['platform']}")
            
            self._init_account()
            
            if self.data_api != 'local':
                if hasattr(self.xtdata, 'connect'):
                    self.xtdata.connect()
                self.logger.info("✅ 远程数据源连接成功")

            self.logger.info("✅ 系统初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ 系统初始化失败: {e}", exc_info=True)
            raise
    
    def _init_account(self) -> None:
        """初始化账户数据"""
        initial_data = {
            '时间': [self.start_date],
            '总资产': [self.total_cash],
            '股票市值': [0.0],
            '可用金额': [self.total_cash],
            '当日盈亏': [0.0],
            '当日盈亏比': [0.0],
            '持仓盈亏': [0.0],
            '收益': [0.0]
        }
        self.account_data = pd.DataFrame(initial_data)
        
        if self.data_api != 'local':
            if system_adapter.is_windows:
                self.xt_client = self.xt_client_class(session_id=1001)
            else:
                self.xt_client = self.xt_client_class(session_id=1001)
            
            if self.xt_client and hasattr(self.xt_client, 'connect'):
                self.xt_client.connect()
    
    def adjust_amount(self, stock: str = '', amount: Union[str, int, float] = '') -> int:
        """调整股票数量 - 类型安全重塑"""
        try:
            if isinstance(amount, str):
                if not amount.strip(): return 0
                amount_num = float(amount)
            else:
                amount_num = float(amount)
            
            if amount_num <= 0: return 0
            if not isinstance(stock, str) or not stock.strip(): return int(amount_num)
            
            stock_clean = stock.strip()
            
            if (len(stock_clean) >= 3 and stock_clean[:3] in ['110', '113', '123', '127', '128', '111']) or 
               (len(stock_clean) >= 2 and stock_clean[:2] in ['11', '12']):
                adjusted = math.floor(amount_num / 10.0) * 10
            else:
                adjusted = math.floor(amount_num / 100.0) * 100
            
            return max(0, int(adjusted))
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"⚠️  调整股票数量失败: {e}")
            return 0

    def set_data(self, data: pd.DataFrame):
        """直接设置历史数据，用于本地回测"""
        if not data.empty:
            self.logger.info(f"📈 注入 {len(data)} 条本地数据进行回测")
            standardized_data = self._standardize_columns(data)
            if 'code' in standardized_data.columns:
                standardized_data['code'] = standardized_data['code'].astype(str)
                self.hist_data = {
                    str(stock): group.copy()
                    for stock, group in standardized_data.groupby('code')
                }
                self.logger.info(f"本地数据已按 {len(self.hist_data)} 个股票代码分组")
            else:
                self.hist_data = {'unknown_stock': standardized_data}
        else:
            self.logger.warning("⚠️  尝试注入空的数据集")
    
    def get_historical_data(self, stock_code: str, 
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> pd.DataFrame:
        """获取历史数据 - 类型安全"""
        if self.data_api == 'local' and isinstance(self.hist_data, dict):
            stock_data = self.hist_data.get(str(stock_code))
            if isinstance(stock_data, pd.DataFrame) and not stock_data.empty:
                self.logger.info(f"📊 从本地缓存获取 {stock_code} 数据")
                return stock_data.copy()
            else:
                self.logger.warning(f"⚠️  在本地缓存中未找到 {stock_code} 的数据, 返回空DataFrame")
                return pd.DataFrame()

        try:
            start = start_date or self.start_date
            end = end_date or self.end_date
            
            if hasattr(self.xtdata, 'download_history_data'):
                df = self.xtdata.download_history_data(
                    stock_code=stock_code, period=self.data_type,
                    start_time=start, end_time=end
                )
            else:
                df = pd.DataFrame()
            
            if not df.empty:
                df = self._standardize_columns(df)
                self.logger.info(f"📊 下载 {stock_code} 历史数据: {len(df)} 条")
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 获取 {stock_code} 历史数据失败: {e}", exc_info=True)
            return pd.DataFrame()
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化数据列名"""
        if df.empty:
            return df
        
        column_mapping = {
            'time': 'date', 'Time': 'date', 'TIME': 'date', '日期': 'date',
            '股票代码': 'code', 'stock_code': 'code',
            'open': 'open', 'Open': 'open', 'OPEN': 'open', '开盘': 'open',
            'high': 'high', 'High': 'high', 'HIGH': 'high', '最高': 'high',
            'low': 'low', 'Low': 'low', 'LOW': 'low', '最低': 'low',
            'close': 'close', 'Close': 'close', 'CLOSE': 'close', '收盘': 'close',
            'volume': 'volume', 'Volume': 'volume', 'VOLUME': 'volume', '成交量': 'volume',
            'amount': 'amount', 'Amount': 'amount', 'AMOUNT': 'amount', '成交额': 'amount'
        }
        
        df = df.rename(columns=column_mapping)
        
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                self.logger.warning(f"⚠️  标准化后的数据缺少必要列: {col}")
        
        return df

    def execute_strategy(self, strategy_name: str = 'equal_weight_buy_hold') -> Dict[str, Any]:
        """执行交易策略"""
        try:
            self.logger.info(f"🎯 执行策略: {strategy_name}")
            
            if strategy_name == 'equal_weight_buy_hold':
                return self._execute_equal_weight_strategy()
            elif strategy_name == 'sell_all_positions':
                return self._execute_sell_strategy(self.position_data)
            else:
                self.logger.warning(f"⚠️  未知策略: {strategy_name}")
                return {'success': False, 'error': f'不支持的策略: {strategy_name}'}
                
        except Exception as e:
            self.logger.error(f"❌ 策略执行失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _execute_equal_weight_strategy(self) -> Dict[str, Any]:
        """执行等权重买入持有策略"""
        try:
            if not self.stock_list:
                return {'success': False, 'error': '股票列表为空'}
            
            cash_per_stock = self.total_cash / len(self.stock_list)
            
            results = {
                'trades': [],
                'positions': [],
                'account_summary': {},
                'performance': {}
            }
            
            for stock in self.stock_list:
                try:
                    hist_data = self.get_historical_data(stock)
                    if hist_data.empty:
                        self.logger.warning(f"⚠️  {stock} 无历史数据，跳过")
                        continue
                    
                    first_day_data = hist_data.iloc[0] if not hist_data.empty else None
                    if first_day_data is None:
                        continue
                    
                    buy_price = float(first_day_data['close'])
                    shares_to_buy = self.adjust_amount(stock, cash_per_stock / buy_price)
                    
                    if shares_to_buy > 0:
                        trade_record = {
                            'stock_code': stock, 'action': 'buy', 'shares': shares_to_buy,
                            'price': buy_price, 'amount': shares_to_buy * buy_price,
                            'date': self.start_date, 'trade_time': datetime.now().isoformat(),
                            'signal': SIGNAL_CODES['buy_signal'], 'signal_type': 'equal_weight_buy_hold'
                        }
                        results['trades'].append(trade_record)
                        self.trade_records.append(trade_record)
                        
                        position = {
                            'stock_code': stock, 'shares': shares_to_buy, 'avg_price': buy_price,
                            'market_value': shares_to_buy * buy_price, 'profit_loss': 0.0
                        }
                        results['positions'].append(position)
                        self.position_data.append(position)
                        
                        self.logger.info(f"💰 买入 {stock}: {shares_to_buy}股 @ {buy_price:.2f}元")
                
                except Exception as e:
                    self.logger.error(f"❌ 处理 {stock} 时出错: {e}", exc_info=True)
            
            total_invested = sum(trade['amount'] for trade in results['trades'])
            remaining_cash = self.total_cash - total_invested
            
            results['account_summary'] = {
                'total_cash': self.total_cash, 'invested_amount': total_invested,
                'remaining_cash': remaining_cash, 'position_count': len(results['positions'])
            }
            
            # 模拟最终评估
            self._evaluate_performance(results)
            
            return {'success': True, 'data': results}

        except Exception as e:
            self.logger.error(f"❌ 等权重策略执行失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _execute_sell_strategy(self, positions_to_sell: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行卖出策略"""
        try:
            results = {'trades': [], 'account_summary': {}}
            total_sell_amount = 0

            for position in positions_to_sell:
                stock_code = position.get('stock_code')
                shares_to_sell = position.get('shares')

                if not stock_code or not shares_to_sell:
                    continue

                hist_data = self.get_historical_data(stock_code, end_date=self.end_date)
                if hist_data.empty:
                    self.logger.warning(f"⚠️  {stock_code} 无历史数据，无法卖出")
                    continue

                last_day_price = float(hist_data.iloc[-1]['close'])
                sell_amount = shares_to_sell * last_day_price
                total_sell_amount += sell_amount

                trade_record = {
                    'stock_code': stock_code, 'action': 'sell', 'shares': shares_to_sell,
                    'price': last_day_price, 'amount': sell_amount, 'date': self.end_date,
                    'trade_time': datetime.now().isoformat(), 'signal': SIGNAL_CODES['sell_signal'],
                    'signal_type': 'end_of_backtest_sell'
                }
                results['trades'].append(trade_record)
                self.trade_records.append(trade_record)
                self.logger.info(f"💰 卖出 {stock_code}: {shares_to_sell}股 @ {last_day_price:.2f}元")

            # 清空持仓
            self.position_data = []
            
            # 更新账户
            final_cash = self.account_data.iloc[-1]['可用金额'] + total_sell_amount
            results['account_summary'] = {'final_cash': final_cash}
            
            return {'success': True, 'data': results}

        except Exception as e:
            self.logger.error(f"❌ 卖出策略执行失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _evaluate_performance(self, results: Dict[str, Any]) -> None:
        """评估回测性能"""
        if not results['trades']:
            results['performance'] = {'message': '无交易记录，无法评估'}
            return

        # 卖出所有持仓以计算最终市值
        sell_results = self._execute_sell_strategy(results['positions'])
        if not sell_results['success']:
            self.logger.error("❌ 评估时卖出持仓失败")
            return
            
        final_cash = sell_results['data']['account_summary']['final_cash']
        total_return = (final_cash - self.total_cash) / self.total_cash
        
        results['performance'] = {
            'initial_cash': self.total_cash,
            'final_cash': final_cash,
            'total_return_pct': f"{total_return:.2%}",
            'total_trades': len(self.trade_records)
        }
        self.logger.info(f"📈 回测评估完成: 最终资产 {final_cash:,.2f}元, 总回报率 {total_return:.2%}")

    def run(self) -> Dict[str, Any]:
        """运行完整的回测流程"""
        self.logger.info("🚀 开始运行回测流程")
        results = self.execute_strategy('equal_weight_buy_hold')
        self.logger.info("✅ 回测流程结束")
        return results

if __name__ == '__main__':
    # 示例：使用本地数据进行回测
    
    # 1. 准备模拟的本地数据
    data_list = []
    date_range = pd.to_datetime(pd.date_range(start='2023-01-01', end='2023-01-10'))
    
    for code in ['600001.SH', '600002.SH']:
        for date in date_range:
            data_list.append({
                '日期': date.strftime('%Y%m%d'),
                '股票代码': code,
                '开盘': np.random.uniform(10, 11),
                '最高': np.random.uniform(11, 12),
                '最低': np.random.uniform(9, 10),
                '收盘': np.random.uniform(10, 11),
                '成交量': np.random.randint(10000, 50000),
                '成交额': np.random.randint(1000000, 5000000)
            })
    
    local_dataframe = pd.DataFrame(data_list)
    
    # 2. 初始化回测引擎，指定 data_api='local'
    backtester = XMSQuantBacktraderRemastered(
        stock_list=['600001.SH', '600002.SH'],
        start_date='20230101',
        end_date='20230110',
        data_api='local'  # 关键：指定使用本地数据
    )
    
    # 3. 注入本地数据
    backtester.set_data(local_dataframe)
    
    # 4. 运行回测
    final_results = backtester.run()
    
    # 5. 打印结果
    import json
    print(json.dumps(final_results, indent=4, ensure_ascii=False))

import os
import sys
import platform
import pandas as pd
import numpy as np
import math
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import logging

# 导入系统适配器
from system_adapter import system_adapter, trading_modules
# 导入信号库
from signal_library import SIGNAL_CODES, generate_buy_signal, generate_sell_signal

class XMSQuantBacktraderRemastered:
    """重塑的西蒙斯量化回测系统 - 现代化且类型安全"""
    
    def __init__(self, trader_tool: str = 'ths', data_api: str = 'dfcf', 
                 data_type: str = 'D', stock_list: Optional[List[str]] = None,
                 start_date: str = '20200101', end_date: str = '20241231',
                 total_cash: float = 100000.0, st_name: str = '量化回测策略'):
        
        # 基础配置
        self.trader_tool = trader_tool
        self.data_api = data_api
        self.data_type = data_type
        self.stock_list = stock_list or []
        self.start_date = start_date
        self.end_date = end_date
        self.total_cash = total_cash
        self.st_name = st_name
        
        # 系统信息
        self.system_info = {
            'platform': platform.system(),
            'python_version': sys.version,
            'trading_platform': trading_modules['platform']
        }
        
        # 交易模块
        self.xtdata = trading_modules['xtdata']
        self.xt_client_class = trading_modules['XTPythonClient']
        self.xt_client: Optional[Any] = None
        
        # 数据存储
        self.hist_data: Union[pd.DataFrame, Dict[str, pd.DataFrame]] = pd.DataFrame()
        self.account_data: pd.DataFrame = pd.DataFrame()
        self.position_data: List[Dict[str, Any]] = []
        self.trade_records: List[Dict[str, Any]] = []
        
        # 日志配置
        self.logger = self._setup_logger()
        
        # 初始化
        self._initialize()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(f'XMSQuant_{self.st_name}')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize(self) -> None:
        """初始化回测系统"""
        try:
            self.logger.info(f"🚀 初始化西蒙斯量化回测系统")
            self.logger.info(f"📊 交易工具: {self.trader_tool}")
            self.logger.info(f"📡 数据源: {self.data_api}")
            self.logger.info(f"⏰ 回测周期: {self.start_date} - {self.end_date}")
            self.logger.info(f"💰 初始资金: {self.total_cash:,.2f}元")
            self.logger.info(f"🖥️  运行平台: {self.system_info['platform']}")
            
            # 初始化账户
            self._init_account()
            
            # 连接数据源
            if hasattr(self.xtdata, 'connect'):
                self.xtdata.connect()
            
            self.logger.info("✅ 系统初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ 系统初始化失败: {e}", exc_info=True)
            raise
    
    def _init_account(self) -> None:
        """初始化账户数据"""
        initial_data = {
            '时间': [self.start_date],
            '总资产': [self.total_cash],
            '股票市值': [0.0],
            '可用金额': [self.total_cash],
            '当日盈亏': [0.0],
            '当日盈亏比': [0.0],
            '持仓盈亏': [0.0],
            '收益': [0.0]
        }
        self.account_data = pd.DataFrame(initial_data)
        
        # 创建交易客户端
        if system_adapter.is_windows:
            # Windows环境可能需要特殊参数
            self.xt_client = self.xt_client_class(session_id=1001)
        else:
            # Linux兼容环境
            self.xt_client = self.xt_client_class(session_id=1001)
        
        if self.xt_client and hasattr(self.xt_client, 'connect'):
            self.xt_client.connect()
    
    def adjust_amount(self, stock: str = '', amount: Union[str, int, float] = '') -> int:
        """调整股票数量 - 类型安全重塑"""
        try:
            # 类型转换和验证
            if isinstance(amount, str):
                if not amount.strip():
                    return 0
                amount_num = float(amount)
            else:
                amount_num = float(amount)
            
            if amount_num <= 0:
                return 0
            
            # 股票代码验证
            if not isinstance(stock, str) or not stock.strip():
                return int(amount_num)
            
            stock_clean = stock.strip()
            
            # 债券和其他特殊品种按10股整数倍
            if (len(stock_clean) >= 3 and stock_clean[:3] in ['110', '113', '123', '127', '128', '111']) or \
               (len(stock_clean) >= 2 and stock_clean[:2] in ['11', '12']):
                adjusted = math.floor(amount_num / 10.0) * 10
            else:
                # 普通股票按100股整数倍（一手）
                adjusted = math.floor(amount_num / 100.0) * 100
            
            return max(0, int(adjusted))
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"⚠️  调整股票数量失败: {e}")
            return 0
    
    def set_data(self, data: pd.DataFrame):
        """直接设置历史数据，用于本地回测"""
        if not data.empty:
            self.logger.info(f"📈 注入 {len(data)} 条本地数据进行回测")
            # 标准化列名并按股票代码分组存储
            standardized_data = self._standardize_columns(data)
            if 'code' in standardized_data.columns:
                self.hist_data = {
                    stock: group.copy()
                    for stock, group in standardized_data.groupby('code')
                }
            else:
                # 如果没有code列，则假定为单一股票数据
                self.hist_data = {'unknown_stock': standardized_data}
        else:
            self.logger.warning("⚠️  尝试注入空的数据集")

    def get_historical_data(self, stock_code: str, 
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> pd.DataFrame:
        """获取历史数据 - 类型安全"""
        # 优先使用本地注入的数据
        if self.data_api == 'local' and isinstance(self.hist_data, dict):
            stock_data = self.hist_data.get(stock_code)
            if stock_data is not None and not stock_data.empty:
                self.logger.info(f"📊 从本地缓存获取 {stock_code} 数据")
                return stock_data
            else:
                self.logger.warning(f"⚠️  在本地缓存中未找到 {stock_code} 的数据")
                return pd.DataFrame()

        try:
            start = start_date or self.start_date
            end = end_date or self.end_date
            
            if hasattr(self.xtdata, 'download_history_data'):
                df = self.xtdata.download_history_data(
                    stock_code=stock_code,
                    period=self.data_type,
                    start_time=start,
                    end_time=end
                )
            else:
                # 兼容模式
                df = pd.DataFrame()
            
            if not df.empty:
                # 标准化列名
                df = self._standardize_columns(df)
                self.logger.info(f"📊 获取 {stock_code} 历史数据: {len(df)} 条")
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 获取 {stock_code} 历史数据失败: {e}", exc_info=True)
            return pd.DataFrame()
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化数据列名"""
        if df.empty:
            return df
        
        # 列名映射
        column_mapping = {
            'time': 'date',
            'Time': 'date',
            'TIME': 'date',
            '股票代码': 'code',
            'stock_code': 'code',
            'open': 'open',
            'Open': 'open', 
            'OPEN': 'open',
            'high': 'high',
            'High': 'high',
            'HIGH': 'high',
            'low': 'low',
            'Low': 'low',
            'LOW': 'low',
            'close': 'close',
            'Close': 'close',
            'CLOSE': 'close',
            'volume': 'volume',
            'Volume': 'volume',
            'VOLUME': 'volume',
            'amount': 'amount',
            'Amount': 'amount',
            'AMOUNT': 'amount'
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 确保必要列存在
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                self.logger.warning(f"⚠️  缺少必要列: {col}")
        
        return df
    
    def execute_strategy(self, strategy_name: str = 'equal_weight_buy_hold') -> Dict[str, Any]:
        """执行交易策略"""
        try:
            self.logger.info(f"🎯 执行策略: {strategy_name}")
            
            if strategy_name == 'equal_weight_buy_hold':
                return self._execute_equal_weight_strategy()
            elif strategy_name == 'sell_all_positions':
                # 获取当前持仓进行卖出
                return self._execute_sell_strategy(self.position_data)
            else:
                self.logger.warning(f"⚠️  未知策略: {strategy_name}")
                return {'success': False, 'error': f'不支持的策略: {strategy_name}'}
                
        except Exception as e:
            self.logger.error(f"❌ 策略执行失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _execute_equal_weight_strategy(self) -> Dict[str, Any]:
        """执行等权重买入持有策略"""
        try:
            if not self.stock_list:
                return {'success': False, 'error': '股票列表为空'}
            
            # 计算每只股票的投资金额
            cash_per_stock = self.total_cash / len(self.stock_list)
            
            results = {
                'trades': [],
                'positions': [],
                'account_summary': {},
                'performance': {}
            }
            
            for stock in self.stock_list:
                try:
                    # 获取股票数据
                    hist_data = self.get_historical_data(stock)
                    if hist_data.empty:
                        self.logger.warning(f"⚠️  {stock} 无历史数据，跳过")
                        continue
                    
                    # 获取首日价格进行买入
                    first_day_data = hist_data.iloc[0] if len(hist_data) > 0 else None
                    if first_day_data is None:
                        continue
                    
                    buy_price = float(first_day_data['close'])
                    shares_to_buy = self.adjust_amount(stock, cash_per_stock / buy_price)
                    
                    if shares_to_buy > 0:
                        # 记录交易
                        # 记录交易（添加信号记录）
                        trade_record = {
                            'stock_code': stock,
                            'action': 'buy',
                            'shares': shares_to_buy,
                            'price': buy_price,
                            'amount': shares_to_buy * buy_price,
                            'date': self.start_date,
                            'trade_time': datetime.now().isoformat(),
                            'signal': SIGNAL_CODES['buy_signal'],  # 添加买入信号
                            'signal_type': 'equal_weight_buy_hold'
                        }
                        results['trades'].append(trade_record)
                        self.trade_records.append(trade_record)
                        
                        # 记录持仓
                        position = {
                            'stock_code': stock,
                            'shares': shares_to_buy,
                            'avg_price': buy_price,
                            'market_value': shares_to_buy * buy_price,
                            'profit_loss': 0.0
                        }
                        results['positions'].append(position)
                        self.position_data.append(position)
                        
                        self.logger.info(f"💰 买入 {stock}: {shares_to_buy}股 @ {buy_price:.2f}元")
                
                except Exception as e:
                    self.logger.error(f"❌ 处理 {stock} 时出错: {e}", exc_info=True)
                    continue
            
            # 更新账户数据
            total_invested = sum(trade['amount'] for trade in results['trades'])
            remaining_cash = self.total_cash - total_invested
            
            results['account_summary'] = {
                'total_cash': self.total_cash,
                'invested_amount': total_invested,
                'remaining_cash': remaining_cash,
                'position_count': len(results['positions'])
            }
            
            results['performance'] = {
                'strategy_name': 'equal_weight_buy_hold',
                'backtest_period': f"{self.start_date} - {self.end_date}",
                'total_trades': len(results['trades']),
                'success_rate': 100.0 if results['trades'] else 0.0
            }
            
            self.logger.info(f"✅ 策略执行完成: 共{len(results['trades'])}笔交易")
            return {'success': True, 'data': results}
            
        except Exception as e:
            self.logger.error(f"❌ 等权重策略执行失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _execute_sell_strategy(self, sell_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行卖出策略"""
        try:
            results = {
                'trades': [],
                'updated_positions': [],
                'account_summary': {},
                'performance': {}
            }
            
            total_sell_amount = 0
            
            for position in sell_positions:
                stock_code = position['stock_code']
                shares_to_sell = position.get('shares', 0)
                
                try:
                    # 获取当前股票数据
                    hist_data = self.get_historical_data(stock_code)
                    if hist_data.empty:
                        continue
                    
                    # 获取当日价格进行卖出（这里用最后一天的价格）
                    last_day_data = hist_data.iloc[-1] if len(hist_data) > 0 else None
                    if last_day_data is None:
                        continue
                    
                    sell_price = float(last_day_data['close'])
                    sell_amount = shares_to_sell * sell_price
                    
                    # 记录卖出交易（添加信号记录）
                    trade_record = {
                        'stock_code': stock_code,
                        'action': 'sell',
                        'shares': shares_to_sell,
                        'price': sell_price,
                        'amount': sell_amount,
                        'date': self.end_date,
                        'trade_time': datetime.now().isoformat(),
                        'signal': SIGNAL_CODES['sell_signal'],  # 添加卖出信号
                        'signal_type': 'end_of_period_sell'
                    }
                    results['trades'].append(trade_record)
                    self.trade_records.append(trade_record)
                    
                    total_sell_amount += sell_amount
                    
                    self.logger.info(f"💸 卖出 {stock_code}: {shares_to_sell}股 @ {sell_price:.2f}元")
                    
                except Exception as e:
                    self.logger.error(f"❌ 卖出 {stock_code} 时出错: {e}", exc_info=True)
                    continue
            
            results['account_summary'] = {
                'total_sell_amount': total_sell_amount,
                'sell_trades': len(results['trades'])
            }
            
            results['performance'] = {
                'strategy_name': 'sell_strategy',
                'total_sell_trades': len(results['trades']),
                'total_sell_amount': total_sell_amount
            }
            
            self.logger.info(f"✅ 卖出策略执行完成: 共{len(results['trades'])}笔卖出交易")
            return {'success': True, 'data': results}
            
        except Exception as e:
            self.logger.error(f"❌ 卖出策略执行失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def execute_sell_all_strategy(self) -> Dict[str, Any]:
        """执行全部卖出策略"""
        try:
            if not self.position_data:
                return {'success': False, 'error': '没有持仓可以卖出'}

            results = {
                'trades': [],
                'positions': [],
                'account_summary': {},
                'performance': {}
            }

            total_sell_amount = 0.0
            
            for position in self.position_data:
                try:
                    stock = position['stock_code']
                    shares = position['shares']
                    
                    # 获取当前价格（使用最后一天的收盘价）
                    hist_data = self.get_historical_data(stock)
                    if hist_data.empty:
                        continue
                    
                    last_day_data = hist_data.iloc[-1]
                    sell_price = float(last_day_data['close'])
                    sell_amount = shares * sell_price
                    
                    # 记录卖出交易
                    trade_record = {
                        'stock_code': stock,
                        'action': 'sell',
                        'shares': shares,
                        'price': sell_price,
                        'amount': sell_amount,
                        'date': self.end_date,
                        'trade_time': datetime.now().isoformat(),
                        'signal': 16  # 卖出信号
                    }
                    results['trades'].append(trade_record)
                    self.trade_records.append(trade_record)
                    total_sell_amount += sell_amount
                    
                    self.logger.info(f"💰 卖出 {stock}: {shares}股 @ {sell_price:.2f}元")
                    
                except Exception as e:
                    self.logger.error(f"❌ 卖出 {stock} 时出错: {e}", exc_info=True)
                    continue

            # 清空持仓
            self.position_data.clear()
            
            # 更新账户数据
            results['account_summary'] = {
                'total_sell_amount': total_sell_amount,
                'remaining_positions': len(self.position_data),
                'total_trades': len(results['trades'])
            }
            
            results['performance'] = {
                'strategy_name': 'sell_all',
                'sell_date': self.end_date,
                'total_sell_trades': len(results['trades']),
                'total_sell_amount': total_sell_amount
            }
            
            self.logger.info(f"✅ 卖出策略执行完成: 共{len(results['trades'])}笔卖出交易")
            return {'success': True, 'data': results}
            
        except Exception as e:
            self.logger.error(f"❌ 卖出策略执行失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def get_last_account_data(self) -> pd.DataFrame:
        """获取最新账户数据"""
        if self.account_data.empty:
            self._init_account()
        return self.account_data.tail(1).copy()
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            **self.system_info,
            'strategy_name': self.st_name,
            'data_source': self.data_api,
            'trading_tool': self.trader_tool,
            'backtest_period': f"{self.start_date} - {self.end_date}",
            'total_stocks': len(self.stock_list),
            'initial_capital': self.total_cash
        }
    
    def cleanup(self) -> None:
        """清理资源"""
        try:
            if hasattr(self.xtdata, 'disconnect'):
                self.xtdata.disconnect()
            
            if self.xt_client and hasattr(self.xt_client, 'disconnect'):
                self.xt_client.disconnect()
            
            self.logger.info("🧹 资源清理完成")
            
        except Exception as e:
            self.logger.error(f"⚠️  资源清理时出现问题: {e}")

# 为了保持向后兼容性，创建别名
xms_quant_backtrader = XMSQuantBacktraderRemastered

# 导出类和检查函数
__all__ = ['XMSQuantBacktraderRemastered', 'xms_quant_backtrader']
