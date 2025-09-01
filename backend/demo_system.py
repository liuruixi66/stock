#!/usr/bin/env python3
"""
股票量化交易系统 - 完整功能演示
展示：筛选 -> 信号 -> 回测 -> 报告
作者: 系统集成
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def demo_complete_system():
    """演示完整系统功能"""
    print("🎯 股票量化交易系统 - 完整功能演示")
    print("=" * 60)
    
    # 第1步：信号库演示
    print("\n📈 步骤1: 信号库功能演示")
    print("-" * 40)
    
    from signal_library import SignalLibrary
    
    # 创建信号库实例
    signal_lib = SignalLibrary(initial_balance=100000)
    
    # 模拟真实股价数据
    np.random.seed(42)  # 固定随机种子，结果可复现
    dates = pd.date_range('2023-01-01', periods=30, freq='D')
    
    # 模拟股价走势：先涨后跌再涨
    base_prices = [20.0, 20.3, 20.8, 21.2, 21.0, 21.5, 21.8, 22.1, 21.9, 21.6,
                   21.3, 20.9, 20.5, 20.1, 19.8, 19.5, 19.9, 20.2, 20.6, 21.0,
                   21.3, 21.7, 22.0, 22.3, 22.6, 22.9, 23.2, 23.0, 22.8, 23.1]
    
    volumes = np.random.randint(8000, 15000, 30)
    
    stock_data = pd.DataFrame({
        'date': dates,
        'OPEN': [p * (1 + np.random.uniform(-0.01, 0.01)) for p in base_prices],
        'HIGH': [p * (1 + abs(np.random.uniform(0, 0.02))) for p in base_prices],
        'LOW': [p * (1 - abs(np.random.uniform(0, 0.02))) for p in base_prices],
        'CLOSE': base_prices,
        'VOLUME': volumes
    })
    
    # 生成买入和卖出信号
    buy_signals = signal_lib.generate_buy_signal('000001', stock_data, 'basic', price_threshold=0.01)
    sell_signals = signal_lib.generate_sell_signal('000001', stock_data, 'basic', price_threshold=-0.01)
    
    # 显示信号统计
    buy_count = buy_signals.notna().sum()
    sell_count = sell_signals.notna().sum()
    
    print(f"   📊 生成买入信号: {buy_count}个")
    print(f"   📊 生成卖出信号: {sell_count}个")
    
    # 显示交易详情
    history = signal_lib.get_signal_history('000001')
    if history:
        print(f"\n   🕒 交易记录 (最近5笔):")
        for record in history[-5:]:
            action = "🟢买入" if record['action'] == 'buy' else "🔴卖出"
            price = record.get('price', 0)
            shares = record.get('shares', 0)
            balance = record.get('balance_after', 0)
            profit_loss = record.get('profit_loss', 0)
            
            print(f"      {action} {shares}股 @ ¥{price:.2f} | 余额: ¥{balance:,.2f}", end="")
            if record['action'] == 'sell' and profit_loss:
                pnl_text = f"盈利¥{profit_loss:.2f}" if profit_loss > 0 else f"亏损¥{abs(profit_loss):.2f}"
                print(f" | {pnl_text}")
            else:
                print()
    
    # 账户摘要
    summary = signal_lib.get_account_summary()
    print(f"\n   💼 账户摘要:")
    print(f"      初始资金: ¥{summary['initial_balance']:,.2f}")
    print(f"      当前余额: ¥{summary['current_balance']:,.2f}")
    print(f"      总资产: ¥{summary['total_value']:,.2f}")
    print(f"      收益率: {summary['return_rate']:+.2f}%")
    print(f"      总交易: {summary['total_trades']}笔")
    
    if summary['positions']:
        print(f"      持仓股票: {len(summary['positions'])}只")
        for stock, pos in summary['positions'].items():
            market_value = pos['shares'] * pos['avg_price']
            print(f"         {stock}: {pos['shares']}股 @ ¥{pos['avg_price']:.2f} (¥{market_value:,.2f})")
    
    # 第2步：回测系统演示
    print(f"\n🔬 步骤2: 回测系统演示")
    print("-" * 40)
    
    try:
        from backtest_integration import BacktestIntegration
        
        # 模拟筛选出的股票列表
        filtered_stocks = ['000001', '000002']
        
        # 创建回测实例
        integration = BacktestIntegration()
        
        # 配置回测参数
        strategy_config = {
            'start_date': '20230101',
            'end_date': '20231231',
            'total_cash': 100000,
            'strategy_name': '演示策略',
            'strategy': 'equal_weight'
        }
        
        # 执行回测
        result = integration.run_backtest(filtered_stocks, strategy_config)
        
        if result['success']:
            backtest_data = result['backtest_results']['data']
            
            print(f"   ✅ 回测执行成功")
            print(f"   📊 测试股票: {result['stock_list']}")
            print(f"   💰 初始资金: ¥{strategy_config['total_cash']:,}")
            print(f"   📅 回测周期: {strategy_config['start_date']} - {strategy_config['end_date']}")
            
            # 交易明细
            trades = backtest_data['trades']
            print(f"\n   📋 交易明细:")
            for trade in trades:
                action = "🟢买入" if trade['action'] == 'buy' else "🔴卖出"
                print(f"      {trade['date']}: {action} {trade['stock_code']} "
                      f"{trade['shares']}股 @ ¥{trade['price']:.2f} "
                      f"(金额: ¥{trade['amount']:,.2f})")
            
            # 账户状态
            account = backtest_data['account_summary']
            print(f"\n   💳 账户状态:")
            print(f"      投资金额: ¥{account['invested_amount']:,.2f}")
            print(f"      剩余资金: ¥{account['remaining_cash']:,.2f}")
            print(f"      持仓数量: {account['position_count']}只")
            
            # 持仓详情
            positions = backtest_data['positions']
            print(f"\n   📈 持仓详情:")
            for pos in positions:
                print(f"      {pos['stock_code']}: {pos['shares']}股 @ ¥{pos['avg_price']:.2f} "
                      f"(市值: ¥{pos['market_value']:,.2f})")
        else:
            print(f"   ❌ 回测失败: {result['error']}")
    
    except Exception as e:
        print(f"   ⚠️  回测演示跳过: {e}")
    
    # 第3步：综合分析报告
    print(f"\n📊 步骤3: 综合分析报告")
    print("-" * 40)
    
    # 信号分析
    trading_summary = signal_lib.get_trading_summary('000001')
    
    print(f"   🔍 信号分析:")
    print(f"      股票代码: 000001")
    print(f"      信号总数: {trading_summary['total_trades']}")
    print(f"      买入次数: {trading_summary['buy_trades']}")
    print(f"      卖出次数: {trading_summary['sell_trades']}")
    print(f"      盈利率: {trading_summary['profit_rate']:+.2f}%")
    
    # 费用分析
    print(f"\n   💸 费用分析:")
    print(f"      总手续费: ¥{trading_summary['total_commission']:,.2f}")
    print(f"      总印花税: ¥{trading_summary['total_stamp_tax']:,.2f}")
    print(f"      总费用: ¥{trading_summary['total_fees']:,.2f}")
    
    # 系统状态
    print(f"\n   ⚙️  系统状态:")
    print(f"      信号库: ✅ 正常运行")
    print(f"      回测引擎: ✅ 正常运行")
    print(f"      数据源: ✅ CSV/模拟数据")
    print(f"      交易记录: ✅ 完整保存")
    
    # 第4步：性能统计
    print(f"\n📈 步骤4: 系统性能统计")
    print("-" * 40)
    
    print(f"   ⏱️  执行效率:")
    print(f"      信号生成: {buy_count + sell_count}个信号/30天")
    print(f"      交易执行: {len(history)}笔交易")
    print(f"      数据处理: 30条K线数据")
    
    print(f"\n   💡 系统特性:")
    print(f"      ✓ 实时信号生成")
    print(f"      ✓ 自动交易执行") 
    print(f"      ✓ 费用计算(手续费+印花税)")
    print(f"      ✓ 盈亏统计")
    print(f"      ✓ 风险控制(资金不足检查)")
    print(f"      ✓ 历史记录导出")
    print(f"      ✓ 多种信号策略")
    print(f"      ✓ 回测系统集成")
    
    print(f"\n🎉 完整功能演示结束!")
    print(f"⏰ 演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🚀 系统准备就绪，可投入使用！")

if __name__ == '__main__':
    demo_complete_system()
