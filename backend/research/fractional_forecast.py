"""Causal De Prado branch of arXiv:2505.19243, not a full paper replication."""

from dataclasses import dataclass
from datetime import date, timedelta
from math import exp, isfinite
from typing import Mapping, Sequence

import numpy as np
from numpy.typing import NDArray
import pandas as pd


class DifferencingError(ValueError):
    pass


@dataclass(frozen=True)
class ForecastConfig:
    train_start: date = date(2014, 1, 1)
    validation_start: date = date(2022, 4, 1)
    test_start: date = date(2024, 4, 1)
    test_end: date = date(2026, 4, 30)
    sequence_length: int = 20
    weight_threshold: float = 0.001
    max_lags: int = 1000
    minimum_train_samples: int = 252
    minimum_validation_samples: int = 60

    def validate(self) -> None:
        if not self.train_start < self.validation_start < self.test_start <= self.test_end:
            raise DifferencingError('Require train_start < validation_start < test_start <= test_end')
        if self.test_end >= date.today():
            raise DifferencingError('Test end must be a completed past date')
        for value in (self.sequence_length, self.max_lags,
                      self.minimum_train_samples, self.minimum_validation_samples):
            if isinstance(value, bool) or not isinstance(value, int) or value < 2:
                raise DifferencingError('Sample counts and sequence length must be integers >= 2')
        if not isfinite(self.weight_threshold) or not 0 < self.weight_threshold < 1:
            raise DifferencingError('weight_threshold must be finite and in (0, 1)')


def fractional_weights(
    order: float, threshold: float = 0.001, max_lags: int = 1000, tempering: float = 0.0,
) -> np.ndarray:
    """Equations 22-24 and 35-36: lag zero first, fixed-width truncation."""
    if (not isfinite(order) or not 0 <= order <= 1
            or not isfinite(tempering) or tempering < 0
            or not isfinite(threshold) or not 0 < threshold < 1
            or isinstance(max_lags, bool) or not isinstance(max_lags, int) or max_lags < 2):
        raise DifferencingError('Invalid differencing order, threshold, tempering or lag limit')
    weights = [1.0]
    for lag in range(1, max_lags):
        value = -weights[-1] * (order - lag + 1) / lag * exp(-tempering)
        if abs(value) < threshold:
            return np.asarray(weights, dtype=float)
        weights.append(value)
    raise DifferencingError('Differencing weights did not truncate; increase max_lags')


def fractional_difference(
    values: Sequence[float] | NDArray[np.float64], weights: np.ndarray,
) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if (values.ndim != 1 or weights.ndim != 1 or not len(weights)
            or weights[0] != 1 or not np.isfinite(values).all()
            or not np.isfinite(weights).all()):
        raise DifferencingError('Differencing requires finite vectors and lag-zero weight 1')
    result = np.full(len(values), np.nan)
    if len(values) >= len(weights):
        result[len(weights) - 1:] = np.convolve(values, weights, mode='valid')
    return result


def invert_one_step(predicted_difference: float, past_log_prices: Sequence[float] | NDArray[np.float64],
                    weights: np.ndarray) -> float:
    """Invert the same finite filter using only history available at the origin."""
    if (not isfinite(predicted_difference) or len(past_log_prices) < len(weights) - 1
            or len(weights) == 0 or weights[0] != 1 or not np.isfinite(weights).all()):
        raise DifferencingError('Invalid inverse prediction or insufficient history')
    if len(weights) == 1:
        return float(predicted_difference)
    history = np.asarray(past_log_prices[-(len(weights) - 1):], dtype=float)[::-1]
    if not np.isfinite(history).all():
        raise DifferencingError('Inverse history must be finite')
    return float(predicted_difference - np.dot(weights[1:], history))


def estimate_order(
    training_log_prices: Sequence[float] | NDArray[np.float64], config: ForecastConfig,
) -> dict:
    """Smallest grid order passing a 5% ADF test, training observations only."""
    from statsmodels.tsa.stattools import adfuller

    config.validate()
    values = np.asarray(training_log_prices, dtype=float)
    if not np.isfinite(values).all() or len(values) < config.minimum_train_samples:
        raise DifferencingError('Insufficient or non-finite training data for ADF')
    trials = []
    for order in np.linspace(0, 1, 21):
        weights = fractional_weights(float(order), config.weight_threshold, config.max_lags)
        transformed = fractional_difference(values, weights)
        transformed = transformed[np.isfinite(transformed)]
        if len(transformed) < config.minimum_train_samples:
            trials.append({'order': float(order), 'status': 'insufficient_after_truncation'})
            continue
        if np.ptp(transformed) <= 1e-12:
            trials.append({'order': float(order), 'status': 'constant_series'})
            continue
        result = adfuller(
            transformed, regression='c', autolag='AIC',
        )
        if len(result) != 6:
            raise DifferencingError('Unexpected ADF result schema')
        statistic, pvalue = float(result[0]), float(result[1])
        observations, critical = result[3], result[4]
        if not isinstance(observations, (int, np.integer)) or not isinstance(critical, dict):
            raise DifferencingError('Unexpected ADF observations or critical values')
        trial = {
            'order': float(order), 'status': 'tested', 'statistic': float(statistic),
            'pvalue': float(pvalue), 'observations': int(observations),
            'critical_5pct': float(critical['5%']), 'lags': len(weights),
        }
        trials.append(trial)
        if pvalue < 0.05 and statistic < critical['5%']:
            return {'order': float(order), 'trials': trials}
    raise DifferencingError('No order in [0, 1] passed training-only ADF; do not invent an order')


def forecast_features(closes: pd.Series, transformed: np.ndarray) -> pd.DataFrame:
    """Paper SMA5/10/20, RSI9/14/21, Bollinger10/2 and MACD12/26/9."""
    if not np.isfinite(closes).all() or (closes <= 0).any():
        raise DifferencingError('Features require finite positive adjusted closes')
    frame = pd.DataFrame({'differenced': transformed}, index=closes.index)
    for window in (5, 10, 20):
        frame[f'sma_{window}'] = closes.rolling(window).mean()
    change = closes.diff()
    for window in (9, 14, 21):
        gain = change.clip(lower=0).rolling(window).mean()
        loss = (-change.clip(upper=0)).rolling(window).mean()
        denominator = gain + loss
        frame[f'rsi_{window}'] = (100 * gain / denominator).where(
            denominator > 0, 50.0,
        ).where(denominator.notna())
    average = closes.rolling(10).mean()
    deviation = closes.rolling(10).std(ddof=0)
    frame['bollinger_upper'] = average + 2 * deviation
    frame['bollinger_lower'] = average - 2 * deviation
    macd = closes.ewm(span=12, adjust=False).mean() - closes.ewm(span=26, adjust=False).mean()
    frame['macd'] = macd
    frame['macd_signal'] = macd.ewm(span=9, adjust=False).mean()
    return frame


class HistoricalTopThirty:
    """Use the latest complete snapshot strictly before the signal date."""

    def __init__(self, frame: pd.DataFrame, maximum_age_days: int = 35):
        required = {'date', 'instrument', 'member_code', 'weight'}
        if not required <= set(frame.columns):
            raise DifferencingError(f'Historical weights need columns {sorted(required)}')
        if maximum_age_days < 1:
            raise DifferencingError('maximum_age_days must be positive')
        frame = frame.copy()
        frame['date'] = pd.to_datetime(frame['date'], errors='raise').dt.date
        if frame['date'].isna().any():
            raise DifferencingError('Missing weight snapshot dates')
        if set(frame['instrument']) != {'000016.SHI'}:
            raise DifferencingError('Expected only historical SSE50 weights: 000016.SHI')
        if frame.duplicated(['date', 'member_code']).any():
            raise DifferencingError('Duplicate historical constituent weights')
        if not frame['member_code'].str.fullmatch(r'\d{6}\.SH').all():
            raise DifferencingError('Invalid Shanghai constituent code')
        frame['weight'] = pd.to_numeric(frame['weight'], errors='raise')
        if not np.isfinite(frame['weight']).all() or (frame['weight'] <= 0).any():
            raise DifferencingError('Historical weights must be finite and positive')
        self.snapshots = {}
        for day, rows in frame.groupby('date'):
            if len(rows) != 50:
                raise DifferencingError(f'Incomplete SSE50 snapshot on {day}: expected 50 members')
            total = float(rows['weight'].sum())
            if not (abs(total - 100) < 0.1 or abs(total - 1) < 0.001):
                raise DifferencingError(f'Historical snapshot weights do not sum to 100% on {day}')
            selected = rows.sort_values(['weight', 'member_code'], ascending=[False, True]).head(30)
            self.snapshots[day] = tuple(selected['member_code'])
        self.days = sorted(self.snapshots)
        self.maximum_age_days = maximum_age_days
        if not self.days:
            raise DifferencingError('Historical weight snapshots are empty')

    def at(self, signal_day: date) -> tuple[date, tuple[str, ...]]:
        from bisect import bisect_left

        position = bisect_left(self.days, signal_day) - 1
        if position < 0:
            raise DifferencingError(f'No weight snapshot strictly before {signal_day}')
        day = self.days[position]
        if (signal_day - day).days > self.maximum_age_days:
            raise DifferencingError(f'Stale historical weight snapshot {day} for {signal_day}')
        return day, self.snapshots[day]

    def members_between(self, start: date, end: date) -> tuple[str, ...]:
        if start > end:
            raise DifferencingError('Universe start must not exceed end')
        members = set(self.at(start)[1])
        for snapshot_day in self.days:
            first_usable = snapshot_day + timedelta(days=1)
            if start <= first_usable <= end:
                members.update(self.at(first_usable)[1])
        return tuple(sorted(members))


def long_only_signal(predicted_return: float, previous: bool, threshold: float) -> bool:
    """Equation 47; retain the existing position inside the transaction-cost band."""
    if (not isfinite(predicted_return) or not isfinite(threshold)
            or not 0 < threshold < 1):
        raise DifferencingError('Invalid forecast return or cost threshold')
    if predicted_return > threshold:
        return True
    if predicted_return < -threshold:
        return False
    return previous


def validate_prices(frame: pd.DataFrame) -> pd.DataFrame:
    required = {'date', 'instrument', 'open', 'high', 'low', 'close', 'volume'}
    if not required <= set(frame.columns) or frame.empty:
        raise DifferencingError(f'Prices need nonempty adjusted OHLCV columns {sorted(required)}')
    frame = frame.copy()
    frame['date'] = pd.to_datetime(frame['date'], errors='raise').dt.date
    if frame['date'].isna().any() or frame.duplicated(['date', 'instrument']).any():
        raise DifferencingError('Missing or duplicate price dates')
    if not frame['instrument'].str.fullmatch(r'\d{6}\.SH').all():
        raise DifferencingError('Expected Shanghai stock instruments')
    for name in ('open', 'high', 'low', 'close', 'volume'):
        frame[name] = pd.to_numeric(frame[name], errors='raise')
    if (not np.isfinite(frame[list(required - {'date', 'instrument'})]).all().all()
            or (frame[['open', 'high', 'low', 'close']] <= 0).any().any()
            or (frame['volume'] < 0).any()
            or (frame['low'] > frame[['open', 'close']].min(axis=1)).any()
            or (frame['high'] < frame[['open', 'close']].max(axis=1)).any()):
        raise DifferencingError('Invalid adjusted OHLCV')
    return frame.sort_values(['instrument', 'date']).reset_index(drop=True)


def simulate_long_only(
    prices: pd.DataFrame, predictions: Mapping[tuple[date, str], float],
    universe: HistoricalTopThirty, start: date, end: date,
    initial_capital: float = 100000, exposure: float = 0.95,
    buy_cost: float = 0.0005, sell_cost: float = 0.001,
    signal_threshold: float = 0.002, benchmark: bool = False,
) -> dict:
    """Continuous adjusted-price research portfolio, NOT an A-share fill simulator.

    Close-time signals execute no earlier than the next supplied daily open.
    Thirty fixed allocation slots; unused slots stay cash. Missing/untradeable
    held prices stop the experiment rather than fabricating a fill.
    """
    prices = validate_prices(prices)
    if (not start <= end or not isfinite(initial_capital) or initial_capital <= 0
            or not isfinite(exposure) or not 0 < exposure <= 1
            or any(not isfinite(c) or not 0 <= c < 1 for c in (buy_cost, sell_cost))):
        raise DifferencingError('Invalid simulation dates, capital, exposure or costs')
    if not isfinite(signal_threshold) or not 0 < signal_threshold < 1:
        raise DifferencingError('Invalid signal threshold')
    frame = prices[prices['date'] <= end]
    days = sorted(day for day in frame['date'].unique() if start <= day <= end)
    if len(days) < 2:
        raise DifferencingError('At least two test trading days are required')
    daily = {
        day: rows.set_index('instrument').to_dict('index')
        for day, rows in frame.groupby('date')
    }
    cash = initial_capital
    units: dict[str, float] = {}
    pending = None
    curve, trades, selections = [], [], []
    fees = 0.0
    missing_predictions = 0
    for day in days:
        rows = daily[day]
        for symbol in units:
            if symbol not in rows or rows[symbol]['volume'] <= 0:
                raise DifferencingError(f'No tradeable held price {symbol} on {day}; cannot simulate')
        if pending is not None:
            origin, targets = pending
            equity_open = cash + sum(quantity * rows[symbol]['open']
                                     for symbol, quantity in units.items())
            for symbol in sorted(units):
                target = targets.get(symbol, 0.0) * equity_open
                value = units[symbol] * rows[symbol]['open']
                reduction = max(0.0, value - target)
                if reduction > 1e-8:
                    units[symbol] -= reduction / rows[symbol]['open']
                    cost = reduction * sell_cost
                    cash += reduction - cost
                    fees += cost
                    trades.append({'signal_date': origin.isoformat(), 'date': day.isoformat(),
                                   'instrument': symbol, 'side': 'SELL', 'value': reduction,
                                   'cost': cost})
            units = {symbol: quantity for symbol, quantity in units.items() if quantity > 1e-10}
            for symbol, weight in sorted(targets.items()):
                if weight <= 0:
                    continue
                if symbol not in rows or rows[symbol]['volume'] <= 0:
                    raise DifferencingError(f'No tradeable target price {symbol} on {day}')
                value = units.get(symbol, 0.0) * rows[symbol]['open']
                increase = min(max(0.0, weight * equity_open - value),
                               max(0.0, cash) / (1 + buy_cost))
                if increase > 1e-8:
                    units[symbol] = units.get(symbol, 0.0) + increase / rows[symbol]['open']
                    cost = increase * buy_cost
                    cash -= increase + cost
                    fees += cost
                    trades.append({'signal_date': origin.isoformat(), 'date': day.isoformat(),
                                   'instrument': symbol, 'side': 'BUY', 'value': increase,
                                   'cost': cost})
        equity = cash + sum(quantity * rows[symbol]['close'] for symbol, quantity in units.items())
        snapshot_day, candidates = universe.at(day)
        targets = {}
        for symbol in candidates:
            if symbol not in rows:
                raise DifferencingError(f'No signal-day data for historical top30 member {symbol} on {day}')
            if benchmark:
                active = True
            elif day == days[-1]:
                active = symbol in units
            elif (day, symbol) not in predictions:
                missing_predictions += 1
                active = False
            else:
                active = long_only_signal(predictions[(day, symbol)], symbol in units, signal_threshold)
            if active:
                targets[symbol] = exposure / 30
        pending = (day, targets)
        selections.append({'date': day.isoformat(), 'weight_date': snapshot_day.isoformat(),
                           'candidates': list(candidates), 'active': list(targets)})
        curve.append({'date': day.isoformat(), 'equity': equity, 'cash': cash})
    equity = np.asarray([initial_capital] + [point['equity'] for point in curve])
    returns = equity[1:] / equity[:-1] - 1
    running = np.maximum.accumulate(equity)
    volatility = float(np.std(returns) * np.sqrt(252))
    return {
        'simulation': 'continuous_adjusted_price_next_open_research_only',
        'total_return': float(equity[-1] / initial_capital - 1),
        'annualized_return': float((equity[-1] / initial_capital) ** (252 / len(days)) - 1),
        'max_drawdown': float(np.min(equity / running - 1)),
        'annualized_volatility': volatility,
        'sharpe_zero_risk_free': float(np.mean(returns) * 252 / volatility) if volatility > 0 else None,
        'costs': fees, 'order_count': len(trades), 'missing_forecasts': missing_predictions,
        'equity_curve': curve, 'trades': trades, 'selection_history': selections,
        'limitations': [
            'No integer lots, minimum commission, T+1 or limit-up/down fill simulation.',
            'Adjusted-price continuous units, not raw-price cash/share corporate-action accounting.',
            'Missing active-market prices stop the run; suspensions require a platform fill model.',
            'Last close signal remains unexecuted; terminal holdings are marked, not liquidated.',
            'Historical snapshot dates must be verified as available at their stated date.',
        ],
    }
