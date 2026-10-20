"""Localize result presentation without changing model parameter identifiers."""

import re
from typing import overload

FIELD_NAMES = {
    'paper': '论文链接', 'status': '状态', 'universe': '股票池说明',
    'data_provenance': '数据溯源', 'inputs': '输入', 'parameters': '实验参数',
    'models': '模型结果', 'forecasts': '逐日预测', 'backtests': '回测结果',
    'deviations': '方法差异与限制', 'database': '数据库', 'source': '数据来源',
    'database_path': '数据库路径', 'table': '行情表', 'ticker_table': '股票代码表',
    'exchange': '交易所', 'adjustment': '复权方式', 'universe_mode': '股票池模式',
    'universe_selection_date': '股票池抽样日期', 'universe_seed': '股票池随机种子',
    'universe_size': '股票池数量', 'eligible_universe_size': '合格股票数量',
    'selected_instruments': '入选股票', 'train_start': '训练开始日期',
    'validation_start': '验证开始日期', 'test_start': '测试开始日期',
    'test_end': '测试结束日期', 'price_rows': '行情行数',
    'selected_prices_sha256': '所选行情SHA256', 'survivorship_bias': '存在幸存者偏差',
    'seed': '随机种子', 'model_seed': '模型随机种子', 'buy_cost': '买入费率',
    'sell_cost': '卖出费率', 'signal_threshold': '信号阈值',
    'initial_capital': '初始资金', 'instrument': '股票代码', 'method': '方法',
    'order_details': '差分阶数估计', 'order': '差分阶数', 'trials': '候选试验',
    'statistic': 'ADF统计量', 'pvalue': 'P值', 'observations': '观测数量',
    'critical_5pct': '百分之五临界值', 'lags': '滤波权重长度', 'estimation': '估计方式',
    'sample_counts': '样本数量', 'train': '训练集', 'validation': '验证集',
    'test': '测试集', 'selected_model': '选中模型', 'trial_index': '试验索引',
    'epoch': '最佳轮次', 'hidden_size': '隐藏单元数', 'learning_rate': '学习率',
    'epochs': '训练轮数', 'batch_size': '批次大小',
    'validation_mse_scaled': '标准化验证均方误差',
    'test_return_mae': '测试收益率平均绝对误差', 'trial': '试验配置',
    'last_validation_mse_scaled': '最后一轮标准化验证均方误差',
    'training_device': '训练设备', 'visible_gpu_count': '可见GPU数量',
    'gpu_names': 'GPU名称', 'data_parallel_gpus': '双卡并行设备编号',
    'gpu_oom_fallback': '是否触发显存不足双卡重试', 'model': '模型权重',
    'scaler': '标准化参数', 'x_mean': '特征均值', 'x_scale': '特征标准差',
    'y_mean': '目标均值', 'y_scale': '目标标准差', 'weights': '差分权重',
    'config': '配置', 'sequence_length': '序列长度', 'weight_threshold': '权重截断阈值',
    'max_lags': '最大滞后数', 'minimum_train_samples': '最少训练样本数',
    'minimum_validation_samples': '最少验证样本数',
    'de_prado': '分数差分LSTM', 'log_return': '普通收益率LSTM',
    'database_random_equal_slot': '随机股票池等权基准', 'simulation': '模拟方式',
    'total_return': '累计收益率', 'annualized_return': '年化收益率',
    'max_drawdown': '最大回撤', 'annualized_volatility': '年化波动率',
    'sharpe_zero_risk_free': '零无风险利率夏普比率', 'costs': '累计交易费用',
    'order_count': '成交笔数', 'missing_forecasts': '缺失预测数量',
    'equity_curve': '净值曲线', 'trades': '成交记录', 'selection_history': '选股记录',
    'limitations': '模拟限制', 'date': '日期', 'equity': '总资产', 'cash': '现金',
    'signal_date': '信号日期', 'side': '买卖方向', 'value': '成交金额',
    'cost': '交易费用', 'weight_date': '股票池依据日期', 'candidates': '候选股票',
    'active': '持仓目标股票', 'predicted_return': '预测收益率',
    'quantity': '成交股数', 'price': '成交价格', 'sellable_before': '卖出前可卖股数',
    'terminal_shares': '期末持股', 'dividend_receivables': '应收分红',
}

TEXT_VALUES = {
    'method_migration_not_exact_replication': '方法迁移实验，非论文精确复现',
    'SSE': '上海证券交易所', 'BUY': '买入', 'SELL': '卖出',
    'de_prado': '分数差分LSTM', 'log_return': '普通收益率LSTM',
    'tested': '已检验', 'constant_series': '常数序列',
    'insufficient_after_truncation': '截断后样本不足',
    'fixed_first_difference': '固定一阶差分',
    'adj_close / close factor applied to OHLC': '复权收盘价除以原收盘价的因子应用于开高低收',
    'seeded random sample of complete-history Shanghai non-ETF stocks':
        '按固定随机种子抽取具有完整历史数据的上海非ETF股票',
    'continuous_adjusted_price_next_open_research_only': '复权价格连续数量、次日开盘成交，仅供研究',
    'database_random_survivorship_biased': '数据库随机股票池，存在幸存者偏差',
    'A seeded sample from the database replaces historical SSE50 membership; the sample has survivorship bias.':
        '使用数据库固定随机样本替代上证50历史成分股，存在幸存者偏差。',
    'Database adjusted-close ratios are applied to OHLC prices.':
        '数据库复权收盘价比例应用于开高低收价格。',
    'De Prado and first-difference branches only; no ARFIMA/ARTFIMA R estimator replication.':
        '仅包含分数差分与一阶差分分支，未复现R语言ARFIMA/ARTFIMA估计器。',
    'ADF grid 0.05, truncation 0.001, AIC lag selection are disclosed implementation settings.':
        'ADF阶数网格步长0.05、权重截断阈值0.001，按AIC选择滞后阶数。',
    'Single-layer PyTorch LSTM; CUDA GPU 0 first, GPU 0+1 after single-GPU OOM, CPU only when CUDA is unavailable.':
        '单层PyTorch LSTM，优先GPU 0，单卡显存不足后使用GPU 0和1，仅CUDA不可用时使用CPU。',
    'Hidden16/32, best validation epoch, no test-time fitting.':
        '隐藏单元16或32，按验证误差选择最佳轮次，测试期间不拟合。',
    'The test interval is ten years by default; exact split dates are recorded in parameters.':
        '默认测试区间十年，具体划分日期见实验参数。',
    'Daily equal allocation slots; no reallocation of inactive slots, 95% max exposure.':
        '每日等额配置，未启用的份额保留现金，目标最大仓位95%。',
    'Research costs cannot replace actual A-share commissions or execution rules.':
        '研究费率不能替代实际A股佣金和成交规则。',
    'Only a research simulator; actual stock execution must be validated separately.':
        '仅为研究模拟器，实际股票成交需要单独验证。',
    'No integer lots, minimum commission, T+1 or limit-up/down fill simulation.':
        '未模拟整数手、最低佣金、T+1或涨跌停成交限制。',
    'Adjusted-price continuous units, not raw-price cash/share corporate-action accounting.':
        '使用复权价格连续数量，非原价现金、股数及公司行动记账。',
    'Missing active-market prices stop the run; suspensions require a platform fill model.':
        '缺失必要行情时停止；停牌成交需要独立成交模型。',
    'Last close signal remains unexecuted; terminal holdings are marked, not liquidated.':
        '最后收盘信号不成交，期末持仓按市值计价而非全部清仓。',
    'Historical snapshot dates must be verified as available at their stated date.':
        '历史快照需核实在其标注日期确实可获取。',
}


@overload
def chinese_result(value: dict) -> dict: ...


@overload
def chinese_result(value: list) -> list: ...


@overload
def chinese_result(value: str) -> str: ...


@overload
def chinese_result(value: object) -> object: ...


def chinese_result(value):
    if isinstance(value, dict):
        return {
            FIELD_NAMES.get(key, key): item if key == 'model' else chinese_result(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [chinese_result(item) for item in value]
    if isinstance(value, str):
        match = re.fullmatch(
            r'Seeded random sample of (\d+) complete-history Shanghai non-ETF stocks '
            r'from stocks\.db; survivorship biased, not SSE50\.', value,
        )
        if match:
            return (
                f'从stocks.db按固定随机种子抽取{match[1]}只具有完整历史的上海非ETF股票；'
                '存在幸存者偏差，并非上证50。'
            )
        return TEXT_VALUES.get(value, value)
    return value
