"""HTTP entrypoints for legacy screening; not registered as new routes."""

import json
from datetime import datetime

import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from stockmarket.models import StockHistoryData
from strategies import compare
from research.screening import (
    MarketAnalyzer, analyze_macd_divergence, analyze_kdj_divergence,
    analyze_trend_signals, get_market_analysis_summary,
    filter_stocks_from_database, compress_stock_results, calculate_indicator,
)

@csrf_exempt
def filter_stocks_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            indicator_names = data.get('indicators', [])
            conditions_dict = data.get('conditions', {})
            
            # 新增：获取启用的指标列表和周期参数
            enabled_indicators = data.get('enabled_indicators', indicator_names)  # 启用的指标
            period = data.get('period', '日')  # 周期：日/周/月/年
            custom_capital = data.get('custom_capital', 100000)  # 自定义资金量
            
            # 🆕 新增：数据频率参数
            data_frequency = data.get('data_frequency', 'daily')  # 数据频率：daily/minute/tick
            minute_interval = data.get('minute_interval', '5')    # 分钟周期：1/5/15/30/60
            initial_capital = data.get('initial_capital', custom_capital)  # 初始资金（优先级更高）
            
            # 🆕 新增：结果压缩参数
            compress_results = data.get('compress_results', True)  # 是否压缩结果
            compress_mode = data.get('compress_mode', 'latest')    # 压缩模式：latest/best/summary
            
            # 🆕 获取指标自定义参数
            macd_params = data.get('macd_params', {})  # MACD参数
            kdj_params = data.get('kdj_params', {})    # KDJ参数  
            ma_params = data.get('ma_params', {})      # MA参数
            rsi_params = data.get('rsi_params', {})    # RSI参数
            boll_params = data.get('boll_params', {})  # BOLL参数
            cci_params = data.get('cci_params', {})    # CCI参数
            wr_params = data.get('wr_params', {})      # Williams %R参数
            
            # 🔧 市场筛选参数 - 重要修复：添加缺失的市场筛选
            market_filter = data.get('market', 'ALL')  # 市场筛选：shanghai/shenzhen/ALL
            enable_divergence = data.get('enable_divergence', True)  # 是否启用背离分析
            
            # 🆕 新增：股票结果压缩参数
            compress_by_stock = data.get('compress_by_stock', False)  # 是否按股票压缩结果
            
            # 📊 智能指标验证：确保只处理有效的启用指标
            SUPPORTED_INDICATORS = ['ma', 'macd', 'kdj', 'rsi', 'boll', 'cci', 'wr']
            validated_indicators = [ind for ind in enabled_indicators if ind in SUPPORTED_INDICATORS]
            skipped_indicators = [ind for ind in enabled_indicators if ind not in SUPPORTED_INDICATORS]
            
            if skipped_indicators:
                print(f"⚠️ 跳过不支持的指标: {skipped_indicators}")
            
            print(f"✅ 验证通过的启用指标: {validated_indicators}")
            print(f"📊 数据周期: {period}")
            print(f"💰 自定义资金量: {custom_capital}")
            print(f"💰 初始资金: {initial_capital}")
            print(f"⏱️ 数据频率: {data_frequency}")
            print(f"📈 分钟周期: {minute_interval}")
            print(f"🏪 市场筛选: {market_filter}")
            print(f"🔍 启用背离分析: {enable_divergence}")
            print(f"🔄 结果压缩: {compress_results} (模式: {compress_mode})")
            if macd_params:
                print(f"MACD自定义参数: {macd_params}")
            if kdj_params:
                print(f"KDJ自定义参数: {kdj_params}")
            if ma_params:
                print(f"MA自定义参数: {ma_params}")
            
            # 支持表达式字符串转 lambda
            conditions = {}
            for k, v in conditions_dict.items():
                # 支持 op/value 格式，自动调用 compare.py
                if isinstance(v, dict) and 'op' in v and 'value' in v:
                    op = v['op']
                    val = v['value']
                    if op == '>':
                        conditions[k] = lambda x, val=val: compare.greater(x, val)
                    elif op == '<':
                        conditions[k] = lambda x, val=val: compare.less(x, val)
                    elif op == '>=':
                        conditions[k] = lambda x, val=val: compare.greater_equal(x, val)
                    elif op == '<=':
                        conditions[k] = lambda x, val=val: compare.less_equal(x, val)
                    elif op == '=':
                        conditions[k] = lambda x, val=val: compare.equal(x, val)
                    else:
                        conditions[k] = lambda x: True
                elif isinstance(v, str):
                    conditions[k] = eval(f'lambda x: {v}')
                else:
                    conditions[k] = v
            
            # 获取日期范围
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            
            # 构建extra参数，传递启用指标和周期信息
            extra_params = {
                'enabled_indicators': validated_indicators,  # 🔧 使用验证后的指标列表
                'period': period,
                'custom_capital': custom_capital,
                'initial_capital': initial_capital,  # 🆕 添加初始资金参数
                'data_frequency': data_frequency,     # 🆕 添加数据频率参数
                'minute_interval': minute_interval,   # 🆕 添加分钟周期参数
                'start_date': start_date,
                'end_date': end_date,
                'macd_params': macd_params,
                'kdj_params': kdj_params,
                'ma_params': ma_params,
                'rsi_params': rsi_params,             # 🆕 添加RSI参数
                'boll_params': boll_params,           # 🆕 添加BOLL参数
                'cci_params': cci_params,             # 🆕 添加CCI参数
                'wr_params': wr_params,               # 🆕 添加Williams %R参数
                'market': market_filter,  # 🔧 重要修复：添加市场筛选参数
                'enable_divergence': enable_divergence,  # 🔧 添加背离分析参数
                'compress_results': compress_results,     # 🆕 添加结果压缩参数
                'compress_mode': compress_mode            # 🆕 添加压缩模式参数
            }
            
            print(f"📋 传递给筛选函数的参数:")
            print(f"   - 启用指标: {validated_indicators}")
            print(f"   - 筛选条件数量: {len(conditions)}")
            print(f"   - 时间范围: {start_date} 到 {end_date}")
            print(f"   - 自定义参数: MACD={bool(macd_params)}, KDJ={bool(kdj_params)}, MA={bool(ma_params)}")
            
            # 使用数据库模式进行筛选
            result_df = filter_stocks_from_database(
                validated_indicators,  # 🔧 使用验证后的指标列表
                conditions, 
                start_date=start_date,
                end_date=end_date,
                limit=100,
                extra_params=extra_params
            )
            
            # 🔧 重要：确保result_df是DataFrame类型
            if not isinstance(result_df, pd.DataFrame):
                print(f"❌ 筛选结果类型错误: {type(result_df)}, 内容: {result_df}")
                return JsonResponse({
                    'success': False, 
                    'error': f'筛选结果类型错误: {type(result_df).__name__}',
                    'details': str(result_df) if len(str(result_df)) < 200 else str(result_df)[:200] + '...'
                })
            
            # 🆕 股票结果压缩处理
            original_count = len(result_df)
            original_unique_stocks = result_df['code'].nunique() if len(result_df) > 0 and 'code' in result_df.columns else 0
            compression_stats = None
            
            # 使用新的compress_by_stock参数进行压缩
            if compress_by_stock and len(result_df) > 0:
                try:
                    compressed_df, compression_stats = compress_stock_results(result_df, compress_by_stock=True)
                    result_df = compressed_df
                    
                    print(f"📊 股票压缩完成：{original_count} 条记录 → {len(result_df)} 只股票")
                    if isinstance(compression_stats, dict):
                        print(f"压缩比率：{compression_stats.get('compression_ratio', 0):.1%}")
                    else:
                        print(f"压缩统计信息类型异常: {type(compression_stats)}")
                    
                except Exception as e:
                    print(f"❌ 股票压缩失败：{e}")
                    import traceback
                    traceback.print_exc()
                    # 压缩失败时保持原始结果
            
            
            # 清理数据中的NaN值，确保JSON序列化正确
            import numpy as np
            result_df = result_df.replace([np.nan, np.inf, -np.inf], None)
            
            # 📊 计算性能统计信息
            performance_stats = {
                'total_indicators_requested': len(enabled_indicators),
                'valid_indicators_processed': len(validated_indicators),
                'skipped_indicators': len(enabled_indicators) - len(validated_indicators),
                'data_rows_processed': original_count,
                'compressed_rows_returned': len(result_df),
                'unique_stocks_found': original_unique_stocks,
                'compression_ratio': len(result_df) / original_count if original_count > 0 else 0,
                'time_range_days': (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days if start_date and end_date else 0,
                'compress_enabled': compress_by_stock,  # 更新为compress_by_stock
                'compress_mode': compress_mode,
                'compression_stats': compression_stats  # 添加详细压缩统计
            }
            
            # 返回 json，包含周期和资金信息以及性能统计
            return JsonResponse({
                'success': True, 
                'data': result_df.to_dict(orient='records'),
                'count': len(result_df),
                'original_count': original_count,  # 🆕 添加原始数据量
                'unique_stocks': original_unique_stocks,  # 🆕 添加唯一股票数量
                'period': period,
                'custom_capital': custom_capital,
                'initial_capital': initial_capital,     # 🆕 添加初始资金到响应
                'data_frequency': data_frequency,       # 🆕 添加数据频率到响应
                'minute_interval': minute_interval,     # 🆕 添加分钟周期到响应
                'enabled_indicators': validated_indicators,  # 🔧 返回验证后的指标列表
                'performance_stats': performance_stats,      # 🆕 添加性能统计信息
                'skipped_indicators': skipped_indicators,    # 🆕 返回跳过的指标
                'compression_info': {                        # 🆕 添加压缩信息
                    'enabled': compress_results,
                    'mode': compress_mode,
                    'original_records': original_count,
                    'compressed_records': len(result_df),
                    'compression_ratio': f"{len(result_df) / original_count * 100:.1f}%" if original_count > 0 else "0%"
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Only POST allowed'})

    
    # 按股票代码分组处理
    for stock_code, group_df in df.groupby('code'):
        try:
            stock_df = group_df.copy().reset_index(drop=True)
            
            # 为每个指标计算值
            for indicator_name in indicator_names:
                indicator_values = calculate_indicator(stock_df, indicator_name)
                if indicator_values is not None:
                    stock_df[indicator_name] = indicator_values
            
            # 应用筛选条件
            meets_conditions = True
            for condition_name, condition_func in conditions.items():
                if condition_name in stock_df.columns:
                    try:
                        # 取最新的指标值进行判断
                        latest_value = stock_df[condition_name].iloc[-1]
                        if pd.notna(latest_value) and not condition_func(latest_value):
                            meets_conditions = False
                            break
                    except Exception as e:
                        print(f"⚠️ 条件检查失败 {condition_name}: {e}")
                        meets_conditions = False
                        break
            
            # 如果满足所有条件，添加到结果中
            if meets_conditions:
                filtered_results.append(stock_df)
                
        except Exception as e:
            print(f"⚠️ 处理股票 {stock_code} 时出错: {e}")
            continue
    
    # 合并所有符合条件的股票数据
    if filtered_results:
        final_df = pd.concat(filtered_results, ignore_index=True)
        return final_df
    else:
        return pd.DataFrame()


@csrf_exempt
def advanced_analysis_api(request):
    """
    高级技术分析API接口
    支持MACD/KDJ背离分析、多空信号识别、市场分析等功能
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            # 获取基本参数
            stock_codes = data.get('stock_codes', [])
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            market_filter = data.get('market', 'ALL')  # 市场筛选：shanghai/shenzhen/ALL
            
            # 获取分析参数
            enable_divergence = data.get('enable_divergence', True)
            enable_trend_signals = data.get('enable_trend_signals', True)
            enable_market_analysis = data.get('enable_market_analysis', True)
            
            # 获取指标参数
            macd_params = data.get('macd_params', {'short': 12, 'long': 26, 'signal': 9})
            kdj_params = data.get('kdj_params', {'n': 9, 'k_factor': 2/3, 'd_factor': 2/3})
            
            print(f"高级分析请求 - 股票数量: {len(stock_codes)}, 市场: {market_filter}")
            
            # 如果没有指定股票代码，从数据库获取
            if not stock_codes:
                queryset = StockHistoryData.objects.all()
                if start_date:
                    if isinstance(start_date, str):
                        start_date = datetime.strptime(start_date.replace('-', ''), '%Y%m%d').date()
                    queryset = queryset.filter(date__gte=start_date)
                
                if end_date:
                    if isinstance(end_date, str):
                        end_date = datetime.strptime(end_date.replace('-', ''), '%Y%m%d').date()
                    queryset = queryset.filter(date__lte=end_date)
                
                stock_codes = list(queryset.values_list('symbol', flat=True).distinct()[:50])
            
            # 市场筛选
            if market_filter != 'ALL':
                if market_filter.lower() in ['shanghai', 'sh', '上证']:
                    stock_codes = MarketAnalyzer.filter_stocks_by_market(stock_codes, 'shanghai')
                elif market_filter.lower() in ['shenzhen', 'sz', '深证']:
                    stock_codes = MarketAnalyzer.filter_stocks_by_market(stock_codes, 'shenzhen')
            
            print(f"市场筛选后股票数量: {len(stock_codes)}")
            
            # 分析结果
            analysis_results = {
                'market_analysis': {},
                'stocks_analysis': {},
                'summary': {}
            }
            
            # 市场分析
            if enable_market_analysis:
                market_analysis = get_market_analysis_summary(
                    stock_codes, 
                    market_filter.lower() if market_filter != 'ALL' else None
                )
                analysis_results['market_analysis'] = market_analysis
            
            # 股票个股分析
            processed_count = 0
            for code in stock_codes[:20]:  # 限制处理数量
                try:
                    # 获取股票数据
                    queryset = StockHistoryData.objects.filter(symbol=code)
                    if start_date:
                        queryset = queryset.filter(date__gte=start_date)
                    if end_date:
                        queryset = queryset.filter(date__lte=end_date)
                    
                    data_records = list(queryset.values(
                        'date', 'symbol', 'open', 'close', 'high', 'low', 'volume'
                    ))
                    
                    if len(data_records) < 20:  # 数据不足
                        continue
                    
                    # 转换为DataFrame
                    stock_df = pd.DataFrame(data_records)
                    stock_df = stock_df.rename(columns={
                        'symbol': 'code',
                        'open': 'open',
                        'close': 'close', 
                        'high': 'high',
                        'low': 'low'
                    })
                    
                    # 确保数据按日期排序
                    stock_df['date'] = pd.to_datetime(stock_df['date'])
                    stock_df = stock_df.sort_values('date').reset_index(drop=True)
                    
                    # 创建股票分析结果
                    stock_analysis = {
                        'code': code,
                        'market': MarketAnalyzer.identify_market(code),
                        'sector': MarketAnalyzer.identify_sector(code),
                        'data_points': len(stock_df),
                        'date_range': {
                            'start': stock_df['date'].min().strftime('%Y-%m-%d'),
                            'end': stock_df['date'].max().strftime('%Y-%m-%d')
                        }
                    }
                    
                    # MACD背离分析
                    if enable_divergence:
                        macd_divergence = analyze_macd_divergence(stock_df, **macd_params)
                        stock_analysis['macd_divergence'] = macd_divergence
                        
                        kdj_divergence = analyze_kdj_divergence(stock_df, **kdj_params)
                        stock_analysis['kdj_divergence'] = kdj_divergence
                    
                    # 趋势信号分析
                    if enable_trend_signals:
                        trend_signals = analyze_trend_signals(
                            stock_df, 
                            **macd_params,
                            n=kdj_params.get('n', 9)
                        )
                        stock_analysis['trend_signals'] = trend_signals
                    
                    analysis_results['stocks_analysis'][code] = stock_analysis
                    processed_count += 1
                    
                except Exception as e:
                    print(f"分析股票 {code} 时出错: {e}")
                    analysis_results['stocks_analysis'][code] = {
                        'code': code,
                        'error': str(e)
                    }
            
            # 生成摘要
            analysis_results['summary'] = {
                'total_requested': len(stock_codes),
                'successfully_analyzed': processed_count,
                'market_filter': market_filter,
                'analysis_features': {
                    'divergence_analysis': enable_divergence,
                    'trend_signals': enable_trend_signals,
                    'market_analysis': enable_market_analysis
                }
            }
            
            print(f"完成高级分析 - 处理 {processed_count} 只股票")
            
            # 转换numpy类型为Python原生类型，解决JSON序列化问题
            def convert_numpy_types(obj):
                if isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(v) for v in obj]
                elif hasattr(obj, 'item'):  # numpy类型
                    return obj.item()
                elif hasattr(obj, 'tolist'):  # numpy数组
                    return obj.tolist()
                else:
                    return obj
            
            # 转换所有数据
            safe_analysis_results = convert_numpy_types(analysis_results)
            
            return JsonResponse({
                'success': True,
                'data': safe_analysis_results
            })
            
        except Exception as e:
            print(f"高级分析API错误: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False, 
                'error': str(e)
            })
    else:
        return JsonResponse({
            'success': False, 
            'error': 'Only POST method allowed'
        })

