import os
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from brokers import OPEN_STATUSES, BrokerError, OrderResult, adapter_class, get_broker, is_external
from market_data import Market, MarketDataError, get_provider
from .models import SimulationAccount, SimulationOrder, SimulationPosition


class TradingError(ValueError):
    """模拟交易请求不符合账户或市场规则时抛出的业务异常。"""

    pass


def _money(value: Decimal) -> Decimal:
    """将金额统一保留四位小数，避免交易过程产生过多小数位。"""
    return value.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)


def live_trading_enabled() -> bool:
    """实盘下单的全局开关，避免误把实盘账户当模拟盘操作。"""
    return os.getenv('LIVE_TRADING_ENABLED', '').strip().lower() in {'1', 'true', 'yes', 'on'}


def create_account(
    name: str,
    market: str,
    initial_cash: Decimal,
    broker: str = 'SIM',
    broker_account_id: str = '',
    trading_mode: str = 'PAPER',
) -> SimulationAccount:
    """创建账户：内置模拟账户按初始资金建账，外部券商账户先连通券商并以其当前总资产作为基准。"""
    normalized_market = Market(market.upper())
    broker = (broker or 'SIM').upper()
    trading_mode = (trading_mode or 'PAPER').upper()
    if broker not in dict(SimulationAccount.BROKER_CHOICES):
        raise TradingError(f'不支持的券商类型: {broker}')
    if trading_mode not in dict(SimulationAccount.MODE_CHOICES):
        raise TradingError(f'交易模式无效: {trading_mode}')
    account = SimulationAccount(
        name=name,
        market=normalized_market.value,
        currency={
            Market.A_SHARE: 'CNY',
            Market.US: 'USD',
            Market.CRYPTO: 'USDT',
        }[normalized_market],
        initial_cash=initial_cash,
        cash=initial_cash,
        broker=broker,
        broker_account_id=broker_account_id.strip(),
        trading_mode=trading_mode,
    )
    if not is_external(broker):
        if initial_cash <= 0:
            raise TradingError('初始资金必须大于0')
        account.trading_mode = 'PAPER'
        account.save()
        return account

    adapter_cls = adapter_class(broker)
    if normalized_market.value not in adapter_cls.markets:
        raise TradingError(f'{adapter_cls.label} 不支持 {normalized_market.value} 市场')
    if trading_mode == 'LIVE' and not adapter_cls.supports_live:
        raise TradingError(f'{adapter_cls.label} 不支持实盘')
    try:
        snapshot = adapter_cls(account).get_account()
    except BrokerError as exc:
        raise TradingError(f'无法连接券商：{exc}') from exc
    # 以绑定时的券商总资产作为收益率基准
    account.initial_cash = _money(snapshot.total_assets)
    account.cash = _money(snapshot.cash)
    account.save()
    sync_account(account)
    return account


def _validate_order(account: SimulationAccount, symbol: str, side: str, quantity: Decimal,
                    order_type: str, requested_price: Decimal | None) -> None:
    if side not in {'BUY', 'SELL'} or order_type not in {'MARKET', 'LIMIT'}:
        raise TradingError('订单方向或类型无效')
    if not symbol:
        raise TradingError('请提供标的代码')
    if quantity <= 0:
        raise TradingError('数量必须大于0')
    if account.market == Market.A_SHARE.value and quantity % 1 != 0:
        raise TradingError('A股数量必须为整数')
    if account.market == Market.A_SHARE.value and side == 'BUY' and quantity % 100 != 0:
        raise TradingError('A股买入数量必须为100股的整数倍')
    if account.market == Market.US.value and account.is_external and quantity % 1 != 0:
        raise TradingError('券商账户的美股数量必须为整数')
    if order_type == 'LIMIT' and (requested_price is None or requested_price <= 0):
        raise TradingError('限价单必须提供有效价格')
    if account.trading_mode == 'LIVE' and not live_trading_enabled():
        raise TradingError('实盘下单未启用：请在服务端设置环境变量 LIVE_TRADING_ENABLED=1 后重试')


def _apply_result(order: SimulationOrder, result: OrderResult) -> SimulationOrder:
    order.status = result.status
    if result.broker_order_id:
        order.broker_order_id = result.broker_order_id
    order.filled_quantity = result.filled_quantity
    if result.executed_price is not None:
        order.executed_price = _money(result.executed_price)
    order.commission = _money(result.commission)
    order.tax = _money(result.tax)
    order.message = result.message[:200]
    if result.status == 'FILLED' and order.executed_at is None:
        order.executed_at = timezone.now()
    order.save()
    return order


def submit_order(
    account_id: int,
    symbol: str,
    side: str,
    quantity: Decimal,
    order_type: str = 'MARKET',
    requested_price: Decimal | None = None,
) -> SimulationOrder:
    """校验订单：内置模拟账户立即本地撮合，外部券商账户则转发给券商并记录券商委托号。"""
    side = side.upper()
    order_type = order_type.upper()
    symbol = symbol.strip().upper()
    with transaction.atomic():
        account = SimulationAccount.objects.select_for_update().get(pk=account_id)
        _validate_order(account, symbol, side, quantity, order_type, requested_price)
        order = SimulationOrder.objects.create(
            account=account,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            requested_price=requested_price,
        )
        if not account.is_external:
            return _fill_locally(account, order)
    # 外部券商的网络调用放在行锁之外，避免长时间锁表
    try:
        result = get_broker(account).place_order(order)
    except BrokerError as exc:
        result = OrderResult(status='REJECTED', message=str(exc))
    return _apply_result(order, result)


def _fill_locally(account: SimulationAccount, order: SimulationOrder) -> SimulationOrder:
    """使用行情源报价立即撮合内置模拟订单。

    成交价包含滑点，A 股卖出另外收取印花税，失败的行情、资金和持仓校验会保留拒单记录。
    """
    side, order_type, symbol, quantity, requested_price = (
        order.side, order.order_type, order.symbol, order.quantity, order.requested_price,
    )
    try:
        quote = get_provider(account.market).get_quote(symbol)
    except MarketDataError as exc:
        order.status = 'REJECTED'
        order.message = str(exc)
        order.save(update_fields=['status', 'message'])
        return order

    market_price = Decimal(str(quote.price))
    if order_type == 'LIMIT':
        if requested_price is None:
            raise TradingError('限价单必须提供有效价格')
        can_fill = requested_price >= market_price if side == 'BUY' else requested_price <= market_price
        if not can_fill:
            # 限价未触发时保留订单，但不改变现金和持仓。
            order.message = f'当前价 {market_price} 未触及限价'
            order.save(update_fields=['message'])
            return order

    slippage = account.slippage_bps / Decimal('10000')
    executed_price = market_price * (Decimal('1') + slippage if side == 'BUY' else Decimal('1') - slippage)
    executed_price = _money(executed_price)
    gross = executed_price * quantity
    commission = _money(max(gross * account.commission_rate, Decimal('0.01')))
    tax_rate = Decimal('0.0005') if account.market == Market.A_SHARE.value and side == 'SELL' else Decimal('0')
    tax = _money(gross * tax_rate)

    position = SimulationPosition.objects.select_for_update().filter(account=account, symbol=symbol).first()
    if side == 'BUY':
        total_cost = gross + commission
        if account.cash < total_cost:
            order.status = 'REJECTED'
            order.message = '可用资金不足'
            order.save(update_fields=['status', 'message'])
            return order
        old_quantity = position.quantity if position else 0
        old_cost = position.average_price * old_quantity if position else Decimal('0')
        if position is None:
            position = SimulationPosition(account=account, symbol=symbol, quantity=0, average_price=0)
        # 新均价只合并成交金额，不把历史佣金重复计入持仓成本。
        position.quantity += quantity
        position.average_price = _money((old_cost + gross) / position.quantity)
        account.cash -= total_cost
        position.save()
    else:
        if position is None or position.quantity < quantity:
            order.status = 'REJECTED'
            order.message = '可卖持仓不足'
            order.save(update_fields=['status', 'message'])
            return order
        position.quantity -= quantity
        account.cash += gross - commission - tax
        if position.quantity == 0:
            position.delete()
        else:
            position.save(update_fields=['quantity', 'updated_at'])

    account.cash = _money(account.cash)
    account.save(update_fields=['cash', 'updated_at'])
    order.status = 'FILLED'
    order.filled_quantity = quantity
    order.executed_price = executed_price
    order.commission = commission
    order.tax = tax
    order.executed_at = timezone.now()
    order.message = f'成交价来源: {quote.source}'
    order.save()
    return order


def cancel_order(order_id: int) -> SimulationOrder:
    """撤销未完成的委托；内置模拟账户只需把待成交的限价单标记为已撤销。"""
    order = SimulationOrder.objects.select_related('account').get(pk=order_id)
    if order.status not in OPEN_STATUSES:
        raise TradingError(f'订单状态为 {order.status}，无法撤单')
    if not order.account.is_external:
        return _apply_result(order, OrderResult(status='CANCELLED', message='用户撤单'))
    if not order.broker_order_id:
        return _apply_result(order, OrderResult(status='CANCELLED', message='券商未返回委托号，已在本地撤销'))
    try:
        result = get_broker(order.account).cancel_order(order)
    except BrokerError as exc:
        raise TradingError(str(exc)) from exc
    return _apply_result(order, result)


def sync_account(account: SimulationAccount) -> SimulationAccount:
    """从券商拉取资金、持仓和未完成委托的最新状态，覆盖本地缓存。"""
    if not account.is_external:
        return account
    broker = get_broker(account)
    snapshot = broker.get_account()
    positions = broker.get_positions()
    open_orders = list(
        SimulationOrder.objects.filter(account=account, status__in=OPEN_STATUSES).exclude(broker_order_id='')
    )
    results: list[tuple[SimulationOrder, OrderResult]] = []
    for order in open_orders:
        try:
            results.append((order, broker.get_order(order)))
        except BrokerError as exc:
            results.append((order, OrderResult(
                status=order.status, broker_order_id=order.broker_order_id,
                filled_quantity=order.filled_quantity, message=f'同步失败: {exc}',
            )))
    with transaction.atomic():
        account.cash = _money(snapshot.cash)
        account.last_synced_at = timezone.now()
        account.save(update_fields=['cash', 'last_synced_at', 'updated_at'])
        SimulationPosition.objects.filter(account=account).delete()
        SimulationPosition.objects.bulk_create([
            SimulationPosition(
                account=account,
                symbol=item.symbol,
                quantity=item.quantity,
                average_price=_money(item.average_price),
            )
            for item in positions
        ])
        for order, result in results:
            _apply_result(order, result)
    return account