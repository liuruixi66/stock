"""JoinQuant entrypoints; export with manage.py export_joinquant_etf."""

from math import isfinite

from stockmarket.etf_rotation import RotationBar, RotationConfig, build_rotation_targets
from jqdata import *


def initialize(context):
    set_option('avoid_future_data', True)
    set_option('use_real_price', True)
    set_benchmark('510300.XSHG')
    set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.0003,
                             close_commission=0.0003, close_today_commission=0,
                             min_commission=5), type='fund')
    set_slippage(PriceRelatedSlippage(0.002))
    g.rotation_config = RotationConfig()
    g.etf_universe = [
        '510300.XSHG', '510500.XSHG', '159915.XSHE', '588000.XSHG',
        '512100.XSHG', '512880.XSHG', '512010.XSHG', '512660.XSHG',
        '515050.XSHG', '518880.XSHG',
    ]
    g.min_average_money = 20000000
    g.rebalance_threshold = 0.03
    run_weekly(rebalance_etfs, weekday=1, time='10:00', reference_security='510300.XSHG')


def rebalance_etfs(context):
    as_of = context.previous_date
    histories = {}
    for symbol in g.etf_universe:
        info = get_security_info(symbol)
        if info is None:
            log.warn('Unknown ETF: {}'.format(symbol))
            continue
        if (as_of - info.start_date).days < 180:
            log.info('ETF not seasoned: {}'.format(symbol))
            continue
        frame = get_price(
            symbol, end_date=as_of, count=g.rotation_config.history_count,
            frequency='daily', fields=['close', 'high', 'low', 'volume', 'money'],
            skip_paused=False, fq='pre', panel=False,
        )
        if frame is None or len(frame) < g.rotation_config.history_count:
            log.warn('Insufficient ETF history: {}'.format(symbol))
            continue
        money = [float(value) for value in frame['money'].iloc[-20:]]
        if not all(isfinite(value) and value >= 0 for value in money):
            raise ValueError('Invalid turnover data: {}'.format(symbol))
        if sum(money) / len(money) < g.min_average_money:
            log.info('Illiquid ETF: {}'.format(symbol))
            continue
        histories[symbol] = [
            RotationBar(day.date(), float(row['close']), float(row['high']),
                        float(row['low']), float(row['volume']))
            for day, row in frame.iterrows()
        ]
    # Empty usable data is not evidence of a bearish market.
    if not histories:
        raise ValueError('No usable ETF histories; no orders submitted')
    result = build_rotation_targets(histories, as_of, g.rotation_config)
    for symbol, reason in result['rejected'].items():
        log.warn('Excluded {}: {}'.format(symbol, reason))
    if len(result['rejected']) == len(histories):
        raise ValueError('All ETF histories rejected; no orders submitted')
    log.info('ETF research targets: {}'.format(result))
    execute_etf_targets(context, result['weights'])
    record(target_exposure=sum(result['weights'].values()),
           target_cash=result['cash_weight'])


def execute_etf_targets(context, weights):
    if get_open_orders():
        log.warn('Outstanding orders; no duplicate rebalance submitted')
        return
    equity = context.portfolio.total_value
    if not isfinite(equity) or equity <= 0:
        raise ValueError('Portfolio equity must be positive and finite')
    current_data = get_current_data()
    targets = {symbol: equity * weight for symbol, weight in weights.items()}
    if any(not isfinite(weight) or weight < 0 or weight > g.rotation_config.max_weight
           for weight in weights.values()):
        raise ValueError('Invalid target weights')
    if sum(weights.values()) > g.rotation_config.max_exposure + 1e-10:
        raise ValueError('Target exposure exceeds limit')
    sales_complete = True
    for symbol in sorted(set(context.portfolio.positions) | set(targets)):
        position = context.portfolio.positions.get(symbol)
        held_value = position.value if position is not None else 0
        target = targets.get(symbol, 0)
        if held_value <= target:
            continue
        if target > 0 and held_value - target < equity * g.rebalance_threshold:
            continue
        snapshot = current_data[symbol]
        if snapshot.paused or not isfinite(snapshot.last_price) or snapshot.last_price <= 0:
            log.warn('Cannot sell paused/invalid-price ETF: {}'.format(symbol))
            sales_complete = False
            continue
        if (snapshot.last_price <= snapshot.low_limit or position.closeable_amount <= 0
                or (target == 0 and position.closeable_amount < position.total_amount)):
            log.warn('Cannot sell limit-down/T+1 ETF: {}'.format(symbol))
            sales_complete = False
            continue
        order = order_target_value(symbol, target)
        if order is None or order.amount <= 0 or order.filled < order.amount:
            log.warn('Sell rejected/unfilled; defer new buys: {}'.format(symbol))
            sales_complete = False
    if not sales_complete:
        log.warn('Unresolved reductions; no new buys this rebalance')
        return
    for symbol in sorted(targets, key=lambda code: (-targets[code], code)):
        position = context.portfolio.positions.get(symbol)
        held_value = position.value if position is not None else 0
        increase = targets[symbol] - held_value
        if increase <= 0 or increase < equity * g.rebalance_threshold:
            continue
        snapshot = current_data[symbol]
        if (snapshot.paused or not isfinite(snapshot.last_price) or snapshot.last_price <= 0
                or snapshot.last_price >= snapshot.high_limit):
            log.warn('Cannot buy paused/limit-up/invalid-price ETF: {}'.format(symbol))
            continue
        gross = sum(position.value for position in context.portfolio.positions.values())
        room = max(0, equity * g.rotation_config.max_exposure - gross)
        affordable = max(0, context.portfolio.available_cash - 5)
        increase = min(increase, room, affordable) * 0.995
        if increase < snapshot.last_price * 100:
            log.info('Below one ETF lot/budget: {}'.format(symbol))
            continue
        order = order_target_value(symbol, held_value + increase)
        if order is None or order.amount <= 0 or order.filled < order.amount:
            log.warn('Buy rejected/unfilled; stop remaining buys: {}'.format(symbol))
            break
