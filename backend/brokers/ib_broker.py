"""盈透 IBKR 适配器：通过 TWS 或 IB Gateway 的 API 端口交易美股（Paper: 7497/4002，Live: 7496/4001）。

`pip install ib_async`（ib_insync 的维护分支，API 相同；也兼容旧的 ib_insync）。
"""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
from decimal import Decimal

from .base import (
    AccountSnapshot,
    BrokerAdapter,
    BrokerError,
    OrderResult,
    PositionSnapshot,
    env,
    to_decimal,
)

_STATUS_MAP = {
    'PendingSubmit': 'SUBMITTED',
    'PendingCancel': 'SUBMITTED',
    'PreSubmitted': 'SUBMITTED',
    'Submitted': 'SUBMITTED',
    'ApiPending': 'SUBMITTED',
    'Filled': 'FILLED',
    'Cancelled': 'CANCELLED',
    'ApiCancelled': 'CANCELLED',
    'Inactive': 'REJECTED',
}


def _import_ib():
    try:
        import ib_async as module
    except ImportError:
        try:
            import ib_insync as module
        except ImportError as exc:
            raise BrokerError(f'未安装 IB SDK：{exc}。请执行 pip install ib_async') from exc
    return module


class IbBroker(BrokerAdapter):
    code = 'IB'
    label = '盈透 IBKR（TWS / IB Gateway）'
    markets = frozenset({'US'})
    supports_live = True
    sdk_module = 'ib_async'
    sdk_package = 'ib_async'
    env_vars = ('IB_HOST', 'IB_PORT', 'IB_CLIENT_ID')
    notes = '开户后在 TWS/IB Gateway 中启用 API（Enable ActiveX and Socket Clients），模拟账号以 DU 开头；IB_PORT 默认模拟 7497、实盘 7496。'

    @contextmanager
    def _session(self):
        module = _import_ib()
        host = env('IB_HOST', '127.0.0.1')
        port = int(env('IB_PORT', '7496' if self.is_live else '7497'))
        client_id = int(env('IB_CLIENT_ID', '17'))
        # Django 工作线程默认没有事件循环，而 ib_async 的同步接口依赖它
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        ib = module.IB()
        try:
            ib.connect(host, port, clientId=client_id, timeout=10)
        except Exception as exc:
            raise BrokerError(f'无法连接 IB（{host}:{port}）：{exc}。请确认 TWS/IB Gateway 已登录并启用 API') from exc
        try:
            yield module, ib
        finally:
            ib.disconnect()

    def _account_code(self, ib) -> str:
        configured = self.account.broker_account_id.strip()
        if configured:
            return configured
        accounts = ib.managedAccounts()
        if not accounts:
            raise BrokerError('IB 未返回任何账号，请在账户上填写 broker_account_id')
        return accounts[0]

    def _contract(self, module, ib, symbol: str):
        contract = module.Stock(symbol.strip().upper(), 'SMART', 'USD')
        qualified = ib.qualifyContracts(contract)
        if not qualified:
            raise BrokerError(f'IB 无法识别合约 {symbol}')
        return qualified[0]

    @staticmethod
    def _result_from_trade(trade) -> OrderResult:
        status = trade.orderStatus
        mapped = _STATUS_MAP.get(status.status, 'SUBMITTED')
        filled = to_decimal(status.filled)
        if mapped == 'SUBMITTED' and filled > 0:
            mapped = 'PARTIAL'
        price = to_decimal(status.avgFillPrice)
        message = trade.log[-1].message if getattr(trade, 'log', None) else ''
        return OrderResult(
            status=mapped,
            broker_order_id=str(trade.order.permId or trade.order.orderId),
            filled_quantity=filled,
            executed_price=price if filled > 0 and price > 0 else None,
            message=message or f'IB 状态: {status.status}',
        )

    def _find_trade(self, ib, broker_order_id: str):
        wanted = int(broker_order_id)
        candidates = list(ib.trades())
        try:
            candidates += list(ib.reqCompletedOrders(False))
        except Exception:  # 部分网关版本不支持 completed orders 查询
            pass
        for trade in candidates:
            if wanted in (trade.order.permId, trade.order.orderId):
                return trade
        return None

    def place_order(self, order) -> OrderResult:
        with self._session() as (module, ib):
            contract = self._contract(module, ib, order.symbol)
            quantity = float(order.quantity)
            if order.order_type == 'MARKET':
                ib_order = module.MarketOrder(order.side, quantity)
            else:
                ib_order = module.LimitOrder(order.side, quantity, float(order.requested_price))
            ib_order.account = self._account_code(ib)
            trade = ib.placeOrder(contract, ib_order)
            ib.sleep(1.5)  # 等待 openOrder/orderStatus 回报填入 permId 与状态
            return self._result_from_trade(trade)

    def get_order(self, order) -> OrderResult:
        with self._session() as (_module, ib):
            ib.sleep(0.5)
            trade = self._find_trade(ib, order.broker_order_id)
            if trade is None:
                raise BrokerError(f'IB 未找到委托 {order.broker_order_id}（可能已在 TWS 中归档）')
            return self._result_from_trade(trade)

    def cancel_order(self, order) -> OrderResult:
        with self._session() as (_module, ib):
            ib.sleep(0.5)
            trade = self._find_trade(ib, order.broker_order_id)
            if trade is None:
                raise BrokerError(f'IB 未找到可撤销的委托 {order.broker_order_id}')
            ib.cancelOrder(trade.order)
            ib.sleep(1.0)
            return self._result_from_trade(trade)

    def get_account(self) -> AccountSnapshot:
        with self._session() as (_module, ib):
            code = self._account_code(ib)
            values = {}
            for item in ib.accountValues(code):
                # 优先取 USD 计价，缺失时才退回 BASE 计价
                if item.currency == 'USD' or (item.currency == 'BASE' and item.tag not in values):
                    values[item.tag] = item.value
            if 'NetLiquidation' not in values:
                raise BrokerError(f'IB 未返回账号 {code} 的资产数据')
            return AccountSnapshot(
                cash=to_decimal(values.get('TotalCashValue')),
                market_value=to_decimal(values.get('GrossPositionValue')),
                total_assets=to_decimal(values.get('NetLiquidation')),
                currency='USD',
                raw={key: str(value) for key, value in values.items()},
            )

    def get_positions(self) -> list[PositionSnapshot]:
        with self._session() as (_module, ib):
            code = self._account_code(ib)
            positions = []
            for item in ib.portfolio(code):
                quantity = to_decimal(item.position)
                if quantity <= 0 or item.contract.secType != 'STK':
                    continue
                positions.append(PositionSnapshot(
                    symbol=item.contract.symbol,
                    quantity=quantity,
                    average_price=to_decimal(item.averageCost),
                    market_value=to_decimal(item.marketValue),
                ))
            if positions:
                return positions
            return [
                PositionSnapshot(symbol=p.contract.symbol, quantity=to_decimal(p.position), average_price=to_decimal(p.avgCost))
                for p in ib.positions(code)
                if p.contract.secType == 'STK' and Decimal(str(p.position)) > 0
            ]

    def list_accounts(self) -> list[dict]:
        with self._session() as (_module, ib):
            return [{'acc_id': code, 'trd_env': 'PAPER' if code.startswith('D') else 'LIVE'} for code in ib.managedAccounts()]
