"""Render a Chinese offline dashboard without restarting the training process."""

import argparse
from html import escape
import json
import logging
import math
from pathlib import Path
import time

from tools.plot_fractional_research import svg_chart


STATUS = {
    'starting': '正在启动',
    'loading_frozen_market_snapshot': '正在装载行情',
    'preparing_sequences': '正在构造训练样本',
    'training': '正在训练模型',
    'validation_threshold_selection': '正在验证与选择入场门槛',
    'held_out_test': '正在独立测试',
    'completed': '实验已完成',
    'failed': '任务已停止',
}
STYLE = """
*{box-sizing:border-box}body{margin:0;background:#f4f7fb;color:#17263c;
font:15px/1.65 "Microsoft YaHei","Segoe UI",sans-serif}main{max-width:1260px;
margin:auto;padding:32px 24px}header{display:flex;justify-content:space-between;
gap:20px;align-items:center;margin-bottom:24px}h1{font-size:27px;margin:0 0 6px}
h2{font-size:19px;margin:0 0 16px}h3{font-size:16px;margin:0 0 12px}
p{margin:6px 0}.muted{color:#64748b;font-size:13px}.badge{background:#e0eaff;
color:#2549a4;border-radius:20px;padding:7px 14px;white-space:nowrap}
.panel,.metric{background:white;border:1px solid #e1e8f0;border-radius:14px;
padding:22px;min-width:0}.panel{margin-bottom:20px}.metrics{display:grid;
grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:20px}
.metric strong{display:block;font-size:23px;margin-top:8px;overflow-wrap:anywhere}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
.grid>div{min-width:0}progress{width:100%;height:13px;accent-color:#4169e1}
.bar-caption{display:flex;justify-content:space-between;gap:12px;margin:14px 0 6px}
.steps{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 4px}
.step{padding:5px 12px;background:#f1f5f9;color:#64748b;border-radius:7px}
.active{background:#e0eaff;color:#2549a4}.done{background:#e4f6ed;color:#19734c}
.empty{padding:36px 20px;text-align:center;border:1px dashed #cbd5e1;
border-radius:10px;color:#64748b;background:#fafcff}
svg{display:block;width:100%;height:auto}table{width:100%;border-collapse:collapse}
td,th{padding:9px 10px;text-align:left;border-bottom:1px solid #edf1f7}
td{font-variant-numeric:tabular-nums}pre{white-space:pre-wrap;overflow-wrap:anywhere;
word-break:break-word;background:#f8fafc;padding:16px;border-radius:8px;font-size:12px}
summary{cursor:pointer;color:#4169e1}details{margin-top:16px}
.notice{border-left:4px solid #e8ad40;background:#fff9eb;padding:14px 18px;
border-radius:6px;margin-bottom:20px}.error{color:#a62323;background:#fff0f0}
@media(max-width:760px){main{padding:18px 12px}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}
.grid{grid-template-columns:minmax(0,1fr)}header{display:block}.badge{display:inline-block;margin-top:10px}
h1{font-size:23px}.panel{padding:16px}.metric strong{font-size:19px}th,td{padding:7px 4px;font-size:12px}}
"""


def text(value):
    return escape(str(value), quote=True)


def numeric(value, percent=False):
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        return '尚无数据'
    return f'{value:.2%}' if percent else f'{value:,.4g}'


def metric(label, value, note):
    return (f'<article class="metric"><span class="muted">{text(label)}</span>'
            f'<strong>{text(value)}</strong><span class="muted">{text(note)}</span></article>')


def render_dashboard(state):
    status = state['status']
    loading = state.get('loading', {})
    loaded, total = loading.get('loaded', 0), loading.get('total', 0)
    history = state.get('epochs', [])
    epochs = state.get('requested_epochs', 0)
    batch = state.get('current_batch', {})
    gpu_ids = state.get('gpu_ids', [])
    device = ('双卡并行' if len(gpu_ids) == 2 else
              f'{len(gpu_ids)} 卡并行' if gpu_ids else state.get('device', '检测中'))
    stage_names = [
        ('loading_frozen_market_snapshot', '装载数据'),
        ('preparing_sequences', '构造样本'), ('training', '训练模型'),
        ('validation_threshold_selection', '验证选型'), ('held_out_test', '独立测试'),
        ('completed', '完成'),
    ]
    current = next((i for i, (name, _) in enumerate(stage_names) if name == status), -1)
    steps = ''.join(
        f'<span class="step {"active" if i == current else "done" if i < current else ""}">'
        f'{i + 1}. {label}</span>' for i, (_, label) in enumerate(stage_names)
    )
    if status == 'loading_frozen_market_snapshot':
        value = loaded / total * 100 if total else 0
        caption = f'{loaded:,} / {total:,} 只股票' if total else '正在读取交易日历和股票名单'
        description = '此阶段使用 CPU 读取数据库；装载完成并构造样本后，显卡才开始训练。'
    elif status == 'training':
        value = (len(history) / epochs * 100) if epochs else 0
        caption = f'已完成 {len(history)} / {epochs} 轮'
        if batch:
            caption += f' · 当前第 {batch["epoch"]} 轮，批次 {batch["batch"]} / {batch["batches"]}'
        description = '批次损失只是本轮累计值；完整训练与验证曲线在每轮结束后更新。'
    else:
        value = 100 if status == 'completed' else None
        caption = STATUS.get(status, status)
        description = '金融图表将在模型训练结束、产生真实预测与回测记录后出现。'
    progress = (f'<progress max="100" value="{max(0, min(100, value)):.2f}"></progress>'
                if value is not None else '<progress max="100"></progress>')
    model = '<div class="empty">尚无完整训练轮次<br>第一轮结束后显示训练／验证误差，不绘制模拟曲线。</div>'
    if history:
        model = svg_chart(
            '逐轮训练与验证误差（标准化 MSE）',
            [('训练误差', [r['train_mse'] for r in history]),
             ('验证误差', [r['validation_mse'] for r in history])],
            [r['epoch'] for r in history], numeric_x=True,
        )
    finance = []
    for name, label in (('validation', '验证集'), ('test', '测试集')):
        result = state.get(name, {})
        curve = result.get('curve', [])
        if not curve:
            finance.append(f'<div><h3>{label}金融表现</h3><div class="empty">'
                           '等待真实回测结果<br>暂无净值、收益或回撤数据。</div></div>')
            continue
        days = [row['date'] for row in curve]
        charts = svg_chart(
            f'{label}净值（初始资金 10 万元）',
            [('净值', [r['equity'] / 100000 for r in curve])], days,
        ) + svg_chart(
            f'{label}历史回撤',
            [('回撤', [r['drawdown'] for r in curve])], days, percent=True,
        )
        finance.append(f'<div><h3>{label}金融表现</h3>{charts}</div>')
    rows = []
    for key, label, percent in (
        ('total_return', '累计收益', True), ('max_drawdown', '最大回撤', True),
        ('sharpe_zero_rate', '夏普比率（零无风险利率）', False), ('fees', '累计费用（元）', False),
    ):
        rows.append('<tr><th>' + label + '</th>' + ''.join(
            '<td>' + numeric(state.get(name, {}).get(key), percent) + '</td>'
            for name in ('validation', 'test')) + '</tr>')
    for key, label in (('mae', '预测收益率 MAE'), ('rmse', '预测收益率 RMSE'),
                       ('directional_accuracy_percent', '方向准确率（%）')):
        rows.append('<tr><th>' + label + '</th>' + ''.join(
            '<td>' + numeric(state.get(name + '_metrics', {}).get(key)) + '</td>'
            for name in ('validation', 'test')) + '</tr>')
    refresh = '<meta http-equiv="refresh" content="15">' if status not in ('completed', 'failed') else ''
    sample_count = sum(state.get('samples', {}).values())
    verified = state.get('verified_training_devices', [])
    device_note = ('已验证 ' + '、'.join(verified)) if verified else '本次训练尚未验证首批计算'
    if status == 'loading_frozen_market_snapshot':
        device_note = '已配置 · 数据装载阶段不训练'
    error = ('<section class="panel error"><h2>任务错误</h2><pre>' + text(state['error'])
             + '</pre></section>') if state.get('error') else ''
    raw = json.dumps({k: v for k, v in state.items()
                      if k not in ('epochs', 'validation', 'test')}, ensure_ascii=False, indent=2)
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        + refresh + '<title>全市场 LSTM · 训练与金融研究看板</title><style>' + STYLE
        + '</style></head><body><main><header><div><h1>全市场 LSTM 研究看板</h1>'
        '<p class="muted">共享模型 · 周度轮动 · 训练与回测分阶段展示</p></div>'
        f'<span class="badge">{text(STATUS.get(state["status"], state["status"]))}</span></header>'
        '<div class="metrics">'
        + metric('计算设备', device, device_note)
        + metric('行情装载', f'{loaded:,} / {total:,}' if total else '准备中', '股票数量，不是训练进度')
        + metric('训练轮次', f'{len(history)} / {epochs}', '完整轮次结束后更新')
        + metric('有效样本', f'{sample_count:,}' if sample_count else '待构造', '训练／验证／测试合计')
        + '</div><section class="panel"><h2>任务进度</h2><div class="bar-caption"><span>'
        + text(caption) + '</span><span class="muted">'
        + (f'{value:.1f}%' if value is not None else '处理中')
        + '</span></div>' + progress + '<div class="steps">' + steps + '</div>'
        '<p class="muted">' + text(description) + '</p><p class="muted">源数据更新时间：'
        + text(state['updated_at']) + ' · 运行期间每 15 秒自动刷新</p></section>'
        + error + '<div class="notice">研究用途，非实盘成交。按约定不排除 ST、暂不限制行业权重；'
        'TWAP／VWAP 因缺少分钟行情暂不可用。</div>'
        '<section class="panel"><h2>模型训练</h2>' + model + '</section>'
        '<section class="panel"><h2>金融表现</h2><div class="grid">' + ''.join(finance)
        + '</div><table><thead><tr><th>指标</th><th>验证集</th><th>测试集</th></tr></thead>'
        '<tbody>' + ''.join(rows) + '</tbody></table></section>'
        '<section class="panel"><h2>时间隔离与策略</h2><p>训练：2020—2023　'
        '验证：2024—2025　测试：2026 至有效数据末日。</p>'
        '<p class="muted">标准化只用训练集，跨边界标签剔除；验证集用于选模型，测试集不参与调参。'
        '历史数据快照未获时点认证，且此前研究已观察过部分 2026 数据。</p>'
        '<p>每周调仓，前 30 候选／前 50 持仓缓冲，最多替换 6 只，目标总仓位不超过 95%。</p>'
        '<p class="muted">停牌持仓冻结；价格上涨和冻结持仓可能使实际仓位偏离目标。</p>'
        '<details><summary>查看设备、参数与原始诊断数据</summary><pre>' + text(raw)
        + '</pre></details><details><summary>完整研究限制</summary><ul>'
        + ''.join('<li>' + text(v) + '</li>' for v in state.get('limitations', []))
        + '</ul></details></section></main></body></html>'
    )


def watch(source, output, source_pid=None, interval=5):
    from tools.run_market_rotation import replace_report_file

    last = None
    while True:
        raw = source.read_text(encoding='utf-8')
        if raw != last:
            state = json.loads(raw)
            temporary = output.with_suffix('.html.tmp')
            temporary.write_text(render_dashboard(state), encoding='utf-8')
            replace_report_file(temporary, output)
            last = raw
            logging.info('Dashboard updated: %s', state['status'])
        if state['status'] in ('completed', 'failed'):
            return
        if source_pid is not None:
            import ctypes
            ctypes.windll.kernel32.OpenProcess.restype = ctypes.c_void_p
            ctypes.windll.kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
            handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, source_pid)
            if not handle:
                state.update(status='failed', error='训练进程已退出；查看原始运行日志。')
                output.write_text(render_dashboard(state), encoding='utf-8')
                raise RuntimeError(f'Training process {source_pid} is no longer available')
            ctypes.windll.kernel32.CloseHandle(handle)
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--source-pid', type=int)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    if args.source.resolve() == args.output.resolve():
        parser.error('Dashboard output cannot replace source progress JSON')
    if args.watch:
        watch(args.source, args.output, args.source_pid)
    else:
        state = json.loads(args.source.read_text(encoding='utf-8'))
        args.output.write_text(render_dashboard(state), encoding='utf-8')


if __name__ == '__main__':
    main()
