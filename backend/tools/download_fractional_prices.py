"""Serial, cached AKShare downloads for an explicitly supplied historical universe."""

import argparse
from datetime import date, datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import time

import pandas as pd

from research.fractional_forecast import DifferencingError, HistoricalTopThirty, validate_prices


LOGGER = logging.getLogger(__name__)


def download(
    weights: Path, cache: Path, output: Path, start: date, end: date,
    interval: float = 6.0, universe_start: date = date(2024, 4, 1),
) -> None:
    if start >= end or end >= date.today():
        raise DifferencingError('Require start < end < today')
    if not 3 <= interval <= 3600:
        raise DifferencingError('Request interval must be between 3 and 3600 seconds')
    combined_metadata = output.with_suffix('.metadata.json')
    if output.exists() or combined_metadata.exists():
        raise DifferencingError('Refusing to overwrite combined prices')
    universe = HistoricalTopThirty(pd.read_csv(weights))
    symbols = universe.members_between(universe_start, end)
    if not symbols:
        raise DifferencingError('No historical stocks in requested period')
    import akshare as ak

    cache.mkdir(parents=True, exist_ok=True)
    collected = []
    previous_request = None
    for symbol in symbols:
        stem = f'{symbol}_{start.isoformat()}_{end.isoformat()}_hfq'
        csv_path = cache / f'{stem}.csv'
        metadata_path = cache / f'{stem}.json'
        if csv_path.exists() or metadata_path.exists():
            if not csv_path.exists() or not metadata_path.exists():
                raise DifferencingError(f'Incomplete cache pair: {csv_path}')
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
            if (metadata['sha256'] != hashlib.sha256(csv_path.read_bytes()).hexdigest()
                    or metadata['instrument'] != symbol or metadata['start'] != start.isoformat()
                    or metadata['end'] != end.isoformat() or metadata['adjustment'] != 'hfq'):
                raise DifferencingError(f'Cached snapshot integrity mismatch: {csv_path}')
            frame = validate_prices(pd.read_csv(csv_path))
            if set(frame['instrument']) != {symbol}:
                raise DifferencingError(f'Cached instrument mismatch: {csv_path}')
            LOGGER.info('Using verified cache: %s', symbol)
        else:
            if previous_request is not None:
                time.sleep(max(0, interval - (time.monotonic() - previous_request)))
            previous_request = time.monotonic()
            LOGGER.info('Downloading %s once; no parallel requests or automatic retry', symbol)
            # On rate limiting, transport failure or malformed data, stop this run.
            raw = ak.stock_zh_a_hist(
                symbol=symbol[:6], period='daily', start_date=start.strftime('%Y%m%d'),
                end_date=end.strftime('%Y%m%d'), adjust='hfq',
            )
            names = {
                '日期': 'date', '开盘': 'open', '最高': 'high', '最低': 'low',
                '收盘': 'close', '成交量': 'volume',
            }
            if not set(names) <= set(raw.columns):
                raise DifferencingError(f'Unexpected AKShare schema or blocked response for {symbol}')
            frame = raw[list(names)].rename(columns=names)
            frame['instrument'] = symbol
            frame = validate_prices(frame)
            if frame['date'].min() < start or frame['date'].max() > end:
                raise DifferencingError(f'AKShare returned dates outside request for {symbol}')
            frame.to_csv(csv_path, index=False)
            metadata = {
                'source': 'akshare.stock_zh_a_hist/eastmoney',
                'akshare_version': ak.__version__, 'instrument': symbol,
                'start': start.isoformat(), 'end': end.isoformat(), 'adjustment': 'hfq',
                'volume_unit': 'lot', 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'observed_first': frame['date'].min().isoformat(),
                'observed_last': frame['date'].max().isoformat(), 'rows': len(frame),
                'sha256': hashlib.sha256(csv_path.read_bytes()).hexdigest(),
            }
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        collected.append(frame)
    combined = validate_prices(pd.concat(collected, ignore_index=True))
    with output.open('x', encoding='utf-8', newline='') as destination:
        combined.to_csv(destination, index=False)
    with combined_metadata.open('x', encoding='utf-8') as destination:
        json.dump({
            'source': 'akshare.stock_zh_a_hist/eastmoney', 'adjustment': 'hfq',
            'prices_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
            'weights_sha256': hashlib.sha256(weights.read_bytes()).hexdigest(),
            'requested_start': start.isoformat(), 'requested_end': end.isoformat(),
            'universe_start': universe_start.isoformat(),
            'stocks': [json.loads((cache / (
                f'{symbol}_{start.isoformat()}_{end.isoformat()}_hfq.json'
            )).read_text(encoding='utf-8')) for symbol in symbols],
        }, destination, indent=2)
    LOGGER.info('Saved %s, %s rows; preserve cache metadata with the dataset', output, len(combined))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--weights', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--start', type=date.fromisoformat, default=date(2014, 1, 1))
    parser.add_argument('--end', type=date.fromisoformat, default=date(2026, 4, 30))
    parser.add_argument('--interval', type=float, default=6.0)
    parser.add_argument('--universe-start', type=date.fromisoformat, default=date(2024, 4, 1))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        download(args.weights, args.cache, args.output, args.start, args.end,
                 args.interval, args.universe_start)
    except (OSError, ValueError, KeyError, ImportError) as exc:
        parser.exit(1, f'Download stopped (no retry): {exc}\n')


if __name__ == '__main__':
    main()
