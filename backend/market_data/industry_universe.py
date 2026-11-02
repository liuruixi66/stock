"""Frozen current industry leaders; explicitly not a point-in-time universe."""

from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
import logging
import math
from pathlib import Path
import re
import sqlite3


logger = logging.getLogger(__name__)
UNIVERSE_VERSION = 1
MAIN_BOARD = '\u4e3b\u677f'


def _digest(payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def _require_download(connection, api: str, day: str) -> None:
    for raw, status in connection.execute(
        'SELECT params, status FROM ts_download_progress WHERE api=?', (api,),
    ):
        parameters = json.loads(raw)
        if (status == 'done' and not parameters.get('ts_code')
                and parameters.get('start_date', '99999999') <= day
                <= parameters.get('end_date', '00000000')):
            return
    raise ValueError(f'No completed market-wide {api} download covers {day}')


def select_industry_leaders(
    database: Path, *, per_industry: int = 5, market_cap_date: date | None = None,
    as_of: date | None = None,
) -> dict:
    if isinstance(per_industry, bool) or not isinstance(per_industry, int) or per_industry < 1:
        raise ValueError('per_industry must be a positive integer')
    as_of = as_of or date.today()
    if not isinstance(as_of, date) or as_of > date.today():
        raise ValueError('as_of cannot be a future date')
    if market_cap_date is not None and (
        not isinstance(market_cap_date, date) or market_cap_date >= as_of
    ):
        raise ValueError('Market-cap date must be a completed past date')
    database = Path(database).resolve()
    if not database.is_file():
        raise ValueError(f'Stocks database not found: {database}')
    connection = sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute('BEGIN')
        day = (market_cap_date.strftime('%Y%m%d') if market_cap_date else
               connection.execute(
                   'SELECT MAX(trade_date) FROM ts_daily_basic WHERE trade_date < ?',
                   (as_of.strftime('%Y%m%d'),),
               ).fetchone()[0])
        if not day or not connection.execute(
            'SELECT 1 FROM ts_daily_basic WHERE trade_date=? LIMIT 1', (day,),
        ).fetchone():
            raise ValueError('No market-cap rows for the requested completed date')
        _require_download(connection, 'daily_basic', day)
        _require_download(connection, 'suspend_d', day)
        calendar = connection.execute(
            'SELECT exchange, is_open FROM ts_trade_cal WHERE cal_date=?', (day,),
        ).fetchall()
        for exchange in ('SSE', 'SZSE'):
            matches = [row['is_open'] for row in calendar if row['exchange'] == exchange]
            if matches != [1]:
                raise ValueError(f'Missing, duplicate or closed {exchange} calendar for {day}')
        info = {}
        for row in connection.execute('SELECT symbol, name, industry, updated_at FROM cn_info'):
            symbol = row['symbol'].replace('.SS', '.SH')
            if symbol in info:
                raise ValueError(f'Ambiguous industry snapshots for {symbol}')
            info[symbol] = dict(row)
        suspended = set()
        for row in connection.execute(
            'SELECT ts_code, suspend_type FROM ts_suspend_d WHERE trade_date=?', (day,),
        ):
            if row['suspend_type'] not in ('S', 'R'):
                raise ValueError(f'Unknown suspension type for {row["ts_code"]} on {day}')
            if row['suspend_type'] == 'S':
                suspended.add(row['ts_code'])
        rows = connection.execute(
            '''SELECT b.ts_code, b.name, b.market, b.exchange, b.curr_type, b.list_status,
                      b.list_date, b.delist_date, b._fetched_at, d.total_mv
               FROM ts_stock_basic b LEFT JOIN ts_daily_basic d
               ON d.ts_code=b.ts_code AND d.trade_date=? ORDER BY b.ts_code''', (day,),
        ).fetchall()
    except sqlite3.Error as exc:
        raise ValueError(f'Unable to read industry selection inputs: {exc}') from exc
    finally:
        connection.close()

    grouped, excluded, source_rows = defaultdict(list), [], []
    for row in rows:
        symbol = row['ts_code']
        classification = info.get(symbol, {})
        industry = (classification.get('industry') or '').strip()
        try:
            capital = float(row['total_mv'])
        except (TypeError, ValueError, OverflowError):
            capital = None
        record = {**dict(row), 'industry_snapshot': classification,
                  'suspended': symbol in suspended}
        if capital is not None and not math.isfinite(capital):
            record['total_mv'] = str(row['total_mv'])
        source_rows.append(record)
        reason = None
        valid_code = (isinstance(symbol, str)
                      and re.fullmatch(r'(60\d{4}\.SH|00\d{4}\.SZ)', symbol))
        if (not valid_code or row['market'] != MAIN_BOARD
                or row['curr_type'] != 'CNY'
                or row['exchange'] != ('SSE' if symbol.endswith('.SH') else 'SZSE')):
            reason = 'outside_sh_sz_main_board_a_shares'
        elif (row['list_status'] != 'L' or not row['list_date']
              or row['list_date'] > day or (row['delist_date'] and row['delist_date'] <= day)):
            reason = 'not_currently_listed_at_selection'
        elif not row['name'] or not row['_fetched_at']:
            reason = 'missing_current_name_or_source_time'
        elif any(re.search(r'^S?\*?ST(?=[^A-Za-z]|$)', str(name).strip(), re.IGNORECASE)
                 for name in (row['name'], classification.get('name', ''))):
            reason = 'current_st_name'
        elif symbol in suspended:
            reason = 'suspended_on_selection_date'
        elif not industry or not classification.get('updated_at'):
            reason = 'missing_industry'
        elif row['total_mv'] is None:
            reason = 'missing_same_day_market_cap'
        elif capital is None or not math.isfinite(capital) or capital <= 0:
            reason = 'invalid_market_cap'
        if reason:
            excluded.append({'instrument': symbol, 'reason': reason})
            continue
        grouped[industry].append({
            'instrument': symbol, 'name': row['name'], 'industry': industry,
            'total_market_cap': capital,
            'industry_snapshot_at': classification['updated_at'],
            'stock_basic_snapshot_at': row['_fetched_at'],
            'list_date': row['list_date'],
        })
    industries = {}
    for industry, stocks in sorted(grouped.items()):
        ordered = sorted(stocks, key=lambda row: (-row['total_market_cap'], row['instrument']))
        industries[industry] = [
            {**row, 'industry_rank': index + 1}
            for index, row in enumerate(ordered[:per_industry])
        ]
        excluded.extend(
            {'instrument': row['instrument'], 'reason': 'below_industry_top_n'}
            for row in ordered[per_industry:]
        )
    selected = sorted(row['instrument'] for stocks in industries.values() for row in stocks)
    if not selected:
        raise ValueError('No eligible industry leaders; refusing an empty universe')
    counts = dict(sorted(Counter(row['reason'] for row in excluded).items()))
    report = {
        'universe_version': UNIVERSE_VERSION,
        'kind': 'current_industry_leaders_fixed_research_universe',
        'as_of': as_of.isoformat(), 'market_cap_date': date.fromisoformat(day).isoformat(),
        'database': str(database), 'source_sha256': _digest({'rows': source_rows}),
        'industry_source': 'cn_info.industry_current_snapshot',
        'ranking_field': 'total_mv', 'market_cap_unit': 'CNY_10000',
        'per_industry': per_industry, 'industry_count': len(industries),
        'stock_count': len(selected), 'selected_instruments': selected,
        'industries': industries,
        'undersized_industries': {name: len(stocks) for name, stocks in industries.items()
                                 if len(stocks) < per_industry},
        'excluded_counts': counts, 'excluded': excluded,
        'historical_st_verified': False, 'point_in_time_verified': False,
        'lookahead_bias': True, 'survivorship_bias': True, 'live_trading_eligible': False,
        'limitations': [
            'Current industry, names and listing snapshots are used to look back at history.',
            'Total market cap is only a reproducible leader proxy, not business leadership.',
            'Historical ST status is unknown; current non-ST names do not prove historical eligibility.',
            'Suspension exclusion here applies to the ranking date only; backtests must gate each session.',
            'This is a frozen research universe, not a trained model or a live-trading qualification.',
        ],
    }
    report['signature'] = _digest(report)
    verify_industry_universe(report)
    logger.warning('Fixed current industry universe has lookahead/survivorship bias; historical ST unknown')
    logger.info('Market-cap date %s: selected %d stocks in %d industries; exclusions=%s',
                day, len(selected), len(industries), counts)
    return report


def verify_industry_universe(report: dict) -> None:
    if (report.get('universe_version') != UNIVERSE_VERSION
            or report.get('signature') != _digest(
                {key: value for key, value in report.items() if key != 'signature'},
            )):
        raise ValueError('Industry universe version or signature mismatch')
    if (report['live_trading_eligible'] is not False
            or report['historical_st_verified'] is not False
            or report['point_in_time_verified'] is not False
            or report['lookahead_bias'] is not True
            or report['survivorship_bias'] is not True):
        raise ValueError('Current snapshot cannot claim point-in-time or live eligibility')
    selected = []
    for industry, stocks in report['industries'].items():
        if not 0 < len(stocks) <= report['per_industry']:
            raise ValueError(f'Invalid industry size: {industry}')
        if stocks != sorted(stocks, key=lambda row: (-row['total_market_cap'], row['instrument'])):
            raise ValueError(f'Invalid industry ranking: {industry}')
        for rank, stock in enumerate(stocks, 1):
            if stock['industry_rank'] != rank or stock['industry'] != industry:
                raise ValueError(f'Invalid industry membership: {industry}')
            selected.append(stock['instrument'])
    if (len(set(selected)) != len(selected) or sorted(selected) != report['selected_instruments']
            or len(selected) != report['stock_count']
            or len(report['industries']) != report['industry_count']):
        raise ValueError('Industry universe membership or count mismatch')
