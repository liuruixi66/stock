"""每日运行一次：用均线交叉状态在模拟/券商账户上调仓，把回测策略搬到模拟盘。"""

from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from brokers import BrokerError
from market_data import MarketDataError, get_provider
from stockmarket.models import SimulationAccount, SimulationPosition
from stockmarket.paper_trading import TradingError, submit_order, sync_account


class Command(BaseCommand):
    help = '按短/长均线状态调仓：金叉且空仓则市价买入，死叉且持仓则市价卖出。建议收盘后由 cron 每日执行。'

    def add_arguments(self, parser):
        parser.add_argument('--account', type=int, required=True, help='SimulationAccount 的 id')
        parser.add_argument('--symbol', required=True)
        parser.add_argument('--short', type=int, default=5)
        parser.add_argument('--long', type=int, default=20)
        parser.add_argument('--allocation', type=float, default=0.95, help='买入时动用的可用资金比例')
        parser.add_argument('--dry-run', action='store_true', help='只打印将要执行的操作，不下单')
        parser.add_argument('--allow-live', action='store_true', help='允许在实盘账户上执行')

    def handle(self, *args, **options):
        short_window, long_window = options['short'], options['long']
        if short_window < 2 or long_window <= short_window:
            raise CommandError('均线参数必须满足 2 <= short < long')
        try:
            account = SimulationAccount.objects.get(pk=options['account'])
        except SimulationAccount.DoesNotExist as exc:
            raise CommandError(f"账户 {options['account']} 不存在") from exc
        if account.trading_mode == 'LIVE' and not options['allow_live']:
            raise CommandError('该账户是实盘账户；确认后加 --allow-live 再执行')
        if account.is_external:
            try:
                sync_account(account)
            except BrokerError as exc:
                raise CommandError(f'同步券商失败：{exc}') from exc

        symbol = options['symbol'].strip().upper()
        end = date.today()
        start = end - timedelta(days=long_window * 3 + 40)
        try:
            bars = get_provider(account.market).get_history(symbol, start, end)
        except MarketDataError as exc:
            raise CommandError(f'获取历史行情失败：{exc}') from exc
        closes = [bar.close for bar in bars]
        if len(closes) < long_window:
            raise CommandError(f'历史数据不足：需要至少 {long_window} 根K线，实际 {len(closes)}')
        short_ma = sum(closes[-short_window:]) / short_window
        long_ma = sum(closes[-long_window:]) / long_window
        signal = short_ma > long_ma
        last_close = Decimal(str(closes[-1]))
        position = SimulationPosition.objects.filter(account=account, symbol=symbol).first()
        held = position.quantity if position else Decimal('0')
        self.stdout.write(
            f'[{account.name}/{account.broker}] {symbol} 收盘 {last_close}  '
            f'MA{short_window}={short_ma:.4f}  MA{long_window}={long_ma:.4f}  '
            f'信号={"多头" if signal else "空仓"}  持仓={held}  可用资金={account.cash}'
        )

        if signal and held == 0:
            side = 'BUY'
            quantity = int(account.cash * Decimal(str(options['allocation'])) / last_close)
            if account.market == 'A':
                quantity -= quantity % 100
            if quantity <= 0:
                self.stdout.write(self.style.WARNING('可用资金不足以买入最小交易单位，跳过'))
                return
        elif not signal and held > 0:
            side = 'SELL'
            quantity = int(held) if account.market != 'CRYPTO' else held
        else:
            self.stdout.write('信号与持仓一致，无需调仓')
            return

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(f'[dry-run] 将以市价 {side} {symbol} x {quantity}'))
            return
        try:
            order = submit_order(account.id, symbol, side, Decimal(quantity), 'MARKET')
        except TradingError as exc:
            raise CommandError(str(exc)) from exc
        line = f'订单 #{order.id} {side} {symbol} x {quantity} -> {order.status}  {order.message}'
        if order.status == 'REJECTED':
            raise CommandError(line)
        self.stdout.write(self.style.SUCCESS(line))
