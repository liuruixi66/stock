from __future__ import annotations

from math import sqrt
from statistics import mean, pstdev
from typing import Mapping, Sequence

from market_data import HistoricalBar


class ResearchError(ValueError):
    pass


def _aligned_closes(
    bars_by_symbol: Mapping[str, Sequence[HistoricalBar]],
) -> tuple[list, dict[str, list[float]]]:
    if not bars_by_symbol:
        raise ResearchError('组合标的不能为空')
    series = {
        symbol.upper(): {bar.date: float(bar.close) for bar in bars}
        for symbol, bars in bars_by_symbol.items()
    }
    dates = sorted(set.intersection(*(set(values) for values in series.values())))
    if len(dates) < 2:
        raise ResearchError('组合标的没有足够的共同交易日')
    return dates, {symbol: [values[item] for item in dates] for symbol, values in series.items()}


def _portfolio_metrics(equity: list[float], daily_returns: list[float], turnover: list[float]) -> dict:
    if not equity:
        return {'annual_return': 0.0, 'annual_volatility': 0.0, 'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0, 'max_drawdown': 0.0, 'calmar_ratio': 0.0,
                'average_turnover': 0.0}
    annual_return = mean(daily_returns) * 252 if daily_returns else 0.0
    annual_volatility = pstdev(daily_returns) * sqrt(252) if len(daily_returns) > 1 else 0.0
    downside = [value for value in daily_returns if value < 0]
    downside_volatility = pstdev(downside) * sqrt(252) if len(downside) > 1 else 0.0
    sharpe = annual_return / annual_volatility if annual_volatility else 0.0
    sortino = annual_return / downside_volatility if downside_volatility else 0.0
    peak = equity[0]
    max_drawdown = 0.0
    for value in equity:
        peak = max(peak, value)
        max_drawdown = min(max_drawdown, value / peak - 1)
    calmar = annual_return / abs(max_drawdown) if max_drawdown < 0 else 0.0
    return {
        'annual_return': round(annual_return * 100, 4),
        'annual_volatility': round(annual_volatility * 100, 4),
        'sharpe_ratio': round(sharpe, 4),
        'sortino_ratio': round(sortino, 4),
        'max_drawdown': round(max_drawdown * 100, 4),
        'calmar_ratio': round(calmar, 4),
        'average_turnover': round(mean(turnover), 6) if turnover else 0.0,
    }


def run_portfolio_baseline(
    bars_by_symbol: Mapping[str, Sequence[HistoricalBar]],
    initial_cash: float,
    strategy: str = 'equal_weight',
    lookback: int | None = None,
    transaction_cost_bps: float = 2.0,
) -> dict:
    """Run paper's rule-based portfolio benchmarks without look-ahead bias."""
    if initial_cash <= 0:
        raise ResearchError('初始资金必须大于0')
    if transaction_cost_bps < 0:
        raise ResearchError('交易成本不能小于0')
    if strategy not in {'equal_weight', 'risk_parity', 'tsmom'}:
        raise ResearchError('策略必须是 equal_weight、risk_parity 或 tsmom')
    default_lookback = 60 if strategy == 'risk_parity' else 252 if strategy == 'tsmom' else 1
    lookback = lookback or default_lookback
    if lookback < 1:
        raise ResearchError('lookback 必须大于0')

    dates, closes = _aligned_closes(bars_by_symbol)
    symbols = list(closes)
    if len(dates) <= lookback:
        raise ResearchError(f'历史数据不足，至少需要 {lookback + 1} 个共同交易日')
    weights = {symbol: 0.0 for symbol in symbols}
    equity = [float(initial_cash)]
    daily_returns: list[float] = []
    turnover: list[float] = []
    weight_history = []
    cost_rate = transaction_cost_bps / 10000

    for index in range(1, len(dates)):
        returns = {
            symbol: closes[symbol][index] / closes[symbol][index - 1] - 1
            for symbol in symbols
        }
        if index > lookback:
            previous_weights = weights.copy()
            if strategy == 'equal_weight':
                weights = {symbol: 1 / len(symbols) for symbol in symbols}
            elif strategy == 'risk_parity':
                volatilities = {}
                for symbol in symbols:
                    trailing = [
                        closes[symbol][item] / closes[symbol][item - 1] - 1
                        for item in range(index - lookback, index)
                    ]
                    volatilities[symbol] = pstdev(trailing) if len(trailing) > 1 else 0.0
                inverse = {symbol: 1 / value for symbol, value in volatilities.items() if value > 0}
                total_inverse = sum(inverse.values())
                weights = {
                    symbol: inverse.get(symbol, 0.0) / total_inverse if total_inverse else 0.0
                    for symbol in symbols
                }
            else:
                signals = {
                    symbol: 1 if closes[symbol][index - 1] > closes[symbol][index - lookback - 1] else -1
                    for symbol in symbols
                }
                absolute = sum(abs(value) for value in signals.values())
                weights = {symbol: signals[symbol] / absolute for symbol in symbols}
            current_turnover = 0.5 * sum(abs(weights[symbol] - previous_weights[symbol]) for symbol in symbols)
            turnover.append(current_turnover)
            weight_history.append({'date': dates[index].isoformat(), 'weights': weights.copy()})
        else:
            current_turnover = 0.0
            turnover.append(current_turnover)
        net_return = sum(weights[symbol] * returns[symbol] for symbol in symbols) - current_turnover * cost_rate
        daily_returns.append(net_return)
        equity.append(equity[-1] * (1 + net_return))

    return {
        'strategy': strategy,
        'parameters': {
            'lookback': lookback,
            'transaction_cost_bps': transaction_cost_bps,
            'symbols': symbols,
        },
        'initial_cash': round(initial_cash, 2),
        'final_equity': round(equity[-1], 2),
        'total_return': round((equity[-1] / initial_cash - 1) * 100, 4),
        'metrics': _portfolio_metrics(equity, daily_returns, turnover),
        'equity_curve': [
            {'date': item.isoformat(), 'equity': round(value, 2)}
            for item, value in zip(dates, equity)
        ],
        'weight_history': weight_history,
    }


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