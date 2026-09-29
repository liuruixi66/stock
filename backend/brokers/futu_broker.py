"""富途 OpenD 适配器：A 股/美股模拟盘，美股（及 A 股通）实盘。

需要本机运行 OpenD（macOS / Windows / Linux 均可），并 `pip install futu-api`。
"""

from __future__ import annotations

from contextlib import contextmanager

from .base import (
    AccountSnapshot,
    BrokerAdapter,
    BrokerError,
    OrderResult,
    PositionSnapshot,
    a_share_exchange,
    env,
    import_sdk,
    to_decimal,
)

_STATUS_MAP = {
    'WAITING_SUBMIT': 'SUBMITTED',
    'SUBMITTING': 'SUBMITTED',
    'SUBMITTED': 'SUBMITTED',
    'NONE': 'SUBMITTED',
    'UNKNOWN': 'SUBMITTED',
    'FILLED_PART': 'PARTIAL',
    'FILLED_ALL': 'FILLED',
    'CANCELLED_PART': 'CANCELLED',
    'CANCELLED_ALL': 'CANCELLED',
    'DELETED': 'CANCELLED',
    'DISABLED': 'CANCELLED',
    'FILL_CANCELLED': 'CANCELLED',
    'FAILED': 'REJECTED',
    'TIMEOUT': 'REJECTED',
}


def to_futu_symbol(market: str, symbol: str) -> str:
    symbol = symbol.strip().upper()
    if '.' in symbol:
        return symbol
    if market == 'A':
        return f'{a_share_exchange(symbol)}.{symbol}'
    return f'US.{symbol}'


def from_futu_symbol(code: str) -> str:
    return str(code).split('.', 1)[-1].upper()


class FutuBroker(BrokerAdapter):
    code = 'FUTU'
    label = '富途 OpenD（futu-api）'
    markets = frozenset({'A', 'US'})
    supports_live = True
    sdk_module = 'futu'
    sdk_package = 'futu-api'
    env_vars = ('FUTU_OPEND_HOST', 'FUTU_OPEND_PORT', 'FUTU_SECURITY_FIRM', 'FUTU_TRADE_PASSWORD')
    notes = '注册富途/moomoo 账号后下载 OpenD 并登录；模拟盘无需入金，A 股模拟走 CN 市场，实盘 A 股通走 HKCC。'

    def _trd_market(self, futu):
        if self.account.market == 'US':
            return futu.TrdMarket.US
        return futu.TrdMarket.HKCC if self.is_live else futu.TrdMarket.CN

    def _trd_env(self, futu):
        return futu.TrdEnv.REAL if self.is_live else futu.TrdEnv.SIMULATE

    def _acc_id(self) -> int:
        value = self.account.broker_account_id.strip()
        if not value:
            return 0
        try:
            return int(value)
        except ValueError as exc:
            raise BrokerError('富途 acc_id 必须是数字，可通过 OpenD 的 get_acc_list 查询') from exc

    @contextmanager
    def _session(self):
        futu = import_sdk('futu', 'futu-api')
        host = env('FUTU_OPEND_HOST', '127.0.0.1')
        port = int(env('FUTU_OPEND_PORT', '11111'))
        firm = getattr(futu.SecurityFirm, env('FUTU_SECURITY_FIRM', 'FUTUSECURITIES'), futu.SecurityFirm.FUTUSECURITIES)
        try:
            ctx = futu.OpenSecTradeContext(
                filter_trdmarket=self._trd_market(futu), host=host, port=port, security_firm=firm,
            )
        except Exception as exc:  # SDK 在无法连接 OpenD 时抛出多种异常类型
            raise BrokerError(f'无法连接富途 OpenD（{host}:{port}）：{exc}') from exc
        try:
            if self.is_live:
                password = env('FUTU_TRADE_PASSWORD')
                if password:
                    ret, data = ctx.unlock_trade(password)
                    if ret != futu.RET_OK:
                        raise BrokerError(f'富途实盘解锁失败：{data}')
            yield futu, ctx
        finally:
            ctx.close()

    @staticmethod
    def _check(futu, ret, data, action: str):
        if ret != futu.RET_OK:
            raise BrokerError(f'富途{action}失败：{data}')
        return data

    def _result_from_row(self, row) -> OrderResult:
        raw_status = str(row.get('order_status', 'NONE')).split('.')[-1].upper()
        filled = to_decimal(row.get('dealt_qty'))
        price = to_decimal(row.get('dealt_avg_price'))
        return OrderResult(
            status=_STATUS_MAP.get(raw_status, 'SUBMITTED'),
            broker_order_id=str(row.get('order_id', '')),
            filled_quantity=filled,
            executed_price=price if filled > 0 and price > 0 else None,
            message=str(row.get('last_err_msg') or '') or f'富途状态: {raw_status}',
        )

    def place_order(self, order) -> OrderResult:
        with self._session() as (futu, ctx):
            ret, data = ctx.place_order(
                price=float(order.requested_price or 0),
                qty=float(order.quantity),
                code=to_futu_symbol(self.account.market, order.symbol),
                trd_side=futu.TrdSide.BUY if order.side == 'BUY' else futu.TrdSide.SELL,
                order_type=futu.OrderType.MARKET if order.order_type == 'MARKET' else futu.OrderType.NORMAL,
                trd_env=self._trd_env(futu),
                acc_id=self._acc_id(),
                remark=f'stock-clone#{order.id}',
            )
            frame = self._check(futu, ret, data, '下单')
            if frame is None or len(frame) == 0:
                raise BrokerError('富途下单未返回订单记录')
            return self._result_from_row(frame.iloc[0])

    def _query_order(self, futu, ctx, broker_order_id: str) -> OrderResult:
        ret, data = ctx.order_list_query(order_id=broker_order_id, trd_env=self._trd_env(futu), acc_id=self._acc_id())
        frame = self._check(futu, ret, data, '查询委托')
        if frame is None or len(frame) == 0:
            ret, data = ctx.history_order_list_query(trd_env=self._trd_env(futu), acc_id=self._acc_id())
            frame = self._check(futu, ret, data, '查询历史委托')
            frame = frame[frame['order_id'].astype(str) == str(broker_order_id)] if frame is not None and len(frame) else frame
        if frame is None or len(frame) == 0:
            raise BrokerError(f'富途未找到委托 {broker_order_id}')
        return self._result_from_row(frame.iloc[0])

    def get_order(self, order) -> OrderResult:
        with self._session() as (futu, ctx):
            return self._query_order(futu, ctx, order.broker_order_id)

    def cancel_order(self, order) -> OrderResult:
        with self._session() as (futu, ctx):
            ret, data = ctx.modify_order(
                futu.ModifyOrderOp.CANCEL, order.broker_order_id, 0, 0,
                trd_env=self._trd_env(futu), acc_id=self._acc_id(),
            )
            self._check(futu, ret, data, '撤单')
            try:
                return self._query_order(futu, ctx, order.broker_order_id)
            except BrokerError:
                return OrderResult(status='CANCELLED', broker_order_id=order.broker_order_id, message='富途已接受撤单')

    def get_account(self) -> AccountSnapshot:
        with self._session() as (futu, ctx):
            currency = futu.Currency.USD if self.account.market == 'US' else futu.Currency.CNH
            ret, data = ctx.accinfo_query(trd_env=self._trd_env(futu), acc_id=self._acc_id(), currency=currency)
            frame = self._check(futu, ret, data, '查询资金')
            if frame is None or len(frame) == 0:
                raise BrokerError('富途未返回资金信息，请确认账号在该市场有交易权限')
            row = frame.iloc[0]
            return AccountSnapshot(
                cash=to_decimal(row.get('cash')),
                market_value=to_decimal(row.get('market_val')),
                total_assets=to_decimal(row.get('total_assets')),
                frozen_cash=to_decimal(row.get('frozen_cash')),
                currency='USD' if self.account.market == 'US' else 'CNY',
                raw={key: (None if str(value) == 'nan' else str(value)) for key, value in row.items()},
            )

    def get_positions(self) -> list[PositionSnapshot]:
        with self._session() as (futu, ctx):
            ret, data = ctx.position_list_query(trd_env=self._trd_env(futu), acc_id=self._acc_id())
            frame = self._check(futu, ret, data, '查询持仓')
            positions = []
            for _, row in (frame.iterrows() if frame is not None else []):
                quantity = to_decimal(row.get('qty'))
                if quantity <= 0:
                    continue
                positions.append(PositionSnapshot(
                    symbol=from_futu_symbol(row.get('code', '')),
                    quantity=quantity,
                    average_price=to_decimal(row.get('cost_price')),
                    available_quantity=to_decimal(row.get('can_sell_qty')),
                    market_value=to_decimal(row.get('market_val')),
                ))
            return positions
