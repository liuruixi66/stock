"""
增强的回测性能分析模块
计算夏普比率、最大回撤、胜率等高级指标
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import math

def calculate_advanced_metrics(trades_data: List[Dict], initial_cash: float, final_cash: float, 
                             daily_returns: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    计算高级回测指标
    
    Args:
        trades_data: 交易记录列表
        initial_cash: 初始资金
        final_cash: 最终资金
        daily_returns: 每日收益率列表（可选）
    
    Returns:
        包含高级指标的字典

    提供日收益率时使用真实收益率计算回撤和夏普；未提供时使用简化估算，
    因而估算结果适合展示，不应与完整净值曲线的风险指标直接比较。
    """
    metrics = {}
    
    try:
        # 1. 计算总回报率
        total_return = (final_cash - initial_cash) / initial_cash
        metrics['total_return_pct'] = f"{total_return:.2%}"
        
        # 2. 计算胜率（盈利交易次数 / 总交易次数）
        if trades_data:
            # 按股票代码分组，计算每笔买卖的盈亏
            stock_trades = {}
            for trade in trades_data:
                stock_code = trade.get('stock_code', '')
                if stock_code not in stock_trades:
                    stock_trades[stock_code] = []
                stock_trades[stock_code].append(trade)
            
            profitable_trades = 0
            total_completed_trades = 0
            
            for stock_code, stock_trade_list in stock_trades.items():
                # 按时间排序
                stock_trade_list.sort(key=lambda x: x.get('date', ''))
                
                # 计算买卖对的盈亏
                i = 0
                while i < len(stock_trade_list) - 1:
                    if (stock_trade_list[i].get('action') == 'buy' and 
                        stock_trade_list[i + 1].get('action') == 'sell'):
                        
                        buy_price = stock_trade_list[i].get('price', 0)
                        sell_price = stock_trade_list[i + 1].get('price', 0)
                        
                        if sell_price > buy_price:
                            profitable_trades += 1
                        total_completed_trades += 1
                        i += 2
                    else:
                        i += 1
            
            win_rate = (profitable_trades / total_completed_trades * 100) if total_completed_trades > 0 else 0
            metrics['win_rate'] = f"{win_rate:.2f}%"
        else:
            metrics['win_rate'] = "0.00%"
        
        # 3. 计算最大回撤；没有日收益率时退化为展示用估算值。
        if daily_returns and len(daily_returns) > 1:
            # 计算累计收益
            cumulative_returns = np.cumprod(1 + np.array(daily_returns))
            
            # 计算最大回撤
            peak = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - peak) / peak
            max_drawdown = np.min(drawdown)
            metrics['max_drawdown'] = f"{abs(max_drawdown):.2%}"
        else:
            # 简化版最大回撤计算：假设在最高点买入，在最低点评估
            # 这里使用保守估计
            if total_return > 0:
                # 假设回撤为总回报的20%（保守估计）
                estimated_drawdown = min(0.2, total_return * 0.3)
                metrics['max_drawdown'] = f"{estimated_drawdown:.2%}"
            else:
                metrics['max_drawdown'] = f"{abs(total_return):.2%}"
        
        # 4. 计算夏普比率，日频数据统一按 252 个交易日年化。
        if daily_returns and len(daily_returns) > 1:
            # 计算年化收益率和波动率
            mean_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            
            if std_return > 0:
                # 假设无风险利率为3%
                risk_free_rate = 0.03 / 252  # 日化无风险利率
                excess_return = mean_return - risk_free_rate
                sharpe_ratio = (excess_return / std_return) * np.sqrt(252)  # 年化夏普比率
                metrics['sharpe_ratio'] = f"{sharpe_ratio:.2f}"
            else:
                metrics['sharpe_ratio'] = "0.00"
        else:
            # 简化版夏普比率计算
            if total_return > 0:
                # 简化计算：(年化收益率 - 无风险利率) / 估计波动率
                annualized_return = (1 + total_return) ** (252/365) - 1
                risk_free_rate = 0.03
                estimated_volatility = 0.15  # 假设15%的年化波动率
                
                sharpe_ratio = (annualized_return - risk_free_rate) / estimated_volatility
                metrics['sharpe_ratio'] = f"{sharpe_ratio:.2f}"
            else:
                metrics['sharpe_ratio'] = "0.00"
        
        # 5. 其他指标
        metrics['total_trades'] = len(trades_data)
        metrics['initial_cash'] = initial_cash
        metrics['final_cash'] = final_cash
        
        # 6. 计算年化收益率
        days_elapsed = 365  # 假设一年的回测期
        if total_return != 0:
            annualized_return = (1 + total_return) ** (365/days_elapsed) - 1
            metrics['annualized_return'] = f"{annualized_return:.2%}"
        else:
            metrics['annualized_return'] = "0.00%"
            
    except Exception as e:
        print(f"❌ 计算高级指标时出错: {e}")
        # 返回默认值
        metrics = {
            'total_return_pct': f"{((final_cash - initial_cash) / initial_cash):.2%}",
            'win_rate': "0.00%",
            'max_drawdown': "0.00%", 
            'sharpe_ratio': "0.00",
            'total_trades': len(trades_data) if trades_data else 0,
            'initial_cash': initial_cash,
            'final_cash': final_cash,
            'annualized_return': "0.00%"
        }
    
    return metrics

def generate_mock_daily_returns(initial_cash: float, final_cash: float, days: int = 365) -> List[float]:
    """
    生成模拟的每日收益率数据
    基于最终收益率生成合理的日收益率序列

    固定随机种子是为了让演示、测试和前端图表每次得到相同序列；该数据
    仅用于缺少真实净值曲线时的展示，不代表实际市场路径。
    """
    try:
        total_return = (final_cash - initial_cash) / initial_cash
        
        # 计算平均日收益率
        avg_daily_return = (1 + total_return) ** (1/days) - 1
        
        # 生成带有随机波动的日收益率
        np.random.seed(42)  # 固定种子确保可重复性
        volatility = 0.02  # 日波动率约2%
        
        daily_returns = []
        for _ in range(days):
            # 在平均收益率基础上添加随机波动
            random_factor = np.random.normal(0, volatility)
            daily_return = avg_daily_return + random_factor
            daily_returns.append(daily_return)
        
        return daily_returns
        
    except Exception as e:
        print(f"❌ 生成模拟日收益率时出错: {e}")
        return [0.0] * days

if __name__ == "__main__":
    # 测试高级指标计算
    test_trades = [
        {'stock_code': '000001', 'action': 'buy', 'price': 20.0, 'shares': 1000, 'date': '20240101'},
        {'stock_code': '000001', 'action': 'sell', 'price': 22.0, 'shares': 1000, 'date': '20240201'},
        {'stock_code': '000002', 'action': 'buy', 'price': 15.0, 'shares': 1000, 'date': '20240115'},
        {'stock_code': '000002', 'action': 'sell', 'price': 14.0, 'shares': 1000, 'date': '20240215'},
    ]
    
    initial_cash = 100000
    final_cash = 120000
    
    # 生成模拟日收益率
    daily_returns = generate_mock_daily_returns(initial_cash, final_cash)
    
    # 计算高级指标
    metrics = calculate_advanced_metrics(test_trades, initial_cash, final_cash, daily_returns)
    
    print("🔍 高级回测指标测试:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
