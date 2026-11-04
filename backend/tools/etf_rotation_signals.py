"""离线检查 ETF 研究目标权重；不连接券商，不提交订单，不模拟真实撮合。"""

import argparse
import json
from datetime import date
from pathlib import Path

from market_data import MarketDataError
from market_data.local_history import LocalHistoryProvider
from strategies.etf_rotation import RotationBar, RotationConfig, build_rotation_targets


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--symbols', nargs='+', required=True)
    parser.add_argument('--start', type=date.fromisoformat, required=True)
    parser.add_argument('--as-of', type=date.fromisoformat, required=True)
    parser.add_argument('--data-dir', type=Path)
    args = parser.parse_args(argv)
    start, as_of = args.start, args.as_of
    if start >= as_of or as_of >= date.today():
        parser.error('Require start < as-of < today (completed daily bars only)')
    symbols = args.symbols
    if len(set(symbols)) != len(symbols) or any(
            len(symbol) != 6 or not symbol.isascii() or not symbol.isdigit()
            for symbol in symbols):
        parser.error('Use unique six-digit local ETF codes')
    provider = LocalHistoryProvider('A', args.data_dir)
    try:
        histories = {
            symbol: [
                RotationBar(bar.date, bar.close, bar.high, bar.low, bar.volume)
                for bar in provider.get_history(symbol, start, as_of)
            ] for symbol in symbols
        }
        result = build_rotation_targets(histories, as_of, RotationConfig())
    except (MarketDataError, ValueError, OSError) as exc:
        parser.exit(2, f'{exc}\n')
    if len(result['rejected']) == len(histories):
        parser.exit(2, 'No valid ETF histories: {}\n'.format(result['rejected']))
    result['execution_filters'] = 'not_applied_offline: turnover, listing_age, tradability'
    result['datasets'] = provider.datasets
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
