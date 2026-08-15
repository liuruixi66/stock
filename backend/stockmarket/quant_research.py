from __future__ import annotations

from math import sqrt

from market_data import HistoricalBar


class ResearchError(ValueError):
    pass


def run_sma_cross(
    bars: list[HistoricalBar],
    initial_cash: float,
    short_window: int,
    long_window: int,
    commission_rate: float = 0.0003,
    slippage_bps: float = 2,
) -> dict:
    if short_window < 2 or long_window <= short_window:
        raise ResearchError('均线参数必须满足 2 <= short_window < long_window')
    if len(bars) <= long_window:
        raise ResearchError(f'历史数据不足，至少需要 {long_window + 1} 根K线')
    if initial_cash <= 0:
        raise ResearchError('初始资金必须大于0')

    cash = initial_cash
    shares = 0
    closes: list[float] = []
    equity_curve = []
    trades = []
    previous_signal = False
    slip = slippage_bps / 10000

    for bar in bars:
        closes.append(bar.close)
        if len(closes) < long_window:
            equity_curve.append({'date': bar.date.isoformat(), 'equity': round(cash, 2)})
            continue
        short_ma = sum(closes[-short_window:]) / short_window
        long_ma = sum(closes[-long_window:]) / long_window
        signal = short_ma > long_ma
        if signal and not previous_signal and shares == 0:
            execution_price = bar.close * (1 + slip)
            shares = int(cash / (execution_price * (1 + commission_rate)))
            if shares:
                amount = shares * execution_price
                fee = amount * commission_rate
                cash -= amount + fee
                trades.append({'date': bar.date.isoformat(), 'side': 'BUY', 'price': round(execution_price, 4), 'quantity': shares, 'fee': round(fee, 4)})
        elif not signal and previous_signal and shares:
            execution_price = bar.close * (1 - slip)
            amount = shares * execution_price
            fee = amount * commission_rate
            cash += amount - fee
            trades.append({'date': bar.date.isoformat(), 'side': 'SELL', 'price': round(execution_price, 4), 'quantity': shares, 'fee': round(fee, 4)})
            shares = 0
        previous_signal = signal
        equity_curve.append({'date': bar.date.isoformat(), 'equity': round(cash + shares * bar.close, 2)})

    final_equity = cash + shares * bars[-1].close
    values = [point['equity'] for point in equity_curve]
    returns = [(values[index] / values[index - 1] - 1) for index in range(1, len(values)) if values[index - 1]]
    average_return = sum(returns) / len(returns) if returns else 0
    variance = sum((item - average_return) ** 2 for item in returns) / max(len(returns) - 1, 1)
    sharpe = average_return / sqrt(variance) * sqrt(252) if variance > 0 else 0
    peak = values[0]
    max_drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        max_drawdown = min(max_drawdown, value / peak - 1)

    return {
        'strategy': 'sma_cross',
        'parameters': {'short_window': short_window, 'long_window': long_window},
        'initial_cash': round(initial_cash, 2),
        'final_equity': round(final_equity, 2),
        'total_return': round((final_equity / initial_cash - 1) * 100, 4),
        'max_drawdown': round(max_drawdown * 100, 4),
        'sharpe_ratio': round(sharpe, 4),
        'trade_count': len(trades),
        'trades': trades,
        'equity_curve': equity_curve,
    }