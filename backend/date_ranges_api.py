#!/usr/bin/env python3
"""
获取可用日期范围API
从cache目录读取JSON文件，提取可用的日期范围
"""

import os
import json
import glob
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["GET"])
def get_available_date_ranges(request):
    """扫描回测缓存文件名并返回可用日期范围及最新推荐项。

    日期来自 ``earnings_overview_YYYYMMDD_YYYYMMDD*.json`` 文件名，文件内容
    只用于补充策略名和交易数；单个文件解析失败不会阻断其他文件返回。
    """
    try:
        print("📅 开始获取可用日期范围...")
        
        # 获取cache目录路径
        cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        
        if not os.path.exists(cache_dir):
            print(f"❌ Cache目录不存在: {cache_dir}")
            return JsonResponse({
                'status': 'error',
                'message': 'Cache目录不存在',
                'data': []
            })
        
        # 查找所有JSON文件
        json_files = glob.glob(os.path.join(cache_dir, 'earnings_overview_*.json'))
        
        if not json_files:
            print("❌ 未找到任何JSON文件")
            return JsonResponse({
                'status': 'error',
                'message': '未找到任何回测数据文件',
                'data': []
            })
        
        date_ranges = []
        
        for json_file in json_files:
            try:
                filename = os.path.basename(json_file)
                print(f"📄 分析文件: {filename}")
                
                # 从文件名中提取日期范围
                if 'earnings_overview_' in filename:
                    # 移除前缀和后缀
                    date_part = filename.replace('earnings_overview_', '').replace('.json', '')
                    
                    # 尝试解析日期范围
                    if '_' in date_part and len(date_part) >= 16:  # 至少包含两个8位日期
                        parts = date_part.split('_')
                        if len(parts) >= 2:
                            start_date = parts[0]
                            end_date = parts[1]
                            
                            # 验证日期格式
                            if len(start_date) == 8 and len(end_date) == 8:
                                # 转换为可读格式
                                formatted_start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"
                                formatted_end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"
                                
                                # 读取文件获取更多信息
                                with open(json_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                
                                # 获取文件修改时间
                                file_time = os.path.getmtime(json_file)
                                formatted_time = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S')
                                
                                date_range_info = {
                                    'filename': filename,
                                    'start_date': formatted_start,
                                    'end_date': formatted_end,
                                    'start_date_raw': start_date,
                                    'end_date_raw': end_date,
                                    'file_modified': formatted_time,
                                    'strategy_name': data.get('strategy_info', {}).get('name', '未知策略'),
                                    'trades_count': len(data.get('trades', [])),
                                    'file_size': os.path.getsize(json_file)
                                }
                                
                                date_ranges.append(date_range_info)
                                print(f"✅ 成功解析: {formatted_start} 至 {formatted_end}")
                
            except Exception as e:
                print(f"⚠️ 解析文件 {filename} 失败: {str(e)}")
                continue
        
        # 按开始日期排序
        date_ranges.sort(key=lambda x: x['start_date'], reverse=True)
        
        # 获取最新的日期范围作为推荐
        recommended = date_ranges[0] if date_ranges else None
        
        result = {
            'status': 'success',
            'message': f'找到 {len(date_ranges)} 个可用日期范围',
            'data': {
                'available_ranges': date_ranges,
                'recommended': recommended,
                'total_count': len(date_ranges)
            }
        }
        
        print(f"✅ 成功返回 {len(date_ranges)} 个日期范围")
        return JsonResponse(result)
        
    except Exception as e:
        print(f"❌ 获取日期范围失败: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'获取日期范围失败: {str(e)}',
            'data': []
        })

# 这个函数需要添加到urls.py中
# path('api/date-ranges/', get_available_date_ranges, name='get_available_date_ranges'),
