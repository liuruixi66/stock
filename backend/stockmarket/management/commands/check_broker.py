"""检查券商连接：确认 SDK、环境变量、可用账号与资金持仓，用于首次接入时排错。"""

import os

from django.core.management.base import BaseCommand, CommandError

from brokers import BrokerError, adapter_class
from stockmarket.models import SimulationAccount


class Command(BaseCommand):
    help = '连接指定券商通道，打印可用账号、资金和持仓；不会下单。'

    def add_arguments(self, parser):
        parser.add_argument('--broker', required=True, choices=['FUTU', 'QMT', 'IB'])
        parser.add_argument('--market', default='US', choices=['A', 'US'])
        parser.add_argument('--mode', default='PAPER', choices=['PAPER', 'LIVE'])
        parser.add_argument('--account-id', default='', help='券商账号 ID；留空时由 SDK 选默认账号')

    def handle(self, *args, **options):
        adapter_cls = adapter_class(options['broker'])
        info = adapter_cls.describe()
        self.stdout.write(f"{info['label']}  SDK={info['sdk_package']}  installed={info['sdk_installed']}")
        for name in info['env_vars']:
            value = os.getenv(name, '')
            shown = '(未设置)' if not value else ('******' if 'PASSWORD' in name else value)
            self.stdout.write(f'  {name} = {shown}')
        if options['market'] not in adapter_cls.markets:
            raise CommandError(f"{info['label']} 不支持 {options['market']} 市场")

        account = SimulationAccount(
            name='check', market=options['market'], currency='USD' if options['market'] == 'US' else 'CNY',
            broker=options['broker'], broker_account_id=options['account_id'], trading_mode=options['mode'],
        )
        adapter = adapter_cls(account)
        try:
            accounts = adapter.list_accounts()
            if accounts:
                self.stdout.write(self.style.SUCCESS(f'券商侧账号 {len(accounts)} 个：'))
                for item in accounts:
                    self.stdout.write('  ' + '  '.join(f'{key}={value}' for key, value in item.items()))
            snapshot = adapter.get_account()
            self.stdout.write(self.style.SUCCESS(
                f'资金：现金 {snapshot.cash} / 市值 {snapshot.market_value} / 总资产 {snapshot.total_assets} {snapshot.currency}'
            ))
            positions = adapter.get_positions()
            self.stdout.write(f'持仓 {len(positions)} 项：')
            for item in positions:
                self.stdout.write(f'  {item.symbol}  数量 {item.quantity}  成本 {item.average_price}')
        except BrokerError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS('连接正常，可以在页面上用该通道创建账户。'))
