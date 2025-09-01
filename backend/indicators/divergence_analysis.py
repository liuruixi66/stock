"""
技术指标背离分析模块
包含MACD、KDJ等指标的顶底背离识别功能
"""
import pandas as pd
import numpy as np
from scipy.signal import find_peaks, find_peaks_cwt
from .macd import calculate as calculate_macd
from .kdj import kdj as calculate_kdj


def find_price_peaks_and_troughs(prices, window=5, prominence=0.01):
    """
    寻找价格的峰值和谷值
    
    Args:
        prices: 价格序列
        window: 窗口大小
        prominence: 峰值显著性
    
    Returns:
        peaks, troughs: 峰值和谷值的索引
    """
    # 标准化价格数据
    price_norm = (prices - prices.min()) / (prices.max() - prices.min())
    
    # 寻找峰值
    peaks, _ = find_peaks(price_norm, distance=window, prominence=prominence)
    
    # 寻找谷值（负峰值）
    troughs, _ = find_peaks(-price_norm, distance=window, prominence=prominence)
    
    return peaks, troughs


def find_indicator_peaks_and_troughs(indicator, window=5, prominence=0.01):
    """
    寻找指标的峰值和谷值
    """
    # 标准化指标数据
    indicator_norm = (indicator - indicator.min()) / (indicator.max() - indicator.min())
    
    # 寻找峰值
    peaks, _ = find_peaks(indicator_norm, distance=window, prominence=prominence)
    
    # 寻找谷值
    troughs, _ = find_peaks(-indicator_norm, distance=window, prominence=prominence)
    
    return peaks, troughs


def analyze_macd_divergence(df, short=12, long=26, signal=9, window=5):
    """
    MACD背离分析
    
    Args:
        df: 包含OHLC数据的DataFrame
        short, long, signal: MACD参数
        window: 峰谷检测窗口
    
    Returns:
        dict: 包含背离分析结果的字典
    """
    try:
        # 计算MACD
        dif, dea, macd = calculate_macd(df, short, long, signal)
        
        # 获取价格数据 - 修复列名问题
        if 'CLOSE' in df.columns:
            close_col = 'CLOSE'
        elif 'close' in df.columns:
            close_col = 'close'
        else:
            available_cols = list(df.columns)
            raise ValueError(f"找不到收盘价列，可用列: {available_cols}")
        
        prices = df[close_col].values
        
        # 寻找价格和MACD的峰谷
        price_peaks, price_troughs = find_price_peaks_and_troughs(prices, window)
        macd_peaks, macd_troughs = find_price_peaks_and_troughs(macd.values, window)
        
        # 分析顶背离（价格高点上升，MACD高点下降）
        top_divergence = []
        if len(price_peaks) >= 2 and len(macd_peaks) >= 2:
            for i in range(1, min(len(price_peaks), len(macd_peaks))):
                price_trend = prices[price_peaks[i]] - prices[price_peaks[i-1]]
                macd_trend = macd.iloc[macd_peaks[i]] - macd.iloc[macd_peaks[i-1]]
                
                if price_trend > 0 and macd_trend < 0:  # 顶背离
                    top_divergence.append({
                        'index': price_peaks[i],
                        'type': 'bearish_divergence',
                        'strength': abs(macd_trend / price_trend) if price_trend != 0 else 0
                    })
        
        # 分析底背离（价格低点下降，MACD低点上升）
        bottom_divergence = []
        if len(price_troughs) >= 2 and len(macd_troughs) >= 2:
            for i in range(1, min(len(price_troughs), len(macd_troughs))):
                price_trend = prices[price_troughs[i]] - prices[price_troughs[i-1]]
                macd_trend = macd.iloc[macd_troughs[i]] - macd.iloc[macd_troughs[i-1]]
                
                if price_trend < 0 and macd_trend > 0:  # 底背离
                    bottom_divergence.append({
                        'index': price_troughs[i],
                        'type': 'bullish_divergence',
                        'strength': abs(macd_trend / price_trend) if price_trend != 0 else 0
                    })
        
        return {
            'top_divergence': top_divergence,
            'bottom_divergence': bottom_divergence,
            'macd_data': {
                'dif': dif.tolist(),
                'dea': dea.tolist(),
                'macd': macd.tolist()
            }
        }
        
    except Exception as e:
        return {
            'error': f'MACD背离分析错误: {str(e)}',
            'top_divergence': [],
            'bottom_divergence': [],
            'macd_data': {}
        }


def analyze_kdj_divergence(df, n=9, k_factor=2/3, d_factor=2/3, window=5):
    """
    KDJ背离分析
    
    Args:
        df: 包含OHLC数据的DataFrame
        n, k_factor, d_factor: KDJ参数
        window: 峰谷检测窗口
    
    Returns:
        dict: 包含背离分析结果的字典
    """
    try:
        # 计算KDJ
        k, d, j = calculate_kdj(df, n, int(1/k_factor), int(1/d_factor))
        
        # 获取价格数据 - 修复列名问题
        if 'CLOSE' in df.columns:
            close_col = 'CLOSE'
        elif 'close' in df.columns:
            close_col = 'close'
        else:
            available_cols = list(df.columns)
            raise ValueError(f"找不到收盘价列，可用列: {available_cols}")
        
        prices = df[close_col].values
        
        # 寻找价格和KDJ的峰谷
        price_peaks, price_troughs = find_price_peaks_and_troughs(prices, window)
        k_peaks, k_troughs = find_price_peaks_and_troughs(k.values, window)
        d_peaks, d_troughs = find_price_peaks_and_troughs(d.values, window)
        
        # 分析K线顶背离
        k_top_divergence = []
        if len(price_peaks) >= 2 and len(k_peaks) >= 2:
            for i in range(1, min(len(price_peaks), len(k_peaks))):
                price_trend = prices[price_peaks[i]] - prices[price_peaks[i-1]]
                k_trend = k.iloc[k_peaks[i]] - k.iloc[k_peaks[i-1]]
                
                if price_trend > 0 and k_trend < 0:
                    k_top_divergence.append({
                        'index': price_peaks[i],
                        'type': 'bearish_divergence',
                        'strength': abs(k_trend / price_trend) if price_trend != 0 else 0
                    })
        
        # 分析K线底背离
        k_bottom_divergence = []
        if len(price_troughs) >= 2 and len(k_troughs) >= 2:
            for i in range(1, min(len(price_troughs), len(k_troughs))):
                price_trend = prices[price_troughs[i]] - prices[price_troughs[i-1]]
                k_trend = k.iloc[k_troughs[i]] - k.iloc[k_troughs[i-1]]
                
                if price_trend < 0 and k_trend > 0:
                    k_bottom_divergence.append({
                        'index': price_troughs[i],
                        'type': 'bullish_divergence',
                        'strength': abs(k_trend / price_trend) if price_trend != 0 else 0
                    })
        
        return {
            'k_top_divergence': k_top_divergence,
            'k_bottom_divergence': k_bottom_divergence,
            'd_top_divergence': [],  # 可以类似实现D线背离
            'd_bottom_divergence': [],
            'kdj_data': {
                'k': k.tolist(),
                'd': d.tolist(),
                'j': j.tolist()
            }
        }
        
    except Exception as e:
        return {
            'error': f'KDJ背离分析错误: {str(e)}',
            'k_top_divergence': [],
            'k_bottom_divergence': [],
            'd_top_divergence': [],
            'd_bottom_divergence': [],
            'kdj_data': {}
        }


def analyze_trend_signals(df, short=12, long=26, signal=9, n=9):
    """
    分析多头空头信号
    
    Args:
        df: 股票数据
        short, long, signal: MACD参数
        n: KDJ参数
    
    Returns:
        dict: 趋势信号分析结果
    """
    try:
        # 计算MACD
        dif, dea, macd = calculate_macd(df, short, long, signal)
        
        # 计算KDJ
        k, d, j = calculate_kdj(df, n)
        
        signals = []
        
        for i in range(1, len(df)):
            current_signals = []  # 当前时刻可能有多个信号
            
            # MACD金叉死叉信号检测
            if dif.iloc[i] > dea.iloc[i] and dif.iloc[i-1] <= dea.iloc[i-1]:
                current_signals.append({
                    'type': 'macd_golden_cross',
                    'strength': abs(dif.iloc[i] - dea.iloc[i])
                })
            elif dif.iloc[i] < dea.iloc[i] and dif.iloc[i-1] >= dea.iloc[i-1]:
                current_signals.append({
                    'type': 'macd_death_cross',
                    'strength': abs(dif.iloc[i] - dea.iloc[i])
                })
            
            # KDJ金叉死叉信号检测
            if k.iloc[i] > d.iloc[i] and k.iloc[i-1] <= d.iloc[i-1]:
                if k.iloc[i] < 20:  # 低位金叉
                    current_signals.append({
                        'type': 'kdj_golden_cross_low',
                        'strength': 20 - k.iloc[i]
                    })
                else:
                    current_signals.append({
                        'type': 'kdj_golden_cross',
                        'strength': abs(k.iloc[i] - d.iloc[i])
                    })
            elif k.iloc[i] < d.iloc[i] and k.iloc[i-1] >= d.iloc[i-1]:
                if k.iloc[i] > 80:  # 高位死叉
                    current_signals.append({
                        'type': 'kdj_death_cross_high',
                        'strength': k.iloc[i] - 80
                    })
                else:
                    current_signals.append({
                        'type': 'kdj_death_cross',
                        'strength': abs(k.iloc[i] - d.iloc[i])
                    })
            
            # 超买超卖信号检测（独立检测，可与其他信号并存）
            if k.iloc[i] > 80 and d.iloc[i] > 80:
                current_signals.append({
                    'type': 'overbought',
                    'strength': min(k.iloc[i], d.iloc[i]) - 80
                })
            elif k.iloc[i] < 20 and d.iloc[i] < 20:
                current_signals.append({
                    'type': 'oversold',
                    'strength': 20 - max(k.iloc[i], d.iloc[i])
                })
            
            # 将所有检测到的信号添加到结果中
            for signal_info in current_signals:
                signals.append({
                    'index': i,
                    'date': df.index[i] if hasattr(df.index[i], 'strftime') else str(df.index[i]),
                    'type': signal_info['type'],
                    'strength': float(signal_info['strength']),
                    'price': float(df.iloc[i]['close'] if 'close' in df.columns else df.iloc[i]['CLOSE'])
                })
        
        return {
            'signals': signals,
            'signal_summary': {
                'bullish_signals': len([s for s in signals if 'golden' in s['type'] or s['type'] == 'oversold']),
                'bearish_signals': len([s for s in signals if 'death' in s['type'] or s['type'] == 'overbought']),
                'total_signals': len(signals)
            }
        }
        
    except Exception as e:
        return {
            'error': f'趋势信号分析错误: {str(e)}',
            'signals': [],
            'signal_summary': {
                'bullish_signals': 0,
                'bearish_signals': 0,
                'total_signals': 0
            }
        }
