#!/usr/bin/env python3
"""
详细分析交易数据，找出计算错误的原因
"""

import json
import pandas as pd
from datetime import datetime

def analyze_trades():
    """详细分析交易数据"""
    
    # 加载数据
    with open('/home/liu/桌面/stock-20250730_update./backend/cache/earnings_overview_latest_equal_weight.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    trades = data.get('trades', [])
    initial_cash = data['strategy_info']['initial_cash']
    
    print(f"🔍 详细交易分析")
    print(f"初始资金: {initial_cash:,.2f}")
    print(f"交易总数: {len(trades)}")
    
    # 转换为DataFrame
    df = pd.DataFrame(trades)
    df['amount'] = pd.to_numeric(df['amount'])
    df['price'] = pd.to_numeric(df['price'])
    df['shares'] = pd.to_numeric(df['shares'])
    
    print(f"\n📊 交易概况:")
    buy_trades = df[df['action'] == 'buy']
    sell_trades = df[df['action'] == 'sell']
    
    print(f"买入交易: {len(buy_trades)}笔")
    print(f"卖出交易: {len(sell_trades)}笔")
    
    # 按股票分组分析
    print(f"\n📈 按股票分析:")
    for stock in df['stock_code'].unique():
        stock_trades = df[df['stock_code'] == stock]
        buy_amount = stock_trades[stock_trades['action'] == 'buy']['amount'].sum()
        sell_amount = stock_trades[stock_trades['action'] == 'sell']['amount'].sum()
        buy_shares = stock_trades[stock_trades['action'] == 'buy']['shares'].sum()
        sell_shares = stock_trades[stock_trades['action'] == 'sell']['shares'].sum()
        
        print(f"\n股票 {stock}:")
        print(f"  买入: {buy_shares}股, 金额: {buy_amount:,.2f}")
        print(f"  卖出: {sell_shares}股, 金额: {sell_amount:,.2f}")
        print(f"  盈亏: {sell_amount - buy_amount:,.2f}")
        if buy_amount > 0:
            profit_rate = (sell_amount - buy_amount) / buy_amount
            print(f"  收益率: {profit_rate:.2%}")
    
    # 按时间分析现金流
    print(f"\n💰 现金流分析:")
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df = df.sort_values('date')
    
    cash = initial_cash
    print(f"初始现金: {cash:,.2f}")
    
    for i, (_, trade) in enumerate(df.iterrows()):
        if trade['action'] == 'buy':
            cash -= trade['amount']
            print(f"{trade['date'].strftime('%Y-%m-%d')} 买入{trade['stock_code']} {trade['shares']}股 -{trade['amount']:,.2f} 余额:{cash:,.2f}")
        else:
            cash += trade['amount']
            print(f"{trade['date'].strftime('%Y-%m-%d')} 卖出{trade['stock_code']} {trade['shares']}股 +{trade['amount']:,.2f} 余额:{cash:,.2f}")
        
        # 检查是否出现负现金
        if cash < 0:
            print(f"⚠️ 警告：现金余额为负 {cash:,.2f}")
    
    print(f"\n最终现金: {cash:,.2f}")
    final_return = (cash - initial_cash) / initial_cash
    print(f"总收益率: {final_return:.2%}")
    
    # 检查等权重策略的逻辑
    print(f"\n🔍 等权重策略验证:")
    
    # 按日期分组看再平衡
    buy_dates = buy_trades['date'].unique()
    for date in sorted(buy_dates):
        date_trades = buy_trades[buy_trades['date'] == date]
        total_amount = date_trades['amount'].sum()
        print(f"\n{pd.to_datetime(date, format='%Y%m%d').strftime('%Y-%m-%d')} 再平衡:")
        print(f"  总投入: {total_amount:,.2f}")
        print(f"  平均每股: {total_amount / len(date_trades):,.2f}")
        
        for _, trade in date_trades.iterrows():
            weight = trade['amount'] / total_amount
            print(f"    {trade['stock_code']}: {trade['amount']:,.2f} ({weight:.1%})")

if __name__ == "__main__":
    analyze_trades()
