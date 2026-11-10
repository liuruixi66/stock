"""Render repeatable QMT experiment comparisons as PNG, without broker access.

Usage: python plot_qmt_experiments.py --config path-to-experiments.json
Metrics must come from each experiment's QMT report, not inferred from trades.
Add a named entry and its export path to qmt_experiments.json after each run.
annual_return, benchmark_annual_return, max_drawdown and win_rate are decimal
ratios (0.009 means 0.90%); sharpe and unit_nav are raw numbers. Omit unknown
metrics instead of copying them from another run. Paths are relative to JSON.
The yearly line chart sums exported profit by operation year, including buy
costs; it is not an annual return rate or a mark-to-market portfolio curve.
Optional entry fields: "nav_file": "daily-nav.csv", "nav_no_external_flows": true.
UTF-8 CSV columns are date,nav (ISO dates, positive unit NAV or total assets).
The first row must be the initial pre-trading value, followed by end-of-day
values. External deposits/withdrawals must already be unitized; otherwise
do not declare nav_no_external_flows. Annual returns include unrealized P&L;
first/last years show only the supplied interval, not extrapolated returns.
"""

import argparse
import csv
import io
import json
import math
from datetime import datetime
from pathlib import Path


def load_operations(path):
    raw = Path(path).read_bytes()
    for encoding in ('utf-8-sig', 'gb18030', 'utf-16'):
        try:
            text = raw.decode(encoding)
        except UnicodeError:
            continue
        if '\t' in text and ('操作时间' in text or '累计交易费用' in text):
            break
    else:
        raise ValueError('Unsupported QMT export encoding or header: {}'.format(path))
    reader = csv.DictReader(io.StringIO(text), delimiter='\t')
    summary = '累计交易费用' in (reader.fieldnames or [])
    if summary:
        required = {'代码', '累计盈亏', '累计交易费用'}
    else:
        required = {'代码', '操作时间', '操作类型', '盈利', '交易费用'}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError('Missing QMT operation columns: {}'.format(path))
    rows = []
    for line, row in enumerate(reader, 2):
        if None in row or any(row.get(key) is None for key in required):
            raise ValueError('Malformed operation row {}: {}'.format(line, path))
        try:
            profit = float(row['累计盈亏'] if summary else row['盈利'])
            fee = float(row['累计交易费用'] if summary else row['交易费用'])
            timestamp = (None if summary else
                         datetime.strptime(row['操作时间'], '%Y-%m-%d %H:%M:%S'))
        except ValueError as exc:
            raise ValueError('Invalid operation row {}: {}'.format(line, path)) from exc
        if not math.isfinite(profit) or not math.isfinite(fee) or fee < 0:
            raise ValueError('Invalid operation amount at row {}'.format(line))
        if not summary and row['操作类型'] not in ('买入', '卖出'):
            raise ValueError('Unsupported operation type: {}'.format(row['操作类型']))
        rows.append({'symbol': row['代码'], 'date': timestamp, 'profit': profit,
                     'fee': fee, 'side': None if summary else row['操作类型']})
    if not rows:
        raise ValueError('Empty operation export: {}'.format(path))
    return rows if summary else sorted(rows, key=lambda row: row['date'])


def load_experiments(config_path):
    config_path = Path(config_path).resolve()
    config = json.loads(config_path.read_text(encoding='utf-8'))
    entries = config['experiments']
    if not entries:
        raise ValueError('At least one experiment is required')
    experiments = []
    names = set()
    for entry in entries:
        name = entry['name']
        if not name or name in names:
            raise ValueError('Experiment names must be non-empty and unique')
        names.add(name)
        path = config_path.parent / entry['operations']
        rows = load_operations(path)
        metrics = entry.get('metrics', {})
        for key, value in metrics.items():
            if value is not None and (
                    isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value)):
                raise ValueError('Invalid report metric {} for {}'.format(key, name))
        nav = []
        if entry.get('nav_file'):
            if entry.get('nav_no_external_flows') is not True:
                raise ValueError('Confirm no external cash flows or use unitized NAV: ' + name)
            nav = load_nav(config_path.parent / entry['nav_file'])
        experiments.append({
            'name': name, 'rows': rows, 'metrics': metrics,
            'nav': nav,
            'fees': sum(row['fee'] for row in rows),
            'profit': sum(row['profit'] for row in rows),
        })
    output = config_path.parent / config.get('output', 'qmt_experiment_comparison.png')
    if output.suffix.lower() != '.png':
        raise ValueError('Output must be a PNG file')
    return experiments, output


def load_nav(path):
    """Load normalized NAV; never guess columns or silently fill missing values."""
    with Path(path).open(encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)
        if not {'date', 'nav'}.issubset(reader.fieldnames or []):
            raise ValueError('NAV CSV requires date,nav columns: {}'.format(path))
        values = []
        for row in reader:
            day = datetime.strptime(row['date'], '%Y-%m-%d').date()
            value = float(row['nav'])
            if not math.isfinite(value) or value <= 0:
                raise ValueError('NAV must be finite and positive: {}'.format(path))
            if values and day <= values[-1][0]:
                raise ValueError('NAV dates must be strictly increasing: {}'.format(path))
            values.append((day, value))
    if len(values) < 2:
        raise ValueError('NAV requires an initial value and at least one closing value')
    return values


def yearly_nav_returns(values):
    """Year-end/previous-year-end return; first interval starts at initial NAV."""
    if not values:
        return {}
    base = values[0][1]
    ends = {}
    for day, value in values[1:]:
        ends[day.year] = value
    result = {}
    for year, value in sorted(ends.items()):
        result[year] = value / base - 1
        base = value
    return result


def yearly_operation_profit(rows):
    """Sum the export's profit column; missing dates cannot be assigned a year."""
    if any(row['date'] is None for row in rows):
        return {}
    years = {}
    for row in rows:
        year = row['date'].year
        years.setdefault(year, []).append(row['profit'])
    return {year: math.fsum(values) for year, values in sorted(years.items())}


def render(experiments, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    installed = {font.name for font in font_manager.fontManager.ttflist}
    fonts = [name for name in ('Microsoft YaHei', 'SimHei', 'Noto Sans CJK SC')
             if name in installed]
    if not fonts:
        raise RuntimeError('Install a Chinese plotting font before rendering')
    plt.rcParams.update({
        'font.family': fonts + ['DejaVu Sans'], 'axes.unicode_minus': False,
        'figure.facecolor': '#101622', 'axes.facecolor': '#182131',
        'text.color': '#e8edf4', 'axes.labelcolor': '#e8edf4',
        'xtick.color': '#c5cfde', 'ytick.color': '#c5cfde',
        'axes.edgecolor': '#45516a', 'font.size': 10,
    })
    fig = plt.figure(figsize=(16, 17 + max(0, len(experiments) - 3) * 0.4))
    grid = fig.add_gridspec(5, 2, height_ratios=[1.2, 1, 1.3, 1.5, 1.2])
    table_ax = fig.add_subplot(grid[0, :])
    table_ax.axis('off')
    labels = [('年化收益', 'annual_return', 'percent'),
              ('基准年化', 'benchmark_annual_return', 'percent'),
              ('单位净值', 'unit_nav', 'number'),
              ('最大回撤', 'max_drawdown', 'percent'),
              ('夏普比率', 'sharpe', 'number'),
              ('胜率', 'win_rate', 'percent')]
    table_rows = []
    for experiment in experiments:
        cells = [experiment['name']]
        for _, key, format_name in labels:
            value = experiment['metrics'].get(key)
            cells.append('未提供' if value is None else
                         ('{:.2%}'.format(value) if format_name == 'percent'
                          else '{:.4f}'.format(value)))
        cells.extend(['未提供' if experiment['rows'][0]['side'] is None
                      else str(len(experiment['rows'])), '{:,.2f}'.format(experiment['fees']),
                      '{:+,.2f}'.format(experiment['profit'])])
        table_rows.append(cells)
    table = table_ax.table(
        cellText=table_rows,
        colLabels=['实验'] + [label[0] for label in labels] +
                  ['操作条数', '费用/元', '导出盈亏合计/元'],
        cellLoc='center', loc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.4)
    for (row, _), cell in table.get_celld().items():
        cell.set_facecolor('#26344b' if row == 0 else '#182131')
        cell.set_edgecolor('#45516a')
        cell.get_text().set_color('#7de1d5' if row == 0 else '#e8edf4')
    table_ax.set_title('QMT 实验对比 · 报告指标与操作统计', fontsize=19, pad=20)
    colors = plt.get_cmap('tab10')
    names = [experiment['name'] for experiment in experiments]
    fee_ax = fig.add_subplot(grid[1, 0])
    bars = fee_ax.bar(names, [experiment['fees'] for experiment in experiments],
                      color=[colors(i % 10) for i in range(len(experiments))])
    fee_ax.bar_label(bars, fmt='%.0f', padding=4)
    fee_ax.set_ylim(0, max(1, max(e['fees'] for e in experiments)) * 1.18)
    fee_ax.set_title('交易费用（已包含在平台收益核算中，不再次扣减）')
    fee_ax.set_ylabel('元')
    count_ax = fig.add_subplot(grid[1, 1])
    buys = [sum(row['side'] == '买入' for row in e['rows']) for e in experiments]
    sells = [sum(row['side'] == '卖出' for row in e['rows']) for e in experiments]
    count_ax.bar(names, buys, label='买入', color='#51b6cb')
    count_ax.bar(names, sells, bottom=buys, label='卖出', color='#dca65a')
    for index, experiment in enumerate(experiments):
        if experiment['rows'][0]['side'] is None:
            count_ax.text(index, 5, '未提供逐笔记录', ha='center', fontsize=9)
    count_ax.set_title('买卖操作条数')
    count_ax.legend()
    contribution_ax = fig.add_subplot(grid[2, :])
    symbols = sorted({row['symbol'] for e in experiments for row in e['rows']})
    symbol_names = {'510300': '沪深300', '510500': '中证500', '159915': '创业板',
                    '588000': '科创50', '511010': '国债', '518880': '黄金',
                    '511880': '货币ETF', '510050': '上证50', '510880': '红利',
                    '512890': '红利低波'}
    width = 0.8 / len(experiments)
    for index, experiment in enumerate(experiments):
        values = [sum(row['profit'] for row in experiment['rows']
                      if row['symbol'] == symbol) for symbol in symbols]
        x = [i - 0.4 + width / 2 + index * width for i in range(len(symbols))]
        contribution_ax.bar(x, values, width, label=experiment['name'],
                            color=colors(index % 10))
    contribution_ax.set_xticks(range(len(symbols)),
                              [symbol_names.get(symbol, symbol) for symbol in symbols])
    contribution_ax.axhline(0, color='#8c98ad', linewidth=0.8)
    contribution_ax.set_ylabel('元')
    contribution_ax.set_title('各标的导出盈亏合计 · 不是独立策略收益率')
    contribution_ax.legend()
    yearly_ax = fig.add_subplot(grid[3, :])
    all_years = set()
    missing_yearly = []
    for index, experiment in enumerate(experiments):
        totals = yearly_operation_profit(experiment['rows'])
        if not totals:
            missing_yearly.append(experiment['name'])
            continue
        first, last = min(totals), max(totals)
        years = list(range(first, last + 1))
        all_years.update(years)
        yearly_ax.plot(
            years, [totals.get(year, 0.0) for year in years], marker='o',
            linewidth=2, markersize=5, label=experiment['name'],
            color=colors(index % 10),
        )
    yearly_ax.set_xticks(sorted(all_years))
    yearly_ax.axhline(0, color='#8c98ad', linewidth=0.8)
    yearly_ax.grid(axis='y', alpha=0.2)
    yearly_ax.set_ylabel('每年导出盈亏合计 / 元')
    yearly_ax.set_xlabel(
        '操作年份 · 不含未实现浮盈亏，不是年度收益率；首末年可能非完整年度'
    )
    yearly_ax.set_title('年度操作盈亏折线对比（按交易日期汇总，费用不重复扣除）')
    if all_years:
        yearly_ax.legend()
    if missing_yearly:
        yearly_ax.text(0.01, 0.97, '无日期，未绘制：' + '、'.join(missing_yearly),
                       transform=yearly_ax.transAxes, va='top', color='#e7ba72')
    from matplotlib.ticker import PercentFormatter
    nav_ax = fig.add_subplot(grid[4, :])
    nav_years = set()
    unavailable = []
    for index, experiment in enumerate(experiments):
        totals = yearly_nav_returns(experiment.get('nav', []))
        if not totals:
            unavailable.append(experiment['name'])
            continue
        years = list(totals)
        nav_years.update(years)
        values = experiment['nav']
        label = '{}（{}～{}）'.format(experiment['name'], values[0][0], values[-1][0])
        nav_ax.plot(years, list(totals.values()), marker='o', linewidth=2,
                    label=label, color=colors(index % 10))
    nav_ax.set_title('含持仓浮盈亏的年度收益率 · 仅使用账户净值数据')
    nav_ax.set_ylabel('区间收益率')
    nav_ax.set_xlabel('首末年可能为部分年度；非年化推算，不重复扣费用')
    nav_ax.yaxis.set_major_formatter(PercentFormatter(1))
    nav_ax.axhline(0, color='#8c98ad', linewidth=0.8)
    nav_ax.grid(axis='y', alpha=0.2)
    if nav_years:
        nav_ax.set_xticks(sorted(nav_years))
        nav_ax.legend(fontsize=9)
    else:
        nav_ax.set_xticks([])
    if unavailable:
        nav_ax.text(0.01, 0.95, '未提供每日净值，无法计算：' + '、'.join(unavailable),
                    transform=nav_ax.transAxes, va='top', color='#e7ba72')
    ranges = ['{}：{}'.format(
        e['name'], '仅标的汇总，日期未知' if e['rows'][0]['date'] is None else
        '{} ～ {}'.format(e['rows'][0]['date'].date(), e['rows'][-1]['date'].date()))
        for e in experiments]
    fig.text(0.035, 0.057, '操作日期（非回测区间）：' + '；'.join(ranges[:2]), fontsize=9)
    fig.text(0.035, 0.039, '；'.join(ranges[2:]), fontsize=9)
    fig.text(0.035, 0.02,
             '报告指标按原报告录入；未提供不推算。操作盈利合计不等于账户净值/最大回撤，'
             '费用不重复扣除。对比前核对区间、资金及费用一致。', fontsize=10,
             color='#e7ba72')
    fig.tight_layout(rect=(0.02, 0.08, 0.98, 0.96))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    experiments, output = load_experiments(args.config)
    render(experiments, output)
    print('PNG saved:', output)


if __name__ == '__main__':
    main()
