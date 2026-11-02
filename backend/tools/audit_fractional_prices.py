"""Read-only price-basis audit for an existing experiment; never certifies live data."""

import argparse
from contextlib import closing
from datetime import date
import json
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd

from config.settings import STOCKS_DATABASE_PATH
from market_data.price_basis import (
    ACTION_COLUMNS, PRICE_COLUMNS, adjusted_ohlc, frame_digest, research_price_contract,
)
from research.fractional_results import chinese_result


def audit(source: Path, database: Path) -> dict:
    data = chinese_result(json.loads(source.read_text(encoding='utf-8')))
    parameters = data['实验参数']
    provenance = data['数据溯源']
    symbols = provenance['入选股票']
    if not symbols or len(symbols) != len(set(symbols)):
        raise ValueError('Audit requires a nonempty unique stock universe')
    codes = [symbol.removesuffix('.SH') for symbol in symbols]
    if any(len(code) != 6 or not code.isdigit() or symbol != f'{code}.SH'
           for symbol, code in zip(symbols, codes)):
        raise ValueError('Audit supports six-digit Shanghai stock codes only')
    start = date.fromisoformat(parameters['训练开始日期'])
    end = date.fromisoformat(parameters['测试结束日期'])
    if start > end:
        raise ValueError('Invalid audit date range')
    with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)) as connection:
        connection.execute('BEGIN')
        placeholders = ','.join('?' for _ in codes)
        rows = connection.execute(
            f'''SELECT t.code, d.date, d.open, d.high, d.low, d.close,
                       d.adj_close, d.volume, d.dividends, d.splits
                FROM cn_tickers t CROSS JOIN cn_daily d
                WHERE t.symbol=d.symbol AND t.code IN ({placeholders})
                  AND d.date BETWEEN ? AND ?
                ORDER BY t.code, d.date''',
            [*codes, start.isoformat(), end.isoformat()],
        ).fetchall()
    frame = pd.DataFrame(rows, columns=[
        'instrument', 'date', 'open', 'high', 'low', 'close',
        'adj_close', 'volume', 'dividends', 'splits',
    ])
    frame['instrument'] = frame['instrument'].map(lambda code: f'{str(code).zfill(6)}.SH')
    frame['date'] = frame['date'].map(date.fromisoformat)
    if set(frame['instrument']) != set(symbols):
        raise ValueError('Audit database is missing selected stocks')
    if frame.duplicated(['instrument', 'date']).any():
        raise ValueError('Audit database contains duplicate stock/date rows')
    adjusted = frame[list(PRICE_COLUMNS)].copy()
    adjusted_values = []
    for row in frame.itertuples(index=False):
        try:
            adjusted_values.append(adjusted_ohlc(row.open, row.high, row.low, row.close, row.adj_close))
        except ValueError as exc:
            raise ValueError(f'{row.instrument} {row.date}: {exc}') from exc
    adjusted[['open', 'high', 'low', 'close']] = adjusted_values
    adjusted['volume'] = adjusted['volume'].astype(float)
    vendor = frame.copy()
    vendor[list(PRICE_COLUMNS)[2:]] = vendor[list(PRICE_COLUMNS)[2:]].astype(float)
    samples = []
    for symbol, group in frame.groupby('instrument', sort=True):
        prices = group[['open', 'high', 'low', 'close']].to_numpy(dtype=float)
        actions = group[['dividends', 'splits']].to_numpy(dtype=float)
        volume = group['volume'].to_numpy(dtype=float)
        factor = group['adj_close'].to_numpy(dtype=float) / group['close'].to_numpy(dtype=float)
        latest = group.iloc[-1]
        non_cent = np.any(np.abs(prices * 100 - np.round(prices * 100)) > 0.002, axis=1)
        action_invalid = ~np.isfinite(actions).all(axis=1) | (actions < 0).any(axis=1)
        samples.append({
            '股票代码': symbol, '行情行数': len(group),
            '首日': group.iloc[0]['date'].isoformat(), '末日': latest['date'].isoformat(),
            '非分币OHLC行数': int(non_cent.sum()),
            '拆股事件行数': int((group['splits'] > 0).sum()),
            '分红事件行数': int((group['dividends'] > 0).sum()),
            '无效公司行动行数': int(action_invalid.sum()),
            '无效成交量行数': int((~np.isfinite(volume) | (volume < 0)).sum()),
            '最小复权因子': float(factor.min()), '最大复权因子': float(factor.max()),
            '末日close': float(latest['close']), '末日adj_close': float(latest['adj_close']),
            '末日复权因子接近1': bool(np.isclose(factor[-1], 1, rtol=0, atol=1e-6)),
            '原价已核验': False,
        })
    digests = {
        '所选行情SHA256': frame_digest(adjusted, PRICE_COLUMNS),
        '供应商OHLC行情SHA256': frame_digest(vendor, PRICE_COLUMNS),
        '公司行动SHA256': frame_digest(frame, ACTION_COLUMNS),
    }
    matches = {key: value == provenance[key] if key in provenance else None
               for key, value in digests.items()}
    declared_contract = data.get('价格口径约定')
    contract_ok = declared_contract is None or (
        declared_contract == chinese_result(research_price_contract())
        and provenance.get('价格口径约定') == declared_contract
        and all(value is True for value in matches.values())
    )
    research_ok = (
        matches['所选行情SHA256'] is True and all(v is not False for v in matches.values())
        and all(row['无效成交量行数'] == 0 for row in samples)
        and contract_ok
    )
    return {
        '来源结果文件': str(source.resolve()), '数据库路径': str(database.resolve()),
        '审计范围': '仅覆盖所选股票的实验历史区间；不是全库审计或历史时点认证',
        '价格口径约定': chinese_result(research_price_contract()),
        '来源口径状态': '旧版未声明' if declared_contract is None else '已声明版本',
        '声明口径一致': contract_ok,
        '研究行情与历史结果一致': research_ok,
        '指纹核验': matches, '当前指纹': digests,
        '股票数量': len(samples), '行情行数': len(frame), '股票明细': samples,
        '可用于实盘': False,
        '实盘阻断项': [
            '供应商OHLC未逐日与交易所或券商不复权原价核验；分币检查不能证明是原价。',
            '复权数据是当前快照，缺少历史时点版本及公司行动当时可得性证据。',
            '增量下载仅刷新重叠窗口，历史复权因子可能来自不同下载快照；须全历史一致性复核。',
            '公司行动缺少到账日、送转股登记/上市日及股息税；现有下载代码将缺失行动填零，零不证明无事件。',
            '缺少经过核验的历史涨跌停价、ST状态、停复牌及可成交量约束。',
        ],
        '处理规则': [
            '模型固定使用供应商adj_close/close调整OHLC，成交量不调整；不冒称已认证前复权或后复权。',
            '禁止将复权价格用于实际股数成交；股数模拟仅为未核验供应商价格的敏感性分析。',
            '新实验、模型和检查点携带版本化口径；旧检查点必须保留，不能按新口径续跑。',
            '逐股逐日仅用目标日前验证数据选型；测试收益不能参与最佳模型选择。',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('result', type=Path)
    parser.add_argument('--database', type=Path, default=Path(STOCKS_DATABASE_PATH))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-live-ready', action='store_true',
                        help='Write audit, then fail because vendor snapshots are not live-certified')
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError('Refusing to overwrite an existing audit')
        report = audit(args.result, args.database)
        with args.output.open('x', encoding='utf-8') as target:
            json.dump(report, target, ensure_ascii=False, allow_nan=False, indent=2)
        print(f'Audited {report["股票数量"]} stocks / {report["行情行数"]} rows: {args.output.resolve()}')
        print('LIVE BLOCKED: vendor nominal prices and point-in-time adjustments are unverified.')
        if not report['研究行情与历史结果一致']:
            raise ValueError('Research data validation failed; inspect the written audit')
        if args.require_live_ready:
            raise ValueError('Live readiness failed; inspect the written audit blockers')
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        parser.exit(1, f'Price audit stopped: {exc}\n')


if __name__ == '__main__':
    main()
