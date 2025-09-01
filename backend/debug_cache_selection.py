#!/usr/bin/env python3
"""
调试缓存文件选择逻辑
"""

import os
import glob
from datetime import datetime

def debug_cache_selection():
    """调试缓存文件选择"""
    
    cache_dir = '/home/liu/桌面/stock-20250730_update./backend/cache'
    
    print("🔍 调试缓存文件选择逻辑")
    print("=" * 50)
    
    # 模拟 find_latest_cache_file 的逻辑
    cache_patterns = [
        'earnings_overview_latest_*.json',
        'earnings_overview_latest.json',
        'earnings_overview_*.json'
    ]
    
    for i, pattern in enumerate(cache_patterns):
        print(f"\n{i+1}. 搜索模式: {pattern}")
        files = glob.glob(os.path.join(cache_dir, pattern))
        if files:
            print(f"   找到 {len(files)} 个文件:")
            for file in files:
                mtime = os.path.getmtime(file)
                mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                print(f"   - {os.path.basename(file)} (修改时间: {mtime_str})")
            
            # 按修改时间排序
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            selected = files[0]
            print(f"   ✅ 选择: {os.path.basename(selected)}")
            
            # 验证内容
            import json
            with open(selected, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            strategy_info = data.get('strategy_info', {})
            performance = data.get('performance_metrics', {})
            
            print(f"   📊 策略类型: {strategy_info.get('strategy_type', 'N/A')}")
            print(f"   📊 时间范围: {strategy_info.get('period', 'N/A')}")
            print(f"   📊 策略收益: {performance.get('strategy_return', 'N/A')}")
            print(f"   📊 胜率: {performance.get('win_rate', 'N/A')}")
            
            return selected  # 返回第一个找到的文件
        else:
            print(f"   ❌ 没有找到匹配的文件")
    
    return None

if __name__ == "__main__":
    selected_file = debug_cache_selection()
    if selected_file:
        print(f"\n🎯 最终选择的文件: {os.path.basename(selected_file)}")
    else:
        print(f"\n❌ 没有找到任何缓存文件")
