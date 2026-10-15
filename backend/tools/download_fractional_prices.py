"""Serial, source-isolated AKShare or Yahoo daily price downloads."""

import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import logging
from pathlib import Path
import random
import time

import pandas as pd
import numpy as np
import requests

from research.fractional_forecast import (
    DifferencingError, FixedRandomThirty, HistoricalTopThirty, validate_prices,
)


LOGGER = logging.getLogger(__name__)


YAHOO_VERIFIED_CORRECTIONS = {
    ('600031.SH', '2019-01-07'): {
        'expected': {'open': 7.87, 'high': 8.17, 'low': 8.03, 'close': 8.14,
                     'volume': 46680785},
        'replacement': {'open': 8.12},
        'reference_raw_row': ['2019-01-07', '8.12', '8.14', '8.17', '8.03', '466807.85'],
    },
    ('600031.SH', '2020-09-08'): {
        'expected': {'open': 22.56, 'high': 23.36, 'low': 22.43, 'close': 23.38,
                     'volume': 72894073},
        'replacement': {'open': 22.60, 'high': 23.38, 'volume': 74171473},
        'reference_raw_row': ['2020-09-08', '22.60', '23.38', '23.38', '22.43', '741714.73'],
    },
}


def correct_verified_yahoo_rows(frame: pd.DataFrame, symbol: str) -> list[dict]:
    audit = []
    for (stock, day), correction in YAHOO_VERIFIED_CORRECTIONS.items():
        if stock != symbol:
            continue
        indices = frame.index[frame['date'].astype(str) == day]
        if not len(indices):
            continue
        if len(indices) != 1:
            raise DifferencingError(f'Duplicate Yahoo correction date: {symbol} {day}')
        index = indices[0]
        actual = {}
        for name in correction['expected']:
            value = frame.at[index, name]
            if not isinstance(value, (int, float, np.integer, np.floating)):
                raise DifferencingError(f'Non-numeric Yahoo correction field: {symbol} {day} {name}')
            actual[name] = float(value)
        if all(np.isclose(actual[name], value, rtol=0, atol=0.00001)
               for name, value in correction['replacement'].items()):
            continue
        if not all(np.isclose(actual[name], value, rtol=0, atol=0.00001)
                   for name, value in correction['expected'].items()):
            raise DifferencingError(f'Yahoo row changed; reverify correction: {symbol} {day}')
        for name, value in correction['replacement'].items():
            frame.loc[index, name] = value
        record = {
            'instrument': symbol, 'date': day, 'original_raw': actual,
            'replacement_fields': correction['replacement'],
            'reference_raw_row': correction['reference_raw_row'],
            'reference_columns': ['date', 'open', 'close', 'high', 'low', 'volume_lots'],
            'source': 'tencent.unadjusted_daily',
            'reference_url': 'https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get',
            'reference_param': 'sh600031,day,2019-01-01,2020-09-10,640,',
            'verified_date': '2026-10-14',
            'reason': 'Yahoo raw OHLC inconsistent; independently verified raw fields.',
        }
        audit.append(record)
        LOGGER.warning('Applying independently verified Yahoo correction: %s %s %s',
                       symbol, day, correction['replacement'])
    return audit


def yahoo_prices(
    symbol: str, start: date, end: date, raw_path: Path | None = None,
) -> pd.DataFrame:
    yahoo_symbol = symbol.replace('.SH', '.SS')
    if raw_path is not None and raw_path.exists():
        payload = json.loads(raw_path.read_text(encoding='utf-8'))
    else:
        response = requests.get(
            f'https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}',
            params={
                'period1': int(datetime.combine(start, datetime.min.time(), timezone.utc).timestamp()),
                'period2': int(datetime.combine(end + timedelta(days=1),
                                               datetime.min.time(), timezone.utc).timestamp()),
                'interval': '1d', 'events': 'div,splits', 'includeAdjustedClose': 'true',
            },
            headers={'User-Agent': 'Mozilla/5.0'}, timeout=(10, 60),
        )
        response.raise_for_status()
        payload = response.json()
        if raw_path is not None:
            with raw_path.open('x', encoding='utf-8') as destination:
                json.dump(payload, destination, allow_nan=False)
    chart = payload['chart']
    if chart.get('error') or not chart.get('result'):
        raise DifferencingError(f'Yahoo returned no valid chart for {symbol}: {chart.get("error")}')
    result = chart['result'][0]
    if result['meta']['symbol'] != yahoo_symbol or result['meta']['currency'] != 'CNY':
        raise DifferencingError(f'Unexpected Yahoo instrument or currency for {symbol}')
    frame = pd.DataFrame(result['indicators']['quote'][0])
    frame['date'] = pd.to_datetime(result['timestamp'], unit='s', utc=True).tz_convert(
        'Asia/Shanghai',
    ).date
    frame['instrument'] = symbol
    adjusted = pd.Series(result['indicators']['adjclose'][0]['adjclose'], dtype=float)
    if len(adjusted) != len(frame) or not np.isfinite(adjusted).all() or (adjusted <= 0).any():
        raise DifferencingError(f'Missing or invalid Yahoo adjusted close for {symbol}')
    if not frame['date'].is_monotonic_increasing:
        raise DifferencingError(f'Unordered Yahoo daily bars for {symbol}')
    corrections = correct_verified_yahoo_rows(frame, symbol)
    frame = validate_prices(frame)
    factor = adjusted.to_numpy() / frame['close'].to_numpy()
    for column in ('open', 'high', 'low', 'close'):
        frame[column] *= factor
    frame = validate_prices(frame)
    frame.attrs['verified_corrections'] = corrections
    return frame


def prepare_random_universe(path: Path, seed: int = 42) -> None:
    if path.exists():
        FixedRandomThirty(json.loads(path.read_text(encoding='utf-8')))
        LOGGER.info('Reusing saved random universe: %s', path)
        return
    import akshare as ak

    raw = ak.index_stock_cons_csindex(symbol='000016')
    if (raw.empty or set(raw['指数代码']) != {'000016'}
            or raw['日期'].isna().any() or raw['日期'].nunique() != 1):
        raise DifferencingError('Invalid current SSE50 constituent response')
    members = sorted(raw['成分券代码'].map(lambda code: f'{str(code).zfill(6)}.SH'))
    manifest = {
        'mode': 'current_sse50_random30', 'index': '000016.SHI',
        'source': 'akshare.index_stock_cons_csindex/csindex',
        'selection_date': date.today().isoformat(),
        'source_snapshot_date': str(raw['日期'].iloc[0]),
        'retrieved_at': datetime.now(timezone.utc).isoformat(),
        'seed': seed, 'members': members,
        'selected': sorted(random.Random(seed).sample(members, 30)),
        'survivorship_bias': True,
        'warning': 'Current constituents projected backwards; NOT historical top30.',
    }
    FixedRandomThirty(manifest)
    with path.open('x', encoding='utf-8') as destination:
        json.dump(manifest, destination, indent=2)
    LOGGER.warning('Saved current random30; survivorship biased, not historical top30: %s', path)


def download(
    weights: Path | None, cache: Path, output: Path, start: date, end: date,
    interval: float = 6.0, universe_start: date = date(2024, 4, 1),
    fixed_universe: Path | None = None,
    source: str = 'akshare',
    quarantine_invalid: bool = False,
) -> None:
    if start >= end or end >= date.today():
        raise DifferencingError('Require start < end < today')
    if not 3 <= interval <= 3600:
        raise DifferencingError('Request interval must be between 3 and 3600 seconds')
    combined_metadata = output.with_suffix('.metadata.json')
    if output.exists() or combined_metadata.exists():
        raise DifferencingError('Refusing to overwrite combined prices')
    if (weights is None) == (fixed_universe is None):
        raise DifferencingError('Supply exactly one of historical weights or fixed universe')
    if fixed_universe is not None:
        universe = FixedRandomThirty(json.loads(fixed_universe.read_text(encoding='utf-8')))
    else:
        if weights is None:
            raise DifferencingError('Historical weights path is required')
        universe = HistoricalTopThirty(pd.read_csv(weights))
    symbols = universe.members_between(universe_start, end)
    if not symbols:
        raise DifferencingError('No historical stocks in requested period')
    if source not in ('akshare', 'yahoo'):
        raise DifferencingError('Unsupported price source')
    if quarantine_invalid and source != 'yahoo':
        raise DifferencingError('Raw-response quarantine is supported only for Yahoo')
    adjustment = 'hfq' if source == 'akshare' else 'yahoo_adjclose_ratio'
    source_name = 'akshare.stock_zh_a_hist/eastmoney' if source == 'akshare' else 'yahoo.chart'
    if source == 'akshare':
        import akshare as ak

    cache.mkdir(parents=True, exist_ok=True)
    collected = []
    quarantined = []
    previous_request = None
    for symbol in symbols:
        stem = f'{symbol}_{start.isoformat()}_{end.isoformat()}_{adjustment}'
        csv_path = cache / f'{stem}.csv'
        metadata_path = cache / f'{stem}.json'
        if csv_path.exists() or metadata_path.exists():
            if not csv_path.exists() or not metadata_path.exists():
                raise DifferencingError(f'Incomplete cache pair: {csv_path}')
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
            if (metadata['sha256'] != hashlib.sha256(csv_path.read_bytes()).hexdigest()
                    or metadata['instrument'] != symbol or metadata['start'] != start.isoformat()
                    or metadata['end'] != end.isoformat() or metadata['adjustment'] != adjustment
                    or metadata['source'] != source_name):
                raise DifferencingError(f'Cached snapshot integrity mismatch: {csv_path}')
            frame = validate_prices(pd.read_csv(csv_path))
            if set(frame['instrument']) != {symbol}:
                raise DifferencingError(f'Cached instrument mismatch: {csv_path}')
            LOGGER.info('Using verified cache: %s', symbol)
        else:
            raw_path = cache / f'{stem}.raw.json' if quarantine_invalid else None
            needs_request = raw_path is None or not raw_path.exists()
            if needs_request and previous_request is not None:
                time.sleep(max(0, interval - (time.monotonic() - previous_request)))
            if needs_request:
                previous_request = time.monotonic()
            LOGGER.info('Downloading %s once; no parallel requests or automatic retry', symbol)
            # On rate limiting, transport failure or malformed data, stop this run.
            if source == 'yahoo':
                try:
                    frame = (yahoo_prices(symbol, start, end, raw_path=raw_path)
                             if quarantine_invalid else yahoo_prices(symbol, start, end))
                except DifferencingError as exc:
                    if not quarantine_invalid or raw_path is None:
                        raise
                    record = {
                        'instrument': symbol, 'error': str(exc),
                        'raw_path': str(raw_path),
                        'status': 'quarantined_not_for_training_or_backtest',
                        'raw_sha256': hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                    }
                    quarantined.append(record)
                    (cache / f'{stem}.quarantine.json').write_text(
                        json.dumps(record, indent=2), encoding='utf-8',
                    )
                    LOGGER.error('Quarantined %s: %s; continuing raw collection only', symbol, exc)
                    continue
            else:
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
                raise DifferencingError(f'{source} returned dates outside request for {symbol}')
            frame.to_csv(csv_path, index=False)
            metadata = {
                'source': source_name,
                'instrument': symbol,
                'start': start.isoformat(), 'end': end.isoformat(), 'adjustment': adjustment,
                'volume_unit': 'lot' if source == 'akshare' else 'share',
                'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'observed_first': frame['date'].min().isoformat(),
                'observed_last': frame['date'].max().isoformat(), 'rows': len(frame),
                'sha256': hashlib.sha256(csv_path.read_bytes()).hexdigest(),
                'verified_corrections': frame.attrs.get('verified_corrections', []),
            }
            if source == 'akshare':
                metadata['akshare_version'] = ak.__version__
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        collected.append(frame)
    if quarantined:
        raise DifferencingError(
            f'Collection finished: {len(collected)} valid stocks, {len(quarantined)} quarantined. '
            'No combined prices created; resolve quarantine before training.'
        )
    combined = validate_prices(pd.concat(collected, ignore_index=True))
    with output.open('x', encoding='utf-8', newline='') as destination:
        combined.to_csv(destination, index=False)
    with combined_metadata.open('x', encoding='utf-8') as destination:
        json.dump({
            'source': source_name, 'adjustment': adjustment,
            'prices_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
            'weights_sha256': hashlib.sha256(weights.read_bytes()).hexdigest() if weights else None,
            'fixed_universe_sha256': (hashlib.sha256(fixed_universe.read_bytes()).hexdigest()
                                      if fixed_universe else None),
            'universe_mode': ('current_sse50_random30_survivorship_biased'
                              if fixed_universe else 'historical_weight_top30'),
            'requested_start': start.isoformat(), 'requested_end': end.isoformat(),
            'universe_start': universe_start.isoformat(),
            'stocks': [json.loads((cache / (
                f'{symbol}_{start.isoformat()}_{end.isoformat()}_{adjustment}.json'
            )).read_text(encoding='utf-8')) for symbol in symbols],
        }, destination, indent=2)
    LOGGER.info('Saved %s, %s rows; preserve cache metadata with the dataset', output, len(combined))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--weights', type=Path)
    group.add_argument('--fixed-universe', type=Path, help='Saved current random30 JSON')
    parser.add_argument('--create-random-universe', action='store_true')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--source', choices=('akshare', 'yahoo'), default='akshare')
    parser.add_argument('--quarantine-invalid', action='store_true',
                        help='Yahoo: persist raw responses, isolate invalid stocks, no partial combined output')
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--start', type=date.fromisoformat, default=date(2014, 1, 1))
    parser.add_argument('--end', type=date.fromisoformat, default=date(2026, 4, 30))
    parser.add_argument('--interval', type=float, default=6.0)
    parser.add_argument('--universe-start', type=date.fromisoformat, default=date(2024, 4, 1))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        if args.create_random_universe:
            if args.fixed_universe is None:
                raise DifferencingError('--create-random-universe requires --fixed-universe')
            prepare_random_universe(args.fixed_universe, args.seed)
            time.sleep(args.interval)
        download(args.weights, args.cache, args.output, args.start, args.end,
                 args.interval, args.universe_start, args.fixed_universe, args.source,
                 args.quarantine_invalid)
    except (OSError, ValueError, KeyError, ImportError) as exc:
        parser.exit(1, f'Download stopped (no retry): {exc}\n')


if __name__ == '__main__':
    main()
