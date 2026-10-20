"""Replay saved forecasts on screened nominal-price candidate subsamples.

Run from backend with:
python -m tools.replay_fractional_execution RESULT.json --output REPLAY.json

Results use Chinese field names. Input may use the original English schema or
the Chinese schema, but must include saved forecasts. Price digests must match
the training run. The post-hoc split/tick screen is NOT a prospective stock
selection rule. Dividend payment dates and historical price limits are absent:
dividends remain non-spendable receivables, and price limits are not simulated.
"""

import argparse
from contextlib import closing
from datetime import date
import hashlib
import json
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd

from config.settings import STOCKS_DATABASE_PATH
from research.fractional_execution import simulate_cash_shares
from research.fractional_forecast import (
    DatabaseRandomUniverse, DifferencingError, simulate_long_only, validate_prices,
)
from research.fractional_results import chinese_result


def replay(source: Path, database: Path, minimum_commission: float) -> dict:
    data = chinese_result(json.loads(source.read_text(encoding='utf-8')))
    if '逐日预测' not in data:
        raise DifferencingError('Result lacks saved forecasts; use a newly completed experiment')
    provenance = data['数据溯源']
    parameters = data['实验参数']
    start = date.fromisoformat(parameters['测试开始日期'])
    end = date.fromisoformat(parameters['测试结束日期'])
    selected = provenance['入选股票']
    codes = [symbol.removesuffix('.SH') for symbol in selected]
    marks = ','.join('?' for _ in codes)
    with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)) as connection:
        rows = connection.execute(
            f'''SELECT t.code, d.date, d.open, d.high, d.low, d.close,
                       d.adj_close, d.volume, d.dividends, d.splits
                FROM cn_daily d JOIN cn_tickers t ON t.symbol=d.symbol
                WHERE t.code IN ({marks}) AND d.date >= ?
                ORDER BY t.code,d.date''',
            [*codes, parameters['训练开始日期']],
        ).fetchall()
    raw = pd.DataFrame(rows, columns=[
        'instrument', 'date', 'open', 'high', 'low', 'close',
        'adj_close', 'volume', 'dividends', 'splits',
    ])
    raw['instrument'] = raw['instrument'].map(lambda code: f'{str(code).zfill(6)}.SH')
    raw = validate_prices(raw)
    historical = raw[raw['date'] <= end].copy()
    adjusted = historical[['date', 'instrument', 'open', 'high', 'low', 'close', 'volume']].copy()
    factor = historical['adj_close'].to_numpy(dtype=float) / historical['close'].to_numpy(dtype=float)
    if not np.isfinite(factor).all() or (factor <= 0).any():
        raise DifferencingError('Invalid adjusted-close factors in replay database')
    for column in ('open', 'high', 'low', 'close'):
        adjusted[column] = adjusted[column] * factor
    digest = hashlib.sha256(
        adjusted.to_csv(index=False, float_format='%.12g', lineterminator='\n').encode('utf-8'),
    ).hexdigest()
    if digest != provenance['所选行情SHA256']:
        raise DifferencingError('Replay database differs from the saved training price digest')
    kept, excluded = [], []
    for symbol in selected:
        stock = raw[(raw['instrument'] == symbol) & (raw['date'] >= start)]
        reasons = []
        if stock.empty:
            reasons.append('缺少测试期行情')
        actions = stock[['dividends', 'splits']].to_numpy(dtype=float)
        if not np.isfinite(actions).all() or (actions < 0).any():
            reasons.append('公司行动字段缺失或无效')
        if (stock['splits'].fillna(0) != 0).any():
            reasons.append('测试期或其后存在拆股，不能直接使用数据库价格计算历史整手')
        values = stock[['open', 'high', 'low', 'close']].to_numpy(dtype=float)
        if (np.abs(values * 100 - np.round(values * 100)) > 0.002).any():
            reasons.append('存在非分币价格，无法确认原价口径')
        if reasons:
            excluded.append({'股票代码': symbol, '排除原因': reasons})
        else:
            kept.append(symbol)
    if not kept:
        raise DifferencingError('No nominal-price candidates remain after data checks')
    universe = DatabaseRandomUniverse(
        kept, date.fromisoformat(provenance['股票池抽样日期']),
        parameters['随机种子'], provenance['合格股票数量'],
    )
    raw_test = raw[
        raw['instrument'].isin(kept) & (raw['date'] >= start) & (raw['date'] <= end)
    ]
    adjusted = adjusted[adjusted['instrument'].isin(kept)]
    options = {
        'initial_capital': parameters['初始资金'],
        'buy_cost': parameters['买入费率'], 'sell_cost': parameters['卖出费率'],
        'signal_threshold': parameters['信号阈值'],
    }
    controls, constrained = {}, {}
    for method in ('分数差分LSTM', '普通收益率LSTM', '随机股票池等权基准'):
        benchmark = method == '随机股票池等权基准'
        forecasts = {}
        if not benchmark:
            for point in data['逐日预测'][method]:
                symbol = point['股票代码']
                key = (date.fromisoformat(point['日期']), symbol)
                if key in forecasts:
                    raise DifferencingError('Duplicate forecast in replay result')
                if symbol in kept:
                    forecasts[key] = point['预测收益率']
        controls[method] = simulate_long_only(
            adjusted, forecasts, universe, start, end, benchmark=benchmark, **options,
        )
        constrained[method] = simulate_cash_shares(
            raw_test, forecasts, universe, start, end, benchmark=benchmark,
            minimum_commission=minimum_commission, **options,
        )
    return chinese_result({
        '来源结果文件': str(source.resolve()), '股票池随机种子': parameters['随机种子'],
        '股票池筛选': {
            '原股票数量': len(selected), '通过检查股票数量': len(kept),
            '入选股票': kept, '排除股票': excluded,
            '原始行情SHA256核验通过': True,
        },
        '规则假设': {
            '买入整手股数': 100, '最低每笔佣金元': minimum_commission,
            'T+1': '仅允许卖出前一交易日已持有的股份；每日先卖后买',
            '分红处理': '除息日记应收资产，不可用于买入；未扣股息税',
            '原价口径': '仅按无拆股及分币价格检查筛选，未获外部原价验证',
            '涨跌停': '未验证，也不限制涨跌停日成交',
            '费率口径': '沿用原买入费率作为佣金率；卖出额外费率为原卖出费率减原买入费率，不复现历史变更',
        },
        '子样本原模拟': controls, '有限交易约束模拟': constrained,
        '解释限制': [
            '筛选依据包含测试期间及其后的拆股信息，只是事后数据质量敏感性测试，不是可部署的事前选股规则。',
            '比较包含价格和分红记账口径的变化，差异不能全归因于佣金、整手或T+1。',
            '控制组和约束组使用相同子样本、相同已保存预测；未重新训练或按测试结果选模型。',
            '10万元资金分散配置时，100股门槛可能导致部分股票无法买入。',
        ],
    })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path, nargs='+')
    parser.add_argument('--database', type=Path, default=STOCKS_DATABASE_PATH)
    parser.add_argument('--minimum-commission', type=float, default=5.0)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.exit(1, 'Refusing to overwrite an existing replay\n')
    try:
        report = {'交易规则敏感性测试': [
            replay(source, args.database, args.minimum_commission) for source in args.results
        ]}
        with args.output.open('x', encoding='utf-8') as output:
            json.dump(report, output, ensure_ascii=False, allow_nan=False, indent=2)
    except (OSError, ValueError, KeyError, sqlite3.Error) as exc:
        parser.exit(1, f'Execution sensitivity stopped: {exc}\n')
    print(args.output)


if __name__ == '__main__':
    main()
