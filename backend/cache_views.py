#!/usr/bin/env python3
"""
缓存视图 - 从缓存文件读取数据的API接口
用于 backtest-details, earnings-overview, transaction-details 页面
"""

import os
import json
import glob
import time
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

def get_cache_dir():
    """获取缓存目录路径"""
    return os.path.join(os.path.dirname(__file__), 'cache')

def find_latest_cache_file(pattern_list):
    """根据优先级查找最新的缓存文件"""
    cache_dir = get_cache_dir()
    
    for pattern in pattern_list:
        files = glob.glob(os.path.join(cache_dir, pattern))
        if files:
            # 按修改时间排序，选择最新的
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            return files[0]
    
    return None

@csrf_exempt
@require_http_methods(["GET"])
def get_backtest_details_cache(request):
    """
    从缓存读取回测详情数据
    用于 http://localhost:3000/backtest-details 页面
    """
    try:
        print("📊 收到回测详情缓存请求")
        
        # 查找缓存文件，按优先级排序
        cache_patterns = [
            'earnings_overview_latest_*.json',  # 最新的策略缓存（优先）
            'earnings_overview_latest.json',    # 通用最新缓存
            'earnings_overview_*.json'          # 所有其他缓存文件
        ]
        
        cache_file = find_latest_cache_file(cache_patterns)
        
        if not cache_file:
            return JsonResponse({
                'status': 'error',
                'message': '未找到回测缓存数据',
                'data': {}
            })
        
        print(f"📂 使用缓存文件: {os.path.basename(cache_file)}")
        
        # 读取缓存数据
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # 提取关键信息
        strategy_info = cache_data.get('strategy_info', {})
        performance_metrics = cache_data.get('performance_metrics', {})
        trades = cache_data.get('trades', [])
        
        # 格式化数据适配前端
        response_data = {
            'status': 'success',
            'message': '从缓存成功读取回测详情',
            'data': {
                'strategy_info': {
                    'name': strategy_info.get('name', '智能选股策略'),
                    'period': strategy_info.get('period', '未知期间'),
                    'initial_capital': strategy_info.get('initial_capital', strategy_info.get('initial_cash', 1000000)),
                    'runtime': strategy_info.get('runtime', '未知'),
                    'status': '已完成',
                    'data_source': '缓存文件'
                },
                'performance_metrics': performance_metrics,
                'trades': trades,
                'positions': cache_data.get('positions', []),
                'account_summary': cache_data.get('account_summary', {}),
                'time_period': cache_data.get('time_period', {}),
                'cache_info': {
                    'file_name': os.path.basename(cache_file),
                    'file_size': os.path.getsize(cache_file),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(cache_file)).strftime('%Y-%m-%d %H:%M:%S'),
                    'cache_version': cache_data.get('cache_version', '1.0')
                }
            }
        }
        
        print(f"✅ 成功返回回测详情缓存，交易记录: {len(trades)} 条")
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"❌ 读取回测详情缓存失败: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'读取回测详情缓存失败: {str(e)}',
            'data': {}
        })

@csrf_exempt
@require_http_methods(["GET"])
def get_cache_status(request):
    """
    获取缓存状态信息
    """
    try:
        cache_dir = get_cache_dir()
        
        if not os.path.exists(cache_dir):
            return JsonResponse({
                'status': 'error',
                'message': '缓存目录不存在',
                'cache_dir': cache_dir
            })
        
        # 查找所有缓存文件
        cache_files = glob.glob(os.path.join(cache_dir, '*.json'))
        
        file_info = []
        for file_path in cache_files:
            file_info.append({
                'name': os.path.basename(file_path),
                'size': os.path.getsize(file_path),
                'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # 按修改时间排序
        file_info.sort(key=lambda x: x['last_modified'], reverse=True)
        
        return JsonResponse({
            'status': 'success',
            'cache_dir': cache_dir,
            'total_files': len(file_info),
            'files': file_info
        })
        
    except Exception as e:
        print(f"❌ 获取缓存状态失败: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'获取缓存状态失败: {str(e)}'
        })
