#!/usr/bin/env python3
"""
验证初始资金传递问题
"""

import json

def check_initial_cash_issue():
    """检查初始资金传递问题"""
    
    print("🔍 检查初始资金传递问题...")
    
    # 检查API返回的数据
    with open('/home/liu/桌面/stock-20250730_update./backend/cache/earnings_overview_latest_indicator_driven.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    initial_cash = data['strategy_info']['initial_cash']
    final_value = data['strategy_info']['final_value']
    strategy_return = data['performance_metrics']['strategy_return']
    
    print(f"📊 后端数据:")
    print(f"初始资金: {initial_cash:,}")
    print(f"最终价值: {final_value:,.2f}")
    print(f"策略收益: {strategy_return:.2%}")
    
    print(f"\n💡 模拟如果初始资金是100万的情况:")
    
    # 模拟100万初始资金的情况
    simulated_initial = 1000000
    simulated_final = simulated_initial * (1 + strategy_return)
    
    print(f"模拟初始资金: {simulated_initial:,}")
    print(f"模拟最终价值: {simulated_final:,.2f}")
    print(f"收益率保持: {strategy_return:.2%}")
    print(f"绝对收益: {simulated_final - simulated_initial:,.2f}")
    
    print(f"\n📝 分析:")
    print("1. 前端显示100万可能是用户输入，但后端实际计算用的是10万")
    print("2. 收益率计算是正确的(5.75%)，问题在于基数")
    print("3. 需要检查前端如何传递initial_cash参数到后端")
    
    print(f"\n🔧 解决方案:")
    print("1. 检查前端表单的initial_cash参数传递")
    print("2. 确认后端backtest_integration.py是否正确接收参数")
    print("3. 验证MockRequest的参数处理逻辑")

if __name__ == "__main__":
    check_initial_cash_issue()
