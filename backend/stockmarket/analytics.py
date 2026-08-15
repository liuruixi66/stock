"""模拟盘绩效分析：按 FIFO 配对已成交订单，产出平仓盈亏与统计指标。"""

from __future__ import annotations

from collections import defaultdict, deque
from decimal import Decimal

from market_data import MarketDataError, get_provider

from .models import SimulationAccount, SimulationOrder


def _fifo_realized_pnl(orders: list[SimulationOrder]) -> dict[int, Decimal]:
    """返回 {卖单id: 平仓盈亏}，买入成本含佣金，卖出收入扣佣金与税费。"""
    lots: dict[str, deque[list[Decimal]]] = defaultdict(deque)
    realized: dict[int, Decimal] = {}
    for order in orders:
        price = order.executed_price or Decimal('0')
        quantity = Decimal(order.quantity)
        fee = order.commission + order.tax
        if order.side == 'BUY':
            unit_cost = price + (fee / quantity if quantity else Decimal('0'))
            lots[order.symbol].append([quantity, unit_cost])
            continue
        proceeds = price * quantity - fee
        cost = Decimal('0')
        remaining = quantity
        queue = lots[order.symbol]
        while remaining > 0 and queue:
            lot = queue[0]
            matched = min(remaining, lot[0])
            cost += matched * lot[1]
            lot[0] -= matched
            remaining -= matched
            if lot[0] <= 0:
                queue.popleft()
        if remaining > 0:  # 没有配对到的部分按成交价视为零盈亏
            cost += remaining * price
        realized[order.id] = proceeds - cost
    return realized


def build_account_analytics(account: SimulationAccount) -> dict:
    filled = list(
        SimulationOrder.objects.filter(account=account, status='FILLED').order_by('created_at', 'id')
    )
    realized_map = _fifo_realized_pnl(filled)

    trades = []
    realized_curve = []
    cumulative = Decimal('0')
    win_amounts: list[Decimal] = []
    loss_amounts: list[Decimal] = []
    total_fees = Decimal('0')
    buy_count = sell_count = 0
    for order in filled:
        price = order.executed_price or Decimal('0')
        fee = order.commission + order.tax
        total_fees += fee
        pnl = realized_map.get(order.id)
        if order.side == 'BUY':
            buy_count += 1
        else:
            sell_count += 1
            cumulative += pnl or Decimal('0')
            realized_curve.append({
                'date': order.created_at.date().isoformat(),
                'cumulative_pnl': float(cumulative),
            })
            if pnl is not None and pnl > 0:
                win_amounts.append(pnl)
            elif pnl is not None and pnl < 0:
                loss_amounts.append(pnl)
        trades.append({
            'id': order.id,
            'symbol': order.symbol,
            'side': order.side,
            'order_type': order.order_type,
            'quantity': order.quantity,
            'executed_price': float(price),
            'amount': float(price * order.quantity),
            'commission': float(order.commission),
            'tax': float(order.tax),
            'fee': float(fee),
            'realized_pnl': float(pnl) if pnl is not None else None,
            'message': order.message,
            'created_at': order.created_at.isoformat(),
        })
    trades.reverse()

    provider = get_provider(account.market)
    positions = []
    market_value = Decimal('0')
    unrealized = Decimal('0')
    for position in account.positions.all():
        try:
            current_price = Decimal(str(provider.get_quote(position.symbol).price))
        except MarketDataError:
            current_price = position.average_price
        value = current_price * position.quantity
        market_value += value
        pnl = (current_price - position.average_price) * position.quantity
        unrealized += pnl
        positions.append({
            'symbol': position.symbol,
            'quantity': position.quantity,
            'average_price': float(position.average_price),
            'current_price': float(current_price),
            'market_value': float(value),
            'unrealized_pnl': float(pnl),
        })

    total_assets = account.cash + market_value
    closed_count = len(win_amounts) + len(loss_amounts)
    average_win = sum(win_amounts) / len(win_amounts) if win_amounts else Decimal('0')
    average_loss = abs(sum(loss_amounts) / len(loss_amounts)) if loss_amounts else Decimal('0')

    return {
        'account': {
            'id': account.id,
            'name': account.name,
            'market': account.market,
            'currency': account.currency,
            'initial_cash': float(account.initial_cash),
            'cash': float(account.cash),
        },
        'summary': {
            'total_assets': float(total_assets),
            'market_value': float(market_value),
            'total_return': float((total_assets / account.initial_cash - 1) * 100),
            'realized_pnl': float(cumulative),
            'unrealized_pnl': float(unrealized),
            'total_fees': float(total_fees),
            'trade_count': len(filled),
            'buy_count': buy_count,
            'sell_count': sell_count,
            'closed_count': closed_count,
            'win_count': len(win_amounts),
            'loss_count': len(loss_amounts),
            'win_rate': float(len(win_amounts) / closed_count * 100) if closed_count else 0.0,
            'profit_loss_ratio': float(average_win / average_loss) if average_loss else 0.0,
            'average_win': float(average_win),
            'average_loss': float(-average_loss),
            'best_trade': float(max(win_amounts)) if win_amounts else 0.0,
            'worst_trade': float(min(loss_amounts)) if loss_amounts else 0.0,
        },
        'positions': positions,
        'trades': trades,
        'realized_curve': realized_curve,
    }
