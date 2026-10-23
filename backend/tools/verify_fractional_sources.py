"""Cross-check vendor history against public raw OHLC and implemented actions.

This is evidence collection, not a data repair or live-trading certification.
Requests contain public stock codes/dates only and do not use system proxies.
"""

import argparse
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
import hashlib
from html import escape
import json
import math
from pathlib import Path
import re
import sqlite3
import time

import requests

from config.settings import STOCKS_DATABASE_PATH
from research.fractional_results import chinese_result


TENCENT_URL = 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get'
ACTIONS_URL = 'https://datacenter-web.eastmoney.com/api/data/v1/get'
PRICE_FIELDS = ('open', 'high', 'low', 'close')
PRICE_TOLERANCE = 0.0051


def finite(value, *, positive=False):
    if isinstance(value, bool):
        raise ValueError('Boolean is not a numerical price or action')
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise ValueError(f'Invalid finite value: {value!r}')
    return result


def windows(start, end):
    """Two calendar years contain fewer than 640 A-share trading sessions."""
    cursor = start
    while cursor <= end:
        stop = min(cursor + timedelta(days=729), end)
        yield cursor, stop
        cursor = stop + timedelta(days=1)


def parse_prices(payload, symbol, start, end):
    if not isinstance(payload, dict) or payload.get('code') != 0:
        raise ValueError('Tencent returned an unsuccessful response')
    container = payload.get('data')
    if not isinstance(container, dict):
        raise ValueError('Tencent response data must be an object')
    data = container.get(symbol)
    if not isinstance(data, dict):
        raise ValueError('Tencent response lacks the requested symbol')
    rows = data.get('day')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Tencent response lacks unadjusted day data')
    prices = {}
    for row in rows:
        if not isinstance(row, list) or len(row) < 6:
            raise ValueError('Invalid Tencent day record')
        day = date.fromisoformat(row[0])
        if not start <= day <= end:
            raise ValueError(f'Tencent returned out-of-range day: {day}')
        if day in prices:
            raise ValueError(f'Duplicate Tencent day: {day}')
        open_price, close, high, low = [finite(v, positive=True) for v in row[1:5]]
        if not low <= min(open_price, close) <= max(open_price, close) <= high:
            raise ValueError(f'Invalid Tencent OHLC on {day}')
        prices[day] = dict(zip(PRICE_FIELDS, (open_price, high, low, close)))
    return prices


def parse_actions(payload, code):
    if not isinstance(payload, dict) or payload.get('success') is not True:
        raise ValueError('Eastmoney returned an unsuccessful action response')
    result = payload.get('result')
    if not isinstance(result, dict) or not isinstance(result.get('data'), list):
        raise ValueError('Action response has no explicit records; empty is not proof of no actions')
    pages = result.get('pages')
    if isinstance(pages, bool) or not isinstance(pages, int) or not 1 <= pages <= 100:
        raise ValueError('Invalid corporate action pagination')
    rows = []
    for item in result['data']:
        if not isinstance(item, dict):
            raise ValueError('Corporate action record must be an object')
        if item.get('SECURITY_CODE') != code:
            raise ValueError('Corporate action symbol mismatch')
        if item.get('ASSIGN_PROGRESS') != '实施分配':
            raise ValueError('Action response contains a non-implemented proposal')
        raw_day = item.get('EX_DIVIDEND_DATE')
        if not isinstance(raw_day, str):
            raise ValueError('Implemented action lacks ex-date')
        day = date.fromisoformat(raw_day[:10])
        cash_raw = item.get('PRETAX_BONUS_RMB')
        bonus_raw = item.get('BONUS_IT_RATIO')
        cash = None if cash_raw is None else finite(cash_raw) / 10
        bonus = None if bonus_raw is None else finite(bonus_raw) / 10
        if any(value is not None and value < 0 for value in (cash, bonus)):
            raise ValueError('Negative corporate action')
        rows.append({
            'date': day.isoformat(), 'cash_per_share': cash,
            'bonus_share_ratio': bonus,
            'record_date': item.get('EQUITY_RECORD_DATE'),
            'notice_date': item.get('NOTICE_DATE'),
            'plan': item.get('IMPL_PLAN_PROFILE'),
            'payment_date_verified': False,
        })
    return rows, pages


def compare(local, external, actions):
    expected = set(local)
    present = set(external)
    mismatches = []
    invalid_local = []
    for day in sorted(expected & present):
        for field in PRICE_FIELDS:
            original = local[day][field]
            try:
                value = finite(original, positive=True)
            except (ValueError, TypeError, OverflowError):
                invalid_local.append({'date': day.isoformat(), 'field': field, 'stored': original})
                continue
            difference = value - external[day][field]
            if abs(difference) > PRICE_TOLERANCE:
                mismatches.append({
                    'date': day.isoformat(), 'field': field, 'stored': value,
                    'reference': external[day][field], 'difference': difference,
                })
    action_days = {date.fromisoformat(item['date']) for item in actions}
    unexplained = []
    factors = []
    invalid_adjustments = []
    for day in sorted(local):
        row = local[day]
        try:
            close = finite(row['close'], positive=True)
            adjusted = finite(row['adj_close'], positive=True)
            factor = adjusted / close
            finite(factor, positive=True)
        except (TypeError, ValueError, OverflowError):
            invalid_adjustments.append(day.isoformat())
            continue
        if factors:
            previous_day, previous_factor = factors[-1]
            ratio = factor / previous_factor
            if abs(ratio - 1) > 0.0001:
                try:
                    dividend = finite(row['dividends'])
                    split = finite(row['splits'])
                except (TypeError, ValueError, OverflowError):
                    dividend, split = None, None
                if dividend is None or split is None or (
                    dividend == 0 and split == 0 and day not in action_days
                ):
                    unexplained.append({
                        'date': day.isoformat(), 'previous_date': previous_day.isoformat(),
                        'factor_ratio': ratio, 'stored_dividend': dividend, 'stored_split': split,
                    })
        factors.append((day, factor))
    action_checks = []
    for item in actions:
        day = date.fromisoformat(item['date'])
        if not min(local) <= day <= max(local):
            continue
        stored = local.get(day)
        action_checks.append({
            **item,
            'stored_day_present': stored is not None,
            'stored_dividend': stored['dividends'] if stored else None,
            'stored_split': stored['splits'] if stored else None,
            'cash_matches': (
                None if stored is None or item['cash_per_share'] is None or stored['dividends'] is None
                else abs(finite(stored['dividends']) - item['cash_per_share']) <= 0.00001
            ),
            'bonus_matches': (
                None if stored is None or item['bonus_share_ratio'] is None or stored['splits'] is None
                else (
                    finite(stored['splits']) in (0, 1) if item['bonus_share_ratio'] == 0
                    else abs(finite(stored['splits']) - (1 + item['bonus_share_ratio'])) <= 0.00001
                )
            ),
        })
    stored_only = []
    for day, row in sorted(local.items()):
        for field in ('dividends', 'splits'):
            value = row[field]
            if value is None or not math.isfinite(float(value)) or float(value) < 0:
                stored_only.append({'date': day.isoformat(), 'field': field, 'status': 'invalid_stored_action'})
            elif float(value) > 0 and day not in action_days:
                stored_only.append({'date': day.isoformat(), 'field': field, 'status': 'no_reference_event'})
    missing = sorted(expected - present)
    return {
        'local_rows': len(local), 'reference_rows': len(external),
        'matched_days': len(expected & present),
        'missing_reference_dates': [day.isoformat() for day in missing],
        'reference_only_dates': [day.isoformat() for day in sorted(present - expected)],
        'price_mismatch_count': len(mismatches), 'price_mismatches': mismatches,
        'price_mismatch_day_count': len({item['date'] for item in mismatches}),
        'invalid_local_prices': invalid_local,
        'invalid_adjustment_dates': invalid_adjustments,
        'unexplained_factor_changes': unexplained,
        'corporate_action_checks': action_checks,
        'stored_actions_without_reference': stored_only,
        'known_action_fields_match': (
            not stored_only
            and all(item['cash_matches'] is not False and item['bonus_matches'] is not False
                    and item['stored_day_present'] for item in action_checks)
        ),
        'unknown_action_field_count': sum(
            item[key] is None for item in action_checks for key in ('cash_matches', 'bonus_matches')
        ),
        'corporate_actions_complete': False,
        'ohlc_crosscheck_passed': not missing and not mismatches and not invalid_local,
        'live_trading_eligible': False,
    }


def fetch(session, url, params, evidence, filename):
    response = session.get(url, params=params, timeout=(8, 25))
    raw = response.content
    path = evidence / filename
    path.write_bytes(raw)
    response.raise_for_status()
    payload = response.json()
    return payload, {
        'file': filename, 'sha256': hashlib.sha256(raw).hexdigest(),
        'url': response.url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
    }


def render_report(report, output):
    """Render only saved evidence; never imply that a failed comparison passed."""
    stocks = report['stocks']
    rows = []
    for stock in stocks:
        cash_mismatches = sum(item['cash_matches'] is False for item in stock['corporate_action_checks'])
        bonus_mismatches = sum(item['bonus_matches'] is False for item in stock['corporate_action_checks'])
        code = stock['symbol'][:6]
        rows.append(
            f'<tr><td><a href="{code}-comparison.json">{escape(stock["symbol"])}</a></td>'
            f'<td>{stock["matched_days"]}/{stock["local_rows"]}</td>'
            f'<td>{len(stock["missing_reference_dates"])}</td>'
            f'<td>{stock["price_mismatch_count"]:,}</td>'
            f'<td>{cash_mismatches}</td><td>{bonus_mismatches}</td>'
            f'<td>{len(stock["unexplained_factor_changes"])}</td>'
            f'<td>{len(stock["errors"])}</td></tr>',
        )
    examples = []
    for stock in stocks:
        if not stock['price_mismatches']:
            continue
        point = stock['price_mismatches'][0]
        examples.append(
            f'<li>{escape(stock["symbol"])} · {escape(point["date"])} · {escape(point["field"])}：'
            f'库中 {point["stored"]:.6f}，参考 {point["reference"]:.6f}</li>',
        )
        if len(examples) == 5:
            break
    passed = report.get('all_ohlc_crosschecks_passed') is True
    heading = 'OHLC 供应商交叉核对通过，仍非实盘认证' if passed else '核验未通过：不启动重训，不覆盖数据库'
    counts = (
        f'已处理 {len(stocks)} 只股票；价格字段差异 '
        f'{sum(stock["price_mismatch_count"] for stock in stocks):,} 处'
        '（同一天多个 OHLC 字段分别计数）。'
    )
    html = (
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>历史原价与公司行动交叉核验</title><style>'
        'body{font:16px "Microsoft YaHei",sans-serif;background:#f1f5f9;color:#17263c;margin:0}'
        'main{max-width:1180px;margin:auto;padding:26px}table{border-collapse:collapse;width:100%;background:white}'
        'td,th{padding:12px;border:1px solid #ddd;text-align:right}td:first-child,th:first-child{text-align:left}'
        '.warning{background:#fff0df;border-left:5px solid #c65c00;padding:18px;line-height:1.8}'
        '.scroll{overflow:auto}li{margin:10px 0}a{color:#2563eb}</style><main>'
        '<h1>历史原价与公司行动交叉核验</h1>'
        f'<p class="warning"><strong>{heading}</strong><br>{counts}<br>'
        '本地输入与外部响应均已保存并记录 SHA256；这是核验输入快照，不是可直接用于训练的完整数据集。</p>'
        '<p>价格参考：腾讯未指定前/后复权的 day 数据；公司行动参考：东方财富已实施分配。'
        '两者都是供应商数据，不等于交易所认证；请求未包含账户、凭据或私有代码。</p>'
        '<p>缺失日期不会补齐为成交日；差异不会自动修复。分红金额单位按每10股换算，空值保持未知。'
        'Yahoo 历史价格和分红可能已随拆股调整，不能直接用于当时的股数记账。'
        '本报告不把缺失参考日期直接认定为停牌或源数据错误。</p>'
        '<p><a href="summary.json">完整汇总 JSON</a> · <a href="evidence/">原始响应及输入证据目录</a></p>'
        '<div class="scroll"><table><tr><th>股票</th><th>日期重合/本地</th><th>参考缺失日</th>'
        '<th>OHLC字段差异</th><th>分红差异</th><th>送转差异</th><th>无事件因子跳变</th><th>请求/解析错误</th></tr>'
        + ''.join(rows) + '</table></div><h2>价格差异示例</h2><ul>' + ''.join(examples)
        + '</ul><h2>仍需核实</h2><ul>'
        + ''.join(f'<li>{escape(item)}</li>' for item in report['limitations'])
        + '</ul></main></html>'
    )
    (output / 'index.html').write_text(html, encoding='utf-8')


def verify(source, database, output, interval=0.5):
    if not math.isfinite(interval) or interval < 0.2:
        raise ValueError('Request interval must be at least 0.2 seconds')
    if output.exists():
        raise ValueError('Refusing to overwrite an existing verification directory')
    source_bytes = source.read_bytes()
    data = chinese_result(json.loads(source_bytes))
    symbols = data['数据溯源']['入选股票']
    parameters = data['实验参数']
    start = date.fromisoformat(parameters['训练开始日期'])
    end = date.fromisoformat(parameters['测试结束日期'])
    if start > end or end >= date.today() or not symbols or len(set(symbols)) != len(symbols):
        raise ValueError('Invalid completed history range or stock universe')
    if any(not re.fullmatch(r'6\d{5}\.SH', symbol) for symbol in symbols):
        raise ValueError('Verification supports Shanghai A-share stocks only')
    local_data = {}
    with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)) as connection:
        connection.execute('BEGIN')
        for symbol in symbols:
            rows = connection.execute(
                '''SELECT d.date,d.open,d.high,d.low,d.close,d.adj_close,d.dividends,d.splits
                   FROM cn_tickers t CROSS JOIN cn_daily d
                   WHERE t.symbol=d.symbol AND t.code=? AND d.date BETWEEN ? AND ?
                   ORDER BY d.date''',
                (symbol[:6], start.isoformat(), end.isoformat()),
            ).fetchall()
            if not rows or len({row[0] for row in rows}) != len(rows):
                raise ValueError(f'Missing or duplicate stored history: {symbol}')
            local_data[symbol] = {
                date.fromisoformat(row[0]): dict(zip(
                    (*PRICE_FIELDS, 'adj_close', 'dividends', 'splits'), row[1:],
                )) for row in rows
            }
    output.mkdir(parents=True)
    evidence = output / 'evidence'
    evidence.mkdir()
    report = {
        'source_result': str(source.resolve()), 'database': str(database.resolve()),
        'source_result_sha256': hashlib.sha256(source_bytes).hexdigest(),
        'started_at': datetime.now(timezone.utc).isoformat(),
        'requested_start': start.isoformat(), 'requested_end': end.isoformat(),
        'price_reference': 'Tencent day (no qfq/hfq key requested)',
        'action_reference': 'Eastmoney implemented distributions; not an exchange certificate',
        'absolute_price_tolerance': PRICE_TOLERANCE,
        'volume_compared': False,
        'live_trading_eligible': False,
        'training_started': False,
        'limitations': [
            'Public vendor agreement is not an exchange or broker nominal-price certification.',
            'Reference data are current snapshots, not point-in-time history.',
            'Corporate action reference does not verify cash payment dates, rights issues or tax.',
            'Null action amounts remain unknown, not zero; no data is repaired automatically.',
            'Tencent volumes may use lots; volume is not compared or substituted.',
        ],
        'stocks': [],
    }
    with requests.Session() as session:
        session.trust_env = False
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        for index, symbol in enumerate(symbols, start=1):
            prices, actions, receipts = {}, [], []
            errors = []
            stored_snapshot = json.dumps(
                [{'date': str(day), **row} for day, row in sorted(local_data[symbol].items())],
                ensure_ascii=False, allow_nan=False, separators=(',', ':'),
            ).encode('utf-8')
            stored_filename = f'{symbol[:6]}-stored-snapshot.json'
            (evidence / stored_filename).write_bytes(stored_snapshot)
            for begin, stop in windows(start, end):
                try:
                    payload, receipt = fetch(
                        session, TENCENT_URL,
                        {'param': f'sh{symbol[:6]},day,{begin},{stop},640,'},
                        evidence, f'{symbol[:6]}-ohlc-{begin}-{stop}.json',
                    )
                    receipts.append(receipt)
                    segment = parse_prices(payload, f'sh{symbol[:6]}', begin, stop)
                    prices.update(segment)
                except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
                    errors.append({'stage': 'prices', 'start': str(begin), 'end': str(stop), 'error': str(exc)})
                time.sleep(interval)
            page, total_pages = 1, 1
            seen_actions = set()
            while page <= total_pages:
                try:
                    payload, receipt = fetch(
                        session, ACTIONS_URL,
                        {'reportName': 'RPT_SHAREBONUS_DET', 'columns': 'ALL',
                         'filter': f'(SECURITY_CODE="{symbol[:6]}")(ASSIGN_PROGRESS="实施分配")',
                         'pageNumber': str(page), 'pageSize': '500',
                         'sortColumns': 'EX_DIVIDEND_DATE', 'sortTypes': '-1'},
                        evidence, f'{symbol[:6]}-actions-{page}.json',
                    )
                    receipts.append(receipt)
                    segment, pages = parse_actions(payload, symbol[:6])
                    if page > 1 and pages != total_pages:
                        raise ValueError('Action pagination changed during download')
                    total_pages = pages
                    for action in segment:
                        key = action['date']
                        if key in seen_actions:
                            raise ValueError(f'Duplicate corporate-action date: {key}')
                        seen_actions.add(key)
                        actions.append(action)
                except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
                    errors.append({'stage': 'actions', 'page': page, 'error': str(exc)})
                    break
                finally:
                    time.sleep(interval)
                page += 1
            result = compare(local_data[symbol], prices, actions)
            result.update({'symbol': symbol, 'errors': errors, 'evidence': receipts})
            result['stored_snapshot'] = {
                'file': stored_filename,
                'sha256': hashlib.sha256(stored_snapshot).hexdigest(),
            }
            result['reference_fetch_complete'] = not errors
            report['stocks'].append(result)
            (output / f'{symbol[:6]}-comparison.json').write_text(
                json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2), encoding='utf-8',
            )
            print(
                f'{index}/{len(symbols)} {symbol}: matched={result["matched_days"]}/{result["local_rows"]} '
                f'price_differences={result["price_mismatch_count"]} errors={len(errors)}',
                flush=True,
            )
            report['completed_stocks'] = len(report['stocks'])
            report['all_requested_stocks_processed'] = len(report['stocks']) == len(symbols)
            report['all_reference_fetches_complete'] = all(r['reference_fetch_complete'] for r in report['stocks'])
            report['all_ohlc_crosschecks_passed'] = (
                report['all_requested_stocks_processed']
                and all(r['ohlc_crosscheck_passed'] and r['reference_fetch_complete'] for r in report['stocks'])
            )
            report['all_known_action_fields_match'] = (
                report['all_requested_stocks_processed']
                and all(r['known_action_fields_match'] and r['reference_fetch_complete'] for r in report['stocks'])
            )
            report['research_crosscheck_passed'] = (
                report['all_ohlc_crosschecks_passed'] and report['all_known_action_fields_match']
                and all(not r['invalid_adjustment_dates'] and not r['unexplained_factor_changes']
                        for r in report['stocks'])
            )
            (output / 'summary.json').write_text(
                json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2), encoding='utf-8',
            )
    render_report(report, output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('result', type=Path)
    parser.add_argument('--database', type=Path, default=Path(STOCKS_DATABASE_PATH))
    parser.add_argument('--output-directory', type=Path, required=True)
    parser.add_argument('--request-interval', type=float, default=0.5)
    args = parser.parse_args()
    try:
        report = verify(args.result, args.database, args.output_directory, args.request_interval)
        print(f'Result: {args.output_directory.resolve()}')
        if not report['research_crosscheck_passed']:
            raise ValueError('Price/action research cross-check did not pass; training remains blocked')
        print('Known price/action fields agree; live certification remains blocked by action/PIT limitations.')
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error) as exc:
        parser.exit(1, f'External verification stopped: {exc}\n')


if __name__ == '__main__':
    main()
