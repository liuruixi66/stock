"""使用项目冻结的 OHLCV 快照检查 ETF 目标权重，不会提交交易订单。

此命令仅验证研究数据并打印策略结果；它既不连接券商，也不模拟真实撮合。
若要用于平台回测或交易，必须另行完成数据可用性、交易规则和订单执行验证。
"""

import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from market_data import MarketDataError
from market_data.local_history import LocalHistoryProvider
from strategies.etf_rotation import RotationBar
from strategies.etf_rotation import RotationConfig
from strategies.etf_rotation import build_rotation_targets


class Command(BaseCommand):
    help = 'Compute research-only ETF targets from local A-share snapshots (offline).'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument('--symbols', nargs='+', required=True)
        parser.add_argument('--start', type=date.fromisoformat, required=True)
        parser.add_argument('--as-of', type=date.fromisoformat, required=True)
        parser.add_argument('--data-dir', type=Path)

    def handle(self, *args, **options):
        start, as_of = options['start'], options['as_of']
        if start >= as_of or as_of >= date.today():
            raise CommandError('Require start < as-of < today (completed daily bars only)')
        symbols = options['symbols']
        if len(set(symbols)) != len(symbols) or any(
                len(symbol) != 6 or not symbol.isascii() or not symbol.isdigit()
                for symbol in symbols):
            raise CommandError('Use unique six-digit local ETF codes')
        provider = LocalHistoryProvider('A', options['data_dir'])
        try:
            histories = {
                symbol: [
                    RotationBar(bar.date, bar.close, bar.high, bar.low, bar.volume)
                    for bar in provider.get_history(symbol, start, as_of)
                ] for symbol in symbols
            }
            result = build_rotation_targets(histories, as_of, RotationConfig())
        except (MarketDataError, ValueError, OSError) as exc:
            raise CommandError(str(exc)) from exc
        if len(result['rejected']) == len(histories):
            raise CommandError('No valid ETF histories: {}'.format(result['rejected']))
        result['execution_filters'] = 'not_applied_offline: turnover, listing_age, tradability'
        result['datasets'] = provider.datasets
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
