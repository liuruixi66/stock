from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from market_data import Market, MarketDataError, get_provider
from .models import SimulationAccount, SimulationOrder, SimulationPosition


class TradingError(ValueError):
    pass


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)


def create_account(name: str, market: str, initial_cash: Decimal) -> SimulationAccount:
    normalized_market = Market(market.upper())
    if initial_cash <= 0:
        raise TradingError('初始资金必须大于0')
    return SimulationAccount.objects.create(
        name=name,
        market=normalized_market.value,
        currency='CNY' if normalized_market == Market.A_SHARE else 'USD',
        initial_cash=initial_cash,
        cash=initial_cash,
    )


@transaction.atomic
def submit_order(
    account_id: int,
    symbol: str,
    side: str,
    quantity: int,
    order_type: str = 'MARKET',
    requested_price: Decimal | None = None,
) -> SimulationOrder:
    account = SimulationAccount.objects.select_for_update().get(pk=account_id)
    side = side.upper()
    order_type = order_type.upper()
    symbol = symbol.strip().upper()
    if side not in {'BUY', 'SELL'} or order_type not in {'MARKET', 'LIMIT'}:
        raise TradingError('订单方向或类型无效')
    if quantity <= 0:
        raise TradingError('数量必须大于0')
    if account.market == Market.A_SHARE.value and quantity % 100 != 0:
        raise TradingError('A股买卖数量必须为100股的整数倍')
    if order_type == 'LIMIT' and (requested_price is None or requested_price <= 0):
        raise TradingError('限价单必须提供有效价格')

    order = SimulationOrder.objects.create(
        account=account,
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        requested_price=requested_price,
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
        can_fill = requested_price >= market_price if side == 'BUY' else requested_price <= market_price
        if not can_fill:
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
    order.executed_price = executed_price
    order.commission = commission
    order.tax = tax
    order.executed_at = timezone.now()
    order.message = f'成交价来源: {quote.source}'
    order.save()
    return order