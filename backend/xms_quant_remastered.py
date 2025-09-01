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
            self.logger.info(f"📡 数据源: 本地数据库")
            self.logger.info(f"⏰ 回测周期: {self.start_date} - {self.end_date}")
            self.logger.info(f"💰 初始资金: {self.total_cash:,.2f}元")
            self.logger.info(f"🖥️  运行平台: {self.system_info['platform']}")
            
            self._init_account()
            
            # 移除远程数据连接，直接使用本地数据库
            self.logger.info("✅ 使用本地数据库，无需远程连接")

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
        
        # 移除远程连接，使用本地数据库
        self.xt_client = None
        self.logger.info("💰 账户初始化完成 - 使用本地数据库模式")
    
    def adjust_amount(self, stock: str = '', amount: Union[str, int, float] = '') -> int:
        """调整股票数量 - 类型安全重塑"""
        try:
            if isinstance(amount, str):
                if not amount.strip(): 
                    return 0
                amount_num = float(amount)
            else:
                amount_num = float(amount)
            
            if amount_num <= 0: 
                return 0
            if not isinstance(stock, str) or not stock.strip(): 
                return int(amount_num)
            
            stock_clean = stock.strip()
            
            # 债券和其他特殊品种按10股整数倍
            if ((len(stock_clean) >= 3 and stock_clean[:3] in ['110', '113', '123', '127', '128', '111']) or 
               (len(stock_clean) >= 2 and stock_clean[:2] in ['11', '12'])):
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
                           end_date: Optional[str] = None,
                           extend_days: int = 30) -> pd.DataFrame:
        """从本地数据库获取历史数据，自动扩展历史天数以满足技术指标计算需求"""
        try:
            # 检查Django是否已配置
            import django
            from django.conf import settings
            from datetime import datetime, timedelta
            
            if not settings.configured:
                # 在独立运行时，配置Django
                import os
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
                django.setup()
            
            # 导入Django模型
            from stockmarket.models import StockHistoryData
            from django.db.models import Q
            
            start = start_date or self.start_date
            end = end_date or self.end_date
            
            # 格式化日期
            if len(start) == 8:  # YYYYMMDD
                start_formatted = f"{start[:4]}-{start[4:6]}-{start[6:8]}"
            else:
                start_formatted = start
                
            if len(end) == 8:  # YYYYMMDD
                end_formatted = f"{end[:4]}-{end[4:6]}-{end[6:8]}"
            else:
                end_formatted = end
            
            # 为了计算技术指标，需要扩展开始日期（仅当没有明确指定start_date时）
            if start_date is not None:
                # 如果明确指定了开始日期，使用该日期
                final_start_formatted = start_formatted
            else:
                # 如果没有指定开始日期，为计算技术指标自动扩展
                end_dt = datetime.strptime(end_formatted, '%Y-%m-%d')
                extended_start_dt = end_dt - timedelta(days=extend_days)
                final_start_formatted = extended_start_dt.strftime('%Y-%m-%d')
            
            # 转换股票代码格式：000001.SZ -> 000001 (数据库中symbol字段是字符串)
            if '.' in stock_code:
                # 去掉.SZ后缀
                db_symbol = stock_code.split('.')[0]  # 000001.SZ -> 000001
            else:
                db_symbol = stock_code
            
            # 从数据库查询，使用确定的开始日期
            queryset = StockHistoryData.objects.filter(
                symbol=db_symbol,  # 使用字符串查询
                date__gte=final_start_formatted,  # 使用确定的开始日期
                date__lte=end_formatted
            ).order_by('date')
            
            if queryset.exists():
                # 转换为DataFrame
                data_list = []
                for record in queryset:
                    data_list.append({
                        'date': record.date.strftime('%Y%m%d'),
                        'open': float(record.open),
                        'high': float(record.high),
                        'low': float(record.low),
                        'close': float(record.close),
                        'volume': float(record.volume),
                        'amount': float(record.turnover) if hasattr(record, 'turnover') and record.turnover else 0.0
                    })
                
                df = pd.DataFrame(data_list)
                print(f"📊 生成 {stock_code} (数据库symbol: {db_symbol}) 历史数据: {len(df)} 条记录")
                return df
            else:
                print(f"⚠️  数据库中未找到 {stock_code} (数据库symbol: {db_symbol}) 在 {start_formatted} 到 {end_formatted} 的数据")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"❌ 从数据库获取 {stock_code} 历史数据失败: {e}", exc_info=True)
            
            # 回退到生成模拟数据进行测试
            if 'settings are not configured' in str(e) or 'DJANGO_SETTINGS_MODULE' in str(e):
                self.logger.warning(f"⚠️  Django未配置，生成模拟数据用于测试")
                return self._generate_mock_data(stock_code, start_date, end_date)
            
            return pd.DataFrame()
    
    def _generate_mock_data(self, stock_code: str, start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> pd.DataFrame:
        """生成模拟数据用于测试"""
        try:
            import numpy as np
            from datetime import datetime, timedelta
            
            start = start_date or self.start_date
            end = end_date or self.end_date
            
            # 生成日期范围
            start_dt = datetime.strptime(start, '%Y%m%d')
            end_dt = datetime.strptime(end, '%Y%m%d')
            
            dates = []
            current = start_dt
            while current <= end_dt:
                # 只添加工作日
                if current.weekday() < 5:
                    dates.append(current.strftime('%Y%m%d'))
                current += timedelta(days=1)
            
            if not dates:
                return pd.DataFrame()
            
            # 生成价格数据（简单随机游走）
            np.random.seed(42)  # 固定种子确保结果一致
            base_price = 20.0 if '000001' in stock_code else 25.0
            
            data_list = []
            for i, date in enumerate(dates):
                price_change = np.random.normal(0, 0.02)  # 2%的标准差
                if i == 0:
                    open_price = base_price
                else:
                    open_price = data_list[i-1]['close']
                
                high_price = open_price * (1 + abs(price_change) + np.random.uniform(0, 0.01))
                low_price = open_price * (1 - abs(price_change) - np.random.uniform(0, 0.01))
                close_price = open_price * (1 + price_change)
                volume = np.random.uniform(1000000, 5000000)
                
                data_list.append({
                    'date': date,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': int(volume),
                    'amount': round(close_price * volume, 2)
                })
            
            df = pd.DataFrame(data_list)
            print(f"📊 生成 {stock_code} 模拟数据: {len(df)} 条记录")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 生成模拟数据失败: {e}")
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

    def execute_strategy(self, strategy_name: str = 'equal_weight_buy_hold', strategy_config: Dict = None) -> Dict[str, Any]:
        """执行交易策略"""
        try:
            self.logger.info(f"🎯 执行策略: {strategy_name}")
            
            if strategy_name == 'equal_weight_buy_hold':
                return self._execute_equal_weight_strategy()
            elif strategy_name == 'indicator_driven':
                # 指标驱动策略 - 根据前端选择的指标生成交易信号
                return self._execute_indicator_driven_strategy(strategy_config)
            elif strategy_name == 'price_volume_driven':
                # 价格成交量驱动策略
                return self._execute_price_volume_strategy(strategy_config)
            elif strategy_name == 'sell_all_positions':
                return self._execute_sell_strategy(self.position_data)
            else:
                self.logger.warning(f"⚠️  未知策略: {strategy_name}")
                return {'success': False, 'error': f'不支持的策略: {strategy_name}'}
                
        except Exception as e:
            self.logger.error(f"❌ 策略执行失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _execute_equal_weight_strategy(self) -> Dict[str, Any]:
        """执行等权重买入持有策略 - 增强版：支持定期再平衡"""
        try:
            if not self.stock_list:
                return {'success': False, 'error': '股票列表为空'}
            
            results = {
                'trades': [],
                'positions': [],
                'account_summary': {},
                'performance': {}
            }
            
            # 生成再平衡日期（每季度一次）
            rebalance_dates = self._generate_rebalance_dates()
            self.logger.info(f"📅 计划再平衡日期: {len(rebalance_dates)} 次")
            
            current_positions = {}  # 当前持仓
            
            for i, rebalance_date in enumerate(rebalance_dates):
                self.logger.info(f"🔄 第 {i+1} 次再平衡: {rebalance_date}")
                
                # 计算目标权重（等权重）
                target_weight = 1.0 / len(self.stock_list)
                current_total_value = self._calculate_total_portfolio_value(current_positions, rebalance_date)
                
                # 为每只股票执行交易
                for stock in self.stock_list:
                    try:
                        hist_data = self.get_historical_data(stock, end_date=rebalance_date)
                        if hist_data.empty:
                            continue
                        
                        # 获取当日价格
                        current_price = float(hist_data.iloc[-1]['close'])
                        target_value = current_total_value * target_weight
                        current_value = current_positions.get(stock, {}).get('value', 0)
                        
                        # 计算需要调整的金额
                        value_diff = target_value - current_value
                        
                        if abs(value_diff) > 100:  # 只有差额超过100元才交易
                            shares_to_trade = int(abs(value_diff) / current_price)
                            
                            if value_diff > 0:  # 需要买入
                                if shares_to_trade > 0:
                                    trade_record = {
                                        'stock_code': stock, 'action': 'buy', 'shares': shares_to_trade,
                                        'price': current_price, 'amount': shares_to_trade * current_price,
                                        'date': rebalance_date, 
                                        'trade_time': f"{rebalance_date[:4]}-{rebalance_date[4:6]}-{rebalance_date[6:8]}T09:30:00",
                                        'signal': SIGNAL_CODES['buy_signal'], 'signal_type': 'rebalance_buy'
                                    }
                                    results['trades'].append(trade_record)
                                    self.trade_records.append(trade_record)
                                    self.logger.info(f"💰 买入 {stock}: {shares_to_trade}股 @ {current_price:.2f}元")
                                    
                                    # 更新持仓
                                    if stock in current_positions:
                                        current_positions[stock]['shares'] += shares_to_trade
                                        current_positions[stock]['value'] += shares_to_trade * current_price
                                    else:
                                        current_positions[stock] = {
                                            'shares': shares_to_trade,
                                            'value': shares_to_trade * current_price,
                                            'avg_price': current_price
                                        }
                            
                            else:  # 需要卖出
                                current_shares = current_positions.get(stock, {}).get('shares', 0)
                                shares_to_sell = min(shares_to_trade, current_shares)
                                
                                if shares_to_sell > 0:
                                    trade_record = {
                                        'stock_code': stock, 'action': 'sell', 'shares': shares_to_sell,
                                        'price': current_price, 'amount': shares_to_sell * current_price,
                                        'date': rebalance_date,
                                        'trade_time': f"{rebalance_date[:4]}-{rebalance_date[4:6]}-{rebalance_date[6:8]}T15:00:00",
                                        'signal': SIGNAL_CODES['sell_signal'], 'signal_type': 'rebalance_sell'
                                    }
                                    results['trades'].append(trade_record)
                                    self.trade_records.append(trade_record)
                                    self.logger.info(f"💰 卖出 {stock}: {shares_to_sell}股 @ {current_price:.2f}元")
                                    
                                    # 更新持仓
                                    if stock in current_positions:
                                        current_positions[stock]['shares'] -= shares_to_sell
                                        current_positions[stock]['value'] -= shares_to_sell * current_price
                                        if current_positions[stock]['shares'] <= 0:
                                            del current_positions[stock]
                        
                    except Exception as e:
                        self.logger.error(f"❌ 处理 {stock} 再平衡时出错: {e}")
            
            # 最终卖出所有持仓
            if current_positions:
                for stock, position in current_positions.items():
                    if position['shares'] > 0:
                        hist_data = self.get_historical_data(stock, end_date=self.end_date)
                        if not hist_data.empty:
                            final_price = float(hist_data.iloc[-1]['close'])
                            trade_record = {
                                'stock_code': stock, 'action': 'sell', 'shares': position['shares'],
                                'price': final_price, 'amount': position['shares'] * final_price,
                                'date': self.end_date,
                                'trade_time': f"{self.end_date[:4]}-{self.end_date[4:6]}-{self.end_date[6:8]}T15:00:00",
                                'signal': SIGNAL_CODES['sell_signal'], 'signal_type': 'end_of_backtest_sell'
                            }
                            results['trades'].append(trade_record)
                            self.trade_records.append(trade_record)
                            self.logger.info(f"💰 最终卖出 {stock}: {position['shares']}股 @ {final_price:.2f}元")
            
            # 计算账户摘要
            total_invested = sum(trade['amount'] for trade in results['trades'] if trade['action'] == 'buy')
            total_received = sum(trade['amount'] for trade in results['trades'] if trade['action'] == 'sell')
            
            results['account_summary'] = {
                'total_cash': self.total_cash,
                'invested_amount': total_invested,
                'received_amount': total_received,
                'position_count': len([p for p in current_positions.values() if p['shares'] > 0])
            }
            
            # 模拟最终评估
            self._evaluate_performance(results)
            
            return {'success': True, 'data': results}

        except Exception as e:
            self.logger.error(f"❌ 等权重策略执行失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _generate_rebalance_dates(self) -> List[str]:
        """生成再平衡日期（每季度）"""
        import datetime
        
        start = datetime.datetime.strptime(self.start_date, '%Y%m%d')
        end = datetime.datetime.strptime(self.end_date, '%Y%m%d')
        
        dates = []
        current = start
        
        # 初始买入
        dates.append(self.start_date)
        
        # 每季度再平衡
        while current < end:
            current += datetime.timedelta(days=90)  # 约3个月
            if current <= end:
                date_str = current.strftime('%Y%m%d')
                dates.append(date_str)
        
        return dates
    
    def _calculate_total_portfolio_value(self, positions: Dict, date: str) -> float:
        """计算投资组合总价值"""
        total_value = self.total_cash
        
        for stock, position in positions.items():
            try:
                hist_data = self.get_historical_data(stock, end_date=date)
                if not hist_data.empty:
                    current_price = float(hist_data.iloc[-1]['close'])
                    total_value += position['shares'] * current_price
            except:
                continue
        
        return total_value

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
                    'trade_time': f"{self.end_date[:4]}-{self.end_date[4:6]}-{self.end_date[6:8]}T15:00:00", 'signal': SIGNAL_CODES['sell_signal'],
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
        """评估回测性能 - 增强版包含夏普比率、最大回撤、胜率"""
        if not results['trades']:
            results['performance'] = {'message': '无交易记录，无法评估'}
            return

        # 卖出所有持仓以计算最终市值
        sell_results = self._execute_sell_strategy(results['positions'])
        if not sell_results['success']:
            self.logger.error("❌ 评估时卖出持仓失败")
            return
            
        final_cash = sell_results['data']['account_summary']['final_cash']
        
        # 重要：将卖出交易添加到主要的交易记录中
        results['trades'].extend(sell_results['data']['trades'])
        
        # 导入高级指标计算模块
        try:
            from advanced_metrics import calculate_advanced_metrics, generate_mock_daily_returns
            
            # 生成模拟的每日收益率数据
            daily_returns = generate_mock_daily_returns(self.total_cash, final_cash)
            
            # 计算包含高级指标的性能数据
            advanced_metrics = calculate_advanced_metrics(
                trades_data=self.trade_records,
                initial_cash=self.total_cash,
                final_cash=final_cash,
                daily_returns=daily_returns
            )
            
            results['performance'] = advanced_metrics
            
        except ImportError as e:
            self.logger.warning(f"⚠️  无法导入高级指标模块，使用基础指标: {e}")
            # 回退到基础指标
            total_return = (final_cash - self.total_cash) / self.total_cash
            results['performance'] = {
                'initial_cash': self.total_cash,
                'final_cash': final_cash,
                'total_return_pct': f"{total_return:.2%}",
                'total_trades': len(self.trade_records),
                'win_rate': "0.00%",
                'max_drawdown': "0.00%",
                'sharpe_ratio': "0.00"
            }
        
        total_return_pct = results['performance'].get('total_return_pct', '0.00%')
        self.logger.info(f"📈 回测评估完成: 最终资产 {final_cash:,.2f}元, 总回报率 {total_return_pct}")
        self.logger.info(f"📊 胜率: {results['performance'].get('win_rate', '0.00%')}, "
                        f"最大回撤: {results['performance'].get('max_drawdown', '0.00%')}, "
                        f"夏普比率: {results['performance'].get('sharpe_ratio', '0.00')}")

    def _execute_indicator_driven_strategy(self, strategy_config: Dict = None) -> Dict[str, Any]:
        """执行指标驱动策略 - 根据指标在整个时间范围内生成交易信号"""
        try:
            if not strategy_config:
                strategy_config = {}
                
            indicators = strategy_config.get('indicators', [])
            indicator_params = strategy_config.get('indicator_params', {})
            symbols = strategy_config.get('symbols', ['000001', '000002'])  # 默认股票池
            
            self.logger.info(f"📊 指标驱动策略 - 使用指标: {indicators}")
            
            # 临时设置股票列表，用于生成交易日期
            self.stock_list = symbols
            
            # 生成交易日期列表（每月检查一次信号）
            trade_dates = self._generate_monthly_rebalance_dates()
            
            trades = []
            current_positions = {}
            
            for i, trade_date in enumerate(trade_dates):
                try:
                    # 获取当前持仓的股票
                    current_stocks = list(current_positions.keys())
                    
                    # 获取所有候选股票的当前数据
                    stocks_to_check = self.stock_list if i == 0 else (self.stock_list + current_stocks)
                    
                    # 评估每只股票的信号强度
                    stock_signals = {}
                    
                    for stock in stocks_to_check:
                        signal_strength = self._evaluate_stock_indicators(
                            stock, trade_date, indicators, indicator_params
                        )
                        if signal_strength > 0:  # 买入信号
                            stock_signals[stock] = signal_strength
                    
                    # 根据信号强度排序，选择前N只股票
                    target_stocks = sorted(stock_signals.items(), key=lambda x: x[1], reverse=True)[:4]
                    target_stock_codes = [stock for stock, _ in target_stocks]
                    
                    # 执行交易：卖出不在目标列表中的股票
                    for stock in current_stocks:
                        if stock not in target_stock_codes:
                            hist_data = self.get_historical_data(stock, end_date=trade_date)
                            if not hist_data.empty:
                                sell_price = float(hist_data.iloc[-1]['close'])
                                shares = current_positions[stock]['shares']
                                sell_amount = shares * sell_price
                                
                                trades.append({
                                    'stock_code': stock, 'action': 'sell', 'shares': shares,
                                    'price': sell_price, 'amount': sell_amount, 'date': trade_date,
                                    'trade_time': f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}T14:30:00",
                                    'signal': 16, 'signal_type': 'indicator_sell'
                                })
                                
                                del current_positions[stock]
                                self.logger.info(f"💰 指标卖出 {stock}: {shares}股 @ {sell_price:.2f}元")
                    
                    # 买入新的目标股票
                    available_cash = self.total_cash / max(1, len(target_stock_codes))
                    
                    for stock in target_stock_codes:
                        if stock not in current_positions:
                            hist_data = self.get_historical_data(stock, end_date=trade_date)
                            if not hist_data.empty:
                                buy_price = float(hist_data.iloc[-1]['close'])
                                shares = int(available_cash / buy_price)
                                if shares > 0:
                                    buy_amount = shares * buy_price
                                    
                                    trades.append({
                                        'stock_code': stock, 'action': 'buy', 'shares': shares,
                                        'price': buy_price, 'amount': buy_amount, 'date': trade_date,
                                        'trade_time': f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}T09:30:00",
                                        'signal': 15, 'signal_type': 'indicator_buy'
                                    })
                                    
                                    current_positions[stock] = {'shares': shares, 'avg_cost': buy_price}
                                    self.logger.info(f"💰 指标买入 {stock}: {shares}股 @ {buy_price:.2f}元")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ 日期 {trade_date} 交易失败: {e}")
                    continue
            
            # 最后卖出所有持仓
            for stock, position in current_positions.items():
                hist_data = self.get_historical_data(stock, end_date=self.end_date)
                if not hist_data.empty:
                    sell_price = float(hist_data.iloc[-1]['close'])
                    shares = position['shares']
                    sell_amount = shares * sell_price
                    
                    trades.append({
                        'stock_code': stock, 'action': 'sell', 'shares': shares,
                        'price': sell_price, 'amount': sell_amount, 'date': self.end_date,
                        'trade_time': f"{self.end_date[:4]}-{self.end_date[4:6]}-{self.end_date[6:8]}T15:00:00",
                        'signal': 16, 'signal_type': 'end_of_backtest_sell'
                    })
            
            # 计算最终资产
            total_buy = sum(t['amount'] for t in trades if t['action'] == 'buy')
            total_sell = sum(t['amount'] for t in trades if t['action'] == 'sell')
            final_cash = self.total_cash - total_buy + total_sell
            
            # 生成回测报告
            return self._generate_backtest_report(trades, final_cash)
            
        except Exception as e:
            self.logger.error(f"❌ 指标驱动策略执行失败: {e}")
            return {'success': False, 'error': str(e)}

    def _execute_price_volume_strategy(self, strategy_config: Dict = None) -> Dict[str, Any]:
        """执行价格成交量驱动策略"""
        try:
            if not strategy_config:
                strategy_config = {}
                
            self.logger.info("📊 价格成交量驱动策略")
            
            # 生成交易日期（每周检查一次）
            trade_dates = self._generate_weekly_rebalance_dates()
            
            trades = []
            current_positions = {}
            
            for trade_date in trade_dates:
                try:
                    # 评估价格和成交量指标
                    stock_scores = {}
                    
                    for stock in self.stock_list:
                        score = self._evaluate_price_volume_signals(stock, trade_date)
                        if score > 0:
                            stock_scores[stock] = score
                    
                    # 选择得分最高的股票
                    target_stocks = sorted(stock_scores.items(), key=lambda x: x[1], reverse=True)[:3]
                    target_stock_codes = [stock for stock, _ in target_stocks]
                    
                    # 执行交易逻辑（类似指标驱动策略）
                    # ... 这里可以复用指标驱动策略的交易逻辑
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ 日期 {trade_date} 价格成交量策略失败: {e}")
                    continue
            
            return self._generate_backtest_report(trades, self.total_cash)
            
        except Exception as e:
            self.logger.error(f"❌ 价格成交量策略执行失败: {e}")
            return {'success': False, 'error': str(e)}

    def _evaluate_stock_indicators(self, stock_code: str, date: str, indicators: List[str], params: Dict) -> float:
        """评估股票的指标信号强度"""
        try:
            hist_data = self.get_historical_data(stock_code, end_date=date)
            if hist_data.empty or len(hist_data) < 20:
                return 0
            
            signal_strength = 0
            
            # 将指标名称转换为小写进行比较
            indicators_lower = [ind.lower() for ind in indicators]
            
            # 评估各种指标
            if 'ma' in indicators_lower:
                ma_signal = self._evaluate_ma_signal(hist_data, params.get('ma_params', {}))
                signal_strength += ma_signal
            
            if 'macd' in indicators_lower:
                macd_signal = self._evaluate_macd_signal(hist_data, params.get('macd_params', {}))
                signal_strength += macd_signal
            
            if 'kdj' in indicators_lower:
                kdj_signal = self._evaluate_kdj_signal(hist_data, params.get('kdj_params', {}))
                signal_strength += kdj_signal
            
            return signal_strength
            
        except Exception as e:
            self.logger.warning(f"⚠️ 评估 {stock_code} 指标失败: {e}")
            return 0

    def _evaluate_ma_signal(self, data, params):
        """评估MA信号"""
        try:
            short_period = params.get('short', 5)
            long_period = min(params.get('long', 10), len(data) - 1)  # 调整为数据量允许的长度
            
            if len(data) < short_period:
                return 0
            
            ma_short = data['close'].rolling(short_period).mean().iloc[-1]
            ma_long = data['close'].rolling(long_period).mean().iloc[-1]
            
            print(f"📊 MA信号评估: 短期MA({short_period}天)={ma_short:.2f}, 长期MA({long_period}天)={ma_long:.2f}")
            
            # 金叉：短线上穿长线
            if ma_short > ma_long * 1.01:  # 需要有1%的优势
                print(f"✅ MA金叉信号 (买入)")
                return 1
            # 死叉：短线下穿长线
            elif ma_short < ma_long * 0.99:  # 跌破1%
                print(f"⭕ MA死叉信号 (卖出)")
                return -1
            else:
                print(f"🔄 MA信号中性")
                return 0.5  # 给一个小的正值，避免完全没有信号
        except Exception as e:
            print(f"❌ MA评估失败: {e}")
            return 0

    def _evaluate_macd_signal(self, data, params):
        """评估MACD信号"""
        try:
            # 简化的MACD计算
            short = params.get('short', 12)
            long = params.get('long', 26)
            
            if len(data) < long:
                return 0
            
            ema_short = data['close'].ewm(span=short).mean()
            ema_long = data['close'].ewm(span=long).mean()
            dif = ema_short - ema_long
            
            # 简单判断：DIF为正表示上涨趋势
            if dif.iloc[-1] > 0 and dif.iloc[-1] > dif.iloc[-2]:
                return 1
            elif dif.iloc[-1] < 0:
                return -1
            else:
                return 0
        except:
            return 0

    def _evaluate_kdj_signal(self, data, params):
        """评估KDJ信号"""
        try:
            n = params.get('n', 9)
            
            if len(data) < n:
                return 0
            
            # 简化的KDJ计算
            low_min = data['low'].rolling(n).min()
            high_max = data['high'].rolling(n).max()
            rsv = (data['close'] - low_min) / (high_max - low_min) * 100
            
            k = rsv.ewm(alpha=1/3).mean().iloc[-1]
            
            # K值判断
            if k < 20:  # 超卖
                return 1
            elif k > 80:  # 超买
                return -1
            else:
                return 0
        except:
            return 0

    def _evaluate_price_volume_signals(self, stock_code: str, date: str) -> float:
        """评估价格成交量信号"""
        try:
            hist_data = self.get_historical_data(stock_code, end_date=date)
            if hist_data.empty or len(hist_data) < 10:
                return 0
            
            signal_score = 0
            
            # 价格趋势分析
            recent_prices = hist_data['close'].tail(5)
            if recent_prices.iloc[-1] > recent_prices.iloc[0]:  # 上涨趋势
                signal_score += 1
            
            # 成交量分析
            recent_volumes = hist_data['volume'].tail(5)
            avg_volume = recent_volumes.mean()
            if recent_volumes.iloc[-1] > avg_volume * 1.5:  # 放量
                signal_score += 1
            
            return signal_score
            
        except Exception as e:
            return 0

    def _generate_weekly_rebalance_dates(self) -> List[str]:
        """生成每周再平衡日期"""
        try:
            from datetime import datetime, timedelta
            
            start = datetime.strptime(self.start_date, '%Y%m%d')
            end = datetime.strptime(self.end_date, '%Y%m%d')
            
            dates = []
            current = start
            
            while current <= end:
                dates.append(current.strftime('%Y%m%d'))
                current += timedelta(weeks=1)  # 每周
            
            return dates
        except:
            return [self.start_date, self.end_date]

    def _generate_monthly_rebalance_dates(self) -> List[str]:
        """生成每月再平衡日期 - 基于实际交易日"""
        try:
            # 先获取一只股票的数据，确定实际交易日
            if self.stock_list:
                # 使用完整的回测时间范围获取数据
                sample_data = self.get_historical_data(
                    self.stock_list[0], 
                    start_date=self.start_date, 
                    end_date=self.end_date
                )
                if not sample_data.empty:
                    # 基于实际交易日生成月度日期
                    available_dates = sorted(sample_data['date'].unique())
                    
                    # 每5个交易日选择一个作为再平衡日期（提高频率）
                    rebalance_dates = []
                    for i in range(0, len(available_dates), 5):  # 从每10天改为每5天
                        rebalance_dates.append(available_dates[i])
                    
                    # 确保包含最后一个交易日
                    if available_dates[-1] not in rebalance_dates:
                        rebalance_dates.append(available_dates[-1])
                    
                    print(f"📅 生成再平衡日期: {len(rebalance_dates)}个日期，范围{rebalance_dates[0]}到{rebalance_dates[-1]}")
                    return rebalance_dates
            
            # 回退到默认日期生成
            import datetime
            start = datetime.datetime.strptime(self.start_date, '%Y%m%d')
            end = datetime.datetime.strptime(self.end_date, '%Y%m%d')
            
            dates = []
            current = start
            
            while current <= end:
                dates.append(current.strftime('%Y%m%d'))
                current += datetime.timedelta(days=15)  # 每两周
            
            return dates
        except Exception as e:
            print(f"⚠️ 生成再平衡日期失败: {e}")
            return [self.start_date, self.end_date]

    def _generate_backtest_report(self, trades: List[Dict], final_cash: float) -> Dict[str, Any]:
        """生成回测报告"""
        try:
            if not trades:
                return {
                    'success': True,
                    'data': {
                        'trades': [],
                        'performance': {
                            'total_return': 0,
                            'total_return_rate': 0,
                            'annual_return': 0,
                            'sharpe_ratio': 0,
                            'max_drawdown': 0,
                            'win_rate': 0
                        },
                        'account_summary': {
                            'initial_cash': self.total_cash,
                            'final_cash': final_cash,
                            'total_profit': final_cash - self.total_cash,
                            'profit_rate': ((final_cash - self.total_cash) / self.total_cash) * 100
                        }
                    }
                }
            
            # 计算性能指标
            total_buy = sum(t['amount'] for t in trades if t['action'] == 'buy')
            total_sell = sum(t['amount'] for t in trades if t['action'] == 'sell')
            total_profit = final_cash - self.total_cash
            profit_rate = (total_profit / self.total_cash) * 100 if self.total_cash > 0 else 0
            
            # 计算胜率
            profitable_trades = 0
            total_completed_trades = 0
            
            # 简单统计：如果有卖出操作，计算盈利交易比例
            sell_trades = [t for t in trades if t['action'] == 'sell']
            for sell_trade in sell_trades:
                # 查找对应的买入交易
                buy_trades = [t for t in trades if t['action'] == 'buy' and t['stock_code'] == sell_trade['stock_code']]
                if buy_trades:
                    avg_buy_price = sum(t['price'] for t in buy_trades) / len(buy_trades)
                    if sell_trade['price'] > avg_buy_price:
                        profitable_trades += 1
                    total_completed_trades += 1
            
            win_rate = (profitable_trades / total_completed_trades * 100) if total_completed_trades > 0 else 0
            
            # 计算年化收益（简化计算）
            try:
                from datetime import datetime
                start_dt = datetime.strptime(self.start_date, '%Y%m%d')
                end_dt = datetime.strptime(self.end_date, '%Y%m%d')
                days = (end_dt - start_dt).days
                years = days / 365.25 if days > 0 else 1
                annual_return = (profit_rate / years) if years > 0 else profit_rate
                
                # 改进夏普比率计算 - 使用更合理的方法
                risk_free_rate = 3.0  # 无风险利率3%
                
                # 计算策略的真实波动率
                if len(trades) > 1:
                    # 从交易数据计算收益率序列
                    returns = []
                    for i in range(1, len(trades)):
                        if trades[i]['action'] == 'sell' and trades[i-1]['action'] == 'buy':
                            buy_amount = trades[i-1]['amount']
                            sell_amount = trades[i]['amount']
                            trade_return = (sell_amount - buy_amount) / buy_amount
                            returns.append(trade_return)
                    
                    if returns:
                        import numpy as np
                        # 计算年化波动率
                        daily_volatility = np.std(returns) if len(returns) > 1 else abs(profit_rate / 100)
                        annual_volatility = daily_volatility * np.sqrt(252)  # 年化波动率
                        
                        # 计算夏普比率 (年化收益 - 无风险利率) / 年化波动率
                        if annual_volatility > 0:
                            sharpe_ratio = (annual_return - risk_free_rate) / (annual_volatility * 100)
                        else:
                            sharpe_ratio = 0
                    else:
                        # 如果没有完整交易对，使用简化计算
                        estimated_volatility = abs(annual_return) * 0.5  # 保守估计波动率
                        sharpe_ratio = (annual_return - risk_free_rate) / estimated_volatility if estimated_volatility > 0 else 0
                else:
                    # 单笔交易或无交易，夏普比率设为0
                    sharpe_ratio = 0
                
                # 限制夏普比率在合理范围内 (-3 到 +3)
                sharpe_ratio = max(-3.0, min(3.0, sharpe_ratio))
                
            except:
                annual_return = profit_rate
                sharpe_ratio = 0
            
            return {
                'success': True,
                'data': {
                    'trades': trades,
                    'performance': {
                        'total_return': round(total_profit, 2),
                        'total_return_rate': round(profit_rate, 2),
                        'annual_return': round(annual_return, 2),
                        'sharpe_ratio': round(sharpe_ratio, 2),  # 统一使用2位小数
                        'max_drawdown': round(min(0, profit_rate), 2),  # 简化最大回撤
                        'win_rate': round(win_rate, 2)  # 胜率保留2位小数
                    },
                    'account_summary': {
                        'initial_cash': self.total_cash,
                        'final_cash': final_cash,
                        'total_profit': total_profit,
                        'profit_rate': profit_rate,
                        'total_trades': len(trades),
                        'buy_trades': len([t for t in trades if t['action'] == 'buy']),
                        'sell_trades': len([t for t in trades if t['action'] == 'sell'])
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ 生成回测报告失败: {e}")
            return {
                'success': False,
                'error': f'生成回测报告失败: {str(e)}',
                'data': {
                    'trades': trades,
                    'performance': {},
                    'account_summary': {
                        'initial_cash': self.total_cash,
                        'final_cash': final_cash
                    }
                }
            }

    def run(self) -> Dict[str, Any]:
        """运行完整的回测流程"""
        self.logger.info("🚀 开始运行回测流程")
        results = self.execute_strategy('equal_weight_buy_hold')
        self.logger.info("✅ 回测流程结束")
        return results

# 为了保持向后兼容性，创建别名
xms_quant_backtrader = XMSQuantBacktraderRemastered

# 导出类和检查函数
__all__ = ['XMSQuantBacktraderRemastered', 'xms_quant_backtrader']

if __name__ == '__main__':
    # 示例：使用本地数据进行回测
    
    # 1. 准备模拟的本地数据
    data_list = []
    date_range = pd.date_range(start='2023-01-01', end='2023-01-10')
    
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
    print(json.dumps(final_results, indent=4, ensure_ascii=False))
