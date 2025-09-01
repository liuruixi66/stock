
def validate_ohlc_data(df):
    """
    验证OHLC数据质量的完整规则集
    """
    validation_results = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'statistics': {}
    }
    
    # 规则1: 高价必须 >= max(开盘价, 收盘价)
    high_violations = df[(df['high'] < df['open']) | (df['high'] < df['close'])]
    if len(high_violations) > 0:
        validation_results['is_valid'] = False
        validation_results['errors'].append({
            'rule': 'HIGH_PRICE_RULE',
            'message': f'发现{len(high_violations)}条高价违规记录',
            'violations': high_violations.index.tolist()
        })
    
    # 规则2: 低价必须 <= min(开盘价, 收盘价)
    low_violations = df[(df['low'] > df['open']) | (df['low'] > df['close'])]
    if len(low_violations) > 0:
        validation_results['is_valid'] = False
        validation_results['errors'].append({
            'rule': 'LOW_PRICE_RULE',
            'message': f'发现{len(low_violations)}条低价违规记录',
            'violations': low_violations.index.tolist()
        })
    
    # 规则3: 价格必须为正数
    negative_prices = df[(df['open'] <= 0) | (df['high'] <= 0) | 
                        (df['low'] <= 0) | (df['close'] <= 0)]
    if len(negative_prices) > 0:
        validation_results['is_valid'] = False
        validation_results['errors'].append({
            'rule': 'POSITIVE_PRICE_RULE',
            'message': f'发现{len(negative_prices)}条负价格记录',
            'violations': negative_prices.index.tolist()
        })
    
    # 规则4: 成交量必须为正数
    negative_volume = df[df['volume'] <= 0]
    if len(negative_volume) > 0:
        validation_results['is_valid'] = False
        validation_results['errors'].append({
            'rule': 'POSITIVE_VOLUME_RULE',
            'message': f'发现{len(negative_volume)}条负成交量记录',
            'violations': negative_volume.index.tolist()
        })
    
    # 警告规则: 异常价格波动
    df['price_change'] = df['close'].pct_change()
    extreme_changes = df[abs(df['price_change']) > 0.2]  # 20%以上变动
    if len(extreme_changes) > 0:
        validation_results['warnings'].append({
            'rule': 'EXTREME_PRICE_CHANGE',
            'message': f'发现{len(extreme_changes)}条极端价格变动记录',
            'count': len(extreme_changes)
        })
    
    # 统计信息
    validation_results['statistics'] = {
        'total_records': len(df),
        'high_violations': len(high_violations),
        'low_violations': len(low_violations),
        'negative_prices': len(negative_prices),
        'negative_volume': len(negative_volume),
        'extreme_changes': len(extreme_changes),
        'violation_rate': (len(high_violations) + len(low_violations)) / len(df) * 100
    }
    
    return validation_results

def fix_ohlc_violations(df):
    """
    修复OHLC数据违规问题
    """
    df_fixed = df.copy()
    fixes_applied = []
    
    for idx, row in df_fixed.iterrows():
        original_high = row['high']
        original_low = row['low']
        
        # 修复高价
        correct_high = max(row['open'], row['close'], row['high'])
        if correct_high != original_high:
            df_fixed.at[idx, 'high'] = correct_high
            fixes_applied.append({
                'index': idx,
                'type': 'HIGH_FIX',
                'original': original_high,
                'fixed': correct_high
            })
        
        # 修复低价
        correct_low = min(row['open'], row['close'], row['low'])
        if correct_low != original_low:
            df_fixed.at[idx, 'low'] = correct_low
            fixes_applied.append({
                'index': idx,
                'type': 'LOW_FIX',
                'original': original_low,
                'fixed': correct_low
            })
    
    return df_fixed, fixes_applied
