"""账户和订单应用服务。

本层负责把 API/管理命令需要的账户工作流组合起来；订单规则、资金冻结和本地
模拟撮合仍由 `execution.paper_trading` 负责，券商协议仍由 `brokers` 负责。
"""

from decimal import Decimal

from brokers import BrokerError, broker_catalog
from execution.paper_trading import live_trading_enabled
from market_data import MarketDataError, get_provider
from research.analytics import build_account_analytics
from stockmarket.models import SimulationAccount, SimulationOrder
from execution.paper_trading import (
    cancel_order,
    create_account,
    submit_order,
    sync_account,
)


def account_data(account: SimulationAccount) -> dict:
    """将账户模型转换为对外稳定的数据结构，不暴露 ORM 实例。"""
    return {
        'id': account.id,
        'name': account.name,
        'market': account.market,
        'currency': account.currency,
        'initial_cash': float(account.initial_cash),
        'cash': float(account.cash),
        'broker': account.broker,
        'broker_label': account.get_broker_display(),
        'broker_account_id': account.broker_account_id,
        'trading_mode': account.trading_mode,
        'is_external': account.is_external,
        'last_synced_at': account.last_synced_at.isoformat() if account.last_synced_at else None,
    }


def order_data(order: SimulationOrder) -> dict:
    """将订单及券商回报转换为前端可直接展示的数据结构。"""
    return {
        'id': order.id,
        'account_id': order.account_id,
        'symbol': order.symbol,
        'side': order.side,
        'order_type': order.order_type,
        'quantity': float(order.quantity),
        'filled_quantity': float(order.filled_quantity),
        'requested_price': float(order.requested_price) if order.requested_price is not None else None,
        'executed_price': float(order.executed_price) if order.executed_price is not None else None,
        'amount': float(order.executed_price * order.quantity) if order.executed_price is not None else None,
        'commission': float(order.commission),
        'tax': float(order.tax),
        'status': order.status,
        'broker_order_id': order.broker_order_id,
        'message': order.message,
        'created_at': order.created_at.isoformat(),
    }


def create_trading_account(
    name: str,
    market: str,
    initial_cash: Decimal,
    broker: str = 'SIM',
    broker_account_id: str = '',
    trading_mode: str = 'PAPER',
) -> SimulationAccount:
    """建立模拟或券商账户，并沿用执行层统一的市场/券商规则校验。"""
    return create_account(
        name, market, initial_cash, broker, broker_account_id, trading_mode,
    )


def trading_capabilities() -> dict:
    """返回可用券商能力及实盘全局开关，供界面展示和账户创建前检查。"""
    return {
        'brokers': broker_catalog(),
        'live_trading_enabled': live_trading_enabled(),
    }


def sync_trading_account(account_id: int) -> SimulationAccount:
    """读取账户并同步外部券商状态；账户不存在或券商失败时保留原异常语义。"""
    account = SimulationAccount.objects.get(pk=account_id)
    sync_account(account)
    return account


def place_account_order(
    account_id: int,
    symbol: str,
    side: str,
    quantity: Decimal,
    order_type: str = 'MARKET',
    requested_price: Decimal | None = None,
) -> SimulationOrder:
    """统一的应用层报单入口，具体校验与模拟/券商分流由执行层完成。"""
    return submit_order(
        account_id, symbol, side, quantity, order_type, requested_price,
    )


def cancel_account_order(order_id: int) -> SimulationOrder:
    """统一的应用层撤单入口，具体状态校验与券商撤单由执行层完成。"""
    return cancel_order(order_id)


def account_summary(account_id: int) -> dict:
    """同步外部账户后计算持仓市值；行情或同步失败时保留可解释的本地结果。

    券商同步异常放入 `sync_error` 返回，不会伪装为同步成功；单个标的行情不可用时
    暂以持仓成本估值，避免整个账户摘要因一个报价失败而不可读。
    """
    account = SimulationAccount.objects.get(pk=account_id)
    sync_error = None
    if account.is_external:
        try:
            sync_account(account)
        except BrokerError as exc:
            # 保留原有响应语义：摘要仍可返回，但必须把同步故障显式交给调用方。
            sync_error = str(exc)

    positions = []
    market_value = Decimal('0')
    provider = get_provider(account.market)
    for position in account.positions.all():
        try:
            quote = provider.get_quote(position.symbol)
            current_price = Decimal(str(quote.price))
        except MarketDataError:
            current_price = position.average_price
        value = current_price * position.quantity
        market_value += value
        positions.append({
            'symbol': position.symbol,
            'quantity': position.quantity,
            'average_price': float(position.average_price),
            'current_price': float(current_price),
            'market_value': float(value),
            'unrealized_pnl': float(
                (current_price - position.average_price) * position.quantity,
            ),
        })

    total_assets = account.cash + market_value
    return {
        **account_data(account),
        'market_value': float(market_value),
        'total_assets': float(total_assets),
        'total_return': (
            float((total_assets / account.initial_cash - 1) * 100)
            if account.initial_cash else 0.0
        ),
        'positions': positions,
        'sync_error': sync_error,
    }


def account_analytics(account_id: int) -> dict:
    """通过统一的应用入口计算账户已实现/未实现盈亏及成交统计。"""
    account = SimulationAccount.objects.get(pk=account_id)
    return build_account_analytics(account)
