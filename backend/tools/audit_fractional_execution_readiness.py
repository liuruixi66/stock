"""Audit local execution inputs without substituting a simplified backtest."""

import argparse
from contextlib import closing
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3

from config.settings import STOCKS_DATABASE_PATH


TABLES = (
    'ts_daily', 'ts_adj_factor', 'ts_stk_limit', 'ts_trade_cal',
    'ts_suspend_d', 'ts_dividend', 'ts_namechange',
)


def compact(day):
    return day.strftime('%Y%m%d')


def audit(source, database, start, end, capital):
    if start > end or end > date.today() or not math.isfinite(capital) or capital <= 0:
        raise ValueError('Require past/current ordered dates and positive finite capital')
    payload = source.read_bytes()
    data = json.loads(payload)
    if 'search_version' not in data:
        raise ValueError('Use an original Optuna search report with a frozen stock list')
    symbols = data['data_provenance']['selected_instruments']
    if (not symbols or len(set(symbols)) != len(symbols)
            or any(not isinstance(s, str) or not re.fullmatch(r'\d{6}\.SH', s) for s in symbols)):
        raise ValueError('Require unique six-digit Shanghai stock codes')
    stocks, missing_tables = [], []
    with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute('BEGIN')
        schema = {row['name'] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'",
        )}
        missing_tables = sorted(set(TABLES) - schema)
        if missing_tables:
            return {
                'status': 'blocked', 'live_trading_eligible': False,
                'missing_tables': missing_tables, 'simulation_executed': False,
            }
        calendar = list(connection.execute(
            'SELECT cal_date,is_open FROM ts_trade_cal WHERE exchange=? AND cal_date BETWEEN ? AND ? ORDER BY cal_date',
            ('SSE', compact(start), compact(end)),
        ))
        expected = {row['cal_date'] for row in calendar if row['is_open'] == 1}
        all_dates = {compact(start + timedelta(days=i)) for i in range((end - start).days + 1)}
        calendar_gaps = sorted(all_dates - {row['cal_date'] for row in calendar})
        invalid_calendar = [row['cal_date'] for row in calendar if row['is_open'] not in (0, 1)]
        for symbol in symbols:
            tables = {}
            for table in ('ts_daily', 'ts_adj_factor', 'ts_stk_limit'):
                tables[table] = {
                    row['trade_date']: dict(row) for row in connection.execute(
                        f'SELECT * FROM {table} WHERE ts_code=? AND trade_date BETWEEN ? AND ? ORDER BY trade_date',
                        (symbol, compact(start), compact(end)),
                    )
                }
            daily, factors, limits = (tables[key] for key in ('ts_daily', 'ts_adj_factor', 'ts_stk_limit'))
            missing_daily = sorted(expected - daily.keys())
            suspensions = [dict(row) for row in connection.execute(
                'SELECT trade_date,suspend_type,suspend_timing FROM ts_suspend_d WHERE ts_code=? AND trade_date BETWEEN ? AND ?',
                (symbol, compact(start), compact(end)),
            )]
            actions = [dict(row) for row in connection.execute(
                '''SELECT ann_date,imp_ann_date,div_proc,record_date,ex_date,pay_date,
                          div_listdate,stk_div,cash_div,cash_div_tax,_source
                   FROM ts_dividend WHERE ts_code=? AND ex_date BETWEEN ? AND ?''',
                (symbol, compact(start), compact(end)),
            )]
            action_gaps = [
                row for row in actions if row['div_proc'] == '\u5b9e\u65bd' and (
                    not row['ann_date'] or not row['record_date']
                    or (row['cash_div'] is not None and row['cash_div'] > 0 and not row['pay_date'])
                    or (row['stk_div'] is not None and row['stk_div'] > 0 and not row['div_listdate'])
                )
            ]
            vendor = {
                row['date'].replace('-', ''): dict(row) for row in connection.execute(
                    '''SELECT d.date,d.open,d.high,d.low,d.close FROM cn_daily d
                       JOIN cn_tickers t ON t.symbol=d.symbol
                       WHERE t.code=? AND d.date BETWEEN ? AND ? ORDER BY d.date''',
                    (symbol[:6], start.isoformat(), end.isoformat()),
                )
            }
            mismatches, invalid_prices, invalid_limits = [], [], []
            for day, row in daily.items():
                prices = [row[key] for key in ('open', 'high', 'low', 'close')]
                if (any(v is None or not math.isfinite(v) or v <= 0 for v in prices)
                        or row['low'] > min(row['open'], row['close'])
                        or row['high'] < max(row['open'], row['close'])
                        or row['vol'] is None or not math.isfinite(row['vol']) or row['vol'] < 0):
                    invalid_prices.append(day)
                if day in vendor and any(
                    vendor[day][key] is None or row[key] is None
                    or not math.isfinite(vendor[day][key]) or not math.isfinite(row[key])
                    or abs(vendor[day][key] - row[key]) > .0051
                    for key in ('open', 'high', 'low', 'close')
                ):
                    mismatches.append(day)
                if day in limits:
                    values = [limits[day][key] for key in ('up_limit', 'down_limit')]
                    if (any(v is None or not math.isfinite(v) or v <= 0 for v in values)
                            or values[0] < values[1]):
                        invalid_limits.append(day)
            stocks.append({
                'instrument': symbol,
                'daily_rows': len(daily), 'first_daily': min(daily) if daily else None,
                'latest_daily': max(daily) if daily else None,
                'missing_open_dates': missing_daily,
                'suspension_records': suspensions,
                'missing_limits_on_price_dates': sorted(daily.keys() - limits.keys()),
                'missing_factors_on_price_dates': sorted(daily.keys() - factors.keys()),
                'invalid_price_dates': invalid_prices, 'invalid_limit_dates': invalid_limits,
                'invalid_factor_dates': [day for day, row in factors.items()
                                         if row['adj_factor'] is None or not math.isfinite(row['adj_factor'])
                                         or row['adj_factor'] <= 0],
                'vendor_compared_rows': len(daily.keys() & vendor.keys()),
                'vendor_ohlc_mismatch_rows': len(mismatches),
                'vendor_mismatch_examples': mismatches[:10],
                'actions': actions, 'incomplete_implemented_actions': action_gaps,
                'historical_name_records': connection.execute(
                    'SELECT count(*) FROM ts_namechange WHERE ts_code=?', (symbol,),
                ).fetchone()[0],
                'sources': sorted({row['_source'] for row in daily.values()}),
            })
    return {
        'status': 'blocked', 'live_trading_eligible': False, 'simulation_executed': False,
        'source': str(source.resolve()), 'source_sha256': hashlib.sha256(payload).hexdigest(),
        'database': str(database.resolve()), 'start': start.isoformat(), 'end': end.isoformat(),
        'initial_capital': capital, 'stock_selection': 'previous search sample; not point-in-time universe',
        'expected_open_sessions': len(expected), 'calendar_gaps': calendar_gaps,
        'invalid_calendar_dates': invalid_calendar, 'stocks': stocks,
        'blockers': [
            'Current fractional simulator uses adjusted fractional units; it is not an A-share execution engine.',
            'Share sensitivity simulator lacks price-limit fills, verified action payments and dividend tax lots.',
            'Tushare inputs are not wired into the existing fractional forecast/replay price contract.',
            'No verified historical risk-warning/delisting state or point-in-time universe policy.',
            'Daily bars cannot establish auction queue position, intraday liquidity or actual order fills.',
            'Account-specific commission, slippage/participation and dividend tax assumptions remain unconfirmed.',
        ],
        'notes': [
            'Empty action or suspension results do not prove complete endpoint coverage.',
            'Missing price dates must be reconciled with suspension records, not forward-filled.',
            'Available table names, price ticks and matching dates alone do not certify live execution.',
            'No trading returns are computed; this report intentionally fails closed.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('search_report', type=Path)
    parser.add_argument('--database', type=Path, default=STOCKS_DATABASE_PATH)
    parser.add_argument('--start', type=date.fromisoformat, default=date(2025, 1, 1))
    parser.add_argument('--end', type=date.fromisoformat, default=date.today())
    parser.add_argument('--capital', type=float, default=200000)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError('Refusing to overwrite an existing readiness report')
        result = audit(args.search_report, args.database, args.start, args.end, args.capital)
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, ensure_ascii=False, allow_nan=False, indent=2)
        print(f'{result["status"]}: {args.output.resolve()}; no simulation executed')
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        parser.exit(1, f'Execution readiness audit failed: {exc}\n')


if __name__ == '__main__':
    main()
