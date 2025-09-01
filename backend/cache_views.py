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
def get_earnings_overview_cache(request):
    """
    从缓存读取收益概览数据
    用于 http://localhost:3000/earnings-overview 页面
    """
    try:
        print("💰 收到收益概览缓存请求")
        
        # 查找缓存文件
        cache_patterns = [
            'earnings_overview_latest_*.json',
            'earnings_overview_latest.json',
            'earnings_overview_*.json'
        ]
        
        cache_file = find_latest_cache_file(cache_patterns)
        
        if not cache_file:
            return JsonResponse({
                'status': 'error',
                'message': '未找到收益概览缓存数据',
                'data': {}
            })
        
        print(f"📂 使用缓存文件: {os.path.basename(cache_file)}")
        
        # 读取缓存数据
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # 提取收益相关数据
        performance = cache_data.get('performance_metrics', {})
        account_summary = cache_data.get('account_summary', {})
        strategy_info = cache_data.get('strategy_info', {})
        
        # 计算关键收益指标
        initial_capital = strategy_info.get('initial_cash', 100000)
        final_value = strategy_info.get('final_value', initial_capital)
        
        # 如果final_value不存在，尝试从performance_metrics获取
        if 'final_value' not in strategy_info and 'strategy_return' in performance:
            strategy_return = performance.get('strategy_return', 0)
            final_value = initial_capital * (1 + strategy_return)
        
        total_return = ((final_value - initial_capital) / initial_capital * 100) if initial_capital > 0 else 0
        
        response_data = {
            'status': 'success',
            'message': '从缓存成功读取收益概览',
            'data': {
                'overview': {
                    'initial_capital': initial_capital,
                    'final_value': final_value,
                    'total_return': round(total_return, 2),
                    'total_profit': final_value - initial_capital,
                    'trading_days': len(cache_data.get('trades', [])),
                    'win_rate': performance.get('win_rate', 0),
                    'sharpe_ratio': performance.get('sharpe_ratio', 0),
                    'max_drawdown': performance.get('max_drawdown', 0)
                },
                'performance_metrics': performance,
                'account_summary': account_summary,
                'strategy_info': strategy_info,
                'time_period': cache_data.get('time_period', {}),
                'cache_info': {
                    'file_name': os.path.basename(cache_file),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(cache_file)).strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        }
        
        print(f"✅ 成功返回收益概览缓存，总收益率: {total_return:.2f}%")
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"❌ 读取收益概览缓存失败: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'读取收益概览缓存失败: {str(e)}',
            'data': {}
        })

@csrf_exempt
@require_http_methods(["GET"])
def get_transaction_details_cache(request):
    """
    从缓存读取交易详情数据
    用于 http://localhost:3000/transaction-details 页面
    """
    try:
        print("📋 收到交易详情缓存请求")
        
        # 查找缓存文件
        cache_patterns = [
            'earnings_overview_latest_*.json',
            'earnings_overview_latest.json',
            'earnings_overview_*.json'
        ]
        
        cache_file = find_latest_cache_file(cache_patterns)
        
        if not cache_file:
            return JsonResponse({
                'status': 'error',
                'message': '未找到交易详情缓存数据',
                'data': {}
            })
        
        print(f"📂 使用缓存文件: {os.path.basename(cache_file)}")
        
        # 读取缓存数据
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # 提取交易相关数据
        trades = cache_data.get('trades', [])
        positions = cache_data.get('positions', [])
        strategy_info = cache_data.get('strategy_info', {})
        
        # 统计交易信息
        buy_trades = [t for t in trades if t.get('action', '').lower() in ['buy', '买入']]
        sell_trades = [t for t in trades if t.get('action', '').lower() in ['sell', '卖出']]
        
        total_trades = len(trades)
        profitable_trades = len([t for t in trades if t.get('profit', 0) > 0])
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        response_data = {
            'status': 'success',
            'message': '从缓存成功读取交易详情',
            'data': {
                'summary': {
                    'total_trades': total_trades,
                    'buy_trades': len(buy_trades),
                    'sell_trades': len(sell_trades),
                    'profitable_trades': profitable_trades,
                    'win_rate': round(win_rate, 2),
                    'total_profit': sum(t.get('profit', 0) for t in trades),
                    'avg_profit_per_trade': sum(t.get('profit', 0) for t in trades) / total_trades if total_trades > 0 else 0
                },
                'trades': trades,
                'positions': positions,
                'strategy_info': strategy_info,
                'time_period': cache_data.get('time_period', {}),
                'cache_info': {
                    'file_name': os.path.basename(cache_file),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(cache_file)).strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        }
        
        print(f"✅ 成功返回交易详情缓存，交易记录: {total_trades} 条，胜率: {win_rate:.2f}%")
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"❌ 读取交易详情缓存失败: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'读取交易详情缓存失败: {str(e)}',
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
