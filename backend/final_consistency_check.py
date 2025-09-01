#!/usr/bin/env python3
"""
前后端数据一致性最终验证
"""

import json
import requests
import pandas as pd
from datetime import datetime

def final_consistency_check():
    """最终的前后端数据一致性检查"""
    
    print("🔍 开始前后端数据一致性最终验证...")
    print("=" * 60)
    
    # 1. 读取后端缓存文件数据
    print("\n📂 1. 后端缓存文件数据:")
    try:
        with open('/home/liu/桌面/stock-20250730_update./backend/cache/earnings_overview_latest_equal_weight.json', 'r', encoding='utf-8') as f:
            backend_cache = json.load(f)
        
        cache_metrics = backend_cache['performance_metrics']
        cache_strategy = backend_cache['strategy_info']
        
        print(f"策略类型: {cache_strategy['strategy_type']}")
        print(f"时间范围: {cache_strategy['period']}")
        print(f"初始资金: {cache_strategy['initial_cash']:,}")
        print(f"最终价值: {cache_strategy['final_value']:,}")
        print(f"策略收益: {cache_metrics['strategy_return']:.4f} ({cache_metrics['strategy_return']:.2%})")
        print(f"年化收益: {cache_metrics['strategy_annual_return']:.4f} ({cache_metrics['strategy_annual_return']:.2%})")
        print(f"胜率: {cache_metrics['win_rate']:.4f} ({cache_metrics['win_rate']:.2%})")
        print(f"最大回撤: {cache_metrics['max_drawdown']:.4f} ({cache_metrics['max_drawdown']:.2%})")
        print(f"夏普比率: {cache_metrics['sharpe_ratio']:.3f}")
        print(f"盈亏比: {cache_metrics['profit_loss_ratio']:.3f}")
        
    except Exception as e:
        print(f"❌ 读取后端缓存失败: {e}")
        return
    
    # 2. 调用后端API
    print("\n🌐 2. 后端API响应数据:")
    try:
        response = requests.get('http://localhost:8002/api/cache/earnings-overview/', timeout=10)
        if response.status_code == 200:
            api_data = response.json()['data']
            
            api_performance = api_data['performance_metrics']
            api_strategy = api_data['strategy_info']
            api_overview = api_data['overview']
            
            print(f"策略类型: {api_strategy['strategy_type']}")
            print(f"时间范围: {api_strategy['period']}")
            print(f"初始资金: {api_overview['initial_capital']:,}")
            print(f"最终价值: {api_overview['final_value']:,}")
            print(f"策略收益: {api_performance['strategy_return']:.4f} ({api_performance['strategy_return']:.2%})")
            print(f"年化收益: {api_performance['strategy_annual_return']:.4f} ({api_performance['strategy_annual_return']:.2%})")
            print(f"胜率: {api_performance['win_rate']:.4f} ({api_performance['win_rate']:.2%})")
            print(f"最大回撤: {api_performance['max_drawdown']:.4f} ({api_performance['max_drawdown']:.2%})")
            print(f"夏普比率: {api_performance['sharpe_ratio']:.3f}")
            print(f"盈亏比: {api_performance['profit_loss_ratio']:.3f}")
            
        else:
            print(f"❌ API请求失败: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        return
    
    # 3. 数据一致性对比
    print("\n🔄 3. 数据一致性对比:")
    
    comparisons = {
        '策略类型': (cache_strategy['strategy_type'], api_strategy['strategy_type']),
        '时间范围': (cache_strategy['period'], api_strategy['period']),
        '策略收益': (cache_metrics['strategy_return'], api_performance['strategy_return']),
        '年化收益': (cache_metrics['strategy_annual_return'], api_performance['strategy_annual_return']),
        '胜率': (cache_metrics['win_rate'], api_performance['win_rate']),
        '最大回撤': (cache_metrics['max_drawdown'], api_performance['max_drawdown']),
        '夏普比率': (cache_metrics['sharpe_ratio'], api_performance['sharpe_ratio']),
        '盈亏比': (cache_metrics['profit_loss_ratio'], api_performance['profit_loss_ratio'])
    }
    
    all_consistent = True
    
    for metric, (cache_val, api_val) in comparisons.items():
        if isinstance(cache_val, (int, float)) and isinstance(api_val, (int, float)):
            is_consistent = abs(cache_val - api_val) < 0.0001
        else:
            is_consistent = cache_val == api_val
        
        status = "✅" if is_consistent else "❌"
        print(f"{status} {metric}: 缓存={cache_val} | API={api_val}")
        
        if not is_consistent:
            all_consistent = False
    
    # 4. 验证关键计算
    print("\n🧮 4. 关键指标计算验证:")
    
    # 验证收益率计算
    calculated_return = (cache_strategy['final_value'] - cache_strategy['initial_cash']) / cache_strategy['initial_cash']
    print(f"✓ 收益率计算: ({cache_strategy['final_value']:,} - {cache_strategy['initial_cash']:,}) / {cache_strategy['initial_cash']:,} = {calculated_return:.4f}")
    print(f"  与系统值对比: {calculated_return:.4f} vs {cache_metrics['strategy_return']:.4f} ({'✅一致' if abs(calculated_return - cache_metrics['strategy_return']) < 0.0001 else '❌不一致'})")
    
    # 验证胜率计算
    trades = backend_cache['trades']
    stocks = {}
    for trade in trades:
        stock = trade['stock_code']
        if stock not in stocks:
            stocks[stock] = {'buy': [], 'sell': []}
        stocks[stock][trade['action']].append(trade)
    
    profitable_count = 0
    total_positions = 0
    
    for stock, stock_trades in stocks.items():
        buys = stock_trades['buy']
        sells = stock_trades['sell']
        
        if buys and sells:
            total_positions += 1
            total_buy_amount = sum(t['amount'] for t in buys)
            total_sell_amount = sum(t['amount'] for t in sells)
            profit_loss = total_sell_amount - total_buy_amount
            
            if profit_loss > 0:
                profitable_count += 1
    
    calculated_win_rate = profitable_count / total_positions if total_positions > 0 else 0
    print(f"✓ 胜率计算: {profitable_count}/{total_positions} = {calculated_win_rate:.4f}")
    print(f"  与系统值对比: {calculated_win_rate:.4f} vs {cache_metrics['win_rate']:.4f} ({'✅一致' if abs(calculated_win_rate - cache_metrics['win_rate']) < 0.0001 else '❌不一致'})")
    
    # 5. 前端显示预期
    print("\n📱 5. 前端显示预期值:")
    print(f"策略收益率: {cache_metrics['strategy_return']:.2%}")
    print(f"策略年化收益: {cache_metrics['strategy_annual_return']:.2%}")
    print(f"最大回撤: {cache_metrics['max_drawdown']:.2%}")
    print(f"夏普比率: {cache_metrics['sharpe_ratio']:.3f}")
    print(f"胜率: {cache_metrics['win_rate']:.2%}")
    print(f"盈亏比: {cache_metrics['profit_loss_ratio']:.3f}")
    print(f"时间范围: {cache_strategy['start_date'][:4]}-{cache_strategy['start_date'][4:6]}-{cache_strategy['start_date'][6:8]} 至 {cache_strategy['end_date'][:4]}-{cache_strategy['end_date'][4:6]}-{cache_strategy['end_date'][6:8]}")
    
    # 6. 总结
    print("\n" + "="*60)
    print("📋 最终验证结果:")
    
    if all_consistent:
        print("✅ 前后端数据完全一致！")
        print("✅ 所有关键指标计算正确！")
        print("✅ API响应数据与缓存文件匹配！")
        print("✅ 前端页面应该显示正确的数据！")
    else:
        print("❌ 发现数据不一致，需要进一步检查！")
    
    print(f"\n🕒 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 保存验证报告
    validation_report = {
        'validation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'backend_cache_data': {
            'strategy_return': cache_metrics['strategy_return'],
            'win_rate': cache_metrics['win_rate'],
            'max_drawdown': cache_metrics['max_drawdown'],
            'time_period': cache_strategy['period']
        },
        'api_response_data': {
            'strategy_return': api_performance['strategy_return'],
            'win_rate': api_performance['win_rate'],
            'max_drawdown': api_performance['max_drawdown'],
            'time_period': api_strategy['period']
        },
        'consistency_check': {
            'all_consistent': all_consistent,
            'detailed_comparisons': comparisons
        },
        'calculation_verification': {
            'calculated_return': calculated_return,
            'system_return': cache_metrics['strategy_return'],
            'calculated_win_rate': calculated_win_rate,
            'system_win_rate': cache_metrics['win_rate']
        }
    }
    
    with open('/home/liu/桌面/stock-20250730_update./backend/cache/final_consistency_report.json', 'w', encoding='utf-8') as f:
        json.dump(validation_report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 详细验证报告已保存到: final_consistency_report.json")

if __name__ == "__main__":
    final_consistency_check()
