#!/usr/bin/env python
"""
高级技术分析模块
包含背离分析、多空信号判断等功能
"""
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema

def identify_macd_divergence(df, price_col='close', macd_col='macd', lookback_periods=20):
    """
    识别MACD背离
    
    Args:
        df: 包含价格和MACD数据的DataFrame
        price_col: 价格列名
        macd_col: MACD列名
        lookback_periods: 回看周期数
    
    Returns:
        dict: 包含背离信息的字典
    """
    if len(df) < lookback_periods + 10:
        return {
            'bullish_divergence': False,
            'bearish_divergence': False,
            'divergence_strength': 0,
            'signal': 'neutral'
        }
    
    # 获取最近的数据
    recent_data = df.tail(lookback_periods).copy()
    
    # 找出价格和MACD的局部极值
    price_highs = argrelextrema(recent_data[price_col].values, np.greater, order=3)[0]
    price_lows = argrelextrema(recent_data[price_col].values, np.less, order=3)[0]
    macd_highs = argrelextrema(recent_data[macd_col].values, np.greater, order=3)[0]
    macd_lows = argrelextrema(recent_data[macd_col].values, np.less, order=3)[0]
    
    bullish_divergence = False
    bearish_divergence = False
    divergence_strength = 0
    
    # 检测牛市背离（价格创新低，MACD创新高）
    if len(price_lows) >= 2 and len(macd_lows) >= 2:
        latest_price_low_idx = price_lows[-1]
        prev_price_low_idx = price_lows[-2]
        latest_macd_low_idx = macd_lows[-1]
        prev_macd_low_idx = macd_lows[-2]
        
        latest_price_low = recent_data[price_col].iloc[latest_price_low_idx]
        prev_price_low = recent_data[price_col].iloc[prev_price_low_idx]
        latest_macd_low = recent_data[macd_col].iloc[latest_macd_low_idx]
        prev_macd_low = recent_data[macd_col].iloc[prev_macd_low_idx]
        
        # 价格创新低，但MACD没有创新低（底背离）
        if latest_price_low < prev_price_low and latest_macd_low > prev_macd_low:
            bullish_divergence = True
            divergence_strength = abs(latest_macd_low - prev_macd_low) / abs(prev_macd_low) * 100
    
    # 检测熊市背离（价格创新高，MACD创新低）
    if len(price_highs) >= 2 and len(macd_highs) >= 2:
        latest_price_high_idx = price_highs[-1]
        prev_price_high_idx = price_highs[-2]
        latest_macd_high_idx = macd_highs[-1]
        prev_macd_high_idx = macd_highs[-2]
        
        latest_price_high = recent_data[price_col].iloc[latest_price_high_idx]
        prev_price_high = recent_data[price_col].iloc[prev_price_high_idx]
        latest_macd_high = recent_data[macd_col].iloc[latest_macd_high_idx]
        prev_macd_high = recent_data[macd_col].iloc[prev_macd_high_idx]
        
        # 价格创新高，但MACD没有创新高（顶背离）
        if latest_price_high > prev_price_high and latest_macd_high < prev_macd_high:
            bearish_divergence = True
            divergence_strength = abs(latest_macd_high - prev_macd_high) / abs(prev_macd_high) * 100
    
    # 确定信号
    signal = 'neutral'
    if bullish_divergence:
        signal = 'bullish_divergence'
    elif bearish_divergence:
        signal = 'bearish_divergence'
    
    return {
        'bullish_divergence': bullish_divergence,
        'bearish_divergence': bearish_divergence,
        'divergence_strength': round(divergence_strength, 2),
        'signal': signal
    }

def identify_kdj_divergence(df, price_col='close', kdj_k_col='kdj_k', lookback_periods=20):
    """
    识别KDJ背离
    
    Args:
        df: 包含价格和KDJ数据的DataFrame
        price_col: 价格列名
        kdj_k_col: KDJ K值列名
        lookback_periods: 回看周期数
    
    Returns:
        dict: 包含背离信息的字典
    """
    if len(df) < lookback_periods + 10:
        return {
            'bullish_divergence': False,
            'bearish_divergence': False,
            'divergence_strength': 0,
            'signal': 'neutral'
        }
    
    # 获取最近的数据
    recent_data = df.tail(lookback_periods).copy()
    
    # 找出价格和KDJ K值的局部极值
    price_highs = argrelextrema(recent_data[price_col].values, np.greater, order=3)[0]
    price_lows = argrelextrema(recent_data[price_col].values, np.less, order=3)[0]
    kdj_highs = argrelextrema(recent_data[kdj_k_col].values, np.greater, order=3)[0]
    kdj_lows = argrelextrema(recent_data[kdj_k_col].values, np.less, order=3)[0]
    
    bullish_divergence = False
    bearish_divergence = False
    divergence_strength = 0
    
    # 检测牛市背离
    if len(price_lows) >= 2 and len(kdj_lows) >= 2:
        latest_price_low_idx = price_lows[-1]
        prev_price_low_idx = price_lows[-2]
        latest_kdj_low_idx = kdj_lows[-1]
        prev_kdj_low_idx = kdj_lows[-2]
        
        latest_price_low = recent_data[price_col].iloc[latest_price_low_idx]
        prev_price_low = recent_data[price_col].iloc[prev_price_low_idx]
        latest_kdj_low = recent_data[kdj_k_col].iloc[latest_kdj_low_idx]
        prev_kdj_low = recent_data[kdj_k_col].iloc[prev_kdj_low_idx]
        
        if latest_price_low < prev_price_low and latest_kdj_low > prev_kdj_low:
            bullish_divergence = True
            divergence_strength = abs(latest_kdj_low - prev_kdj_low)
    
    # 检测熊市背离
    if len(price_highs) >= 2 and len(kdj_highs) >= 2:
        latest_price_high_idx = price_highs[-1]
        prev_price_high_idx = price_highs[-2]
        latest_kdj_high_idx = kdj_highs[-1]
        prev_kdj_high_idx = kdj_highs[-2]
        
        latest_price_high = recent_data[price_col].iloc[latest_price_high_idx]
        prev_price_high = recent_data[price_col].iloc[prev_price_high_idx]
        latest_kdj_high = recent_data[kdj_k_col].iloc[latest_kdj_high_idx]
        prev_kdj_high = recent_data[kdj_k_col].iloc[prev_kdj_high_idx]
        
        if latest_price_high > prev_price_high and latest_kdj_high < prev_kdj_high:
            bearish_divergence = True
            divergence_strength = abs(latest_kdj_high - prev_kdj_high)
    
    # 确定信号
    signal = 'neutral'
    if bullish_divergence:
        signal = 'bullish_divergence'
    elif bearish_divergence:
        signal = 'bearish_divergence'
    
    return {
        'bullish_divergence': bullish_divergence,
        'bearish_divergence': bearish_divergence,
        'divergence_strength': round(divergence_strength, 2),
        'signal': signal
    }

def identify_bull_bear_signals(df, macd_col='macd', macd_signal_col='macd_signal', 
                              kdj_k_col='kdj_k', kdj_d_col='kdj_d'):
    """
    识别多头/空头信号
    
    Args:
        df: 数据DataFrame
        macd_col: MACD列名
        macd_signal_col: MACD信号线列名
        kdj_k_col: KDJ K值列名
        kdj_d_col: KDJ D值列名
    
    Returns:
        dict: 包含多空信号的字典
    """
    if len(df) < 3:
        return {
            'macd_signal': 'neutral',
            'kdj_signal': 'neutral',
            'combined_signal': 'neutral',
            'signal_strength': 0
        }
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # MACD多空信号
    macd_signal = 'neutral'
    if latest[macd_col] > latest[macd_signal_col] and prev[macd_col] <= prev[macd_signal_col]:
        macd_signal = 'bullish'  # MACD金叉
    elif latest[macd_col] < latest[macd_signal_col] and prev[macd_col] >= prev[macd_signal_col]:
        macd_signal = 'bearish'  # MACD死叉
    elif latest[macd_col] > latest[macd_signal_col]:
        macd_signal = 'bullish_continuation'  # 多头延续
    elif latest[macd_col] < latest[macd_signal_col]:
        macd_signal = 'bearish_continuation'  # 空头延续
    
    # KDJ多空信号
    kdj_signal = 'neutral'
    if latest[kdj_k_col] > latest[kdj_d_col] and prev[kdj_k_col] <= prev[kdj_d_col]:
        kdj_signal = 'bullish'  # KDJ金叉
    elif latest[kdj_k_col] < latest[kdj_d_col] and prev[kdj_k_col] >= prev[kdj_d_col]:
        kdj_signal = 'bearish'  # KDJ死叉
    elif latest[kdj_k_col] > 80:
        kdj_signal = 'overbought'  # 超买
    elif latest[kdj_k_col] < 20:
        kdj_signal = 'oversold'  # 超卖
    elif latest[kdj_k_col] > latest[kdj_d_col]:
        kdj_signal = 'bullish_continuation'
    elif latest[kdj_k_col] < latest[kdj_d_col]:
        kdj_signal = 'bearish_continuation'
    
    # 综合信号
    bullish_signals = ['bullish', 'bullish_continuation']
    bearish_signals = ['bearish', 'bearish_continuation']
    
    signal_strength = 0
    combined_signal = 'neutral'
    
    if macd_signal in bullish_signals and kdj_signal in bullish_signals:
        combined_signal = 'strong_bullish'
        signal_strength = 2
    elif macd_signal in bearish_signals and kdj_signal in bearish_signals:
        combined_signal = 'strong_bearish'
        signal_strength = -2
    elif macd_signal in bullish_signals or kdj_signal in bullish_signals:
        combined_signal = 'weak_bullish'
        signal_strength = 1
    elif macd_signal in bearish_signals or kdj_signal in bearish_signals:
        combined_signal = 'weak_bearish'
        signal_strength = -1
    
    return {
        'macd_signal': macd_signal,
        'kdj_signal': kdj_signal,
        'combined_signal': combined_signal,
        'signal_strength': signal_strength
    }

def get_market_from_stock_code(stock_code):
    """
    根据股票代码判断所属市场
    
    Args:
        stock_code: 股票代码
    
    Returns:
        str: 'SH' (上海) 或 'SZ' (深圳)
    """
    if not stock_code:
        return 'UNKNOWN'
    
    code = str(stock_code).zfill(6)  # 确保6位数字
    
    # 上海证券交易所
    if code.startswith(('600', '601', '603', '605', '688')):
        return 'SH'  # 上海主板、科创板
    
    # 深圳证券交易所
    elif code.startswith(('000', '002', '003', '300')):
        return 'SZ'  # 深圳主板、中小板、创业板
    
    else:
        return 'UNKNOWN'

def filter_stocks_by_market(df, market='ALL'):
    """
    根据市场筛选股票
    
    Args:
        df: 股票数据DataFrame
        market: 'SH' (上海), 'SZ' (深圳), 'ALL' (全部)
    
    Returns:
        DataFrame: 筛选后的数据
    """
    if market == 'ALL':
        return df
    
    # 为DataFrame添加市场标识
    df['market'] = df['code'].apply(get_market_from_stock_code)
    
    # 根据市场筛选
    filtered_df = df[df['market'] == market].copy()
    
    return filtered_df

def analyze_market_indices(market='SH'):
    """
    分析大盘指数
    
    Args:
        market: 'SH' (上证指数), 'SZ' (深证成指)
    
    Returns:
        dict: 指数分析结果
    """
    # 这里可以添加具体的指数数据获取和分析逻辑
    # 暂时返回模拟数据
    index_codes = {
        'SH': '000001',  # 上证指数
        'SZ': '399001'   # 深证成指
    }
    
    return {
        'market': market,
        'index_code': index_codes.get(market, '000001'),
        'index_name': '上证指数' if market == 'SH' else '深证成指',
        'trend': 'bullish',  # 这里可以添加实际的趋势分析
        'support_level': 3000,  # 支撑位
        'resistance_level': 3200  # 阻力位
    }
