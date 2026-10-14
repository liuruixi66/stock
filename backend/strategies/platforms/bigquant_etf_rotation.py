"""BigTrader daily ETF research adapter; export before uploading to AIStudio."""

from datetime import date
from datetime import timedelta
from importlib import import_module
from math import isfinite
from numbers import Real
from typing import Dict
from typing import Mapping
from typing import Optional
from typing import Protocol

import pandas as pd

from strategies.etf_rotation import RotationBar
from strategies.etf_rotation import RotationConfig
from strategies.etf_rotation import build_rotation_targets


ETF_UNIVERSE = (
    '510300.SH', '510500.SH', '159915.SZ', '588000.SH', '512100.SH',
    '512880.SH', '512010.SH', '512660.SH', '515050.SH', '518880.SH',
)
REQUIRED_COLUMNS = {'date', 'instrument', 'close', 'high', 'low', 'volume', 'amount'}
MIN_AVERAGE_AMOUNT = 20000000
REBALANCE_THRESHOLD = 0.03
STATE_KEY = 'etf_rotation_pending_v1'
SIGNAL_KEY = 'etf_rotation_signal_date_v1'
ATTEMPT_KEY = 'etf_rotation_attempt_date_v1'
WEEK_KEY = 'etf_rotation_signal_week_v1'


class Position(Protocol):
    current_qty: int
    avail_qty: int
    market_value: float


class Logger(Protocol):
    def info(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...


class UserStore(Protocol):
    def init_once(self, **kwargs: object) -> None: ...
    def __getitem__(self, key: str): ...
    def __setitem__(self, key: str, value: object) -> None: ...


class BigQuantContext(Protocol):
    user_store: UserStore
    logger: Logger

    def get_positions(self) -> Mapping[str, Position]: ...
    def get_open_orders(self): ...
    def get_portfolio_value(self) -> float: ...
    def get_available_cash(self) -> float: ...
    def get_last_price(self, instrument: str) -> float: ...
    def order(self, instrument: str, order_qty: int) -> int: ...
    def get_error_msg(self, return_code: int) -> str: ...
    def set_commission(self, commission: object) -> None: ...
    def set_slippage_value(self, slippage_type: int, slippage_value: float) -> None: ...


def initialize(context: BigQuantContext) -> None:
    if not hasattr(context, 'user_store'):
        raise RuntimeError(
            'This strategy requires bigquant.bigtrader.run and its persistent user_store; '
            'M.bigtrader.v30 / bigtraderv1 is not supported. Do not substitute an '
            'in-memory dictionary for paper trading persistence.'
        )
    if not callable(getattr(context.user_store, 'init_once', None)):
        raise RuntimeError('BigTrader user_store.init_once is required for daily persistence')
    bigtrader = import_module('bigquant.bigtrader')
    context.set_commission(
        bigtrader.PerOrder(buy_cost=0.0003, sell_cost=0.0003, min_cost=5, tax_ratio=0),
    )
    context.set_slippage_value(slippage_type=2, slippage_value=0.002)
    context.user_store.init_once(**{
        STATE_KEY: None, SIGNAL_KEY: '', ATTEMPT_KEY: '', WEEK_KEY: '',
    })
    context.logger.info('ETF research V1: daily signals, next-bar execution; paper use only')


def load_fund_history(as_of: date) -> pd.DataFrame:
    dai = import_module('dai')
    instruments = ', '.join("'{}'".format(symbol) for symbol in ETF_UNIVERSE)
    sql = (
        'SELECT date, instrument, close, high, low, volume, amount '
        'FROM cn_fund_bar1d WHERE instrument IN ({}) ORDER BY instrument, date'
    ).format(instruments)
    frame = dai.query(sql, filters={
        'date': [(as_of - timedelta(days=600)).isoformat(), as_of.isoformat()],
    }).df()
    if not isinstance(frame, pd.DataFrame):
        raise ValueError('cn_fund_bar1d query did not return a DataFrame')
    return frame


def _number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError('Non-numeric fund field {}: {}'.format(field, type(value)))
    return float(value)


def targets_from_fund_frame(
    frame: pd.DataFrame, as_of: date, config: Optional[RotationConfig] = None,
) -> dict:
    config = config or RotationConfig()
    config.validate()
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError('Missing cn_fund_bar1d fields: {}'.format(sorted(missing)))
    frame = frame.copy()
    frame['date'] = pd.to_datetime(frame['date'], errors='raise').dt.date
    if frame['date'].isna().any():
        raise ValueError('Fund history contains missing dates')
    frame = frame[frame['date'] <= as_of]
    histories = {}
    excluded = {}
    for symbol in ETF_UNIVERSE:
        rows = frame[frame['instrument'] == symbol]
        if rows.empty:
            excluded[symbol] = 'missing_history'
            continue
        if rows['date'].duplicated().any():
            raise ValueError('Duplicate ETF dates: {}'.format(symbol))
        rows = rows.sort_values('date')
        if rows['date'].iloc[-1] != as_of:
            excluded[symbol] = 'stale_history'
            continue
        if len(rows) < config.history_count:
            excluded[symbol] = 'insufficient_history'
            continue
        # Observed coverage is a conservative seasoning proxy, not listing metadata.
        if (as_of - rows['date'].iloc[0]).days < 180:
            excluded[symbol] = 'observed_history_under_180_days'
            continue
        amounts = [_number(value, 'amount') for value in rows['amount'].iloc[-20:]]
        if not all(isfinite(value) and value >= 0 for value in amounts):
            raise ValueError('Invalid ETF amount: {}'.format(symbol))
        if sum(amounts) / len(amounts) < MIN_AVERAGE_AMOUNT:
            excluded[symbol] = 'illiquid'
            continue
        bars = []
        for row in rows.itertuples(index=False):
            if not isinstance(row.date, date):
                raise ValueError('Invalid fund bar date: {}'.format(symbol))
            bars.append(RotationBar(
                row.date, _number(row.close, 'close'), _number(row.high, 'high'),
                _number(row.low, 'low'), _number(row.volume, 'volume'),
            ))
        histories[symbol] = bars
    if not histories:
        raise ValueError('No usable ETF histories; no orders submitted: {}'.format(excluded))
    result = build_rotation_targets(histories, as_of, config)
    result['rejected'].update(excluded)
    if not result['features']:
        raise ValueError('All ETF histories rejected; no orders submitted: {}'.format(
            result['rejected'],
        ))
    result['weights'] = {symbol: result['weights'].get(symbol, 0.0) for symbol in ETF_UNIVERSE}
    return result


def handle_data(context: BigQuantContext, data) -> None:
    signal_day = data.current_dt.date()
    day_text = signal_day.isoformat()
    iso_year, iso_week, _ = signal_day.isocalendar()
    week_text = '{}-{:02d}'.format(iso_year, iso_week)
    if context.get_open_orders():
        context.logger.warning('Outstanding orders; defer ETF rebalance')
        return
    if context.user_store[ATTEMPT_KEY] == day_text:
        return
    if context.user_store[WEEK_KEY] != week_text:
        result = targets_from_fund_frame(load_fund_history(signal_day), signal_day)
        held = {symbol for symbol, position in context.get_positions().items()
                if position.current_qty > 0}
        unreliable = {
            symbol: reason for symbol, reason in result['rejected'].items()
            if symbol in held and reason != 'illiquid'
        }
        if unreliable:
            raise ValueError('Held ETF data unavailable; no orders submitted: {}'.format(
                unreliable,
            ))
        context.logger.info('ETF targets: {}'.format(result))
        context.user_store[STATE_KEY] = {
            'signal_date': day_text, 'weights': result['weights'],
        }
        context.user_store[SIGNAL_KEY] = day_text
        context.user_store[WEEK_KEY] = week_text
    pending = context.user_store[STATE_KEY]
    if pending is None:
        return
    if (signal_day - date.fromisoformat(pending['signal_date'])).days > 7:
        context.logger.warning('ETF target expired; wait for a new weekly signal')
        context.user_store[STATE_KEY] = None
        return
    context.user_store[ATTEMPT_KEY] = day_text
    if execute_targets(context, data, pending['weights']):
        context.user_store[STATE_KEY] = None


def _send_order(context: BigQuantContext, symbol: str, quantity: int) -> bool:
    result = context.order(symbol, quantity)
    if not isinstance(result, int):
        raise ValueError('Unexpected BigTrader order return type: {}'.format(type(result)))
    if result < 0:
        context.logger.warning('Order failed {} x {}: {}'.format(
            symbol, quantity, context.get_error_msg(result),
        ))
        return False
    context.logger.info('Order sent (not a fill) {} x {}, return={}'.format(
        symbol, quantity, result,
    ))
    return True


def _price_if_active(context: BigQuantContext, data, symbol: str) -> Optional[float]:
    price = float(context.get_last_price(symbol))
    volume = float(data.current(symbol, 'volume'))
    if not isfinite(price) or price <= 0 or not isfinite(volume) or volume <= 0:
        context.logger.warning('Inactive/invalid-price ETF: {}'.format(symbol))
        return None
    return price


def execute_targets(context: BigQuantContext, data, weights: Dict[str, float]) -> bool:
    """Return False while reductions/orders remain unresolved; never assume fills."""
    config = RotationConfig()
    if (any(symbol not in ETF_UNIVERSE or not isfinite(weight)
            or not 0 <= weight <= config.max_weight for symbol, weight in weights.items())
            or sum(weights.values()) > config.max_exposure + 1e-10):
        raise ValueError('Invalid ETF target weights')
    equity = float(context.get_portfolio_value())
    cash = float(context.get_available_cash())
    if not isfinite(equity) or equity <= 0 or not isfinite(cash) or cash < 0:
        raise ValueError('Portfolio equity/cash is invalid')
    if context.get_open_orders():
        context.logger.warning('Outstanding orders; no duplicate orders')
        return False
    positions = context.get_positions()
    if any(symbol not in ETF_UNIVERSE and position.current_qty > 0
           for symbol, position in positions.items()):
        raise ValueError('Use a dedicated ETF strategy account; unrelated positions found')
    if any(position.current_qty < 0 or position.avail_qty < 0
           or not isfinite(position.market_value) or position.market_value < 0
           for position in positions.values()):
        raise ValueError('Invalid or short ETF position')
    threshold = equity * REBALANCE_THRESHOLD
    needs_reduction = False
    for symbol in sorted(positions):
        position = positions[symbol]
        if position.current_qty == 0:
            continue
        target = equity * weights.get(symbol, 0)
        reduction = position.market_value - target
        if reduction <= 0 or (target > 0 and reduction < threshold):
            continue
        price = _price_if_active(context, data, symbol)
        if price is None:
            needs_reduction = True
            continue
        quantity = position.current_qty if target == 0 else int(reduction / price / 100) * 100
        if quantity == 0:
            context.logger.info('ETF reduction below one lot: {}'.format(symbol))
            continue
        quantity = min(quantity, position.avail_qty, position.current_qty)
        needs_reduction = True
        if quantity <= 0:
            context.logger.warning('No sellable ETF shares (T+1): {}'.format(symbol))
            continue
        if not _send_order(context, symbol, -quantity):
            return False
    if needs_reduction:
        context.logger.info('Reductions pending; verify actual holdings on a later daily bar')
        return False
    gross = sum(position.market_value for position in positions.values())
    exposure_room = max(0.0, equity * config.max_exposure - gross)
    sent_buy = False
    for symbol in sorted(weights, key=lambda code: (-weights[code], code)):
        position = positions.get(symbol)
        held_value = position.market_value if position is not None else 0.0
        increase = equity * weights[symbol] - held_value
        if increase <= 0 or increase < threshold:
            continue
        price = _price_if_active(context, data, symbol)
        if price is None:
            return False
        budget = min(increase, exposure_room, max(0.0, cash - 5)) / 1.005
        quantity = int(budget / price / 100) * 100
        if quantity < 100:
            context.logger.info('Below one ETF lot/remaining budget: {}'.format(symbol))
            continue
        if not _send_order(context, symbol, quantity):
            return False
        sent_buy = True
        value = quantity * price
        # Reserve locally too: the asynchronous engine may not freeze cash yet.
        cash -= value * 1.005 + 5
        exposure_room -= value
    return not sent_buy


def run_backtest(start_date='2024-01-01', end_date=None, capital_base=100000):
    """AIStudio entrypoint. This creates a backtest, not a live broker session."""
    if end_date is None:
        end_date = (date.today() - timedelta(days=1)).isoformat()
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    if start > end or end >= date.today():
        raise ValueError('Require start_date <= end_date < today')
    if not isfinite(capital_base) or capital_base <= 0:
        raise ValueError('capital_base must be positive and finite')
    bigtrader = import_module('bigquant.bigtrader')
    return bigtrader.run(
        market=bigtrader.Market.CN_FUND, frequency=bigtrader.Frequency.DAILY,
        start_date=start_date, end_date=end_date, instruments=list(ETF_UNIVERSE),
        initialize=initialize, handle_data=handle_data,
        capital_base=capital_base, volume_limit=0.025,
        order_price_field_buy='open', order_price_field_sell='open',
        benchmark='000300.SH',
    )


if __name__ == '__main__':
    performance = run_backtest()
