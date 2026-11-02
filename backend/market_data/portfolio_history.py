"""Read a single Tushare price snapshot for a frozen industry research universe."""

from contextlib import closing
from datetime import date
import json
import logging
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd

from market_data.industry_universe import verify_industry_universe
from market_data.price_basis import frame_digest


logger = logging.getLogger(__name__)
PORTFOLIO_PRICE_VERSION = 'tushare-factor-portfolio-research-v1'


class PortfolioHistoryError(ValueError):
    def __init__(self, issues: list[dict]):
        self.issues = issues
        super().__init__(f'Portfolio history blocked by {len(issues)} issue(s): {issues[0]["message"]}')


def portfolio_price_contract() -> dict:
    return {
        'version': PORTFOLIO_PRICE_VERSION,
        'price_source': 'ts_daily',
        'adjustment_source': 'ts_adj_factor',
        'adjustment_formula': 'daily OHLC * same-day adj_factor',
        'anchor': 'supplier cumulative factor; no end-date rebasing',
        'volume': 'ts_daily.vol hands * 100 shares',
        'execution': 'adjusted fractional units, signal close to next session open',
        'point_in_time_verified': False,
        'historical_st_verified': False,
        'live_trading_eligible': False,
    }


def load_portfolio_history(database: Path, universe: dict, start: date, end: date):
    verify_industry_universe(universe)
    if not isinstance(start, date) or not isinstance(end, date) or not start < end < date.today():
        raise ValueError('History requires start < end and a completed end date')
    database = Path(database).resolve()
    if not database.is_file():
        raise ValueError(f'Stocks database not found: {database}')
    start_raw, end_raw = start.strftime('%Y%m%d'), end.strftime('%Y%m%d')
    symbols = universe['selected_instruments']
    frames, counts, issues = [], {}, []
    logger.info('Reading unified Tushare snapshot: %d stocks, %s to %s',
                len(symbols), start, end)
    try:
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as conn:
            conn.execute('BEGIN')
            calendars = {}
            for exchange in ('SSE', 'SZSE'):
                calendar = conn.execute(
                    '''SELECT cal_date, is_open FROM ts_trade_cal
                       WHERE exchange=? AND cal_date BETWEEN ? AND ? ORDER BY cal_date''',
                    (exchange, start_raw, end_raw),
                ).fetchall()
                expected = pd.date_range(start, end, freq='D').strftime('%Y%m%d').tolist()
                if [day for day, _ in calendar] != expected:
                    raise ValueError(f'Incomplete or duplicate {exchange} calendar')
                if any(flag not in (0, 1) for _, flag in calendar):
                    raise ValueError(f'Invalid {exchange} trading calendar flag')
                calendars[exchange] = [day for day, flag in calendar if flag == 1]
            if calendars['SSE'] != calendars['SZSE'] or len(calendars['SSE']) < 2:
                raise ValueError('Shanghai/Shenzhen trading sessions differ or are empty')
            raw_sessions = calendars['SSE']
            ranges = []
            for raw, status in conn.execute(
                "SELECT params,status FROM ts_download_progress WHERE api='suspend_d'",
            ):
                params = json.loads(raw)
                if status == 'done' and not params.get('ts_code'):
                    ranges.append((params.get('start_date', '99999999'),
                                   params.get('end_date', '00000000')))
            uncovered = [day for day in raw_sessions
                         if not any(first <= day <= last for first, last in ranges)]
            if uncovered:
                raise ValueError(f'Unverified suspension download coverage: {uncovered[:5]}')
            placeholders = ','.join('?' for _ in symbols)
            suspension_rows = conn.execute(
                f'''SELECT ts_code,trade_date,suspend_type FROM ts_suspend_d
                    WHERE ts_code IN ({placeholders}) AND trade_date BETWEEN ? AND ?''',
                [*symbols, start_raw, end_raw],
            ).fetchall()
            suspended = {symbol: set() for symbol in symbols}
            for symbol, day, kind in suspension_rows:
                if kind not in ('S', 'R'):
                    raise ValueError(f'Unknown suspension type: {symbol} {day} {kind}')
                if kind == 'S':
                    suspended[symbol].add(day)
            metadata = {
                row[0]: row[1:] for row in conn.execute(
                    f'''SELECT ts_code,list_date,delist_date FROM ts_stock_basic
                        WHERE ts_code IN ({placeholders})''', symbols,
                )
            }
            for index, symbol in enumerate(symbols):
                if symbol not in metadata or not metadata[symbol][0]:
                    raise ValueError(f'Missing listing date: {symbol}')
                listing, delisting = metadata[symbol]
                stock_days = [day for day in raw_sessions if day >= listing
                              and (not delisting or day < delisting)]
                rows = conn.execute(
                    '''SELECT d.trade_date,d.open,d.high,d.low,d.close,d.vol,a.adj_factor
                       FROM ts_daily d LEFT JOIN ts_adj_factor a
                       ON a.ts_code=d.ts_code AND a.trade_date=d.trade_date
                       WHERE d.ts_code=? AND d.trade_date BETWEEN ? AND ?
                       ORDER BY d.trade_date''', (symbol, start_raw, end_raw),
                ).fetchall()
                quoted = {row[0] for row in rows}
                gaps = sorted(set(stock_days) - quoted - suspended[symbol])
                if gaps:
                    issues.append({
                        'instrument': symbol, 'kind': 'unexplained_quote_gaps',
                        'count': len(gaps), 'first_dates': gaps[:5], 'last_date': gaps[-1],
                        'message': f'Unexplained quote gaps: {symbol}: {gaps[:5]}',
                    })
                if not quoted <= set(stock_days):
                    outside = sorted(quoted - set(stock_days))
                    issues.append({
                        'instrument': symbol, 'kind': 'quote_outside_calendar_or_listing',
                        'count': len(outside), 'first_dates': outside[:5], 'last_date': outside[-1],
                        'message': f'Quote outside listing/calendar interval: {symbol}',
                    })
                if not rows:
                    if stock_days:
                        issues.append({
                            'instrument': symbol, 'kind': 'missing_listed_history',
                            'message': f'No prices in requested listed history: {symbol}',
                        })
                    counts[symbol] = {'price_rows': 0, 'reason': 'not_yet_listed'}
                    continue
                stock = pd.DataFrame(rows, columns=[
                    'raw_date', 'raw_open', 'raw_high', 'raw_low', 'raw_close', 'raw_volume', 'factor',
                ])
                numeric = stock.drop(columns='raw_date').to_numpy(dtype=float)
                if (not np.isfinite(numeric).all() or (numeric[:, :4] <= 0).any()
                        or (numeric[:, 4] < 0).any() or (numeric[:, 5] <= 0).any()
                        or (numeric[:, 2] > np.minimum(numeric[:, 0], numeric[:, 3])).any()
                        or (numeric[:, 1] < np.maximum(numeric[:, 0], numeric[:, 3])).any()):
                    issues.append({
                        'instrument': symbol, 'kind': 'invalid_ohlcv_or_factor',
                        'message': f'Missing/invalid OHLC, volume or adjustment factor: {symbol}',
                    })
                    continue
                for column in ('open', 'high', 'low', 'close'):
                    stock[column] = stock['raw_' + column] * stock['factor']
                stock['volume'] = stock['raw_volume'] * 100
                stock['instrument'] = symbol
                stock['date'] = pd.to_datetime(stock.pop('raw_date'), format='%Y%m%d').dt.date
                stock['suspended'] = [
                    day.strftime('%Y%m%d') in suspended[symbol] for day in stock['date']
                ]
                if not np.isfinite(stock[['open', 'high', 'low', 'close', 'volume']]).all().all():
                    raise ValueError(f'Adjusted price/volume overflow: {symbol}')
                frames.append(stock)
                counts[symbol] = {
                    'price_rows': len(stock),
                    'suspension_sessions': len(set(stock_days) & suspended[symbol]),
                    'missing_quotes_explained_by_suspension': len(set(stock_days) - quoted),
                }
                if (index + 1) % 50 == 0 or index + 1 == len(symbols):
                    logger.info('Checked Tushare history %d/%d; issues=%d',
                                index + 1, len(symbols), len(issues))
            if issues:
                raise PortfolioHistoryError(issues)
            if not frames:
                raise ValueError('No history available for the frozen universe')
    except sqlite3.Error as exc:
        raise ValueError(f'Unable to read portfolio history: {exc}') from exc
    frame = pd.concat(frames, ignore_index=True)
    sessions = [date.fromisoformat(day) for day in raw_sessions]
    columns = ['date', 'instrument', 'raw_open', 'raw_high', 'raw_low', 'raw_close',
               'raw_volume', 'factor', 'suspended']
    provenance = {
        'price_contract': portfolio_price_contract(),
        'database': str(database), 'universe_signature': universe['signature'],
        'start': start.isoformat(), 'end': end.isoformat(),
        'stock_count': len(symbols), 'price_rows': len(frame),
        'sessions': len(sessions), 'stock_coverage': counts,
        'prices_sha256': frame_digest(frame, columns),
        'calendar_sha256': frame_digest(
            pd.DataFrame({'date': sessions, 'instrument': 'SSE/SZSE'}), ['date', 'instrument'],
        ),
        'limitations': universe['limitations'] + [
            'Historical ST filtering remains unavailable and is not inferred from price limits.',
            'Suspension gaps are valuation-only; no fictitious quote or trade is inserted.',
            'Adjusted continuous-unit research does not certify nominal fills or corporate-action accounting.',
        ],
    }
    return frame, sessions, suspended, provenance
