#!/usr/bin/env python3
"""
验证前后端时间范围数据一致性
"""

import json
import requests
from datetime import datetime

def validate_time_range_consistency():
    """验证前后端时间范围一致性"""
    
    print("🕒 验证前后端时间范围数据一致性...")
    
    # 1. 检查后端缓存数据
    print("\n📁 后端缓存数据:")
    try:
        with open('/home/liu/桌面/stock-20250730_update./backend/cache/earnings_overview_latest_equal_weight.json', 'r', encoding='utf-8') as f:
            backend_data = json.load(f)
        
        time_period = backend_data.get('time_period', {})
        strategy_info = backend_data.get('strategy_info', {})
        
        print(f"time_period.start_date: {time_period.get('start_date')}")
        print(f"time_period.end_date: {time_period.get('end_date')}")
        print(f"strategy_info.start_date: {strategy_info.get('start_date')}")
        print(f"strategy_info.end_date: {strategy_info.get('end_date')}")
        print(f"strategy_info.period: {strategy_info.get('period')}")
        
        # 获取最大回撤期间
        max_drawdown_period = backend_data['performance_metrics'].get('max_drawdown_period')
        print(f"max_drawdown_period: {max_drawdown_period}")
        
        backend_start = time_period.get('start_date') or strategy_info.get('start_date')
        backend_end = time_period.get('end_date') or strategy_info.get('end_date')
        
    except FileNotFoundError:
        print("❌ 后端缓存文件不存在")
        return
    except Exception as e:
        print(f"❌ 读取后端数据失败: {e}")
        return
    
    # 2. 检查后端API响应
    print("\n🌐 后端API响应:")
    try:
        response = requests.get('http://localhost:8002/api/cache/earnings_overview/', timeout=5)
        if response.status_code == 200:
            api_data = response.json()
            
            if api_data.get('success'):
                data = api_data.get('data', {})
                api_time_period = data.get('time_period', {})
                api_strategy_info = data.get('strategy_info', {})
                
                print(f"API time_period.start_date: {api_time_period.get('start_date')}")
                print(f"API time_period.end_date: {api_time_period.get('end_date')}")
                print(f"API strategy_info.period: {api_strategy_info.get('period')}")
                
                api_start = api_time_period.get('start_date') or api_strategy_info.get('start_date')
                api_end = api_time_period.get('end_date') or api_strategy_info.get('end_date')
            else:
                print(f"❌ API返回错误: {api_data.get('message')}")
                return
        else:
            print(f"❌ API请求失败: {response.status_code}")
            return
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API请求异常: {e}")
        return
    
    # 3. 分析时间格式和一致性
    print("\n📊 时间范围一致性分析:")
    
    def format_date_for_display(date_str):
        """将日期格式化为显示格式"""
        if not date_str:
            return "未知"
        if len(date_str) == 8:  # YYYYMMDD格式
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return date_str
    
    backend_start_formatted = format_date_for_display(backend_start)
    backend_end_formatted = format_date_for_display(backend_end)
    api_start_formatted = format_date_for_display(api_start)
    api_end_formatted = format_date_for_display(api_end)
    
    print(f"后端缓存时间范围: {backend_start_formatted} 至 {backend_end_formatted}")
    print(f"API返回时间范围: {api_start_formatted} 至 {api_end_formatted}")
    
    # 检查一致性
    backend_consistent = (backend_start == api_start) and (backend_end == api_end)
    print(f"后端数据一致性: {'✅ 一致' if backend_consistent else '❌ 不一致'}")
    
    # 4. 检查前端默认值（从代码中提取）
    print("\n🖥️ 前端默认值分析:")
    
    # 从MenuLayoutRefactored.vue中提取
    menu_default_start = "2023-01-01"
    menu_default_end = "2023-12-31"
    
    # 从EarningsOverview.vue中提取
    earnings_default_start = "2024-12-02"  # 从代码中看到的硬编码值
    earnings_default_end = "2025-05-30"    # 从代码中看到的硬编码值
    
    print(f"MenuLayout默认值: {menu_default_start} 至 {menu_default_end}")
    print(f"EarningsOverview默认值: {earnings_default_start} 至 {earnings_default_end}")
    
    # 5. 问题诊断
    print("\n🔍 问题诊断:")
    issues = []
    
    if backend_start_formatted != menu_default_start:
        issues.append(f"MenuLayout默认开始日期({menu_default_start})与后端({backend_start_formatted})不一致")
    
    if backend_end_formatted != menu_default_end:
        issues.append(f"MenuLayout默认结束日期({menu_default_end})与后端({backend_end_formatted})不一致")
    
    if earnings_default_start != backend_start_formatted:
        issues.append(f"EarningsOverview默认开始日期({earnings_default_start})与后端({backend_start_formatted})严重不一致")
    
    if earnings_default_end != backend_end_formatted:
        issues.append(f"EarningsOverview默认结束日期({earnings_default_end})与后端({backend_end_formatted})严重不一致")
    
    if issues:
        print("发现以下问题:")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
    else:
        print("✅ 未发现时间范围不一致问题")
    
    # 6. 生成修复建议
    print("\n🔧 修复建议:")
    print("1. 修复EarningsOverview.vue中的硬编码日期")
    print("2. 确保前端从后端API获取正确的时间范围")
    print("3. 统一时间格式处理逻辑")
    
    # 7. 生成修复报告
    fix_report = {
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'backend_data': {
            'start_date': backend_start,
            'end_date': backend_end,
            'formatted_range': f"{backend_start_formatted} 至 {backend_end_formatted}"
        },
        'frontend_defaults': {
            'menu_layout': {
                'start_date': menu_default_start,
                'end_date': menu_default_end
            },
            'earnings_overview': {
                'start_date': earnings_default_start,
                'end_date': earnings_default_end
            }
        },
        'consistency_check': {
            'backend_api_consistent': backend_consistent,
            'issues_found': issues
        },
        'recommendations': [
            '修复EarningsOverview.vue中的硬编码日期',
            '确保前端组件正确读取API返回的时间范围',
            '添加时间范围验证机制'
        ]
    }
    
    with open('/home/liu/桌面/stock-20250730_update./backend/cache/time_range_validation_report.json', 'w', encoding='utf-8') as f:
        json.dump(fix_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细验证报告已保存到: time_range_validation_report.json")
    
    return fix_report

if __name__ == "__main__":
    validate_time_range_consistency()
