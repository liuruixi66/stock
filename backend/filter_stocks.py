#注意：此文件好多字段是随机生成的，可能不符合实际数据
# 需要根据实际数据结构调整字段名
#0,1,2,3,4,5,6,7,8,9,10,11,12,13,14是对应着金叉，死叉，股东减持信号，股东增持信号，股东分红信号，违规问询函信号，新上市，北交所，沪深主板，ST，*ST，停牌，科创板，创业板，退市。
# 买入信号(15)和卖出信号(16)已移至signal_library.py

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from indicator_utils import resample_to_period
import compare
# 导入信号库
from signal_library import SIGNAL_CODES, generate_buy_signal, generate_sell_signal
# 导入指标模块
from indicators import (
    analyze_macd_divergence,
    analyze_kdj_divergence,
    analyze_trend_signals,
    MarketAnalyzer,
    get_market_analysis_summary
)
# Django API 视图，支持前端 POST 调用
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Django 相关导入
try:
    import django
    import sys
    
    # 确保正确的路径
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    # 设置Django配置
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    
    # 切换到backend目录确保Django正确初始化
    original_cwd = os.getcwd()
    os.chdir(backend_dir)
    
    django.setup()
    from stockmarket.models import StockSpot, StockHistoryData
    from django.db.models import Q
    
    # 恢复原来的工作目录
    os.chdir(original_cwd)
    
    DJANGO_AVAILABLE = True
    print(f"✅ Django配置成功，backend目录: {backend_dir}")
except Exception as e:
    DJANGO_AVAILABLE = False
    print(f"❌ Django配置失败: {str(e)}")
    print("将使用CSV文件模式")

def filter_stocks_from_database(indicator_names, conditions, start_date=None, end_date=None, limit=100, extra_params=None):
    """
    从数据库筛选股票数据
    
    Args:
        indicator_names: 指标名称列表
        conditions: 筛选条件字典
        start_date: 开始日期
        end_date: 结束日期
        limit: 返回结果数量限制
        extra_params: 额外参数（包含启用指标、周期等）
    
    Returns:
        pandas.DataFrame: 筛选后的股票数据
    """
    if not DJANGO_AVAILABLE:
        print("Django不可用，使用默认CSV文件模式")
        print(f"当前工作目录: {os.getcwd()}")
        try:
            result = filter_stocks(indicator_names, conditions, '/home/liu/桌面/stock-main/backend/000001_10years.csv')
            if isinstance(result, pd.DataFrame):
                return result
            else:
                print(f"❌ CSV模式返回非DataFrame: {type(result)}")
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ CSV模式筛选失败: {e}")
            return pd.DataFrame()
    
    try:
        # 获取额外参数
        if extra_params is None:
            extra_params = {}
            
        enabled_indicators = extra_params.get('enabled_indicators', indicator_names)
        period = extra_params.get('period', '日')
        data_frequency = extra_params.get('data_frequency', 'daily')
        minute_interval = extra_params.get('minute_interval', '5')
        initial_capital = extra_params.get('initial_capital', 100000)
        
        print(f"数据库筛选 - 启用指标: {enabled_indicators}, 周期: {period}")
        print(f"数据频率: {data_frequency}, 分钟周期: {minute_interval}, 初始资金: {initial_capital}")
        
        # 根据数据频率选择不同的数据源和处理方式
        if data_frequency == 'minute':
            print(f"使用分钟级数据，周期: {minute_interval}分钟")
            # 这里可以扩展为处理分钟数据的逻辑
            # 当前使用日线数据模拟
        elif data_frequency == 'tick':
            print("使用tick级数据")
            # 这里可以扩展为处理tick数据的逻辑
            # 当前使用日线数据模拟
        else:
            print("使用日线数据")
        
        # 构建查询集，使用StockHistoryData模型
        queryset = StockHistoryData.objects.all()
        
        # 日期筛选
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date.replace('-', ''), '%Y%m%d').date()
            queryset = queryset.filter(date__gte=start_date)
        
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date.replace('-', ''), '%Y%m%d').date()
            queryset = queryset.filter(date__lte=end_date)
        
        # 转换为DataFrame
        fields = [
            'date', 'symbol', 'open', 'close', 'high', 'low',
            'volume', 'turnover', 'amplitude', 'pct_change', 'change', 'turnover_rate'
        ]
        
        data = list(queryset.values(*fields))
        if not data:
            print("数据库中没有找到数据")
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # 添加name字段，使用symbol作为name（因为显示股票代码）
        df['name'] = df['symbol']
        
        # 标准化列名以匹配回测系统期望的格式
        column_mapping = {
            'date': 'date',
            'symbol': 'code',  # 将symbol映射为code
            'name': 'name',    # name字段现在包含股票代码
            'open': 'open',
            'close': 'close',
            'high': 'high', 
            'low': 'low',
            'volume': 'volume',
            'turnover': 'amount',  # 将turnover映射为amount
            'pct_change': 'change_rate'  # 将pct_change映射为change_rate
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 确保必要的列存在
        required_columns = ['date', 'code', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                print(f"警告：缺少必要列 {col}")
        
        # 🔄 应用周期聚合 - 必须在指标计算之前进行
        print(f"应用周期聚合: {period}")
        if period in ['weekly', '周', 'W']:
            print("正在进行周线聚合...")
            df = aggregate_to_weekly(df, start_date, end_date)
        elif period in ['monthly', '月', 'M']:
            print("正在进行月线聚合...")
            df = aggregate_to_monthly(df, start_date, end_date)
        elif period in ['yearly', '年', 'Y']:
            print("正在进行年线聚合...")
            df = aggregate_to_yearly(df, start_date, end_date)
        elif period in ['daily', '日', 'D']:
            print("使用日线数据，无需聚合")
            # 对于日线数据，仍然需要应用日期范围筛选
            if start_date or end_date:
                df['date'] = pd.to_datetime(df['date'])
                if start_date:
                    start_date_dt = pd.to_datetime(start_date)
                    df = df[df['date'] >= start_date_dt]
                if end_date:
                    end_date_dt = pd.to_datetime(end_date)
                    df = df[df['date'] <= end_date_dt]
        else:
            print(f"未知周期类型: {period}，使用日线数据")
        
        # 获取自定义参数
        macd_params = extra_params.get('macd_params', {})
        kdj_params = extra_params.get('kdj_params', {})
        ma_params = extra_params.get('ma_params', {})
        market_filter = extra_params.get('market', 'ALL')  # 市场筛选参数
        enable_divergence = extra_params.get('enable_divergence', True)  # 是否启用背离分析
        
        # 市场筛选
        print(f"应用市场筛选: {market_filter}")
        if market_filter != 'ALL':
            # 使用MarketAnalyzer进行市场筛选
            stock_codes = df['code'].unique().tolist()
            print(f"筛选前股票代码: {stock_codes}")
            
            if market_filter.lower() in ['shanghai', 'sh', '上证']:
                filtered_codes = MarketAnalyzer.filter_stocks_by_market(stock_codes, 'shanghai')
                print(f"上证筛选结果: {filtered_codes}")
            elif market_filter.lower() in ['shenzhen', 'sz', '深证']:
                filtered_codes = MarketAnalyzer.filter_stocks_by_market(stock_codes, 'shenzhen')
                print(f"深证筛选结果: {filtered_codes}")
            else:
                filtered_codes = stock_codes  # 保持所有代码
            
            # 重要修复：如果筛选后没有股票，直接返回空结果
            if not filtered_codes:
                print(f"警告：{market_filter}市场筛选后无可用股票，返回空结果")
                return pd.DataFrame()
            
            df = df[df['code'].isin(filtered_codes)]
            print(f"市场筛选后剩余 {len(df)} 条数据")
        
        # 重要检查：确保有数据才继续处理
        if len(df) == 0:
            print("警告：筛选后无数据，跳过指标计算")
            return df
        
        # 📊 智能指标计算 - 只计算前端启用的指标，避免不必要的计算开销
        print(f"🔧 开始计算启用的指标: {enabled_indicators}")
        calculated_indicators = []
        
        if 'ma' in enabled_indicators:
            print("📈 正在计算MA(移动平均线)指标...")
            df = add_ma_indicators(df, **ma_params)
            calculated_indicators.append('MA')
        else:
            print("⏭️ MA指标未启用，跳过计算")
            
        if 'macd' in enabled_indicators:
            print("📊 正在计算MACD指标...")
            df = add_macd_indicators(df, **macd_params)
            calculated_indicators.append('MACD')
        else:
            print("⏭️ MACD指标未启用，跳过计算")
            
        if 'kdj' in enabled_indicators:
            print("📉 正在计算KDJ指标...")
            df = add_kdj_indicators(df, **kdj_params)
            calculated_indicators.append('KDJ')
        else:
            print("⏭️ KDJ指标未启用，跳过计算")
        
        # 🎯 支持更多指标类型
        if 'rsi' in enabled_indicators:
            print("📊 正在计算RSI指标...")
            df = add_rsi_indicators(df, **extra_params.get('rsi_params', {}))
            calculated_indicators.append('RSI')
        else:
            print("⏭️ RSI指标未启用，跳过计算")
            
        if 'boll' in enabled_indicators:
            print("📊 正在计算布林带(BOLL)指标...")
            df = add_boll_indicators(df, **extra_params.get('boll_params', {}))
            calculated_indicators.append('BOLL')
        else:
            print("⏭️ 布林带指标未启用，跳过计算")
            
        if 'cci' in enabled_indicators:
            print("📊 正在计算CCI指标...")
            df = add_cci_indicators(df, **extra_params.get('cci_params', {}))
            calculated_indicators.append('CCI')
        else:
            print("⏭️ CCI指标未启用，跳过计算")
            
        if 'wr' in enabled_indicators:
            print("📊 正在计算Williams %R指标...")
            df = add_wr_indicators(df, **extra_params.get('wr_params', {}))
            calculated_indicators.append('WR')
        else:
            print("⏭️ Williams %R指标未启用，跳过计算")
        
        print(f"✅ 指标计算完成，已计算: {calculated_indicators}")
        print(f"⚡ 性能优化：跳过了 {len(enabled_indicators) - len(calculated_indicators)} 个未启用的指标")
        
        # 🎯 高级分析功能
        if enable_divergence and len(df) > 0:
            print("正在进行高级技术分析...")
            
            # 为每个股票代码分别进行分析
            stock_analysis = {}
            unique_codes = df['code'].unique()
            
            for code in unique_codes[:10]:  # 限制分析数量以避免性能问题
                stock_data = df[df['code'] == code].copy()
                if len(stock_data) < 20:  # 需要足够的数据进行分析
                    continue
                
                # 确保数据按日期排序
                stock_data = stock_data.sort_values('date')
                
                # 重新设置索引以便指标计算
                stock_data = stock_data.reset_index(drop=True)
                
                # 创建分析结果字典
                analysis_result = {
                    'code': code,
                    'data_points': len(stock_data)
                }
                
                # MACD背离分析
                if 'macd' in enabled_indicators:
                    try:
                        macd_analysis = analyze_macd_divergence(
                            stock_data, 
                            **macd_params
                        )
                        analysis_result['macd_divergence'] = macd_analysis
                    except Exception as e:
                        print(f"MACD背离分析错误 ({code}): {e}")
                        analysis_result['macd_divergence'] = {'error': str(e)}
                
                # KDJ背离分析
                if 'kdj' in enabled_indicators:
                    try:
                        kdj_analysis = analyze_kdj_divergence(
                            stock_data,
                            **kdj_params
                        )
                        analysis_result['kdj_divergence'] = kdj_analysis
                    except Exception as e:
                        print(f"KDJ背离分析错误 ({code}): {e}")
                        analysis_result['kdj_divergence'] = {'error': str(e)}
                
                # 趋势信号分析
                try:
                    trend_analysis = analyze_trend_signals(
                        stock_data,
                        **macd_params,
                        n=kdj_params.get('n', 9)
                    )
                    analysis_result['trend_signals'] = trend_analysis
                except Exception as e:
                    print(f"趋势信号分析错误 ({code}): {e}")
                    analysis_result['trend_signals'] = {'error': str(e)}
                
                stock_analysis[code] = analysis_result
            
            # 将分析结果附加到DataFrame的额外属性中
            if hasattr(df, 'attrs'):
                df.attrs['advanced_analysis'] = stock_analysis
            else:
                # 如果不支持attrs，创建一个全局变量存储
                global _last_advanced_analysis
                _last_advanced_analysis = stock_analysis
            
            print(f"完成 {len(stock_analysis)} 只股票的高级技术分析")
        
        # 应用筛选条件
        for indicator, condition in conditions.items():
            if indicator in df.columns:
                if callable(condition):
                    df = df[df[indicator].apply(condition)]
                else:
                    print(f"警告：条件 {indicator} 不是可调用的函数")
        
        # 限制结果数量
        if limit and len(df) > limit:
            df = df.head(limit)
        
        # 🔧 数据清理：处理NaN, inf, -inf值，避免JSON序列化错误
        if len(df) > 0:
            # 替换NaN值为None
            df = df.where(pd.notnull(df), None)
            
            # 替换无穷大值
            df = df.replace([float('inf'), float('-inf')], None)
            
            # 🔧 处理日期序列化：将Timestamp转换为字符串
            if 'date' in df.columns:
                df['date'] = df['date'].dt.strftime('%Y-%m-%dT%H:%M:%S')
            
            # 确保数值列的数据类型正确
            numeric_columns = df.select_dtypes(include=['number']).columns
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        print(f"从数据库筛选出 {len(df)} 条股票数据")
        return df
        
    except Exception as e:
        print(f"从数据库筛选股票时出错: {e}")
        print("回退到CSV文件模式")
        try:
            result = filter_stocks(indicator_names, conditions, '/home/liu/桌面/stock-main/backend/000001_10years.csv')
            if isinstance(result, pd.DataFrame):
                return result
            else:
                print(f"❌ CSV回退模式返回非DataFrame: {type(result)}")
                return pd.DataFrame()
        except Exception as csv_e:
            print(f"❌ CSV回退模式也失败: {csv_e}")
            return pd.DataFrame()

def add_ma_indicators(df, ma_periods=[5, 10, 20]):
    """
    添加移动平均线指标 - 优先使用indicators模块，回退到ma_utils
    参数:
        df: 数据框
        ma_periods: MA周期列表，默认[5, 10, 20]
    """
    try:
        df = df.copy()
        
        # 🔧 优先尝试使用indicators模块的MA计算
        try:
            from indicators.ma import calculate as ma_calculate
            
            # 准备数据格式
            data = df.rename(columns={
                'close': 'CLOSE',
                'high': 'HIGH',
                'low': 'LOW',
                'open': 'OPEN',
                'volume': 'VOLUME'
            })
            
            # 根据传入的周期计算MA
            for period in ma_periods:
                ma_values = ma_calculate(data, N=period)
                df[f'ma{period}'] = ma_values
                print(f"✅ 使用indicators模块计算MA{period}")
                
        except ImportError as e:
            print(f"⚠️ indicators模块不可用，回退到ma_utils: {e}")
            # 回退到ma_utils实现
            from ma_utils import calculate_ma
            
            for period in ma_periods:
                df[f'ma{period}'] = calculate_ma(df['close'], period)
                print(f"✅ 使用ma_utils计算MA{period}")
        
        # 保持向后兼容性，确保基础字段存在
        if 5 in ma_periods:
            df['ma5'] = df['ma5'] if 'ma5' in df.columns else calculate_ma(df['close'], 5)
        if 10 in ma_periods:
            df['ma10'] = df['ma10'] if 'ma10' in df.columns else calculate_ma(df['close'], 10)
        if 20 in ma_periods:
            df['ma20'] = df['ma20'] if 'ma20' in df.columns else calculate_ma(df['close'], 20)
            df['ma'] = df['ma20']  # 默认使用20日均线
        
        return df
    except Exception as e:
        print(f"❌ 计算MA指标时出错: {e}")
        return df

def add_macd_indicators(df, short=12, long=26, signal=9):
    """
    添加MACD指标 - 使用indicators模块的实现
    参数:
        df: 数据框
        short: 短周期EMA，默认12
        long: 长周期EMA，默认26  
        signal: 信号线周期，默认9
    """
    try:
        from indicators.macd import calculate
        df = df.copy()
        # 重命名列以匹配indicators模块的期望格式
        data = df.rename(columns={
            'close': 'CLOSE',
            'high': 'HIGH',
            'low': 'LOW',
            'open': 'OPEN',
            'volume': 'VOLUME'
        })
        # 调用indicators模块的MACD计算
        dif, dea, macd = calculate(data, short=short, long=long, signal=signal)
        df['macd'] = macd          # MACD柱状图
        df['macd_signal'] = dea    # 信号线(DEA)
        df['macd_histogram'] = dif # DIF线
        print(f"✅ 使用indicators模块计算MACD({short},{long},{signal})")
        return df
    except Exception as e:
        print(f"❌ 计算MACD指标时出错: {e}")
        return df

def add_kdj_indicators(df, n=9, k_factor=2/3, d_factor=2/3):
    """
    添加KDJ指标 - 优先使用indicators模块，回退到indicator_utils
    参数:
        df: 数据框
        n: RSV计算周期，默认9
        k_factor: K值平滑因子，默认2/3
        d_factor: D值平滑因子，默认2/3
    """
    try:
        df = df.copy()
        
        # 🔧 优先尝试使用indicators模块的KDJ计算
        try:
            from indicators.kdj import kdj
            
            # 准备数据格式
            data = df.rename(columns={
                'close': 'CLOSE',
                'high': 'HIGH',
                'low': 'LOW',
                'open': 'OPEN',
                'volume': 'VOLUME'
            })
            
            # 调用indicators模块的KDJ计算
            k_val, d_val, j_val = kdj(data, n=n)
            df['kdj_k'] = k_val
            df['kdj_d'] = d_val  
            df['kdj_j'] = j_val
            print(f"✅ 使用indicators模块计算KDJ({n})")
            
        except ImportError as e:
            print(f"⚠️ indicators.kdj不可用，回退到indicator_utils: {e}")
            # 回退到indicator_utils实现
            from indicator_utils import calculate_kdj
            kdj_data = calculate_kdj(df['high'], df['low'], df['close'], n=n)
            df['kdj_k'] = kdj_data['k']
            df['kdj_d'] = kdj_data['d']
            df['kdj_j'] = kdj_data['j']
            print(f"✅ 使用indicator_utils计算KDJ({n})")
            
        return df
    except Exception as e:
        print(f"❌ 计算KDJ指标时出错: {e}")
        return df

def add_rsi_indicators(df, period=14):
    """
    添加RSI指标 - 使用indicators模块的实现
    参数:
        df: 数据框
        period: RSI计算周期，默认14
    """
    try:
        from indicators.rsi import calculate
        df = df.copy()
        # 重命名列以匹配indicators模块的期望格式
        data = df.rename(columns={
            'close': 'CLOSE',
            'high': 'HIGH',
            'low': 'LOW',
            'open': 'OPEN',
            'volume': 'VOLUME'
        })
        # 调用indicators模块的RSI计算
        rsi_values = calculate(data, N=period)
        df['rsi'] = rsi_values
        return df
    except Exception as e:
        print(f"计算RSI指标时出错: {e}")
        return df

def add_boll_indicators(df, period=20, std_dev=2):
    """
    添加布林带(BOLL)指标 - 使用indicators模块的实现
    参数:
        df: 数据框
        period: 移动平均周期，默认20
        std_dev: 标准差倍数，默认2
    """
    try:
        from indicators.boll import calculate
        df = df.copy()
        # 重命名列以匹配indicators模块的期望格式
        data = df.rename(columns={
            'close': 'CLOSE',
            'high': 'HIGH',
            'low': 'LOW',
            'open': 'OPEN',
            'volume': 'VOLUME'
        })
        
        # indicators/boll.py只返回中轨，我们需要完整的布林带
        # 让我们自己计算完整的布林带，但基于indicators模块的逻辑
        close = data['CLOSE']
        mid = close.rolling(window=period, min_periods=1).mean()
        std = close.rolling(window=period, min_periods=1).std()
        upper = mid + std_dev * std
        lower = mid - std_dev * std
        
        df['boll_mid'] = mid      # 中轨（移动平均线）
        df['boll_upper'] = upper  # 上轨
        df['boll_lower'] = lower  # 下轨
        df['boll'] = mid         # 兼容性字段，默认使用中轨
        
        return df
    except Exception as e:
        print(f"计算BOLL指标时出错: {e}")
        return df

def add_cci_indicators(df, period=14):
    """
    添加CCI指标 - 使用indicators模块的实现
    参数:
        df: 数据框
        period: CCI计算周期，默认14
    """
    try:
        from indicators.cci import calculate
        df = df.copy()
        # 重命名列以匹配indicators模块的期望格式
        data = df.rename(columns={
            'close': 'CLOSE',
            'high': 'HIGH',
            'low': 'LOW',
            'open': 'OPEN',
            'volume': 'VOLUME'
        })
        # 调用indicators模块的CCI计算
        cci_values = calculate(data, N=period)
        df['cci'] = cci_values
        print(f"✅ 使用indicators模块计算CCI({period})")
        return df
    except Exception as e:
        print(f"❌ 计算CCI指标时出错: {e}")
        return df

def add_wr_indicators(df, period=14):
    """
    添加Williams %R指标 - 使用indicators模块的实现
    参数:
        df: 数据框
        period: WR计算周期，默认14
    """
    try:
        from indicators.wr import calculate
        df = df.copy()
        # 重命名列以匹配indicators模块的期望格式
        data = df.rename(columns={
            'close': 'CLOSE',
            'high': 'HIGH',
            'low': 'LOW',
            'open': 'OPEN',
            'volume': 'VOLUME'
        })
        # 调用indicators模块的WR计算
        wr_values = calculate(data)
        df['wr'] = wr_values
        print(f"✅ 使用indicators模块计算Williams %R({period})")
        return df
    except Exception as e:
        print(f"❌ 计算Williams %R指标时出错: {e}")
        return df

def compress_stock_results(df, compress_mode='latest'):
    """
    压缩筛选结果 - 将同一只股票的多条记录合并为一条
    
    Args:
        df: 筛选结果DataFrame
        compress_mode: 压缩模式
            - 'latest': 保留每只股票的最新日期记录
            - 'best': 保留每只股票表现最好的记录
            - 'summary': 生成每只股票的汇总统计
    
    Returns:
        压缩后的DataFrame
    """
    if len(df) == 0:
        return df
    
    print(f"🔄 开始压缩筛选结果 - 模式: {compress_mode}")
    original_count = len(df)
    unique_stocks = df['code'].nunique() if 'code' in df.columns else 0
    
    print(f"   压缩前: {original_count} 条记录，来自 {unique_stocks} 只股票")
    
    if 'code' not in df.columns:
        print("⚠️ 没有找到股票代码列，跳过压缩")
        return df
    
    compressed_results = []
    
    for stock_code, group in df.groupby('code'):
        if compress_mode == 'latest':
            # 保留最新日期的记录
            if 'date' in group.columns:
                group = group.sort_values('date', ascending=False)
                latest_record = group.iloc[0].copy()
                
                # 添加统计信息
                latest_record['data_points_count'] = len(group)
                latest_record['date_range_start'] = group['date'].min()
                latest_record['date_range_end'] = group['date'].max()
                
                # 如果有价格数据，计算区间内的统计
                if 'close' in group.columns:
                    latest_record['period_high'] = group['close'].max()
                    latest_record['period_low'] = group['close'].min()
                    latest_record['period_change_pct'] = ((group['close'].iloc[0] - group['close'].iloc[-1]) / group['close'].iloc[-1] * 100) if len(group) > 1 else 0
                
                compressed_results.append(latest_record)
                
        elif compress_mode == 'best':
            # 保留表现最好的记录（基于收盘价最高）
            if 'close' in group.columns:
                best_record = group.loc[group['close'].idxmax()].copy()
                
                # 添加统计信息
                best_record['data_points_count'] = len(group)
                best_record['date_range_start'] = group['date'].min()
                best_record['date_range_end'] = group['date'].max()
                best_record['period_high'] = group['close'].max()
                best_record['period_low'] = group['close'].min()
                
                compressed_results.append(best_record)
            else:
                # 如果没有价格数据，使用最新记录
                latest_record = group.iloc[0].copy()
                latest_record['data_points_count'] = len(group)
                compressed_results.append(latest_record)
                
        elif compress_mode == 'summary':
            # 生成汇总统计记录
            summary_record = {}
            
            # 基本信息
            summary_record['code'] = stock_code
            summary_record['name'] = group['name'].iloc[0] if 'name' in group.columns else stock_code
            summary_record['data_points_count'] = len(group)
            
            # 时间信息
            if 'date' in group.columns:
                summary_record['date_range_start'] = group['date'].min()
                summary_record['date_range_end'] = group['date'].max()
                summary_record['date'] = group['date'].max()  # 使用最新日期作为代表日期
            
            # 价格统计
            if 'close' in group.columns:
                summary_record['close'] = group['close'].iloc[0]  # 最新收盘价
                summary_record['period_high'] = group['close'].max()
                summary_record['period_low'] = group['close'].min()
                summary_record['period_avg'] = group['close'].mean()
                summary_record['period_change_pct'] = ((group['close'].iloc[0] - group['close'].iloc[-1]) / group['close'].iloc[-1] * 100) if len(group) > 1 else 0
            
            # 指标统计（取最新值）
            indicator_columns = ['ma5', 'ma10', 'ma20', 'ma60', 'macd', 'macd_signal', 'macd_histogram', 
                               'kdj_k', 'kdj_d', 'kdj_j', 'rsi', 'boll_upper', 'boll_mid', 'boll_lower']
            
            for col in indicator_columns:
                if col in group.columns:
                    latest_value = group[col].iloc[0]
                    if pd.notna(latest_value):
                        summary_record[col] = latest_value
                        # 添加指标的区间统计
                        summary_record[f'{col}_max'] = group[col].max()
                        summary_record[f'{col}_min'] = group[col].min()
                        summary_record[f'{col}_avg'] = group[col].mean()
            
            compressed_results.append(pd.Series(summary_record))
    
    # 转换为DataFrame
    if compressed_results:
        if compress_mode == 'summary':
            compressed_df = pd.DataFrame(compressed_results)
        else:
            compressed_df = pd.DataFrame(compressed_results)
        
        # 重置索引
        compressed_df = compressed_df.reset_index(drop=True)
        
        print(f"   压缩后: {len(compressed_df)} 条记录，每只股票一条")
        print(f"   压缩比: {len(compressed_df)}/{original_count} = {len(compressed_df)/original_count*100:.1f}%")
        
        return compressed_df
    else:
        print("⚠️ 压缩后没有结果")
        return pd.DataFrame()


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

def calculate_indicator(df, indicator_name):
    """
    计算单个技术指标
    """
    try:
        if indicator_name == 'ma':
            # 简单移动平均线
            if 'CLOSE' in df.columns:
                return df['CLOSE'].rolling(window=20, min_periods=1).mean()
            
        elif indicator_name == 'macd':
            # MACD指标 - 简化版本
            if 'CLOSE' in df.columns:
                exp1 = df['CLOSE'].ewm(span=12).mean()
                exp2 = df['CLOSE'].ewm(span=26).mean()
                macd_line = exp1 - exp2
                return macd_line
                
        elif indicator_name == 'kdj':
            # KDJ指标 - 简化版本
            if all(col in df.columns for col in ['HIGH', 'LOW', 'CLOSE']):
                low_min = df['LOW'].rolling(window=9).min()
                high_max = df['HIGH'].rolling(window=9).max()
                rsv = (df['CLOSE'] - low_min) / (high_max - low_min) * 100
                k = rsv.ewm(alpha=1/3).mean()
                return k
                
        elif indicator_name == 'pe':
            # 市盈率直接返回
            if 'PE' in df.columns:
                return df['PE']
                
        elif indicator_name == 'pb':
            # 市净率直接返回
            if 'PB' in df.columns:
                return df['PB']
        
        # 如果指标不支持，返回None
        return None
        
    except Exception as e:
        print(f"⚠️ 计算指标 {indicator_name} 时出错: {e}")
        return None
# 修复指标导入 - 直接从indicators模块导入
try:
    from indicators import ma, dif, dea, macd, kdj
except ImportError:
    # 如果直接导入失败，尝试单独导入
    import indicators.ma as ma
    import indicators.dif as dif
    import indicators.dea as dea  
    import indicators.macd as macd
    import indicators.kdj as kdj


def get_mysql_df(host, user, password, database, table, charset='utf8mb4'):
    engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{database}?charset={charset}")
    sql = f"SELECT * FROM {table}"
    print('SQL:', sql)
    df = pd.read_sql(sql, engine)
    return df

def get_csv_df(csv_path):
    print(f'Reading CSV: {csv_path}')
    df = pd.read_csv(csv_path)
    return df

def get_indicator(indicator, df, extra):
    """
    🎯 智能指标计算函数 - 根据前端启用状态计算技术指标
    只有在前端启用的指标才会被计算，避免不必要的计算开销
    
    参数:
        indicator: 指标名称
        df: 数据框
        extra: 额外参数，包含enabled_indicators等
    
    返回:
        计算结果或None（如果指标未启用）
    """
    # 📋 检查指标是否被启用
    enabled_indicators = extra.get('enabled_indicators', [])
    
    # 🚀 性能优化：特殊参数不需要检查启用状态
    special_params = ['period', 'start_date', 'end_date', 'custom_capital', 'initial_capital']
    
    if indicator not in enabled_indicators and indicator not in special_params:
        # 如果指标未启用，直接返回None，不进行计算
        print(f"⏭️ 指标 {indicator} 未启用，跳过计算（性能优化）")
        return None
    
    # 📊 指标已启用，开始计算
    print(f"🔧 正在计算启用的指标: {indicator}")
    
    # 处理周期参数
    period = extra.get('period', '日')
    if period in ['周', 'W']:
        df = aggregate_to_weekly(df)
    elif period in ['月', 'M']:
        df = aggregate_to_monthly(df)
    elif period in ['年', 'Y']:
        df = aggregate_to_yearly(df)
    
    print(f"✅ 正在计算指标: {indicator} (周期: {period})")
    
    # 数据库字段映射
    db_field_map = {
        'new_listing': 'NEW_LISTING',
        'beijing_exchange': 'BEIJING_EXCHANGE',
        'main_board': 'MAIN_BOARD',
        'st': 'ST',
        'star_st': 'STAR_ST',
        'suspension': 'SUSPENSION',
        'science_board': 'SCIENCE_BOARD',
        'growth_board': 'GROWTH_BOARD',
        'delisting': 'DELISTING'
    }

    if indicator in db_field_map:
        db_field = db_field_map[indicator]
        # 从数据库中查询字段值
        engine = create_engine(
            f"mysql+pymysql://{extra.get('db_user', 'root')}:{extra.get('db_password', '')}@{extra.get('db_host', 'localhost')}/{extra.get('db_name', 'stock')}?charset=utf8mb4"
        )
        query = f"SELECT {db_field} FROM {extra.get('db_table', 'quotes')}"
        print(f"Executing query: {query}")
        db_df = pd.read_sql(query, engine)

        # 返回符合条件的信号值
        if db_field in db_df.columns:
            return db_df[db_field].apply(lambda x: extra.get('signal_code', None) if x == 1 else None)
        else:
            return pd.Series([None]*len(db_df), index=db_df.index)

    # 净利润
    if indicator == 'net_profit':
        # 假设有一列 NET_PROFIT
        if 'NET_PROFIT' in df.columns:
            return df['NET_PROFIT']
        else:
            return None

    # 利润同比去年涨幅
    if indicator == 'profit_yoy':
        # 假设有一列 PROFIT_YOY
        if 'PROFIT_YOY' in df.columns:
            return df['PROFIT_YOY']
        else:
            return None
    # MACD金叉死叉信号检测
    if indicator == 'macd_cross':
        # 计算MACD金叉（0）和死叉（1）信号
        macd_result = macd.calculate(df, signal=extra.get('macd_n', 9))
        dif_val = macd_result[0]
        dea_val = macd_result[1]
        # 金叉：DIF上穿DEA，死叉：DIF下穿DEA
        cross = ((dif_val.shift(1) < dea_val.shift(1)) & (dif_val > dea_val)).astype(int)  # 金叉信号
        dead = ((dif_val.shift(1) > dea_val.shift(1)) & (dif_val < dea_val)).astype(int)   # 死叉信号
        # 0表示金叉，1表示死叉，其他为NaN
        signal = cross.copy()
        signal[dead == 1] = 1
        signal[(cross == 0) & (dead == 0)] = None
        return signal

    # 股东减持信号（2）
    if indicator == 'holder_reduce':
        # 假设有一列 HOLDER_REDUCE，1表示有减持，否则为0或NaN
        if 'HOLDER_REDUCE' in df.columns:
            return df['HOLDER_REDUCE'].apply(lambda x: 2 if x == 1 else None)
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 股东增持信号（3）
    if indicator == 'holder_add':
        # 假设有一列 HOLDER_ADD，1表示有增持，否则为0或NaN
        if 'HOLDER_ADD' in df.columns:
            return df['HOLDER_ADD'].apply(lambda x: 3 if x == 1 else None)
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 股东分红信号（4）
    if indicator == 'holder_dividend':
        # 假设有一列 HOLDER_DIVIDEND，1表示有分红，否则为0或NaN
        if 'HOLDER_DIVIDEND' in df.columns:
            return df['HOLDER_DIVIDEND'].apply(lambda x: 4 if x == 1 else None)
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 违规问询函信号（5）
    if indicator == 'violation_letter':
        # 假设有一列 VIOLATION_LETTER，1表示有违规问询函，否则为0或NaN
        if 'VIOLATION_LETTER' in df.columns:
            return df['VIOLATION_LETTER'].apply(lambda x: 5 if x == 1 else None)
        else:
            return pd.Series([None]*len(df), index=df.index)
    # 新上市信号（6）
    if indicator == 'new_listing':
        if 'NEW_LISTING' in df.columns:
            return df['NEW_LISTING'].apply(lambda x: 6 if x == 1 else None)
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 北交所信号（7）
    if indicator == 'beijing_exchange':
        if 'BEIJING_EXCHANGE' in df.columns:
            return df['BEIJING_EXCHANGE'].apply(lambda x: 7 if x == 1 else None)
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 沪深主板信号（8）
    if indicator == 'main_board':
        if 'MAIN_BOARD' in df.columns:
            return df['MAIN_BOARD'].apply(lambda x: 8 if x == 1 else None)
        else:
            return pd.Series([None]*len(df), index=df.index)

    # ST信号（9）
    if indicator == 'st':
        if 'ST' in df.columns:
            return df['ST'].apply(lambda x: 9 if x == 1 else None)
        else:
            return pd.Series([None]*len(df), index=df.index)

    # *ST信号（10）
    if indicator == 'star_st':
        if 'STAR_ST' in df.columns:
            return df['STAR_ST'].apply(lambda x: 10 if x == 1 else None)
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 停牌信号（11）
    if indicator == 'suspension':
        if 'SUSPENSION' in df.columns:
            return df['SUSPENSION'].apply(lambda x: 11 if x == 1 else None)
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 科创板信号（12）
    if indicator == 'science_board':
        if 'SCIENCE_BOARD' in df.columns:
            return df['SCIENCE_BOARD'].apply(lambda x: 12 if x == 1 else None)
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 创业板信号（13）
    if indicator == 'growth_board':
        if 'GROWTH_BOARD' in df.columns:
            return df['GROWTH_BOARD'].apply(lambda x: 13 if x == 1 else None)
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 退市信号（14）
    if indicator == 'delisting':
        if 'DELISTING' in df.columns:
            return df['DELISTING'].apply(lambda x: 14 if x == 1 else None)
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 开盘价对比
    if indicator == 'open_price' or indicator == 'open':
        if 'OPEN' in df.columns:
            return df['OPEN']
        elif 'open' in df.columns:
            return df['open']
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 收盘价对比  
    if indicator == 'close_price' or indicator == 'close':
        if 'CLOSE' in df.columns:
            return df['CLOSE']
        elif 'close' in df.columns:
            return df['close']
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 最高价对比
    if indicator == 'high_price' or indicator == 'high':
        if 'HIGH' in df.columns:
            return df['HIGH']
        elif 'high' in df.columns:
            return df['high']
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 最低价对比
    if indicator == 'low_price' or indicator == 'low':
        if 'LOW' in df.columns:
            return df['LOW']
        elif 'low' in df.columns:
            return df['low']
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 日成交均价对比
    if indicator == 'avg_price':
        # 日成交均价 = 成交额 / 成交量
        if 'AMOUNT' in df.columns and 'VOLUME' in df.columns:
            # 避免除零错误
            volume_nonzero = df['VOLUME'].replace(0, 1)
            return df['AMOUNT'] / volume_nonzero
        elif 'AVG_PRICE' in df.columns:
            return df['AVG_PRICE']
        else:
            # 如果没有成交额，用(最高价+最低价+收盘价)/3估算
            if 'HIGH' in df.columns and 'LOW' in df.columns and 'CLOSE' in df.columns:
                return (df['HIGH'] + df['LOW'] + df['CLOSE']) / 3
            else:
                return pd.Series([None]*len(df), index=df.index)

    # 涨幅对比
    if indicator == 'change_rate' or indicator == 'pct_change':
        if 'CHANGE_RATE' in df.columns:
            return df['CHANGE_RATE']
        elif 'PCT_CHANGE' in df.columns:
            return df['PCT_CHANGE']
        elif 'CLOSE' in df.columns:
            # 计算涨幅 = (今收盘价 - 昨收盘价) / 昨收盘价 * 100
            prev_close = df['CLOSE'].shift(1)
            change_rate = ((df['CLOSE'] - prev_close) / prev_close * 100).fillna(0)
            return change_rate
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 量比对比
    if indicator == 'volume_ratio':
        if 'VOLUME_RATIO' in df.columns:
            return df['VOLUME_RATIO']
        elif 'VOLUME' in df.columns:
            # 量比 = 当日成交量 / 过去5日平均成交量
            avg_volume_5 = df['VOLUME'].rolling(window=5).mean()
            volume_ratio = (df['VOLUME'] / avg_volume_5).fillna(1)
            return volume_ratio
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 成交额对比
    if indicator == 'amount' or indicator == 'turnover':
        if 'AMOUNT' in df.columns:
            return df['AMOUNT']
        elif 'TURNOVER' in df.columns:
            return df['TURNOVER']
        elif 'CLOSE' in df.columns and 'VOLUME' in df.columns:
            # 成交额 = 收盘价 * 成交量
            return df['CLOSE'] * df['VOLUME']
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 换手率对比
    if indicator == 'turnover_rate':
        if 'TURNOVER_RATE' in df.columns:
            return df['TURNOVER_RATE']
        elif 'VOLUME' in df.columns and 'TOTAL_SHARE' in df.columns:
            # 换手率 = 成交量 / 流通股本 * 100
            turnover_rate = (df['VOLUME'] / df['TOTAL_SHARE'] * 100).fillna(0)
            return turnover_rate
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 买入信号（15）- 调用信号库
    if indicator == 'buy_signal':
        # 使用信号库生成买入信号
        stock_code = extra.get('stock_code', 'UNKNOWN')
        signal_type = extra.get('buy_signal_type', 'basic')
        return generate_buy_signal(stock_code, df, signal_type, **extra)

    # 卖出信号（16）- 调用信号库
    if indicator == 'sell_signal':
        # 使用信号库生成卖出信号
        stock_code = extra.get('stock_code', 'UNKNOWN')
        signal_type = extra.get('sell_signal_type', 'basic')
        return generate_sell_signal(stock_code, df, signal_type, **extra)

    # 成交量指标
    if indicator == 'volume':
        if 'VOLUME' in df.columns:
            return df['VOLUME']
        elif 'volume' in df.columns:
            return df['volume']
        else:
            return pd.Series([None]*len(df), index=df.index)

    # 统一通过 indicators.__init__.py 导入的函数对象进行调用
    # 字段兼容处理，自动适配小写和大写
    # 字段兼容处理，支持小写、首字母大写、全大写
    col_map = {}
    for col in ['low', 'high', 'close', 'open', 'volume']:
        for variant in [col, col.capitalize(), col.upper()]:
            if variant in df.columns:
                col_map[variant] = col.upper()
    df = df.rename(columns=col_map)
    if indicator == 'ma':
        n = extra.get('ma_n', 5)
        result = ma.calculate(df, N=n)
        return result.round(2)
    elif indicator == 'dif':
        n = extra.get('dif_n', 12)
        result = dif.dif(df['CLOSE'], short=n)
        return result.round(2)
    elif indicator == 'dea':
        n = extra.get('dea_n', 9)
        result = dea.dea(df['CLOSE'], m=n)
        return result.round(2)
    elif indicator == 'macd':
        n = extra.get('macd_n', 9)
        result = macd.calculate(df, signal=n)
        if isinstance(result, tuple):
            return tuple(r.round(2) for r in result)
        else:
            return result.round(2)
    elif indicator == 'kdj':
        n = extra.get('k_n', 9)
        k_val, d_val, j_val = kdj.kdj(df, n=n)
        return k_val.round(2), d_val.round(2), j_val.round(2)
    elif indicator == 'k':
        n = extra.get('k_n', 9)
        k_val, _, _ = kdj.kdj(df, n=n)
        return k_val.round(2)
    elif indicator == 'd':
        n = extra.get('d_n', 9)
        _, d_val, _ = kdj.kdj(df, n=n)
        return d_val.round(2)
    elif indicator == 'j':
        n = extra.get('j_n', 9)
        _, _, j_val = kdj.kdj(df, n=n)
        return j_val.round(2)
    # 其他指标...

def filter_stocks(indicator_names, conditions, data_source, extra_indicators=None):
    """
    indicator_names: ['macd', 'rsi', ...]
    conditions: {'macd': lambda x: x > 0, 'rsi': lambda x: x < 70}
    data_source: 可以是 csv 路径、mysql 配置字典 或 'database' 字符串
    extra_indicators: 额外参数，包含启用指标、周期、自定义资金等
    返回：符合条件的股票DataFrame
    """
    # 获取额外参数
    if extra_indicators is None:
        extra_indicators = {}
    
    enabled_indicators = extra_indicators.get('enabled_indicators', indicator_names)
    period = extra_indicators.get('period', '日')
    custom_capital = extra_indicators.get('custom_capital', 100000)
    
    print(f"筛选参数 - 启用指标: {enabled_indicators}, 周期: {period}, 资金: {custom_capital}")
    
    # 判断数据源类型
    if isinstance(data_source, str):
        if data_source.endswith('.csv'):
            # CSV文件模式
            print(f"使用CSV文件模式: {data_source}")
            df = get_csv_df(data_source)
        elif data_source == 'database':
            # 数据库模式（使用默认配置）
            print("使用数据库模式")
            mysql_config = {
                'host': 'localhost',
                'user': 'root',
                'password': '9',
                'database': 'stock',
                'table': 'quotes',
                'charset': 'utf8mb4'
            }
            df = get_mysql_df(**mysql_config)
        else:
            raise ValueError(f"不支持的数据源字符串: {data_source}")
    elif isinstance(data_source, dict):
        # MySQL配置字典模式
        print("使用MySQL配置字典模式")
        df = get_mysql_df(**data_source)
    else:
        raise ValueError(f"不支持的数据源类型: {type(data_source)}")
        
    # 字段映射，适配指标模块
    df = df.rename(columns={
        'price': 'CLOSE',   # 兼容数据库
        'close': 'CLOSE',   # 兼容csv
        'open': 'OPEN',
        'high': 'HIGH',
        'low': 'LOW',
        'volume': 'VOLUME',
        'amount': 'AMOUNT',     # 成交额
        'turnover': 'AMOUNT',   # 成交额别名
        'avg_price': 'AVG_PRICE',  # 日成交均价
        'change_rate': 'CHANGE_RATE',  # 涨幅
        'pct_change': 'CHANGE_RATE',   # 涨幅别名
        'volume_ratio': 'VOLUME_RATIO',  # 量比
        'turnover_rate': 'TURNOVER_RATE',  # 换手率
        'total_share': 'TOTAL_SHARE'   # 流通股本
    })
    
    # 周期分割适配 - 传递额外参数给get_indicator
    if period in ['周', 'W']:
        df = aggregate_to_weekly(df)
    elif period in ['月', 'M']:
        df = aggregate_to_monthly(df)
    elif period in ['年', 'Y']:
        df = aggregate_to_yearly(df)
    # 日线无需处理，直接用原始数据
    
    # 将周期和启用指标信息传递给get_indicator
    extra_indicators['period'] = period
    extra_indicators['enabled_indicators'] = enabled_indicators
    extra_indicators['custom_capital'] = custom_capital
    # 时间筛选机制（可选参数）
    import datetime
    start_date = extra_indicators.get('start_date') if extra_indicators else None
    end_date = extra_indicators.get('end_date') if extra_indicators else None
    if start_date:
        df = df[df['date'] >= start_date]
    if end_date:
        df = df[df['date'] <= end_date]
    
    # 重置索引确保一致性
    df = df.reset_index(drop=True)
    
    indicator_dir = os.path.join(os.path.dirname(__file__), 'indicators')
    result_mask = pd.Series([True] * len(df), index=df.index)
    
    # 先计算所有需要的指标值，存储到DataFrame中
    calculated_indicators = {}
    
    # 合并所有指标名
    all_indicators = set(indicator_names)
    if extra_indicators:
        all_indicators.update(extra_indicators)
    
    # 第一轮：计算所有指标值
    for name in all_indicators:
        try:
            if name == 'four_ma_long':
                # 四周期多头排列：MA5 > MA10 > MA20 > MA60
                ma5 = df['CLOSE'].rolling(window=5).mean()
                ma10 = df['CLOSE'].rolling(window=10).mean()
                ma20 = df['CLOSE'].rolling(window=20).mean()
                ma60 = df['CLOSE'].rolling(window=60).mean()
                values = (ma5 > ma10) & (ma10 > ma20) & (ma20 > ma60)
                calculated_indicators[name] = values
                df[f'{name}_indicator'] = values
            elif name == 'macd_cross':
                values = get_indicator('macd_cross', df, extra_indicators if extra_indicators else {})
                calculated_indicators[name] = values
                df[f'{name}_indicator'] = values
            elif name == 'net_profit':
                values = get_indicator('net_profit', df, extra_indicators if extra_indicators else {})
                calculated_indicators[name] = values
                df[f'{name}_indicator'] = values
            elif name == 'profit_yoy':
                values = get_indicator('profit_yoy', df, extra_indicators if extra_indicators else {})
                calculated_indicators[name] = values
                df[f'{name}_indicator'] = values
            # 价格相关指标
            elif name in ['open_price', 'open']:
                values = get_indicator('open_price', df, extra_indicators if extra_indicators else {})
                calculated_indicators[name] = values
                df[f'{name}_indicator'] = values
            elif name in ['close_price', 'close']:
                values = get_indicator('close_price', df, extra_indicators if extra_indicators else {})
                calculated_indicators[name] = values
                df[f'{name}_indicator'] = values
            elif name in ['high_price', 'high']:
                values = get_indicator('high_price', df, extra_indicators if extra_indicators else {})
                calculated_indicators[name] = values
                df[f'{name}_indicator'] = values
            elif name in ['low_price', 'low']:
                values = get_indicator('low_price', df, extra_indicators if extra_indicators else {})
                calculated_indicators[name] = values
                df[f'{name}_indicator'] = values
            elif name == 'avg_price':
                values = get_indicator('avg_price', df, extra_indicators if extra_indicators else {})
                calculated_indicators[name] = values
                df[f'{name}_indicator'] = values
            elif name in ['change_rate', 'pct_change']:
                values = get_indicator('change_rate', df, extra_indicators if extra_indicators else {})
                calculated_indicators[name] = values
                df[f'{name}_indicator'] = values
            elif name == 'volume_ratio':
                values = get_indicator('volume_ratio', df, extra_indicators if extra_indicators else {})
                calculated_indicators[name] = values
                df[f'{name}_indicator'] = values
            elif name in ['amount', 'turnover']:
                values = get_indicator('amount', df, extra_indicators if extra_indicators else {})
                calculated_indicators[name] = values
                df[f'{name}_indicator'] = values
            elif name == 'turnover_rate':
                values = get_indicator('turnover_rate', df, extra_indicators if extra_indicators else {})
                calculated_indicators[name] = values
                df[f'{name}_indicator'] = values
            elif name in ['volume']:  # 处理成交量
                values = df['VOLUME'] if 'VOLUME' in df.columns else None
                calculated_indicators[name] = values
                df[f'{name}_indicator'] = values
            else:
                values = get_indicator(name, df, extra_indicators if extra_indicators else {})
                calculated_indicators[name] = values
                if values is not None:
                    df[f'{name}_indicator'] = values
                    
        except Exception as e:
            print(f'指标 {name} 计算失败: {e}')
            continue
    
    # 第二轮：应用筛选条件
    for name in all_indicators:
        try:
            if name not in calculated_indicators:
                continue
                
            values = calculated_indicators[name]
            if values is None:
                continue
                
            # 自动适配返回值类型
            if isinstance(values, tuple):
                # KDJ相关，按 name 返回 k/d/j
                if name == 'kdj':
                    values = values[0]  # 默认取K
                elif name == 'k':
                    values = values[0]
                elif name == 'd':
                    values = values[1]
                elif name == 'j':
                    values = values[2]
                else:
                    values = values[0]
            if isinstance(values, pd.DataFrame):
                values = values.iloc[:, 0]
            cond = conditions.get(name, lambda x: True)
            # 如果是价格、成交相关指标，且条件为dict，自动用compare.py
            price_volume_indicators = [
                'net_profit', 'profit_yoy', 'open_price', 'open', 'close_price', 'close',
                'high_price', 'high', 'low_price', 'low', 'avg_price', 'change_rate', 
                'pct_change', 'volume_ratio', 'amount', 'turnover', 'turnover_rate'
            ]
            
            if name in price_volume_indicators and isinstance(cond, dict) and 'op' in cond and 'value' in cond:
                import compare
                op = cond['op']
                val = cond['value']
                print(f"处理指标 {name}: {op} {val}")
                
                if op == '>':
                    mask = compare.greater(values, val)
                elif op == '<':
                    mask = compare.less(values, val)
                elif op == '>=':
                    mask = compare.greater_equal(values, val)
                elif op == '<=':
                    mask = compare.less_equal(values, val)
                elif op == '=':
                    mask = compare.equal(values, val)
                else:
                    mask = pd.Series([True]*len(values), index=values.index)
            else:
                if callable(cond):
                    mask = cond(values)
                else:
                    # 如果条件不是可调用的，则跳过
                    mask = pd.Series([True]*len(values), index=values.index)
            if not isinstance(mask, pd.Series):
                # 确保mask是布尔类型的列表或数组
                try:
                    if hasattr(mask, '__iter__') and not isinstance(mask, (str, bytes)):
                        mask = pd.Series(list(mask), index=df.index)  # type: ignore
                    else:
                        mask = pd.Series([bool(mask)] * len(df), index=df.index)
                except (TypeError, ValueError):
                    # 如果转换失败，默认为 True
                    mask = pd.Series([True] * len(df), index=df.index)
            # 确保mask和result_mask的索引匹配
            mask = mask.reindex(df.index, fill_value=False)
            result_mask &= mask
        except Exception as e:
            print(f'指标 {name} 加载失败: {e}')
    return df[result_mask]

# 示例用法

if __name__ == '__main__':
    import sys, json, os
    # 支持前端传递参数：指标、条件、时间区间、数据路径
    indicator_names = os.environ.get('INDICATORS')
    if indicator_names:
        try:
            indicator_names = json.loads(indicator_names)
        except:
            indicator_names = indicator_names.split(',')
    else:
        indicator_names = []
    conditions_str = os.environ.get('CONDITIONS')
    if conditions_str:
        conditions = json.loads(conditions_str)
        # 支持前端传递比较表达式，如 {'OPEN': {'op': '>', 'value': 10}}
        for k, v in conditions.items():
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
        conditions = {}
    start_date = os.environ.get('START_DATE')
    end_date = os.environ.get('END_DATE')
    extra = {}
    if start_date:
        extra['start_date'] = start_date
    if end_date:
        extra['end_date'] = end_date
    # 数据库配置
    mysql_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '9',
        'database': 'stock',
        'table': 'quotes',
        'charset': 'utf8mb4'
    }
    print(f'MySQL配置: {mysql_config}')
    print(f'指标: {indicator_names}')
    print(f'条件: {conditions_str}')
    print(f'时间区间: {extra}')
    # 读取数据库数据
    df = get_mysql_df(
        host=mysql_config['host'],
        user=mysql_config['user'],
        password=mysql_config['password'],
        database=mysql_config['database'],
        table=mysql_config['table'],
        charset=mysql_config['charset']
    )
    df = df.rename(columns={
        'price': 'CLOSE',
        'close': 'CLOSE',
        'open': 'OPEN',
        'high': 'HIGH',
        'low': 'LOW',
        'volume': 'VOLUME',
        'amount': 'AMOUNT',     # 成交额
        'turnover': 'AMOUNT',   # 成交额别名
        'avg_price': 'AVG_PRICE',  # 日成交均价
        'change_rate': 'CHANGE_RATE',  # 涨幅
        'pct_change': 'CHANGE_RATE',   # 涨幅别名
        'volume_ratio': 'VOLUME_RATIO',  # 量比
        'turnover_rate': 'TURNOVER_RATE',  # 换手率
        'total_share': 'TOTAL_SHARE'   # 流通股本
    })
    
    # 计算衍生字段（如果原始数据没有的话）
    if 'AVG_PRICE' not in df.columns and 'AMOUNT' in df.columns and 'VOLUME' in df.columns:
        # 日成交均价 = 成交额 / 成交量
        volume_nonzero = df['VOLUME'].replace(0, 1)
        df['AVG_PRICE'] = df['AMOUNT'] / volume_nonzero
    
    if 'CHANGE_RATE' not in df.columns and 'CLOSE' in df.columns:
        # 计算涨幅
        prev_close = df['CLOSE'].shift(1)
        df['CHANGE_RATE'] = ((df['CLOSE'] - prev_close) / prev_close * 100).fillna(0)
    
    if 'VOLUME_RATIO' not in df.columns and 'VOLUME' in df.columns:
        # 计算量比
        avg_volume_5 = df['VOLUME'].rolling(window=5).mean()
        df['VOLUME_RATIO'] = (df['VOLUME'] / avg_volume_5).fillna(1)
    
    if 'AMOUNT' not in df.columns and 'CLOSE' in df.columns and 'VOLUME' in df.columns:
        # 计算成交额
        df['AMOUNT'] = df['CLOSE'] * df['VOLUME']
    
    if 'TURNOVER_RATE' not in df.columns and 'VOLUME' in df.columns and 'TOTAL_SHARE' in df.columns:
        # 计算换手率
        df['TURNOVER_RATE'] = (df['VOLUME'] / df['TOTAL_SHARE'] * 100).fillna(0)
    # 合并所有比较结果到 DataFrame
    compare_results = {}
    for field, cond_func in conditions.items():
        if field in df.columns:
            compare_results[f'{field}_compare_result'] = df[field].apply(cond_func)
    
    # 合并比较结果到 df
    for col, result in compare_results.items():
        df[col] = result
    
    # 应用筛选条件
    if compare_results:
        # 获取所有比较结果列
        condition_columns = list(compare_results.keys())
        # 创建布尔索引：所有条件都为True的行
        if condition_columns:
            mask = df[condition_columns[0]]
            for col in condition_columns[1:]:
                mask = mask & df[col]
            df_filtered = df[mask]
        else:
            df_filtered = df.copy()
    else:
        df_filtered = df.copy()
    
    # 输出所有字段比较结果到前端（控制台）
    if compare_results:
        print('所有字段比较结果（筛选后）:')
        print(df_filtered[[col for col in compare_results.keys() if col in df_filtered.columns]])
    
    log_path = '/home/liu/桌面/stock-main/backend/filter_stocks_result.log'
    df_filtered.to_csv(log_path, index=False, encoding='utf-8')
    print(f'筛选结果已保存到: {log_path}')


def aggregate_to_weekly(df, start_date=None, end_date=None):
    """
    将日K线数据聚合为周K线
    
    Args:
        df: 数据DataFrame
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    """
    try:
        df = df.copy()
        
        # 确保有日期列
        if 'date' not in df.columns and 'DATE' not in df.columns:
            print("警告：没有找到日期列，无法进行周聚合")
            return df
            
        date_col = 'date' if 'date' in df.columns else 'DATE'
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 如果提供了日期范围，先进行筛选
        if start_date is not None:
            # 确保start_date是pandas datetime类型
            start_date = pd.to_datetime(start_date)
            df = df[df[date_col] >= start_date]
            
        if end_date is not None:
            # 确保end_date是pandas datetime类型
            end_date = pd.to_datetime(end_date)
            df = df[df[date_col] <= end_date]
        
        df.set_index(date_col, inplace=True)
        
        # 周聚合规则
        agg_rules = {
            'OPEN': 'first',     # 开盘价取第一天
            'open': 'first',
            'HIGH': 'max',       # 最高价取最大值
            'high': 'max',
            'LOW': 'min',        # 最低价取最小值
            'low': 'min',
            'CLOSE': 'last',     # 收盘价取最后一天
            'close': 'last',
            'VOLUME': 'sum',     # 成交量累加
            'volume': 'sum',
            'AMOUNT': 'sum',     # 成交额累加
            'amount': 'sum',
            'turnover': 'sum',
            'code': 'first',     # 股票代码取第一个
            'name': 'first',     # 股票名称取第一个
            'change': 'last',    # 变化额取最后一天
            'change_rate': 'last', # 变化率取最后一天
            'amplitude': 'max',   # 振幅取最大值
            'turnover_rate': 'sum' # 换手率累加
        }
        
        # 只聚合存在的列
        existing_agg_rules = {k: v for k, v in agg_rules.items() if k in df.columns}
        
        if existing_agg_rules:
            # 按股票代码分组进行聚合
            if 'code' in df.columns:
                # 先按code分组，再对每组进行周聚合
                grouped_dfs = []
                for code, group in df.groupby('code'):
                    group_copy = group.copy()
                    # 对每只股票单独进行周聚合
                    weekly_group = group_copy.resample('W').agg(existing_agg_rules)
                    weekly_group.reset_index(inplace=True)
                    # 确保股票代码正确传递
                    weekly_group['code'] = code
                    if 'name' in group_copy.columns:
                        weekly_group['name'] = group_copy['name'].iloc[0]
                    grouped_dfs.append(weekly_group)
                
                if grouped_dfs:
                    weekly_df = pd.concat(grouped_dfs, ignore_index=True)
                    print(f"成功将 {len(df)} 行日数据聚合为 {len(weekly_df)} 行周数据")
                    return weekly_df
            else:
                weekly_df = df.resample('W').agg(existing_agg_rules)
                weekly_df.reset_index(inplace=True)
                print(f"成功将 {len(df)} 行日数据聚合为 {len(weekly_df)} 行周数据")
                return weekly_df
        else:
            print("警告：没有找到可聚合的OHLCV列")
            return df
            
    except Exception as e:
        print(f"周聚合失败: {e}")
        print(f"错误详细信息: start_date类型={type(start_date)}, end_date类型={type(end_date)}")
        import traceback
        traceback.print_exc()
        return df


def aggregate_to_monthly(df, start_date=None, end_date=None):
    """
    将日K线数据聚合为月K线
    
    Args:
        df: 数据DataFrame
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    """
    try:
        df = df.copy()
        
        # 确保有日期列
        if 'date' not in df.columns and 'DATE' not in df.columns:
            print("警告：没有找到日期列，无法进行月聚合")
            return df
            
        date_col = 'date' if 'date' in df.columns else 'DATE'
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 如果提供了日期范围，先进行筛选
        if start_date is not None:
            # 确保start_date是pandas datetime类型
            start_date = pd.to_datetime(start_date)
            df = df[df[date_col] >= start_date]
            
        if end_date is not None:
            # 确保end_date是pandas datetime类型
            end_date = pd.to_datetime(end_date)
            df = df[df[date_col] <= end_date]
        
        df.set_index(date_col, inplace=True)
        
        # 月聚合规则
        agg_rules = {
            'OPEN': 'first',     # 开盘价取第一天
            'open': 'first',
            'HIGH': 'max',       # 最高价取最大值
            'high': 'max',
            'LOW': 'min',        # 最低价取最小值
            'low': 'min',
            'CLOSE': 'last',     # 收盘价取最后一天
            'close': 'last',
            'VOLUME': 'sum',     # 成交量累加
            'volume': 'sum',
            'AMOUNT': 'sum',     # 成交额累加
            'amount': 'sum',
            'turnover': 'sum',
            'code': 'first',     # 股票代码取第一个
            'name': 'first',     # 股票名称取第一个
            'change': 'last',    # 变化额取最后一天
            'change_rate': 'last', # 变化率取最后一天
            'amplitude': 'max',   # 振幅取最大值
            'turnover_rate': 'sum' # 换手率累加
        }
        
        # 只聚合存在的列
        existing_agg_rules = {k: v for k, v in agg_rules.items() if k in df.columns}
        
        if existing_agg_rules:
            # 按股票代码分组进行聚合
            if 'code' in df.columns:
                # 先按code分组，再对每组进行月聚合
                grouped_dfs = []
                for code, group in df.groupby('code'):
                    group_copy = group.copy()
                    # 对每只股票单独进行月聚合
                    monthly_group = group_copy.resample('ME').agg(existing_agg_rules)
                    monthly_group.reset_index(inplace=True)
                    # 确保股票代码正确传递
                    monthly_group['code'] = code
                    if 'name' in group_copy.columns:
                        monthly_group['name'] = group_copy['name'].iloc[0]
                    grouped_dfs.append(monthly_group)
                
                if grouped_dfs:
                    monthly_df = pd.concat(grouped_dfs, ignore_index=True)
                    print(f"成功将 {len(df)} 行日数据聚合为 {len(monthly_df)} 行月数据")
                    return monthly_df
            else:
                monthly_df = df.resample('ME').agg(existing_agg_rules)
                monthly_df.reset_index(inplace=True)
                print(f"成功将 {len(df)} 行日数据聚合为 {len(monthly_df)} 行月数据")
                return monthly_df
        else:
            print("警告：没有找到可聚合的OHLCV列")
            return df
            
    except Exception as e:
        print(f"月聚合失败: {e}")
        print(f"错误详细信息: start_date类型={type(start_date)}, end_date类型={type(end_date)}")
        import traceback
        traceback.print_exc()
        return df


def aggregate_to_yearly(df, start_date=None, end_date=None):
    """
    将日K线数据聚合为年K线
    
    Args:
        df: 数据DataFrame
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    """
    try:
        df = df.copy()
        
        # 确保有日期列
        if 'date' not in df.columns and 'DATE' not in df.columns:
            print("警告：没有找到日期列，无法进行年聚合")
            return df
            
        date_col = 'date' if 'date' in df.columns else 'DATE'
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 如果提供了日期范围，先进行筛选
        if start_date is not None:
            # 确保start_date是pandas datetime类型
            start_date = pd.to_datetime(start_date)
            df = df[df[date_col] >= start_date]
            
        if end_date is not None:
            # 确保end_date是pandas datetime类型
            end_date = pd.to_datetime(end_date)
            df = df[df[date_col] <= end_date]
        
        df.set_index(date_col, inplace=True)
        
        # 年聚合规则
        agg_rules = {
            'OPEN': 'first',     # 开盘价取第一天
            'open': 'first',
            'HIGH': 'max',       # 最高价取最大值
            'high': 'max',
            'LOW': 'min',        # 最低价取最小值
            'low': 'min',
            'CLOSE': 'last',     # 收盘价取最后一天
            'close': 'last',
            'VOLUME': 'sum',     # 成交量累加
            'volume': 'sum',
            'AMOUNT': 'sum',     # 成交额累加
            'amount': 'sum',
            'turnover': 'sum',
            'code': 'first',     # 股票代码取第一个
            'name': 'first',     # 股票名称取第一个
            'change': 'last',    # 变化额取最后一天
            'change_rate': 'last', # 变化率取最后一天
            'amplitude': 'max',   # 振幅取最大值
            'turnover_rate': 'sum' # 换手率累加
        }
        
        # 只聚合存在的列
        existing_agg_rules = {k: v for k, v in agg_rules.items() if k in df.columns}
        
        if existing_agg_rules:
            # 按股票代码分组进行聚合
            if 'code' in df.columns:
                # 先按code分组，再对每组进行年聚合
                grouped_dfs = []
                for code, group in df.groupby('code'):
                    group_copy = group.copy()
                    # 对每只股票单独进行年聚合
                    yearly_group = group_copy.resample('YE').agg(existing_agg_rules)
                    yearly_group.reset_index(inplace=True)
                    # 确保股票代码正确传递
                    yearly_group['code'] = code
                    if 'name' in group_copy.columns:
                        yearly_group['name'] = group_copy['name'].iloc[0]
                    grouped_dfs.append(yearly_group)
                
                if grouped_dfs:
                    yearly_df = pd.concat(grouped_dfs, ignore_index=True)
                    print(f"成功将 {len(df)} 行日数据聚合为 {len(yearly_df)} 行年数据")
                    return yearly_df
            else:
                yearly_df = df.resample('YE').agg(existing_agg_rules)
                yearly_df.reset_index(inplace=True)
                print(f"成功将 {len(df)} 行日数据聚合为 {len(yearly_df)} 行年数据")
                return yearly_df
        else:
            print("警告：没有找到可聚合的OHLCV列")
            return df
            
    except Exception as e:
        print(f"年聚合失败: {e}")
        print(f"错误详细信息: start_date类型={type(start_date)}, end_date类型={type(end_date)}")
        import traceback
        traceback.print_exc()
        return df


def compress_stock_results(df, compress_by_stock=True):
    """
    压缩股票筛选结果，将同一只股票的多条记录合并为一条
    
    Args:
        df: 筛选结果DataFrame
        compress_by_stock: 是否按股票代码压缩，默认True
    
    Returns:
        压缩后的DataFrame和统计信息
    """
    if not compress_by_stock or len(df) == 0:
        return df, {
            'compressed': False,
            'original_records': len(df),
            'unique_stocks': len(df['code'].unique()) if 'code' in df.columns else 0,
            'compression_ratio': 1.0
        }
    
    try:
        # 确保有股票代码列
        if 'code' not in df.columns:
            print("警告：没有找到股票代码列，无法进行压缩")
            return df, {
                'compressed': False,
                'original_records': len(df),
                'unique_stocks': 0,
                'compression_ratio': 1.0
            }
        
        print(f"开始压缩股票结果，原始记录数: {len(df)}")
        
        # 按股票代码分组
        compressed_results = []
        compression_stats = {
            'stock_details': {}
        }
        
        for code, group in df.groupby('code'):
            # 获取该股票的基本信息（取最新的记录）
            if 'date' in group.columns:
                # 按日期排序，取最新的记录作为基准
                group_sorted = group.sort_values('date', ascending=False)
                latest_record = group_sorted.iloc[0].copy()
            else:
                # 如果没有日期列，取第一条记录
                latest_record = group.iloc[0].copy()
            
            # 添加统计信息
            latest_record['data_points'] = len(group)  # 该股票的数据点数量
            latest_record['date_range_start'] = group['date'].min() if 'date' in group.columns else None
            latest_record['date_range_end'] = group['date'].max() if 'date' in group.columns else None
            
            # 计算该股票在时间范围内的统计指标
            if 'close' in group.columns:
                latest_record['period_high'] = group['close'].max()
                latest_record['period_low'] = group['close'].min()
                latest_record['period_avg'] = group['close'].mean()
            
            # 保留指标的平均值（如果有的话）
            indicator_columns = [col for col in group.columns if col.startswith(('ma', 'macd', 'kdj', 'rsi', 'boll', 'cci', 'wr'))]
            for col in indicator_columns:
                if group[col].notna().any():
                    latest_record[f'{col}_avg'] = group[col].mean()
                    latest_record[f'{col}_latest'] = group[col].iloc[-1] if not group[col].isna().all() else None
            
            compressed_results.append(latest_record)
            
            # 记录压缩统计信息
            compression_stats['stock_details'][code] = {
                'original_records': len(group),
                'date_range': f"{group['date'].min()} 至 {group['date'].max()}" if 'date' in group.columns else "无日期信息"
            }
        
        # 创建压缩后的DataFrame
        if compressed_results:
            compressed_df = pd.DataFrame(compressed_results)
        else:
            compressed_df = pd.DataFrame()
        
        # 计算压缩统计信息
        original_count = len(df)
        compressed_count = len(compressed_df)
        unique_stocks = len(df['code'].unique())
        
        stats = {
            'compressed': True,
            'original_records': original_count,
            'compressed_records': compressed_count,
            'unique_stocks': unique_stocks,
            'compression_ratio': original_count / compressed_count if compressed_count > 0 else 0,
            'compression_details': compression_stats['stock_details']
        }
        
        print(f"压缩完成: {original_count} 条记录 → {compressed_count} 条记录 (压缩比: {stats['compression_ratio']:.1f}:1)")
        print(f"涉及 {unique_stocks} 只不同股票")
        
        return compressed_df, stats
        
    except Exception as e:
        print(f"压缩股票结果时出错: {e}")
        import traceback
        traceback.print_exc()
        return df, {
            'compressed': False,
            'original_records': len(df),
            'unique_stocks': len(df['code'].unique()) if 'code' in df.columns else 0,
            'compression_ratio': 1.0,
            'error': str(e)
        }


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
