"""检查券商连接、资金和持仓；不下单，不依赖网站账户数据库。"""

import argparse
import os
from types import SimpleNamespace

from config import runtime  # 加载与研究工具相同的环境配置。
from brokers import BrokerError, adapter_class


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--broker', required=True, choices=['FUTU', 'QMT', 'IB'])
    parser.add_argument('--market', default='US', choices=['A', 'US'])
    parser.add_argument('--mode', default='PAPER', choices=['PAPER', 'LIVE'])
    parser.add_argument('--account-id', default='', help='券商账号 ID；留空时由 SDK 选默认账号')
    args = parser.parse_args(argv)
    adapter_cls = adapter_class(args.broker)
    info = adapter_cls.describe()
    print(f"{info['label']}  SDK={info['sdk_package']}  installed={info['sdk_installed']}")
    for name in info['env_vars']:
        print(f"  {name}: {'已设置' if os.getenv(name) else '未设置'}")
    if args.market not in adapter_cls.markets:
        parser.error(f"{info['label']} 不支持 {args.market} 市场")
    account = SimpleNamespace(
        name='check', market=args.market, currency='USD' if args.market == 'US' else 'CNY',
        broker=args.broker, broker_account_id=args.account_id, trading_mode=args.mode,
    )
    adapter = adapter_cls(account)
    try:
        accounts = adapter.list_accounts()
        if accounts:
            print(f'券商侧账号 {len(accounts)} 个：')
            for item in accounts:
                print('  ' + '  '.join(f'{key}={value}' for key, value in item.items()))
        snapshot = adapter.get_account()
        print(
            f'资金：现金 {snapshot.cash} / 市值 {snapshot.market_value} / '
            f'总资产 {snapshot.total_assets} {snapshot.currency}'
        )
        positions = adapter.get_positions()
        print(f'持仓 {len(positions)} 项：')
        for item in positions:
            print(f'  {item.symbol}  数量 {item.quantity}  成本 {item.average_price}')
    except BrokerError as exc:
        parser.exit(2, f'连接失败：{exc}\n')
    print('连接正常。')


if __name__ == '__main__':
    main()
