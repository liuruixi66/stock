"""迅投 QMT / miniQMT 适配器：A 股券商模拟盘与实盘（国金、国盛、华鑫等提供 QMT 权限的券商）。

只能在 Windows 上运行：需要券商 QMT 客户端以“极简模式”登录，本服务与其同机或共享 userdata_mini 目录。
`pip install xtquant`，或使用仓库内 backend/trading_system/qmt_trader/xtquant。
"""

from __future__ import annotations

import random
import threading
from decimal import Decimal

from .base import (
    AccountSnapshot,
    BrokerAdapter,
    BrokerError,
    OrderResult,
    PositionSnapshot,
    a_share_exchange,
    env,
    require_env,
    to_decimal,
)

_traders: dict[str, object] = {}
_lock = threading.Lock()


def to_qmt_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if '.' in symbol:
        return symbol
    return f'{symbol}.{a_share_exchange(symbol)}'


def from_qmt_symbol(code: str) -> str:
    return str(code).split('.', 1)[0].upper()


def _import_xtquant():
    try:
        from xtquant import xtconstant
        from xtquant.xttrader import XtQuantTrader
        from xtquant.xttype import StockAccount
    except ImportError:
        try:
            from trading_system.qmt_trader.xtquant import xtconstant
            from trading_system.qmt_trader.xtquant.xttrader import XtQuantTrader
            from trading_system.qmt_trader.xtquant.xttype import StockAccount
        except ImportError as exc:
            raise BrokerError(f'无法导入 xtquant（仅支持 Windows）：{exc}。请 pip install xtquant 并安装券商 QMT 客户端') from exc
    return xtconstant, XtQuantTrader, StockAccount


def _shared_trader(path: str, session_id: int):
    """XtQuantTrader 会启动后台线程，按 userdata 路径复用一个连接。"""
    _, XtQuantTrader, _ = _import_xtquant()
    with _lock:
        trader = _traders.get(path)
        if trader is None:
            trader = XtQuantTrader(path, session_id)
            trader.start()
            if trader.connect() != 0:
                trader.stop()
                raise BrokerError(f'无法连接 QMT（{path}），请确认 QMT 客户端已用极简模式登录')
            _traders[path] = trader
        return trader


class QmtBroker(BrokerAdapter):
    code = 'QMT'
    label = '迅投 QMT / miniQMT（xtquant）'
    markets = frozenset({'A'})
    supports_live = True
    sdk_module = 'xtquant'
    sdk_package = 'xtquant'
    env_vars = ('QMT_USERDATA_PATH', 'QMT_SESSION_ID')
    notes = '仅 Windows。向券商申请 QMT 权限后，用极简模式登录客户端；账号 ID 填资金账号，模拟/实盘由登录的客户端决定。'

    def _status(self, xtconstant, raw: int) -> str:
        mapping = {
            xtconstant.ORDER_PART_SUCC: 'PARTIAL',
            xtconstant.ORDER_SUCCEEDED: 'FILLED',
            xtconstant.ORDER_PART_CANCEL: 'CANCELLED',
            xtconstant.ORDER_CANCELED: 'CANCELLED',
            xtconstant.ORDER_JUNK: 'REJECTED',
        }
        return mapping.get(raw, 'SUBMITTED')

    def _client(self):
        xtconstant, _, StockAccount = _import_xtquant()
        path = require_env('QMT_USERDATA_PATH', '填写 QMT 客户端 userdata_mini 目录，例如 D:/国金QMT交易端模拟/userdata_mini')
        session_id = int(env('QMT_SESSION_ID', '0')) or random.randint(100000, 999999)
        account_id = self.account.broker_account_id.strip()
        if not account_id:
            raise BrokerError('QMT 需要在账户上填写资金账号（broker_account_id）')
        trader = _shared_trader(path, session_id)
        account = StockAccount(account_id, 'STOCK')
        if trader.subscribe(account) != 0:
            raise BrokerError(f'QMT 订阅账号 {account_id} 失败，请确认该资金账号已在客户端登录')
        return xtconstant, trader, account

    def _result_from_xt_order(self, xtconstant, xt_order, fallback_id: str) -> OrderResult:
        if xt_order is None:
            return OrderResult(status='SUBMITTED', broker_order_id=fallback_id, message='QMT 已接收委托，等待回报')
        filled = Decimal(int(xt_order.traded_volume or 0))
        price = to_decimal(xt_order.traded_price)
        return OrderResult(
            status=self._status(xtconstant, xt_order.order_status),
            broker_order_id=str(xt_order.order_id),
            filled_quantity=filled,
            executed_price=price if filled > 0 and price > 0 else None,
            message=str(xt_order.status_msg or '') or f'QMT 状态码 {xt_order.order_status}',
        )

    def place_order(self, order) -> OrderResult:
        xtconstant, trader, account = self._client()
        symbol = to_qmt_symbol(order.symbol)
        if order.order_type == 'MARKET':
            price = 0.0
            price_type = {
                'SH': xtconstant.MARKET_SH_CONVERT_5_CANCEL,
                'SZ': xtconstant.MARKET_SZ_CONVERT_5_CANCEL,
            }.get(symbol.rsplit('.', 1)[-1], xtconstant.LATEST_PRICE)
        else:
            price = float(order.requested_price)
            price_type = xtconstant.FIX_PRICE
        order_id = trader.order_stock(
            account, symbol,
            xtconstant.STOCK_BUY if order.side == 'BUY' else xtconstant.STOCK_SELL,
            int(order.quantity), price_type, price, 'stock-clone', f'paper#{order.id}',
        )
        if order_id is None or int(order_id) < 0:
            raise BrokerError('QMT 拒绝了委托（返回 -1）：请检查账号登录状态、资金或标的代码')
        return self._result_from_xt_order(xtconstant, trader.query_stock_order(account, int(order_id)), str(order_id))

    def get_order(self, order) -> OrderResult:
        xtconstant, trader, account = self._client()
        xt_order = trader.query_stock_order(account, int(order.broker_order_id))
        if xt_order is None:
            raise BrokerError(f'QMT 未找到委托 {order.broker_order_id}（仅能查询当日委托）')
        return self._result_from_xt_order(xtconstant, xt_order, order.broker_order_id)

    def cancel_order(self, order) -> OrderResult:
        xtconstant, trader, account = self._client()
        code = trader.cancel_order_stock(account, int(order.broker_order_id))
        if code != 0:
            reasons = {-1: '委托已完成', -2: '未找到对应委托编号', -3: '账号未登录'}
            raise BrokerError(f'QMT 撤单失败：{reasons.get(code, code)}')
        return self._result_from_xt_order(xtconstant, trader.query_stock_order(account, int(order.broker_order_id)), order.broker_order_id)

    def get_account(self) -> AccountSnapshot:
        _, trader, account = self._client()
        asset = trader.query_stock_asset(account)
        if asset is None:
            raise BrokerError('QMT 未返回资金信息')
        return AccountSnapshot(
            cash=to_decimal(asset.cash),
            market_value=to_decimal(asset.market_value),
            total_assets=to_decimal(asset.total_asset),
            frozen_cash=to_decimal(asset.frozen_cash),
            currency='CNY',
        )

    def get_positions(self) -> list[PositionSnapshot]:
        _, trader, account = self._client()
        positions = []
        for item in trader.query_stock_positions(account) or []:
            quantity = Decimal(int(item.volume or 0))
            if quantity <= 0:
                continue
            positions.append(PositionSnapshot(
                symbol=from_qmt_symbol(item.stock_code),
                quantity=quantity,
                average_price=to_decimal(item.open_price),
                available_quantity=Decimal(int(item.can_use_volume or 0)),
                market_value=to_decimal(item.market_value),
            ))
        return positions
