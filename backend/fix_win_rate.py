#!/usr/bin/env python3
"""
修复胜率计算错误
"""

import json

def fix_win_rate():
    """修复胜率计算"""
    
    # 加载数据
    with open('/home/liu/桌面/stock-20250730_update./backend/cache/earnings_overview_latest_equal_weight.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    trades = data['trades']
    
    print("🔧 修复胜率计算...")
    
    # 按股票分组分析
    stocks = {}
    for trade in trades:
        stock = trade['stock_code']
        if stock not in stocks:
            stocks[stock] = {'buy': [], 'sell': []}
        stocks[stock][trade['action']].append(trade)
    
    profitable_count = 0
    loss_count = 0
    total_positions = 0
    
    print("\n📊 个股盈亏分析:")
    for stock, stock_trades in stocks.items():
        buys = stock_trades['buy']
        sells = stock_trades['sell']
        
        if buys and sells:
            total_positions += 1
            total_buy_amount = sum(t['amount'] for t in buys)
            total_sell_amount = sum(t['amount'] for t in sells)
            profit_loss = total_sell_amount - total_buy_amount
            profit_loss_pct = profit_loss / total_buy_amount * 100
            
            is_profitable = profit_loss > 0
            if is_profitable:
                profitable_count += 1
            else:
                loss_count += 1
            
            print(f"{stock}: {profit_loss_pct:+.2f}% ({'盈利' if is_profitable else '亏损'})")
    
    # 计算正确的胜率
    win_rate = profitable_count / total_positions if total_positions > 0 else 0
    
    print(f"\n📈 胜率统计:")
    print(f"盈利头寸: {profitable_count}")
    print(f"亏损头寸: {loss_count}")
    print(f"总头寸: {total_positions}")
    print(f"胜率: {win_rate:.2%}")
    
    # 计算盈亏比
    profitable_trades = []
    loss_trades = []
    
    for stock, stock_trades in stocks.items():
        buys = stock_trades['buy']
        sells = stock_trades['sell']
        
        if buys and sells:
            total_buy_amount = sum(t['amount'] for t in buys)
            total_sell_amount = sum(t['amount'] for t in sells)
            profit_loss = total_sell_amount - total_buy_amount
            
            if profit_loss > 0:
                profitable_trades.append(profit_loss)
            else:
                loss_trades.append(abs(profit_loss))
    
    # 计算盈亏比
    if profitable_trades and loss_trades:
        avg_profit = sum(profitable_trades) / len(profitable_trades)
        avg_loss = sum(loss_trades) / len(loss_trades)
        profit_loss_ratio = avg_profit / avg_loss
    else:
        profit_loss_ratio = 0
    
    print(f"平均盈利: {avg_profit:.2f}" if profitable_trades else "平均盈利: 0")
    print(f"平均亏损: {avg_loss:.2f}" if loss_trades else "平均亏损: 0")
    print(f"盈亏比: {profit_loss_ratio:.3f}")
    
    # 更新数据
    data['performance_metrics']['win_rate'] = win_rate
    data['performance_metrics']['profit_count'] = profitable_count
    data['performance_metrics']['loss_count'] = loss_count
    data['performance_metrics']['profit_loss_ratio'] = profit_loss_ratio
    
    # 保存修复后的数据
    with open('/home/liu/桌面/stock-20250730_update./backend/cache/earnings_overview_latest_equal_weight.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 胜率已修复: {win_rate:.2%}")
    print(f"盈亏比已修复: {profit_loss_ratio:.3f}")
    
    return {
        'win_rate': win_rate,
        'profit_count': profitable_count,
        'loss_count': loss_count,
        'profit_loss_ratio': profit_loss_ratio
    }

if __name__ == "__main__":
    result = fix_win_rate()
    print(f"\n📋 修复结果:")
    for key, value in result.items():
        print(f"{key}: {value}")
