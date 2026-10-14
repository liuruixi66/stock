"""Portable, long-only ETF rotation research rules (no broker or network calls)."""

from dataclasses import dataclass
from datetime import date
from math import isfinite, sqrt
from statistics import mean, pstdev
from typing import Dict, Mapping, Optional, Sequence


@dataclass(frozen=True)
class RotationBar:
    date: date
    close: float
    high: float
    low: float
    volume: float


@dataclass(frozen=True)
class RotationConfig:
    short_window: int = 20
    momentum_window: int = 60
    trend_window: int = 120
    volatility_window: int = 20
    holdings: int = 3
    shrinkage: float = 0.5
    max_weight: float = 0.40
    max_exposure: float = 0.95
    target_volatility: float = 0.15
    max_asset_volatility: float = 0.45
    max_daily_loss: float = 0.04

    @property
    def history_count(self) -> int:
        return max(self.trend_window, self.momentum_window + 1,
                   self.volatility_window + 1, self.short_window + 1)

    def validate(self) -> None:
        windows = (self.short_window, self.momentum_window, self.trend_window,
                   self.volatility_window, self.holdings)
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 1
               for value in windows):
            raise ValueError('Windows and holdings must be positive integers')
        if not 2 <= self.volatility_window <= self.momentum_window:
            raise ValueError('Require 2 <= volatility_window <= momentum_window')
        if not 2 <= self.short_window < self.momentum_window < self.trend_window:
            raise ValueError('Require 2 <= short_window < momentum_window < trend_window')
        if not isfinite(self.shrinkage) or not 0 <= self.shrinkage <= 1:
            raise ValueError('shrinkage must be in [0, 1]')
        for name in ('max_weight', 'max_exposure', 'target_volatility',
                     'max_asset_volatility', 'max_daily_loss'):
            value = getattr(self, name)
            if not isfinite(value) or not 0 < value <= 1:
                raise ValueError('{} must be in (0, 1]'.format(name))


def shrink_to_equal(weights: Mapping[str, float], strength: float) -> Dict[str, float]:
    """Convex equal-weight shrinkage, not an entropy optimization solver."""
    if not isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be in [0, 1]')
    if not weights:
        return {}
    equal = 1.0 / len(weights)
    return {symbol: (1 - strength) * weight + strength * equal
            for symbol, weight in weights.items()}


def build_rotation_targets(
    histories: Mapping[str, Sequence[RotationBar]],
    as_of: date,
    config: Optional[RotationConfig] = None,
) -> dict:
    """Compute weights using completed bars dated at or before explicit as_of.

    Future bars are discarded before validation and scoring. Invalid, stale and
    short histories have explicit rejection reasons; they never receive weight.
    """
    config = config or RotationConfig()
    config.validate()
    if not histories:
        raise ValueError('ETF universe must not be empty')
    features = {}
    rejected = {}
    for symbol, history in histories.items():
        bars = [bar for bar in history if bar.date <= as_of]
        if any(left.date >= right.date for left, right in zip(bars, bars[1:])):
            rejected[symbol] = 'duplicate_or_unsorted_dates'
            continue
        if len(bars) < config.history_count:
            rejected[symbol] = 'insufficient_history'
            continue
        bars = bars[-config.history_count:]
        if bars[-1].date != as_of:
            rejected[symbol] = 'stale_history'
            continue
        if any(not all(isfinite(value) for value in
                       (bar.close, bar.high, bar.low, bar.volume))
               or bar.low <= 0 or not bar.low <= bar.close <= bar.high
               or bar.volume < 0 for bar in bars):
            rejected[symbol] = 'invalid_ohlcv'
            continue
        closes = [bar.close for bar in bars]
        returns = [right / left - 1 for left, right in zip(closes, closes[1:])]
        volatility = pstdev(returns[-config.volatility_window:]) * sqrt(252)
        slow_volatility = pstdev(returns[-config.momentum_window:]) * sqrt(252)
        prior_volume = mean(bar.volume for bar in bars[-config.short_window - 1:-1])
        if prior_volume <= 0 or bars[-1].volume <= 0 or volatility <= 1e-10:
            rejected[symbol] = 'inactive_or_zero_volatility'
            continue
        volume_ratio = bars[-1].volume / prior_volume
        short_momentum = closes[-1] / closes[-config.short_window - 1] - 1
        momentum = closes[-1] / closes[-config.momentum_window - 1] - 1
        trend_ma = mean(closes[-config.trend_window:])
        intraday_range = (bars[-1].high - bars[-1].low) / closes[-2]
        stress = (volatility > config.max_asset_volatility
                  or volatility > 2 * max(slow_volatility, 0.03)
                  or returns[-1] <= -config.max_daily_loss
                  or (intraday_range > 0.08 and volume_ratio > 2))
        if stress:
            regime = 'stress'
        elif volume_ratio < 0.3:
            regime = 'thin'
        elif closes[-1] > trend_ma and short_momentum > 0 and momentum > 0:
            regime = 'trend'
        else:
            regime = 'weak'
        features[symbol] = {
            'short_momentum': short_momentum,
            'medium_momentum': momentum,
            'annual_volatility': volatility,
            'volume_ratio': volume_ratio,
            'trend_ma': trend_ma,
            'regime': regime,
            'score': (0.4 * short_momentum + 0.6 * momentum) / max(volatility, 0.03),
        }
    ranked = sorted(
        (symbol for symbol, feature in features.items() if feature['regime'] == 'trend'),
        key=lambda symbol: (-features[symbol]['score'], symbol),
    )
    selected = ranked[:config.holdings]
    weights = {symbol: 0.0 for symbol in histories}
    if selected:
        inverse = {symbol: 1 / max(features[symbol]['annual_volatility'], 0.03)
                   for symbol in selected}
        total = sum(inverse.values())
        allocation = shrink_to_equal(
            {symbol: value / total for symbol, value in inverse.items()}, config.shrinkage,
        )
        # The weighted sum of asset volatilities bounds covariance-based vol.
        conservative_vol = sum(allocation[symbol] * features[symbol]['annual_volatility']
                               for symbol in selected)
        exposure = min(config.max_exposure, config.target_volatility / conservative_vol)
        for symbol in selected:
            weights[symbol] = min(config.max_weight, exposure * allocation[symbol])
    return {
        'strategy': 'regime_filtered_etf_rotation_v1',
        'as_of': as_of.isoformat(),
        'weights': weights,
        'cash_weight': 1 - sum(weights.values()),
        'selected': selected,
        'features': features,
        'rejected': rejected,
    }
