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


"""BigQuant v17 graph adapter using only daily ETF bars; backtest use only."""

from datetime import date, timedelta
from math import isfinite

import pandas as pd
from bigmodule import M



ETF_UNIVERSE = (
    '510300.SH', '510500.SH', '159915.SZ', '588000.SH', '512100.SH',
    '512880.SH', '512010.SH', '512660.SH', '515050.SH', '518880.SH',
)
BAR_COLUMNS = {'date', 'instrument', 'close', 'high', 'low', 'volume', 'amount'}
OPTIONS_KEY = 'etf_rotation_v17_state'
MIN_AVERAGE_AMOUNT = 20000000
BACKTEST_START_DATE = '2024-10-16'
DATA_START_DATE = '2024-01-01'


def _frame_targets(frame: pd.DataFrame, as_of: date) -> dict:
    missing = BAR_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError('Missing daily ETF bar fields: {}'.format(sorted(missing)))

    bars_frame = frame.copy()
    bars_frame['date'] = pd.to_datetime(bars_frame['date'], errors='raise').dt.date
    bars_frame = bars_frame[bars_frame['date'] <= as_of]
    histories = {}
    excluded = {}
    for symbol in ETF_UNIVERSE:
        rows = bars_frame[bars_frame['instrument'] == symbol].sort_values('date')
        if rows.empty:
            excluded[symbol] = 'missing_history'
            continue
        if rows['date'].duplicated().any():
            raise ValueError('Duplicate ETF dates: {}'.format(symbol))
        if rows['date'].iloc[-1] != as_of:
            excluded[symbol] = 'stale_history'
            continue
        if (as_of - rows['date'].iloc[0]).days < 180:
            excluded[symbol] = 'observed_history_under_180_days'
            continue
        amounts = [float(value) for value in rows['amount'].iloc[-20:]]
        if any(not isfinite(value) or value < 0 for value in amounts):
            raise ValueError('Invalid ETF amount: {}'.format(symbol))
        if sum(amounts) / len(amounts) < MIN_AVERAGE_AMOUNT:
            excluded[symbol] = 'illiquid'
            continue
        bars = []
        for row in rows.itertuples(index=False):
            bars.append(RotationBar(
                row.date, float(row.close), float(row.high), float(row.low),
                float(row.volume),
            ))
        histories[symbol] = bars
    if not histories:
        raise ValueError('No ETF daily bars available on or before {}'.format(as_of))
    targets = build_rotation_targets(histories, as_of, RotationConfig())
    targets['rejected'].update(excluded)
    if not targets['features']:
        raise ValueError('All ETF daily histories rejected: {}'.format(targets['rejected']))
    return targets


def m8_before_trading_start_bigquant_run(context, data):
    pass


def m8_handle_tick_bigquant_run(context, tick):
    pass


def m8_handle_trade_bigquant_run(context, trade):
    pass


def m8_handle_order_bigquant_run(context, order):
    pass


def m8_after_trading_bigquant_run(context, data):
    pass


def m8_initialize_bigquant_run(context):
    from bigtrader.finance.commission import PerOrder

    context.set_commission(PerOrder(buy_cost=0.0003, sell_cost=0.0013, min_cost=5))
    context.stock_count = 3
    context.stock_weights = 1 / context.stock_count
    context.options[OPTIONS_KEY] = {
        'signal_week': '',
        'pending': None,
    }


def m8_handle_data_bigquant_run(context, data):
    signal_day = data.current_dt.date()
    iso_year, iso_week, _ = signal_day.isocalendar()
    week_key = '{}-{:02d}'.format(iso_year, iso_week)
    state = context.options[OPTIONS_KEY]
    pending = state['pending']
    if pending is not None and (signal_day - date.fromisoformat(pending['signal_date'])).days > 7:
        context.logger.warning('ETF target expired; wait for a new weekly signal')
        state['pending'] = None
        pending = None

    if pending is None and state['signal_week'] != week_key:
        frame = context.data
        if not isinstance(frame, pd.DataFrame):
            raise ValueError('BigTrader context.data must contain extracted daily ETF bars')
        frame = frame.copy()
        frame['date'] = pd.to_datetime(frame['date'], errors='raise').dt.date
        # Use completed bars only; today's open execution must not see today's close.
        completed = frame[frame['date'] < signal_day]
        if completed.empty:
            context.logger.warning(
                'No completed ETF bars before {}; skip signal'.format(signal_day),
            )
            return
        as_of = max(completed['date'])
        targets = _frame_targets(completed, as_of)
        state['signal_week'] = week_key
        pending = {
            'signal_date': signal_day.isoformat(),
            'weights': targets['weights'],
            'sell_submitted': [],
            'buy_submitted': [],
        }
        state['pending'] = pending
        context.logger.info('ETF targets as of {}: {}'.format(as_of, targets))

    if pending is not None:
        execute_pending_targets(context, data, pending)


def _held_positions(context) -> dict:
    return {
        symbol: position for symbol, position in context.portfolio.positions.items()
        if position.amount > 0
    }


def sell_unselected(context, pending: dict, held: dict, selected: set) -> bool:
    submitted = set(pending['sell_submitted'])
    to_sell = sorted((set(held) - selected) - submitted)
    for symbol in to_sell:
        result = context.order_target(symbol, 0)
        if result < 0:
            context.logger.warning('Sell order failed {}: {}'.format(
                symbol, context.get_error_msg(result),
            ))
            continue
        pending['sell_submitted'].append(symbol)
        context.logger.info('Sell order submitted: {}'.format(symbol))
    return bool(set(held) - selected)


def buy_missing(context, data, pending: dict, held: dict, selected: set) -> bool:
    submitted = set(pending['buy_submitted'])
    missing = selected - set(held) - submitted
    if not missing:
        return False

    equity = float(context.portfolio.portfolio_value)
    cash = float(context.portfolio.cash)
    if equity <= 0 or cash < 0:
        raise ValueError('Portfolio equity/cash is invalid')
    for symbol in sorted(missing, key=lambda code: (-pending['weights'][code], code)):
        price = float(data.current(symbol, 'close'))
        if not isfinite(price) or price <= 0:
            context.logger.warning('Invalid ETF price; skip buy: {}'.format(symbol))
            continue
        budget = min(equity * pending['weights'][symbol], cash)
        if budget < price * 100:
            context.logger.info('Insufficient cash for one ETF lot: {}'.format(symbol))
            continue
        result = context.order_value(symbol, budget)
        if result < 0:
            context.logger.warning('Buy order failed {}: {}'.format(
                symbol, context.get_error_msg(result),
            ))
            continue
        pending['buy_submitted'].append(symbol)
        cash -= budget
        context.logger.info('Buy order submitted: {} value={:.2f}'.format(symbol, budget))
    return bool(pending['buy_submitted'])


def execute_pending_targets(context, data, pending: dict) -> None:
    held = _held_positions(context)
    unrelated = set(held) - set(ETF_UNIVERSE)
    if unrelated:
        raise ValueError('Use a dedicated ETF strategy account; unrelated positions found')
    selected = {
        symbol for symbol, weight in pending['weights'].items() if weight > 0
    }
    if sell_unselected(context, pending, held, selected):
        return
    buy_missing(context, data, pending, held, selected)
    held = _held_positions(context)
    if selected <= set(held):
        context.options[OPTIONS_KEY]['pending'] = None


m9 = M.input_features_dai.v23(
    mode='SQL',
    expr='',
    expr_filters='',
    expr_tables='cn_fund_bar1d',
    extra_fields='date, instrument, close, high, low, volume, amount',
    order_by='date, instrument',
    expr_drop_na=True,
    sql="""select date, instrument, close, high, low, volume, amount
from cn_fund_bar1d
where instrument in ('510300.SH', '510500.SH', '159915.SZ', '588000.SH',
                     '512100.SH', '512880.SH', '512010.SH', '512660.SH',
                     '515050.SH', '518880.SH')
order by date, instrument""",
    extract_data=False,
    m_name='m9',
)

m7 = M.extract_data_dai.v15(
    sql=m9.data,
    start_date=DATA_START_DATE,
    start_date_bound_to_trading_date=True,
    end_date=(date.today() - timedelta(days=1)).isoformat(),
    end_date_bound_to_trading_date=True,
    before_start_days=250,
    debug=False,
    m_name='m7',
)

m8 = M.bigtrader.v17(
    data=m7.data,
    start_date=BACKTEST_START_DATE,
    end_date=(date.today() - timedelta(days=1)).isoformat(),
    initialize=m8_initialize_bigquant_run,
    before_trading_start=m8_before_trading_start_bigquant_run,
    handle_tick=m8_handle_tick_bigquant_run,
    handle_data=m8_handle_data_bigquant_run,
    handle_trade=m8_handle_trade_bigquant_run,
    handle_order=m8_handle_order_bigquant_run,
    after_trading=m8_after_trading_bigquant_run,
    capital_base=1000000,
    frequency='daily',
    product_type='\u80a1\u7968',
    rebalance_period_type='\u4ea4\u6613\u65e5',
    rebalance_period_days='5',
    rebalance_period_roll_forward=True,
    backtest_engine_mode='\u6807\u51c6\u6a21\u5f0f',
    before_start_days=0,
    volume_limit=1,
    order_price_field_buy='open',
    order_price_field_sell='open',
    benchmark='\u6caa\u6df1300\u6307\u6570',
    plot_charts=True,
    debug=False,
    backtest_only=False,
    m_name='m8',
)
