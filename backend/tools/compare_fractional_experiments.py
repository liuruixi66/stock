"""Compare completed experiments without selecting models on the test results."""

import argparse
import json
from pathlib import Path
from statistics import mean

from research.fractional_results import chinese_result


def compare(paths: list[Path]) -> dict:
    experiments = []
    selected_sets = []
    for path in paths:
        source = json.loads(path.read_text(encoding='utf-8'))
        data = chinese_result(source)
        params = data['实验参数']
        if experiments:
            reference = experiments[0]['实验参数']
            for name in ('训练开始日期', '验证开始日期', '测试开始日期', '测试结束日期',
                         '买入费率', '卖出费率', '初始资金', '信号阈值', '股票池数量'):
                if params[name] != reference[name]:
                    raise ValueError(f'不可直接比较：{path} 的{name}不同')
        models = data['模型结果']
        signatures = {
            json.dumps([trial['试验配置'] for trial in model['候选试验']],
                       ensure_ascii=False, sort_keys=True)
            for model in models.values()
        }
        training_seeds = {model['随机种子'] for model in models.values()}
        if len(signatures) != 1 or len(training_seeds) != 1:
            raise ValueError(f'同一实验的模型配置或随机种子不一致：{path}')
        signature = next(iter(signatures))
        training_seed = next(iter(training_seeds))
        if experiments and (
            signature != experiments[0]['训练配置签名']
            or training_seed != experiments[0]['模型随机种子']
        ):
            raise ValueError(f'模型训练配置不同：{path}')
        provenance = data['数据溯源']
        selected_sets.append(set(provenance['入选股票']))
        backtests = data['回测结果']
        baseline = backtests['随机股票池等权基准']['累计收益率']
        metrics = {}
        for method, backtest in backtests.items():
            metrics[method] = {
                key: backtest[key] for key in (
                    '累计收益率', '年化收益率', '最大回撤', '零无风险利率夏普比率',
                    '累计交易费用', '成交笔数', '缺失预测数量',
                )
            }
            metrics[method]['期末资产'] = backtest['净值曲线'][-1]['总资产']
            metrics[method]['相对基准累计收益差'] = backtest['累计收益率'] - baseline
        experiments.append({
            '结果文件': str(path.resolve()), '股票池随机种子': params['随机种子'],
            '实验参数': params, '模型随机种子': training_seed,
            '训练配置签名': signature, '入选股票': provenance['入选股票'],
            '模型数量': len(models), '训练设备': sorted({m['训练设备'] for m in models.values()}),
            '回测指标': metrics,
        })
    overlaps = [
        {
            '种子甲': experiments[i]['股票池随机种子'],
            '种子乙': experiments[j]['股票池随机种子'],
            '重合股票数量': len(selected_sets[i] & selected_sets[j]),
        }
        for i in range(len(experiments)) for j in range(i + 1, len(experiments))
    ]
    summaries = {}
    for method in ('分数差分LSTM', '普通收益率LSTM'):
        rows = [item['回测指标'][method] for item in experiments]
        summaries[method] = {
            '跑赢基准样本组数': sum(row['相对基准累计收益差'] > 0 for row in rows),
            '样本组数': len(rows),
            '平均累计收益率': mean(row['累计收益率'] for row in rows),
            '最低累计收益率': min(row['累计收益率'] for row in rows),
            '最高累计收益率': max(row['累计收益率'] for row in rows),
        }
    return {
        '说明': '仅更换股票池随机种子，保持模型配置不变；此报告不是新模型选择依据。',
        '比例单位': '收益率和回撤使用小数，例如0.1代表10%；金额单位为人民币元。',
        '年化口径': '沿用原模拟器每年252交易日口径，不等于按日历十年计算的复合收益率。',
        '样本稳定性汇总': summaries, '股票池重合情况': overlaps,
        '实验明细': experiments,
        '限制': [
            '三个样本使用相同市场时期，且可能有股票重合，并非独立统计检验。',
            '当前数据库完整历史股票抽样存在幸存者偏差。',
            '仍沿用原连续复权数量模拟器，不包含整手、最低佣金、T+1或涨跌停成交约束。',
            '缺少历史每日涨跌停价和ST状态，未验证历史涨跌停规则。',
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path, nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execution-results', type=Path)
    args = parser.parse_args()
    try:
        report = compare(args.results)
        if args.execution_results:
            replay = json.loads(args.execution_results.read_text(encoding='utf-8'))
            summaries = []
            for experiment in replay['交易规则敏感性测试']:
                metrics = {}
                for method in experiment['有限交易约束模拟']:
                    original = experiment['子样本原模拟'][method]
                    constrained = experiment['有限交易约束模拟'][method]
                    metrics[method] = {
                        '子样本原模拟累计收益率': original['累计收益率'],
                        '有限交易约束累计收益率': constrained['累计收益率'],
                        '有限交易约束年化收益率': constrained['年化收益率'],
                        '有限交易约束最大回撤': constrained['最大回撤'],
                        '有限交易约束期末资产': constrained['净值曲线'][-1]['总资产'],
                        '原模拟累计交易费用': original['累计交易费用'],
                        '约束模拟累计交易费用': constrained['累计交易费用'],
                    }
                summaries.append({
                    '股票池随机种子': experiment['股票池随机种子'],
                    '股票池筛选': experiment['股票池筛选'],
                    '规则假设': experiment['规则假设'],
                    '指标对照': metrics, '解释限制': experiment['解释限制'],
                })
            report['第二阶段交易规则敏感性'] = summaries
        with args.output.open('x', encoding='utf-8') as output:
            json.dump(report, output, ensure_ascii=False, allow_nan=False, indent=2)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'Comparison stopped: {exc}\n')
    print(args.output)


if __name__ == '__main__':
    main()
