"""Collect one simple A-share distribution announcement as research evidence."""

import argparse
from datetime import date, datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import unicodedata

import requests


SEARCH_URL = 'https://www.cninfo.com.cn/new/information/topSearch/query'
ANNOUNCEMENTS_URL = 'https://www.cninfo.com.cn/new/hisAnnouncement/query'
PDF_ROOT = 'https://static.cninfo.com.cn/'


def parse_distribution(text, code):
    """Accept only the explicit simple per-share/table format; never guess dates."""
    normalized = re.sub(r'\s+', '', unicodedata.normalize('NFKC', text))
    if not re.search(r'证券代码[:：]?' + re.escape(code), normalized):
        raise ValueError('Announcement security code does not match')
    if '差异化分红送转:否' not in normalized:
        raise ValueError('Only explicitly non-differentiated distributions are supported')
    cash = re.search(r'A股每股现金红利(\d+(?:\.\d+)?)元', normalized)
    transfer = re.search(r'每股转增股份(\d+(?:\.\d+)?)股', normalized)
    header = normalized.find('股份类别股权登记日')
    if not cash or not transfer or header < 0:
        raise ValueError('Unsupported per-share distribution or date-table layout')
    table = normalized[header:header + 240]
    matches = re.search(
        r'A股(20\d{2}/\d{1,2}/\d{1,2})[-—－]+'
        r'(20\d{2}/\d{1,2}/\d{1,2})'
        r'(20\d{2}/\d{1,2}/\d{1,2})'
        r'(20\d{2}/\d{1,2}/\d{1,2})', table,
    )
    if not matches:
        raise ValueError('Unsupported A-share date table; manual review required')
    parsed = []
    for value in matches.groups():
        year, month, day = map(int, value.split('/'))
        parsed.append(date(year, month, day))
    record_day, ex_day, listing_day, payment_day = parsed
    if not record_day < ex_day <= listing_day or payment_day < ex_day:
        raise ValueError('Inconsistent distribution dates; manual review required')
    return {
        'instrument': f'{code}.SH',
        'cash_per_share_pretax': float(cash.group(1)),
        'transfer_shares_per_share': float(transfer.group(1)),
        'record_date': record_day.isoformat(), 'ex_date': ex_day.isoformat(),
        'new_share_listing_date': listing_day.isoformat(),
        'cash_payment_date': payment_day.isoformat(),
        'parser_scope': 'simple_non_differentiated_A_share_cash_and_transfer',
        'live_trading_eligible': False,
    }


def collect(code, year, output):
    if not re.fullmatch(r'6\d{5}', code) or not 2000 <= year <= date.today().year:
        raise ValueError('Expected a Shanghai stock code and a completed announcement year')
    if output.exists():
        raise ValueError('Refusing to overwrite an existing announcement directory')
    from pypdf import PdfReader

    output.mkdir(parents=True)
    receipts = []

    def save_response(response, filename):
        (output / filename).write_bytes(response.content)
        response.raise_for_status()
        receipts.append({
            'file': filename, 'sha256': hashlib.sha256(response.content).hexdigest(),
            'url': response.url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
        })
        return response

    with requests.Session() as session:
        session.trust_env = False
        session.headers.update({'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.cninfo.com.cn/'})
        search = save_response(session.post(
            SEARCH_URL, data={'keyWord': code, 'maxNum': '10'}, timeout=(8, 25),
        ), 'symbol-search.json').json()
        matches = [item for item in search if item.get('code') == code and item.get('orgId')]
        if len(matches) != 1:
            raise ValueError('No unique announcement issuer found')
        body = {
            'pageNum': '1', 'pageSize': '30', 'column': 'sse', 'tabName': 'fulltext',
            'plate': 'sh', 'stock': f'{code},{matches[0]["orgId"]}',
            'searchkey': '权益分派实施', 'secid': '', 'category': '', 'trade': '',
            'seDate': f'{year}-01-01~{year}-12-31', 'sortName': 'time',
            'sortType': 'asc', 'isHLtitle': 'false',
        }
        listings = save_response(session.post(
            ANNOUNCEMENTS_URL, data=body, timeout=(8, 25),
        ), 'announcement-list.json').json()
        candidates = [
            item for item in listings.get('announcements', [])
            if item.get('secCode') == code and '权益分派实施公告' in item.get('announcementTitle', '')
        ]
        if len(candidates) != 1 or listings.get('hasMore'):
            raise ValueError('Expected one unambiguous announcement; manual selection required')
        announcement = candidates[0]
        relative = announcement.get('adjunctUrl', '')
        if not re.fullmatch(r'finalpage/\d{4}-\d{2}-\d{2}/\d+\.[Pp][Dd][Ff]', relative):
            raise ValueError('Unexpected announcement PDF location')
        response = save_response(session.get(PDF_ROOT + relative, timeout=(8, 30)), 'announcement.pdf')
        reader = PdfReader(io.BytesIO(response.content))
        text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        record = parse_distribution(text, code)
    report = {
        'title': announcement['announcementTitle'],
        'announcement_id': announcement['announcementId'],
        'source': PDF_ROOT + relative, 'record': record,
        'evidence': receipts, 'training_started': False,
        'scope': 'One public announcement only; not full-universe action coverage.',
        'limitations': [
            'Parsing supports only explicit non-differentiated per-share cash/transfer and a complete A-share date table.',
            'An announced payment date is not proof of a particular account receiving funds.',
            'Tax, later corrections, trading restrictions and complete historical actions remain unverified.',
            'Original Yahoo records are preserved and not automatically overwritten.',
        ],
    }
    (output / 'normalized-event.json').write_text(
        json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2), encoding='utf-8',
    )
    print(f'Collected official event: {code}, ex-date={record["ex_date"]}, output={output.resolve()}')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--code', required=True)
    parser.add_argument('--year', type=int, required=True)
    parser.add_argument('--output-directory', type=Path, required=True)
    args = parser.parse_args()
    try:
        collect(args.code, args.year, args.output_directory)
    except (OSError, ValueError, KeyError, TypeError, ImportError, requests.RequestException) as exc:
        parser.exit(1, f'Announcement collection stopped: {exc}\n')


if __name__ == '__main__':
    main()
