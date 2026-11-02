"""Plot saved experiments and Optuna searches as static Seaborn images."""

import argparse
from collections import defaultdict
from datetime import date
from html import escape
import json
import math
from pathlib import Path
from statistics import mean

from research.fractional_results import chinese_result


COLORS = ('#2563eb', '#e87924', '#16a085', '#9b59b6')
METHODS = ('分数差分LSTM', '普通收益率LSTM')
STYLE = """
body{margin:0;background:#f1f5f9;color:#17263c;font:16px "Microsoft YaHei",sans-serif}
main{max-width:1280px;margin:auto;padding:28px}
h1{font-size:30px}h2{margin-top:40px;border-left:5px solid #2563eb;padding-left:12px}
.note{padding:16px 20px;background:#fff7df;border-radius:10px;line-height:1.8}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,540px),1fr));gap:20px}
.card{background:white;border-radius:14px;padding:18px;box-shadow:0 2px 10px #17263c0a}
.card svg{width:100%;height:auto}.card p{color:#526175;font-size:14px;line-height:1.7}
a{color:#2563eb}nav{display:flex;gap:20px;flex-wrap:wrap}
table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:9px;border-bottom:1px solid #e2e8f0;text-align:right}
th:first-child,td:first-child{text-align:left}.scroll{overflow:auto}
"""


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'Expected a finite metric, got {value!r}')
    return float(value)


def label(value):
    return escape(str(value), quote=True)


def chart_data(title, series, categories, *, bars=False, numeric_x=False):
    if not categories or not series:
        raise ValueError(f'Empty chart: {title}')
    for _, values in series:
        if len(values) != len(categories):
            raise ValueError(f'Misaligned chart series: {title}')
    values = [number(v) for _, row in series for v in row if v is not None]
    if not values:
        raise ValueError(f'No finite observations: {title}')
    if bars:
        positions = list(range(len(categories)))
    elif numeric_x:
        positions = [number(float(item)) for item in categories]
        if positions != sorted(set(positions)):
            raise ValueError(f'X coordinates must be unique and ascending: {title}')
    else:
        positions = [date.fromisoformat(day).toordinal() for day in categories]
        if positions != sorted(set(positions)):
            raise ValueError(f'Dates must be unique and ascending: {title}')
    return values, positions


def svg_chart(title, series, categories, *, bars=False, percent=False, numeric_x=False):
    """Render all observations; lines use real calendar spacing when dated."""
    values, positions = chart_data(
        title, series, categories, bars=bars, numeric_x=numeric_x,
    )
    low, high = min(0, min(values)), max(0, max(values))
    padding = (high - low) * 0.08 or 1
    low, high = low - padding, high + padding
    left, top, width, height = 85, 65, 650, 290
    y = lambda value: top + height * (high - value) / (high - low)
    span = positions[-1] - positions[0] or 1
    x = lambda index: (
        left + width * (index + 0.5) / len(categories) if bars
        else left + width * (positions[index] - positions[0]) / span
    )
    fmt = lambda value: f'{value * 100:.2f}%' if percent else f'{value:.4g}'
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 780 455" role="img" '
        f'aria-label="{label(title)}" style="font-family:Microsoft YaHei,sans-serif">',
        f'<title>{label(title)}</title><rect width="780" height="455" fill="white"/>',
        f'<text x="390" y="20" text-anchor="middle" font-size="17" fill="#17263c">{label(title)}</text>',
    ]
    for tick in range(6):
        value = low + (high - low) * tick / 5
        py = y(value)
        parts.extend([
            f'<line x1="{left}" y1="{py:.2f}" x2="735" y2="{py:.2f}" stroke="#e2e8f0"/>',
            f'<text x="78" y="{py + 5:.2f}" text-anchor="end" font-size="12" fill="#526175">{fmt(value)}</text>',
        ])
    parts.append(f'<line x1="{left}" y1="{y(0):.2f}" x2="735" y2="{y(0):.2f}" stroke="#94a3b8"/>')
    for index, (name, row) in enumerate(series):
        color = COLORS[index % len(COLORS)]
        parts.append(
            f'<rect x="{left + index * 165}" y="37" width="12" height="12" fill="{color}"/>'
            f'<text x="{left + 18 + index * 165}" y="48" font-size="12">{label(name)}</text>',
        )
        if bars:
            bar_width = min(48, width / len(categories) * 0.8 / len(series))
            for i, value in enumerate(row):
                if value is None:
                    continue
                px = x(i) + (index - len(series) / 2) * bar_width
                py = min(y(value), y(0))
                parts.append(
                    f'<rect x="{px:.2f}" y="{py:.2f}" width="{bar_width:.2f}" '
                    f'height="{max(abs(y(value) - y(0)), 0.6):.2f}" fill="{color}">'
                    f'<title>{label(categories[i])} · {label(name)}: {fmt(value)}</title></rect>',
                )
        else:
            segment = []
            for i, value in enumerate(row):
                if value is None:
                    if segment:
                        parts.append(f'<polyline points="{" ".join(segment)}" fill="none" stroke="{color}" stroke-width="1.8"/>')
                    segment = []
                else:
                    segment.append(f'{x(i):.2f},{y(value):.2f}')
            if segment:
                parts.append(f'<polyline points="{" ".join(segment)}" fill="none" stroke="{color}" stroke-width="1.8"/>')
    step = max(1, math.ceil(len(categories) / (10 if bars else 6)))
    ticks = sorted(set(range(0, len(categories), step)) | {len(categories) - 1})
    for i in ticks:
        text = str(categories[i])
        transform = f' transform="rotate(-40 {x(i):.2f} 375)"' if bars else ''
        parts.append(f'<text x="{x(i):.2f}" y="375" text-anchor="end" font-size="11"{transform}>{label(text)}</text>')
    parts.append('</svg>')
    return ''.join(parts)


class Report:
    def __init__(self, directory):
        self.directory = directory
        self.sections = []
        self.count = 0

    def chart(self, title, description, series, categories, **options):
        if not any(value is not None for _, row in series for value in row):
            return f'<article class="card"><h3>{label(title)}</h3><p>此指标全部不可用，未绘图。</p><p>{label(description)}</p></article>'
        svg = svg_chart(title, series, categories, **options)
        self.count += 1
        filename = f'chart-{self.count:02d}.svg'
        (self.directory / filename).write_text(svg, encoding='utf-8')
        return (
            f'<article class="card"><h3>{label(title)}</h3>{svg}'
            f'<p>{label(description)}</p><a href="{filename}" download>下载 SVG 矢量图</a></article>'
        )

    def section(self, title, cards):
        self.sections.append(f'<h2>{label(title)}</h2><div class="grid">{"".join(cards)}</div>')


class SeabornReport(Report):
    def __init__(self, directory, image_format='png', dpi=180):
        super().__init__(directory)
        if image_format not in ('png', 'svg', 'pdf') or dpi < 72:
            raise ValueError('Static format must be png/svg/pdf and DPI must be >= 72')
        import matplotlib

        matplotlib.use('Agg')
        self.image_format, self.dpi = image_format, dpi
        self.charts = []

    def chart(self, title, description, series, categories, **options):
        if not any(value is not None for _, row in series for value in row):
            self.charts.append({'title': title, 'description': description, 'status': 'unavailable'})
            return ''
        figure = self.figure(title, series, categories, **options)
        import matplotlib.pyplot as plt

        filename = f'chart-{self.count + 1:02d}.{self.image_format}'
        try:
            figure.savefig(self.directory / filename, dpi=self.dpi, bbox_inches='tight')
        finally:
            plt.close(figure)
        self.count += 1
        self.charts.append({'file': filename, 'title': title, 'description': description})
        return ''

    def figure(self, title, series, categories, *, bars=False, percent=False, numeric_x=False):
        chart_data(title, series, categories, bars=bars, numeric_x=numeric_x)
        import matplotlib.dates as mdates
        from matplotlib import font_manager
        import matplotlib.pyplot as plt
        from matplotlib.ticker import PercentFormatter
        import pandas as pd
        import seaborn as sns

        installed = {font.name for font in font_manager.fontManager.ttflist}
        fonts = [name for name in ('Microsoft YaHei', 'SimHei', 'Noto Sans CJK SC')
                 if name in installed]
        if not fonts:
            raise ValueError('Install a Chinese font (Microsoft YaHei/SimHei/Noto Sans CJK SC)')
        sns.set_theme(style='whitegrid', rc={'font.sans-serif': fonts, 'axes.unicode_minus': False})
        rows = []
        for name, values in series:
            segment = 0
            for category, value in zip(categories, values):
                if value is None:
                    segment += 1
                    continue
                x = category if bars else (
                    float(category) if numeric_x else pd.Timestamp(category)
                )
                rows.append({'x': x, 'value': number(value), 'method': name, 'segment': segment})
        frame = pd.DataFrame(rows)
        figure, axis = plt.subplots(figsize=(max(12, min(24, len(categories) * .85)) if bars else 12, 6))
        try:
            palette = sns.color_palette('deep', len(series))
            names = [name for name, _ in series]
            if bars:
                sns.barplot(data=frame, x='x', y='value', hue='method', hue_order=names,
                            order=list(categories), palette=palette, errorbar=None, ax=axis)
                axis.tick_params(axis='x', labelrotation=25)
            else:
                sns.lineplot(data=frame, x='x', y='value', hue='method', hue_order=names,
                             units='segment', estimator=None, sort=False, palette=palette,
                             marker='o' if len(categories) < 3 else None, ax=axis)
                if not numeric_x:
                    locator = mdates.AutoDateLocator(minticks=3, maxticks=8)
                    axis.xaxis.set_major_locator(locator)
                    axis.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
            if percent:
                axis.yaxis.set_major_formatter(PercentFormatter(xmax=1))
            axis.axhline(0, color='gray', linewidth=.7)
            axis.set(title=title, xlabel='', ylabel='')
            axis.legend(title='', fontsize=9, loc='best')
            figure.tight_layout()
            return figure
        except Exception:
            plt.close(figure)
            raise

    def section(self, title, cards):
        pass

    def finish(self, source, notes):
        (self.directory / 'charts.json').write_text(json.dumps({
            'source': str(source.resolve()), 'format': self.image_format,
            'notes': notes, 'charts': self.charts,
        }, ensure_ascii=False, allow_nan=False, indent=2), encoding='utf-8')


def search_charts(report, data):
    methods = data['methods']
    if not methods:
        raise ValueError('Search report lacks methods')
    names = {'de_prado': METHODS[0], 'log_return': METHODS[1]}
    report.chart(
        '搜索赢家相对 MAE（低于 1 才优于零收益）',
        '历史验证折等权平均；同一验证集调参及评分，有选型偏差，不是独立测试。',
        [(names.get(method, method), [value['relative_mae']]) for method, value in methods.items()]
        + [('零收益基线', [1.0])], ['相对 MAE'], bars=True,
    )
    for method, result in methods.items():
        name = names.get(method, method)
        completed = [trial for trial in result['trials'] if trial['state'] == 'COMPLETE']
        if completed:
            report.chart(
                f'{name} 完整试验对比', '仅比较 COMPLETE 的完整目标值；剪枝和失败不当作完整评分。',
                [(name, [trial['value'] for trial in completed]),
                 ('零收益基线', [1.0] * len(completed))],
                [str(trial['number']) for trial in completed], bars=True,
            )
        folds = result['best_folds']
        if not folds:
            raise ValueError(f'No winner folds: {method}')
        labels = [f'{fold["instrument"]} / {fold["validation_start"][:4]}' for fold in folds]
        report.chart(
            f'{name} 各折相对 MAE', '每只股票、每个验证年的真实记录；低于 1 表示该折优于零收益。',
            [(name, [fold['relative_mae'] for fold in folds]),
             ('零收益基线', [1.0] * len(folds))], labels, bars=True,
        )
        report.chart(
            f'{name} 最佳轮次与实际训练轮数', '最佳轮次与早停前实际轮数不同；不能用训练上限代替实际训练量。',
            [('最佳 epoch', [fold['epoch'] for fold in folds]),
             ('实际训练轮数', [fold['epochs_run'] for fold in folds])], labels, bars=True,
        )
        for fold in folds:
            history = fold['epoch_history']
            if not history:
                raise ValueError(f'Missing epoch history: {method} {fold["instrument"]}')
            categories = [str(point['epoch']) for point in history]
            heading = f'{name} {fold["instrument"]} {fold["validation_start"][:4]}'
            report.chart(
                f'{heading} 逐轮损失', '训练/验证标准化 MSE；跨差分方法不可直接比较目标尺度。',
                [('训练 MSE', [point['training_mse_scaled'] for point in history]),
                 ('验证 MSE', [point['validation_mse_scaled'] for point in history])],
                categories, numeric_x=True,
            )
            report.chart(
                f'{heading} 选型指标', '实际早停指标为逆差分后的收益 MAE，不是标准化验证 MSE。',
                [('验证收益 MAE', [point['selection_score'] for point in history])],
                categories, numeric_x=True, percent=True,
            )


def model_charts(report, data):
    models = data.get('模型结果', {})
    if not models:
        raise ValueError('Result lacks model metadata')
    grouped = {method: {} for method in METHODS}
    for model in models.values():
        method = model['方法']
        if method in grouped:
            grouped[method][model['股票代码']] = model
    symbols = sorted(set().union(*(set(rows) for rows in grouped.values())))
    cards = []
    for title, key, description, percent in (
        ('各股票验证误差', '标准化验证均方误差',
         '选中 epoch 的标准化验证 MSE；默认按收益 MAE 选型，因此不一定是最低 MSE。不同差分方法的目标尺度不同，不能据此比较预测能力。', False),
        ('各股票测试收益率 MAE', '测试收益率平均绝对误差',
         '样本外下一交易日收益率预测的平均绝对误差，越低越好。1% 表示约 1 个百分点的收益率误差。', True),
        ('各股票最佳训练轮次', None,
         '验证集选出的最佳 epoch；滚动实验展示最后一个预测日的选型，不代表训练总进度。', False),
    ):
        rows = []
        for method, entries in grouped.items():
            values = [
                (entries[symbol].get(key) if key else entries[symbol]['选中模型']['最佳轮次'])
                if symbol in entries else None for symbol in symbols
            ]
            rows.append((method, values))
        cards.append(report.chart(title, description, rows, symbols, bars=True, percent=percent))
    trial_series = []
    for method, entries in grouped.items():
        for size, layers in sorted({
            (trial['试验配置']['隐藏单元数'], trial['试验配置'].get('LSTM层数', 1))
            for model in entries.values() for trial in model.get('候选试验', [])
        }):
            values = []
            for symbol in symbols:
                trials = entries.get(symbol, {}).get('候选试验', [])
                matches = [
                    t['最后一轮标准化验证均方误差'] for t in trials
                    if (t['试验配置']['隐藏单元数'], t['试验配置'].get('LSTM层数', 1))
                    == (size, layers)
                ]
                values.append(mean(matches) if matches else None)
            trial_series.append((f'{method} H{size} L{layers}', values))
    if trial_series:
        cards.append(report.chart(
            '候选模型最终验证误差', '各隐藏单元配置最后一轮的验证 MSE，并非最佳轮次 MSE；滚动实验仅展示最后一个预测日。',
            trial_series, symbols, bars=True,
        ))
    report.section('一、模型训练与测试预测', cards)
    histories = []
    for method, entries in grouped.items():
        daily = defaultdict(list)
        for model in entries.values():
            for point in model.get('逐日选型记录', model.get('daily_selections', [])):
                daily[point.get('目标日期', point.get('target_date'))].append(
                    number(point['标准化验证均方误差']),
                )
        if daily:
            histories.append((method, daily))
    extra = []
    if histories:
        days = sorted(set().union(*(set(rows) for _, rows in histories)))
        extra.append(report.chart(
            '滚动验证误差随预测日变化', '每个预测日跨股票的平均标准化验证 MSE；每天都是独立训练，并非同一个模型的 epoch 收敛曲线。',
            [(method, [mean(rows[day]) if day in rows else None for day in days]) for method, rows in histories],
            days,
        ))
    for method, entries in grouped.items():
        for symbol, model in sorted(entries.items()):
            trials = [t for t in model.get('候选试验', []) if t.get('逐轮训练记录')]
            if not trials:
                continue
            for trial in trials:
                history = trial['逐轮训练记录']
                extra.append(report.chart(
                    f'{symbol} {method} H{trial["试验配置"]["隐藏单元数"]} '
                    f'L{trial["试验配置"].get("LSTM层数", 1)} 逐轮损失',
                    '按代码排序首只具有记录的股票；滚动实验为最后一个预测日的候选训练。训练 MSE 是各批次更新前损失按样本数加权，验证 MSE 在该轮结束后计算。',
                    [('训练 MSE', [p['标准化训练均方误差'] for p in history]),
                     ('验证 MSE', [p['标准化验证均方误差'] for p in history])],
                    [str(p['最佳轮次']) for p in history], numeric_x=True,
                ))
            break
    if extra:
        report.section('补充：已记录的训练过程', extra)
    else:
        report.sections.append('<p class="note">此结果未保存逐轮 loss 或逐日滚动记录，不能还原收敛曲线。以上均为真实已保存指标；后续新训练将保存逐轮记录。</p>')
    evaluations = data.get('模型效果评价', {}).get('机器学习视角', {}).get('预测方法评价', {})
    if evaluations:
        cards = []
        for title, keys, percent in (
            ('测试集预测误差与零收益基线', ['平均绝对误差', '均方根误差'], True),
            ('测试集方向准确率', ['方向准确率（百分比）'], False),
            ('测试集百分比误差', ['平均绝对百分比误差（百分比）', '对称平均绝对百分比误差（百分比）'], False),
        ):
            series = []
            for method, metrics in evaluations.items():
                series.extend([
                    (method, [metrics[k] for k in keys]),
                    (f'{method}零基线', [metrics['零收益预测基线'][k] for k in keys]),
                ])
            cards.append(report.chart(title, '同一批测试样本；百分比误差图单位为 %，MAPE 对接近零的实际收益十分敏感。缺失值不绘制。', series, keys, bars=True, percent=percent))
        report.section('测试集机器学习评价', cards)
    else:
        report.sections.append('<p class="note">此旧结果未保存整体 RMSE、MAPE、方向准确率，不能从 MAE 反推，未展示这些指标。可直接查看各股票真实测试 MAE。</p>')


def financial_charts(report, backtests, capital, heading):
    capital = number(capital)
    if capital <= 0:
        raise ValueError('Initial capital must be positive')
    curves = {}
    for name, metrics in backtests.items():
        points = metrics['净值曲线']
        if not points:
            raise ValueError(f'Empty equity curve: {name}')
        days = [p['日期'] for p in points]
        if days != sorted(set(days)):
            raise ValueError(f'Duplicate or unordered equity dates: {name}')
        curves[name] = {p['日期']: number(p['总资产']) for p in points}
    days = sorted(set().union(*(set(row) for row in curves.values())))
    if not curves:
        raise ValueError('No backtests')
    cards = [report.chart(
        '累计净值对比', '总资产 / 实验初始资金；使用原始全部交易日，不做抽样或平滑。策略与随机股票池等权基准使用同一模拟口径。',
        [(name, [rows[day] / capital if day in rows else None for day in days]) for name, rows in curves.items()], days,
    )]
    drawdowns = []
    for name, rows in curves.items():
        peak = capital
        values = []
        for day in days:
            if day not in rows:
                values.append(None)
                continue
            peak = max(peak, rows[day])
            values.append(rows[day] / peak - 1)
        drawdowns.append((name, values))
    cards.append(report.chart('历史回撤', '相对截至当日的历史资产峰值（含初始资金）；越接近 0 越好。', drawdowns, days, percent=True))
    names = list(backtests)
    for title, keys, percent, description in (
        ('收益与风险指标', ['累计收益率', '年化收益率', '最大回撤', '年化波动率'], True,
         '直接使用结果文件指标；年化按 252 个交易日，最大回撤为负值。累计收益与年化收益口径不同。'),
        ('夏普比率', ['零无风险利率夏普比率'], False,
         '无风险利率假设为 0；收益波动为零时指标可能不可用，缺失值不绘制。'),
        ('累计交易费用', ['累计交易费用'], False,
         '单位：元。费用是整个测试期间累计发生的金额，并非本金一次性费率。'),
        ('成交笔数', ['成交笔数'], False, '单位：笔；辅助判断换手频率与交易成本压力。'),
    ):
        cards.append(report.chart(title, description, [(name, [backtests[name][key] for key in keys]) for name in names], keys, bars=True, percent=percent))
    report.section(heading, cards)
    keys = ['累计收益率', '年化收益率', '最大回撤', '年化波动率', '零无风险利率夏普比率', '累计交易费用', '成交笔数']
    rows = []
    for name in names:
        cells = []
        for i, key in enumerate(keys):
            value = backtests[name][key]
            cells.append('不可用' if value is None else (f'{number(value):.2%}' if i < 4 else f'{number(value):,.4g}'))
        rows.append(f'<tr><td>{label(name)}</td>{"".join(f"<td>{cell}</td>" for cell in cells)}</tr>')
    report.sections.append('<div class="card scroll"><table><tr><th>方法</th>' + ''.join(f'<th>{key}</th>' for key in keys) + '</tr>' + ''.join(rows) + '</table></div>')


def page(title, content):
    return f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{label(title)}</title><style>{STYLE}</style><body><main><h1>{label(title)}</h1>{content}</main></body></html>'


def generate(source, output, execution=None, *, image_format='html', dpi=180):
    raw = json.loads(source.read_text(encoding='utf-8'))
    if image_format not in ('html', 'png', 'svg', 'pdf'):
        raise ValueError('Unsupported report format')
    is_search = 'search_version' in raw
    if is_search:
        if image_format == 'html' or execution is not None:
            raise ValueError('Search reports require static images and no execution replay')
        output.mkdir(parents=True, exist_ok=False)
        report = SeabornReport(output, image_format, dpi)
        search_charts(report, raw)
        report.finish(source, [
            '历史验证选型记录，不是独立测试或实盘收益；失败与剪枝不作为完整试验比较。',
            '不支持从训练误差推断交易收益；本报告不重新训练。',
        ])
        return report.count
    data = chinese_result(raw)
    parameters = data['实验参数']
    seed = parameters['随机种子']
    output.mkdir(parents=True, exist_ok=False)
    report = Report(output) if image_format == 'html' else SeabornReport(output, image_format, dpi)
    model_charts(report, data)
    financial_charts(report, data['回测结果'], parameters['初始资金'], '二、原研究模拟：金融表现')
    if execution:
        financial_charts(report, execution['子样本原模拟'], parameters['初始资金'], '三、筛选子样本：原模拟控制组')
        financial_charts(report, execution['有限交易约束模拟'], parameters['初始资金'], '四、筛选子样本：有限交易约束')
        report.sections.append('<p class="note">' + '<br>'.join(label(note) for note in execution['解释限制']) + '</p>')
    if image_format != 'html':
        report.finish(source, [
            '仅复用保存结果，不重新训练。研究模拟不是真实 A 股执行验证。',
            '股票池存在幸存者偏差；供应商复权快照与原价均未获实盘认证。',
            '缺失指标不绘制；逐轮损失仅限实际保存的记录，不还原未保存的训练过程。',
        ] + (execution['解释限制'] if execution else []))
        return report.count
    intro = (
        '<nav><a href="../index.html">返回报告目录</a><a href="#charts">查看图表</a></nav>'
        f'<p>股票池种子：{label(seed)} · 测试期：{label(parameters["测试开始日期"])} — {label(parameters["测试结束日期"])}'
        f' · 初始资金：{number(parameters["初始资金"]):,.0f} 元</p>'
        f'<p>数据来源：{label(source.name)}。图表仅复用已保存结果，不重新训练。</p>'
        '<p class="note">模型误差与金融收益应分开解读。股票池存在幸存者偏差；研究模拟并非实盘业绩。'
        '费用约束复算使用事后筛选子样本，不可直接与完整股票池归因比较；未完整模拟涨跌停、股息税及历史费率。</p><div id="charts"></div>'
    )
    contract = data.get('价格口径约定')
    intro += (
        '<p class="note">价格口径：'
        + (f'版本 {label(contract["version"])}；' if contract else '旧版未声明版本；')
        + '供应商复权快照用于研究，不等于已认证的前/后复权；供应商 OHLC 未核验为原价。'
        '本报告不可用于证明实盘可交易性。</p>'
    )
    (output / 'index.html').write_text(page(f'LSTM 研究可视化 · 种子 {seed}', intro + ''.join(report.sections)), encoding='utf-8')
    return report.count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path, nargs='+', help='Completed experiment JSON files')
    parser.add_argument('--output-directory', type=Path, required=True, help='New directory; refuses overwrite')
    parser.add_argument('--execution-results', type=Path, help='Optional execution sensitivity JSON')
    parser.add_argument('--format', choices=('png', 'svg', 'pdf', 'html'), default='png',
                        help='Default: static PNG; HTML must be explicitly requested')
    parser.add_argument('--dpi', type=int, default=180)
    args = parser.parse_args()
    try:
        if args.output_directory.exists():
            raise ValueError('Refusing to overwrite an existing report directory')
        if len({p.stem for p in args.results}) != len(args.results):
            raise ValueError('Input result filenames must have unique stems')
        if args.dpi < 72:
            raise ValueError('DPI must be >= 72')
        execution_by_source = {}
        if args.execution_results:
            replay = chinese_result(json.loads(args.execution_results.read_text(encoding='utf-8')))
            for item in replay['交易规则敏感性测试']:
                source = Path(item['来源结果文件']).resolve()
                if source in execution_by_source:
                    raise ValueError(f'Duplicate execution source: {source}')
                execution_by_source[source] = item
            missing = [p for p in args.results if p.resolve() not in execution_by_source]
            if missing:
                raise ValueError(f'Execution results lack exact source matches: {missing}')
        args.output_directory.mkdir(parents=True)
        links = []
        for source in args.results:
            count = generate(
                source, args.output_directory / source.stem,
                execution_by_source.get(source.resolve()), image_format=args.format, dpi=args.dpi,
            )
            links.append(f'<li><a href="{label(source.stem)}/index.html">{label(source.name)}</a> · {count} 张图</li>')
            print(f'{source.name}: {count} charts')
        if args.format == 'html':
            index = args.output_directory / 'index.html'
            index.write_text(page('模型与金融指标可视化', '<p>各随机股票池独立展示；点击下方报告。所有图表均可离线查看、下载 SVG。</p><ul>' + ''.join(links) + '</ul>'), encoding='utf-8')
        print(args.output_directory.resolve())
    except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
        parser.exit(1, f'Visualization failed: {exc}\n')


if __name__ == '__main__':
    main()
