#!/usr/bin/env python3
"""
验证前端显示的指标数据与后端计算的一致性
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def validate_frontend_backend_consistency():
    """验证前端显示数据与后端数据的一致性"""
    
    print("🔍 验证前端显示数据与后端计算的一致性")
    print("="*60)
    
    # 加载后端缓存数据
    with open('/home/liu/桌面/stock-20250730_update./backend/cache/earnings_overview_latest_equal_weight.json', 'r', encoding='utf-8') as f:
        backend_data = json.load(f)
    
    backend_metrics = backend_data['performance_metrics']
    backend_info = backend_data['strategy_info']
    
    print("📊 后端系统数据:")
    print(f"回测时间: {backend_info['period']}")
    print(f"初始资金: ¥{backend_info['initial_cash']:,.2f}")
    print(f"最终价值: ¥{backend_info['final_value']:,.2f}")
    print()
    
    # 前端截图显示的数据
    frontend_displayed = {
        "策略收益": -29.36,  # %
        "策略年化收益": -16.78,  # %
        "超额收益": -26.78,  # %
        "基准收益": 10.00,  # %
        "阿尔法": -31.780,
        "贝塔": 2.000,
        "夏普比率": -0.030,
        "胜率": 45.83,  # %
        "索提诺比率": 0.000,
        "最大回撤": 29.36,  # %
        "日均超额收益": -0.04,  # %
        "超额收益最大回撤": 13.01,  # %
        "超额收益震荡比率": -0.910,
        "日胜率": 0.471,
        "盈利次数": 1,
        "亏损次数": 8,
        "信息比率": -0.672,
        "策略波动率": 0.084,
        "基准波动率": 0.165,
        "回测基本信息": {
            "策略名称": "指标驱动回测策略",
            "回测时间": "2022-04-01 至 2023-12-31",
            "初始资金": 1000000,  # 100万
            "回测频率": "每日",
            "回测状态": "已完成",
            "执行时间": "刚刚"
        },
        "回测结果统计": {
            "总收益率": -29.36,  # %
            "回测天数": 639,
            "交易次数": 48,
            "胜率": 45.83,  # %
            "最大回撤": -29.36,  # %
            "夏普比率": -0.03
        }
    }
    
    print("🖥️ 前端显示数据:")
    for key, value in frontend_displayed["回测基本信息"].items():
        if key == "初始资金":
            print(f"{key}: ¥{value:,.2f}")
        else:
            print(f"{key}: {value}")
    print()
    
    # 数据对比分析
    print("🔍 关键差异分析:")
    print("-" * 40)
    
    # 1. 初始资金差异
    backend_initial = backend_info['initial_cash']
    frontend_initial = frontend_displayed["回测基本信息"]["初始资金"]
    
    print(f"1️⃣ 初始资金:")
    print(f"   后端数据: ¥{backend_initial:,.2f}")
    print(f"   前端显示: ¥{frontend_initial:,.2f}")
    print(f"   差异: {abs(frontend_initial - backend_initial):,.2f} (相差{(frontend_initial/backend_initial-1)*100:.0f}%)")
    
    # 2. 收益率差异
    backend_return = backend_metrics['strategy_return'] * 100
    frontend_return = frontend_displayed["策略收益"]
    
    print(f"\n2️⃣ 策略收益率:")
    print(f"   后端数据: {backend_return:.2f}%")
    print(f"   前端显示: {frontend_return:.2f}%")
    print(f"   差异: {abs(frontend_return - backend_return):.2f}百分点")
    
    # 3. 年化收益率差异
    backend_annual = backend_metrics['strategy_annual_return'] * 100
    frontend_annual = frontend_displayed["策略年化收益"]
    
    print(f"\n3️⃣ 年化收益率:")
    print(f"   后端数据: {backend_annual:.2f}%")
    print(f"   前端显示: {frontend_annual:.2f}%")
    print(f"   差异: {abs(frontend_annual - backend_annual):.2f}百分点")
    
    # 4. 胜率差异
    backend_winrate = backend_metrics['win_rate'] * 100
    frontend_winrate = frontend_displayed["胜率"]
    
    print(f"\n4️⃣ 胜率:")
    print(f"   后端数据: {backend_winrate:.2f}%")
    print(f"   前端显示: {frontend_winrate:.2f}%")
    print(f"   差异: {abs(frontend_winrate - backend_winrate):.2f}百分点")
    
    # 5. 最大回撤差异
    backend_drawdown = backend_metrics['max_drawdown'] * 100
    frontend_drawdown = frontend_displayed["最大回撤"]
    
    print(f"\n5️⃣ 最大回撤:")
    print(f"   后端数据: {backend_drawdown:.2f}%")
    print(f"   前端显示: {frontend_drawdown:.2f}%")
    print(f"   差异: {abs(frontend_drawdown - backend_drawdown):.2f}百分点")
    
    # 6. 时间周期差异
    backend_period = backend_info['period']
    frontend_period = frontend_displayed["回测基本信息"]["回测时间"]
    
    print(f"\n6️⃣ 回测时间周期:")
    print(f"   后端数据: {backend_period}")
    print(f"   前端显示: {frontend_period}")
    
    # 分析问题根源
    print("\n" + "="*60)
    print("🚨 问题诊断:")
    
    problems = []
    
    if frontend_initial != backend_initial:
        problems.append(f"初始资金不一致: 前端显示{frontend_initial:,.0f}，后端实际{backend_initial:,.0f}")
    
    if abs(frontend_return - backend_return) > 1:
        problems.append(f"收益率差异过大: 前端{frontend_return:.2f}% vs 后端{backend_return:.2f}%")
    
    if abs(frontend_winrate - backend_winrate) > 5:
        problems.append(f"胜率差异过大: 前端{frontend_winrate:.2f}% vs 后端{backend_winrate:.2f}%")
    
    if frontend_period != backend_period:
        problems.append(f"时间周期不一致: 前端显示'{frontend_period}' vs 后端'{backend_period}'")
    
    if problems:
        print("发现以下问题:")
        for i, problem in enumerate(problems, 1):
            print(f"{i}. {problem}")
        
        print("\n🔧 可能的原因:")
        print("1. 前端缓存数据未更新")
        print("2. 前端使用了错误的API接口")
        print("3. 数据传递过程中格式转换错误") 
        print("4. 前端显示逻辑有bug")
        print("5. 后端计算逻辑被修改但前端未同步")
    else:
        print("✅ 所有关键指标数据一致!")
    
    # 生成修复建议
    print("\n📋 修复建议:")
    print("1. 检查前端是否正确读取了最新的缓存数据")
    print("2. 确认前端API调用的URL和参数是否正确")
    print("3. 验证数据格式转换（百分比、小数点等）")
    print("4. 检查初始资金传递逻辑")
    print("5. 确保前后端使用相同的计算公式")
    
    # 创建对比报告
    comparison_report = {
        "validation_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "backend_data": {
            "initial_cash": backend_initial,
            "strategy_return": backend_return,
            "annual_return": backend_annual,
            "win_rate": backend_winrate,
            "max_drawdown": backend_drawdown,
            "period": backend_period
        },
        "frontend_displayed": {
            "initial_cash": frontend_initial,
            "strategy_return": frontend_return,
            "annual_return": frontend_annual,
            "win_rate": frontend_winrate,
            "max_drawdown": frontend_drawdown,
            "period": frontend_period
        },
        "differences": {
            "initial_cash_diff": abs(frontend_initial - backend_initial),
            "return_diff": abs(frontend_return - backend_return),
            "annual_return_diff": abs(frontend_annual - backend_annual),
            "winrate_diff": abs(frontend_winrate - backend_winrate),
            "drawdown_diff": abs(frontend_drawdown - backend_drawdown)
        },
        "problems_found": problems,
        "consistency_status": "inconsistent" if problems else "consistent"
    }
    
    # 保存对比报告
    with open('/home/liu/桌面/stock-20250730_update./backend/cache/frontend_backend_comparison.json', 'w', encoding='utf-8') as f:
        json.dump(comparison_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细对比报告已保存到: frontend_backend_comparison.json")

if __name__ == "__main__":
    validate_frontend_backend_consistency()
