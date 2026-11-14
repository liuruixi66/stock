"""Download frozen daily research history; never overwrite existing snapshots."""

import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from market_data import MarketDataError
from market_data.local_history import RESEARCH_START, RESEARCH_UNIVERSE, available_end, download_history


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--market', choices=['ALL', *RESEARCH_UNIVERSE], default='ALL')
    parser.add_argument('--symbols', nargs='+')
    parser.add_argument('--start', type=date.fromisoformat, default=RESEARCH_START)
    parser.add_argument('--end', type=date.fromisoformat, default=available_end())
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    start = args.start
    requested_end = args.end
    end = min(requested_end, datetime.now(timezone.utc).date() - timedelta(days=1))
    if start > end:
        parser.error('Start must not exceed the last completed UTC day')
    if args.symbols and args.market == 'ALL':
        parser.error('--symbols requires a single --market')
    if end != requested_end:
        print(f'End capped from {requested_end} to {end}; future/incomplete days excluded.')
    print(f'History range: {start}..{end}; interval=1d')
    markets = RESEARCH_UNIVERSE if args.market == 'ALL' else [args.market]
    failures = []
    completed = 0
    for market in markets:
        for symbol in args.symbols or RESEARCH_UNIVERSE[market]:
            print(f'Downloading {market}/{symbol}...', flush=True)
            try:
                metadata = download_history(market, symbol, start, end, args.output)
            except (MarketDataError, OSError) as exc:
                failures.append(f'{market}/{symbol}: {exc}')
                print(failures[-1])
                continue
            completed += 1
            action = 'CACHED' if metadata['cached'] else 'SAVED'
            print(
                f"{action} {market}/{symbol}: {metadata['bar_count']} bars, "
                f"{metadata['first_bar']}..{metadata['last_bar']}, sha256={metadata['sha256']}"
            )
    print(f'Completed: {completed}; failed: {len(failures)}')
    if failures:
        parser.exit(2, 'Some datasets were not downloaded. Successful snapshots are retained; rerun to retry failures.\n')


if __name__ == '__main__':
    main()
