"""Independent shared-model weekly rotation research; never sends orders."""

from dataclasses import dataclass
from datetime import date
import math

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RotationConfig:
    train_start: str = '2020-01-01'
    validation_start: str = '2024-01-01'
    test_start: str = '2026-01-01'
    sequence_length: int = 20
    horizon: int = 5
    slots: int = 30
    retention_rank: int = 50
    replacements: int = 6
    exposure: float = 0.95
    buy_cost: float = 0.0005
    sell_cost: float = 0.001

    def validate(self):
        boundaries = [date.fromisoformat(value) for value in (
            self.train_start, self.validation_start, self.test_start,
        )]
        if not boundaries[0] < boundaries[1] < boundaries[2]:
            raise ValueError('Training, validation and test boundaries must increase')
        for value in (self.sequence_length, self.horizon, self.slots,
                      self.retention_rank, self.replacements):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError('Rotation sizes must be positive integers')
        if self.retention_rank < self.slots or self.replacements > self.slots:
            raise ValueError('Invalid retention rank or replacement limit')
        if not math.isfinite(self.exposure) or not 0 < self.exposure <= 0.95:
            raise ValueError('Exposure must be positive and at most 95 percent')
        if any(not math.isfinite(v) or not 0 <= v < 1
               for v in (self.buy_cost, self.sell_cost)):
            raise ValueError('Invalid trading costs')


def temporal_split(origin, target, config):
    """Purge labels crossing either boundary, not just their origin dates."""
    if origin < config.train_start or target is None:
        return None
    if origin < config.validation_start and target < config.validation_start:
        return 'train'
    if config.validation_start <= origin < config.test_start and target < config.test_start:
        return 'validation'
    if origin >= config.test_start:
        return 'test'
    return None


def prepare_panel(prices, sessions, config):
    """Store feature rows once; sequence indices avoid duplicating whole panels."""
    config.validate()
    session_index = {day: index for index, day in enumerate(sessions)}
    features, sample_ends, targets, metadata = [], [], [], []
    offset = 0
    for symbol, stock in prices.groupby('symbol', sort=True):
        stock = stock.sort_values('day').reset_index(drop=True)
        if stock['day'].duplicated().any():
            raise ValueError(f'Duplicate prices for {symbol}')
        close = stock['close'] * stock['factor']
        volume = stock['volume']
        values = pd.DataFrame({
            'return': np.log(close).diff(),
            'range': (stock['high'] - stock['low']) / stock['close'],
            'intraday': np.log(stock['close'] / stock['open']),
            'trend': np.log(close / close.rolling(20).mean()),
            'volume': np.log1p(volume / volume.rolling(20).mean()),
        }).to_numpy(dtype=np.float32)
        positions = np.asarray([session_index[day] for day in stock['day']])
        days = stock['day'].tolist()
        for end in range(config.sequence_length - 1, len(stock)):
            begin = end - config.sequence_length + 1
            if (positions[end] - positions[begin] != config.sequence_length - 1
                    or not np.isfinite(values[begin:end + 1]).all()):
                continue
            future = end + config.horizon
            target_day, target = None, float('nan')
            if (future < len(stock)
                    and positions[future] - positions[end] == config.horizon):
                target_day = days[future]
                target = float(close.iloc[future] / close.iloc[end] - 1)
            sample_ends.append(offset + end)
            targets.append(target)
            metadata.append((symbol, days[end], target_day,
                             temporal_split(days[end], target_day, config)))
        features.append(values)
        offset += len(values)
    if not metadata:
        raise ValueError('No valid sequences after warm-up and calendar-gap checks')
    raw = np.concatenate(features)
    ends = np.asarray(sample_ends, dtype=np.int64)
    y = np.asarray(targets, dtype=np.float32)
    masks = {
        split: np.asarray([row[3] == split for row in metadata])
        for split in ('train', 'validation', 'test')
    }
    if any(not mask.any() for mask in masks.values()):
        raise ValueError('All three chronological partitions require labeled samples')
    # Each feature row counts once, and only if used by a training sequence.
    used = np.zeros(len(raw), dtype=bool)
    for end in ends[masks['train']]:
        used[end - config.sequence_length + 1:end + 1] = True
    mean = raw[used].mean(axis=0, dtype=np.float64).astype(np.float32)
    scale = raw[used].std(axis=0, dtype=np.float64).astype(np.float32)
    scale[scale < 1e-8] = 1
    target_mean = float(y[masks['train']].mean())
    target_scale = float(y[masks['train']].std())
    if not math.isfinite(target_scale) or target_scale < 1e-8:
        raise ValueError('Training targets are constant or invalid')
    return {
        'features': (raw - mean) / scale, 'ends': ends, 'y': y,
        'metadata': metadata, 'masks': masks, 'mean': mean, 'scale': scale,
        'target_mean': target_mean, 'target_scale': target_scale,
    }


def select_targets(ranked, holdings, config, threshold, initialized):
    """Retention buffer plus a bound on voluntary name replacements."""
    ranked = [(symbol, score) for symbol, score in ranked if score > threshold]
    top = [symbol for symbol, _ in ranked[:config.slots]]
    retained = {symbol for symbol, _ in ranked[:config.retention_rank]}
    selected = [symbol for symbol in holdings if symbol in retained]
    protected = set(selected)
    exits = [symbol for symbol in holdings if symbol not in retained]
    if initialized:
        # Delaying voluntary exits is intentional; mandatory ineligibility is
        # handled separately by the simulator and never consumes this budget.
        protected.update(exits[config.replacements:])
        selected.extend(exits[config.replacements:])
    additions = 0
    for symbol in top:
        if symbol in selected or len(selected) >= config.slots:
            continue
        if initialized and additions >= config.replacements:
            break
        selected.append(symbol)
        additions += 1
    return selected, protected


def simulate_rotation(prices, predictions, sessions, start, end, config, threshold,
                      progress=None):
    """Adjusted fractional-unit research, with conservative daily fill gates."""
    config.validate()
    if not math.isfinite(threshold) or threshold < 0:
        raise ValueError('Threshold must be finite and nonnegative')
    days = [day for day in sessions if start <= day <= end]
    if len(days) < 2:
        raise ValueError('At least two portfolio sessions are required')
    prior = {day: sessions[index - 1] if index else None
             for index, day in enumerate(sessions)}
    first_origin = prior[days[0]]
    by_day = {day: rows for day, rows in prices.groupby('day', sort=False)
              if (first_origin or start) <= day <= end}
    holdings, last_prices = {}, {}
    cash, fees, initialized = 100000.0, 0.0, False
    curve, trades, selections = [], [], []
    peak, previous_equity = cash, cash
    previous_week = None
    for index, day in enumerate(days):
        if day not in by_day:
            raise ValueError(f'Missing entire market session {day}')
        rows = by_day[day].set_index('symbol').to_dict('index')
        week = date.fromisoformat(day).isocalendar()[:2]
        rebalance = week != previous_week
        previous_week = week
        equity_open = cash
        for symbol, quantity in holdings.items():
            row = rows.get(symbol)
            if row:
                last_prices[symbol] = row['open'] * row['factor']
            if symbol not in last_prices:
                raise ValueError(f'No valuation available for held {symbol} on {day}')
            equity_open += quantity * last_prices[symbol]
        origin = prior[day]
        scores = predictions.get(origin, {})
        if rebalance:
            signal_rows = (by_day[origin].set_index('symbol').to_dict('index')
                           if origin in by_day else {})
            ranked = sorted(
                ((symbol, score) for symbol, score in scores.items()
                 if symbol in signal_rows and not signal_rows[symbol]['suspended']
                 and signal_rows[symbol]['volume'] > 0),
                key=lambda item: (-item[1], item[0]),
            )
            # Missing quotes/suspended holdings remain frozen, not sold at
            # fabricated prices, and still occupy portfolio slots.
            frozen = {s for s in holdings
                      if s not in rows or rows[s]['suspended']}
            active = sorted(set(holdings) - frozen)
            selected, _ = select_targets(ranked, active, config, threshold, initialized)
            selected = list(sorted(frozen)) + [
                s for s in selected if s not in frozen
            ][:max(0, config.slots - len(frozen))]
            targets = {s: config.exposure / config.slots for s in selected}
            selections.append({'date': day, 'signal_date': origin, 'symbols': selected})
            for symbol in sorted(list(holdings)):
                row = rows.get(symbol)
                if (not row or row['suspended'] or row['volume'] <= 0
                        or row['open'] <= row['down_limit'] + 1e-6):
                    continue
                price = row['open'] * row['factor']
                value = holdings[symbol] * price
                reduction = max(0.0, value - targets.get(symbol, 0) * equity_open)
                if reduction <= 1e-8:
                    continue
                holdings[symbol] -= reduction / price
                cost = reduction * config.sell_cost
                cash += reduction - cost
                fees += cost
                trades.append({'date': day, 'signal_date': origin, 'symbol': symbol,
                               'side': 'SELL', 'value': reduction, 'cost': cost})
                if holdings[symbol] <= 1e-8:
                    del holdings[symbol]
            for symbol in selected:
                row = rows.get(symbol)
                if (not row or row['suspended'] or row['volume'] <= 0
                        or row['open'] >= row['up_limit'] - 1e-6):
                    continue
                price = row['open'] * row['factor']
                invested = sum(q * last_prices[s] for s, q in holdings.items())
                equity_now = cash + invested
                room = max(0.0, config.exposure * equity_now - invested)
                wanted = max(0.0, targets[symbol] * equity_open
                             - holdings.get(symbol, 0) * price)
                increase = min(wanted, max(0.0, cash) / (1 + config.buy_cost),
                               room / (1 + config.exposure * config.buy_cost))
                if increase <= 1e-8 or (symbol not in holdings
                                       and len(holdings) >= config.slots):
                    continue
                holdings[symbol] = holdings.get(symbol, 0) + increase / price
                last_prices[symbol] = price
                cost = increase * config.buy_cost
                cash -= increase + cost
                fees += cost
                trades.append({'date': day, 'signal_date': origin, 'symbol': symbol,
                               'side': 'BUY', 'value': increase, 'cost': cost})
            initialized = initialized or bool(holdings)
        for symbol in holdings:
            if symbol in rows:
                last_prices[symbol] = rows[symbol]['close'] * rows[symbol]['factor']
        invested = sum(q * last_prices[s] for s, q in holdings.items())
        equity = cash + invested
        peak = max(peak, equity)
        curve.append({'date': day, 'equity': equity, 'cash': cash,
                      'drawdown': equity / peak - 1, 'fees': fees,
                      'daily_return': equity / previous_equity - 1,
                      'exposure': invested / equity, 'holdings': len(holdings)})
        previous_equity = equity
        if progress and (index % 20 == 0 or index == len(days) - 1):
            progress(curve)
    returns = np.asarray([row['daily_return'] for row in curve])
    volatility = float(returns.std())
    return {
        'curve': curve, 'trades': trades, 'selections': selections,
        'total_return': curve[-1]['equity'] / 100000 - 1,
        'max_drawdown': min(row['drawdown'] for row in curve),
        'sharpe_zero_rate': (float(returns.mean() / volatility * np.sqrt(252))
                             if volatility > 0 else None),
        'fees': fees, 'threshold': threshold,
        'unresolved_terminal_holdings': sorted(holdings),
    }
