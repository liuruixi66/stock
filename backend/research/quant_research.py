from __future__ import annotations

from math import sqrt
from statistics import mean, pstdev
from typing import Iterable, Mapping, Sequence

from market_data import HistoricalBar

from strategies.etf_rotation import shrink_to_equal


class ResearchError(ValueError):
    """量化研究参数或历史数据不满足要求时抛出的业务异常。"""

    pass


def reconstruct_differenced_forecast(
    anchor: float,  # 预测起点的价格
    predicted_differences: Iterable[float], #每一步预测的价格差分
    gamma: float = 1.0, #历史累计预测影响的保留比例
) -> list[float]:
    """将一步差分预测还原为价格路径，gamma=1 为普通累加还原。"""
    if not 0 < gamma <= 1:
        raise ResearchError('gamma 必须在 0 到 1 之间，且不能等于 0')
    accumulated = 0.0
    path = []
    for difference in predicted_differences:
        accumulated = float(difference) + gamma * accumulated
        path.append(float(anchor) + accumulated)
    return path


def _forecast_error_metrics(forecasts: list[float], actuals: list[float], anchor: float) -> dict:
    errors = [forecast - actual for forecast, actual in zip(forecasts, actuals)]
    absolute_errors = [abs(error) for error in errors]
    squared_errors = [error ** 2 for error in errors]
    actual_direction = 1 if actuals[-1] > anchor else -1 if actuals[-1] < anchor else 0
    forecast_direction = 1 if forecasts[-1] > anchor else -1 if forecasts[-1] < anchor else 0
    return {
        'mae': mean(absolute_errors),
        'rmse': sqrt(mean(squared_errors)),
        'final_error': errors[-1],
        'direction_hit': forecast_direction == actual_direction,
    }


def run_leaky_integrator_experiment(
    bars: Sequence[HistoricalBar],
    train_window: int = 20,
    horizon: int = 20,
    gamma_values: Sequence[float] | None = None,
) -> dict:
    """比较普通累加与 leaky-integrator 对差分递归预测误差的影响。

    实验使用滚动窗口的一步差分均值作为最小可复现预测器：每个预测起点只使用
    起点及之前的价格差分，随后把同一个一步差分预测递归还原成多步价格路径。
    这能隔离还原算子本身的误差累积问题，不把效果归因给复杂模型训练。
    """
    # 未提供 gamma，或提供了空序列时，使用普通累加及三种衰减强度作对照。
    gamma_values = gamma_values or (1.0, 0.95, 0.9, 0.8)
    # 差分均值至少需要两个样本；预测步数必须为正。
    if train_window < 2:
        raise ResearchError('train_window 必须至少为 2')
    if horizon < 1:
        raise ResearchError('horizon 必须大于 0')
    # 至少要有训练差分和一段完整的未来路径，否则没有可比较的滚动预测起点。
    if len(bars) <= train_window + horizon:
        raise ResearchError(f'历史数据不足，至少需要 {train_window + horizon + 1} 根K线')
    # gamma=1 表示不衰减；0<gamma<1 表示逐步减弱前几步累计变化的影响。
    for gamma in gamma_values:
        if not 0 < gamma <= 1:
            raise ResearchError('gamma_values 中的每个 gamma 都必须在 0 到 1 之间，且不能等于 0')

    # 收盘价和日期沿用输入 K 线的顺序；本函数假设 bars 已按日期从旧到新排列。
    closes = [float(bar.close) for bar in bars]
    dates = [bar.date for bar in bars]
    # differences[i] = closes[i + 1] - closes[i]，共比价格点少一项。
    differences = [closes[index] - closes[index - 1] for index in range(1, len(closes))]
    # observations 保存每个 gamma 在每一个起点上的整段预测指标。
    observations = {gamma: [] for gamma in gamma_values}
    # 此结构按 gamma、再按预测步数分组，用于统计“预测第几步”的误差。
    horizon_absolute_errors = {gamma: [[] for _ in range(horizon)] for gamma in gamma_values}

    # 每个 origin 都作为一次独立的历史预测起点；循环上界保证未来有完整 horizon 根 K 线。
    for origin in range(train_window, len(closes) - horizon):
        # 只使用 origin 之前已观测到的 train_window 个差分，不包含未来实际差分。
        trailing_differences = differences[origin - train_window:origin]
        # 以近期平均日价格变化作为简单的一步预测基线。
        one_step_difference = mean(trailing_differences)
        # 基线把同一个一步变化重复用于未来每一步，实验重点是比较 gamma 的还原方式。
        predicted_differences = [one_step_difference] * horizon
        # 真实未来价格路径只用于事后评分；预测生成时不会读它。
        actual_path = closes[origin + 1:origin + horizon + 1]
        anchor = closes[origin]
        for gamma in gamma_values:
            # 用指定 gamma 将差分序列递归还原为价格路径。
            forecast_path = reconstruct_differenced_forecast(anchor, predicted_differences, gamma)
            # 将同一预测步数在不同 origin 上的绝对误差放到同一组中。
            for step, (forecast, actual) in enumerate(zip(forecast_path, actual_path)):
                horizon_absolute_errors[gamma][step].append(abs(forecast - actual))
            # 计算当前 origin 的整段 MAE、RMSE、末端误差和终点方向是否判断正确。
            metrics = _forecast_error_metrics(forecast_path, actual_path, anchor)
            observations[gamma].append({
                'origin_date': dates[origin].isoformat(),
                'forecast_end_date': dates[origin + horizon].isoformat(),
                **metrics,
            })

    gamma_metrics = []
    # 将各预测起点的结果汇总为每个 gamma 一行的总体统计。
    for gamma, items in observations.items():
        gamma_metrics.append({
            'gamma': gamma,
            # 先求每个 origin 自己的 MAE/RMSE，再对这些指标取均值。
            'mae': round(mean(item['mae'] for item in items), 6),
            'rmse': round(mean(item['rmse'] for item in items), 6),
            # 末端误差保留正负号；正值表示平均预测偏高，负值表示平均预测偏低。
            'mean_final_error': round(mean(item['final_error'] for item in items), 6),
            # direction_hit 是布尔值；True 的个数除以总起点数得到方向命中率。
            'direction_accuracy': round(
                sum(1 for item in items if item['direction_hit']) / len(items) * 100,
                4,
            ),
            # 列表位置 0 是第 1 步，位置 1 是第 2 步，以此类推。
            'horizon_mae': [round(mean(errors), 6) for errors in horizon_absolute_errors[gamma]],
        })

    # MAE 越小越优先；MAE 相同则用 RMSE 较小者打破平局。
    gamma_metrics.sort(key=lambda item: (item['mae'], item['rmse']))
    # 把 gamma=1 的普通累加作为基线；gamma_values 必须包含 1.0 才能计算比较。
    standard = next(item for item in gamma_metrics if item['gamma'] == 1.0)
    best = gamma_metrics[0]
    return {
        'experiment': 'leaky_integrator_differenced_forecast',
        'parameters': {
            'train_window': train_window,
            'horizon': horizon,
            'gamma_values': list(gamma_values),
            # 所有 gamma 使用同样的滚动起点，因此取任一组的长度作为样本数。
            'sample_count': len(next(iter(observations.values()))),
        },
        'baseline_gamma': 1.0,
        # “推荐”仅表示本次样本内 MAE 最低，并不自动代表独立样本外表现更好。
        'recommended_gamma': best['gamma'],
        # 相对 MAE 改善百分比；基线误差为零时避免除以零。
        'relative_mae_improvement': round(
            (standard['mae'] - best['mae']) / standard['mae'] * 100,
            4,
        ) if standard['mae'] else 0.0,
        'metrics_by_gamma': gamma_metrics,
    }


def _aligned_closes(
    bars_by_symbol: Mapping[str, Sequence[HistoricalBar]],
) -> tuple[list, dict[str, list[float]]]:
    """整理各标的收盘价，并只保留所有标的共同拥有的交易日。"""
    if not bars_by_symbol:
        raise ResearchError('组合标的不能为空')
    # 每个标的整理为“日期 -> 收盘价”；统一大写代码，便于组合结果中识别。
    series = {
        symbol.upper(): {bar.date: float(bar.close) for bar in bars}
        for symbol, bars in bars_by_symbol.items()
    }
    # 仅保留所有标的都存在价格的共同日期，避免缺失行情被误当作零收益。
    dates = sorted(set.intersection(*(set(values) for values in series.values())))
    if len(dates) < 2:
        raise ResearchError('组合标的没有足够的共同交易日')
    # 所有返回价格序列都按相同日期顺序排列，便于逐日计算组合收益。
    return dates, {symbol: [values[item] for item in dates] for symbol, values in series.items()}


def _portfolio_metrics(equity: list[float], daily_returns: list[float], turnover: list[float]) -> dict:
    """根据净值、日收益率和换手率计算组合回测摘要指标。"""
    if not equity:
        # 防御空输入：返回结构完整的零值指标，调用方不必处理缺失字段。
        return {'annual_return': 0.0, 'annual_volatility': 0.0, 'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0, 'max_drawdown': 0.0, 'calmar_ratio': 0.0,
                'average_turnover': 0.0}
    # 年化收益采用“平均日收益 × 252”的算术近似，不是基于净值的复合年化收益率。
    annual_return = mean(daily_returns) * 252 if daily_returns else 0.0
    # 独立日收益假设下，年化波动率 = 日波动率 × sqrt(每年交易日数)。
    annual_volatility = pstdev(daily_returns) * sqrt(252) if len(daily_returns) > 1 else 0.0
    # 当前实现只抽取负收益，再计算其自身的标准差，作为下行波动的简化估计。
    downside = [value for value in daily_returns if value < 0]
    downside_volatility = pstdev(downside) * sqrt(252) if len(downside) > 1 else 0.0
    # 夏普比率按无风险收益率为 0 计算；分母为零时返回 0。
    sharpe = annual_return / annual_volatility if annual_volatility else 0.0
    # Sortino 使用上述下行波动率作分母；没有足够负收益时返回 0。
    sortino = annual_return / downside_volatility if downside_volatility else 0.0
    peak = equity[0]
    max_drawdown = 0.0
    for value in equity:
        # peak 始终是截至当前的历史最高净值；净值/峰值 - 1 即当前回撤比例。
        peak = max(peak, value)
        max_drawdown = min(max_drawdown, value / peak - 1)
    # Calmar 用年化收益除以最大回撤绝对值；没有回撤时定义为 0。
    calmar = annual_return / abs(max_drawdown) if max_drawdown < 0 else 0.0
    return {
        'annual_return': round(annual_return * 100, 4),
        'annual_volatility': round(annual_volatility * 100, 4),
        'sharpe_ratio': round(sharpe, 4),
        'sortino_ratio': round(sortino, 4),
        'max_drawdown': round(max_drawdown * 100, 4),
        'calmar_ratio': round(calmar, 4),
        'average_turnover': round(mean(turnover), 6) if turnover else 0.0,
    }


def _entropy_regularized_weights(
    weights: dict[str, float], strength: float,
) -> dict[str, float]:
    """将基础权重向等权收缩，降低集中度和样本外漂移。"""
    # strength=0 保留原权重，strength=1 完全等权；这是线性收缩，不是熵优化求解。
    if not 0 <= strength <= 1:
        raise ResearchError('entropy_strength 必须在 0 到 1 之间')
    if not weights:
        return {}
    return shrink_to_equal(weights, strength)


def run_portfolio_baseline(
    bars_by_symbol: Mapping[str, Sequence[HistoricalBar]],
    initial_cash: float,
    strategy: str = 'equal_weight',
    lookback: int | None = None,
    transaction_cost_bps: float = 2.0,
    entropy_strength: float = 0.0,
    impact_bps: float = 0.0,
    impact_exponent: float = 1.0,
) -> dict:
    """运行规则型组合基准策略，并避免使用未来数据。

    ``equal_weight`` 使用等权重，``risk_parity`` 按历史波动率倒数分配，
    ``tsmom`` 根据过去一段时间的动量决定多空方向，``entropy_risk_parity``
    在风险平价权重上施加等权收缩。每个交易日先用前一日收盘价得到信号，
    再将当日收益、交易成本和换手率代理的冲击成本计入净值。
    """
    if initial_cash <= 0:
        raise ResearchError('初始资金必须大于0')
    if transaction_cost_bps < 0:
        raise ResearchError('交易成本不能小于0')
    if impact_bps < 0:
        raise ResearchError('冲击成本不能小于0')
    if impact_exponent <= 0:
        raise ResearchError('impact_exponent 必须大于0')
    # 策略名决定下面使用哪种目标权重规则。
    if strategy not in {'equal_weight', 'risk_parity', 'tsmom', 'entropy_risk_parity'}:
        raise ResearchError('策略必须是 equal_weight、risk_parity、entropy_risk_parity 或 tsmom')
    # 风险平价默认看 60 个收益；时间序列动量默认看 252 个收益；
    # 等权和收缩风险平价默认只需 1 个收益期即可开始。
    default_lookback = 60 if strategy == 'risk_parity' else 252 if strategy == 'tsmom' else 1
    lookback = lookback or default_lookback
    if lookback < 1:
        raise ResearchError('lookback 必须大于0')

    dates, closes = _aligned_closes(bars_by_symbol)
    symbols = list(closes)
    # 要算 lookback 长度的历史收益，至少需要 lookback+1 个共同日期。
    if len(dates) <= lookback:
        raise ResearchError(f'历史数据不足，至少需要 {lookback + 1} 个共同交易日')
    # 开始时全部资金留在现金中，尚未建立风险敞口。
    weights = {symbol: 0.0 for symbol in symbols}
    equity = [float(initial_cash)]
    daily_returns: list[float] = []
    turnover: list[float] = []
    weight_history = []
    # 1 个基点等于万分之一，将 bps 转成小数费率。
    cost_rate = transaction_cost_bps / 10000

    for index in range(1, len(dates)):
        # 计算前一共同交易日收盘到当前收盘的简单收益率。
        returns = {
            symbol: closes[symbol][index] / closes[symbol][index - 1] - 1
            for symbol in symbols
        }
        if index > lookback:
            # 保存调仓前权重，用于计算本次权重变化及换手成本。
            previous_weights = weights.copy()
            if strategy == 'equal_weight':
                # 等权：每个标的分配相同资金比例，权重总和为 1。
                weights = {symbol: 1 / len(symbols) for symbol in symbols}
            elif strategy in {'risk_parity', 'entropy_risk_parity'}:
                volatilities = {}
                for symbol in symbols:
                    # 只取截至上一日期的 lookback 个日收益，避免使用当前日之后的数据。
                    trailing = [
                        closes[symbol][item] / closes[symbol][item - 1] - 1
                        for item in range(index - lookback, index)
                    ]
                    # 标准差衡量该标的近期波动；不足两个收益时暂记为 0。
                    volatilities[symbol] = pstdev(trailing) if len(trailing) > 1 else 0.0
                # 逆波动率：波动越低，原始配置权重越高；零波动资产不参与倒数计算。
                inverse = {symbol: 1 / value for symbol, value in volatilities.items() if value > 0}
                total_inverse = sum(inverse.values())
                # 归一化逆波动率，使非零权重之和为 1；全部波动为 0 时维持零权重。
                weights = {
                    symbol: inverse.get(symbol, 0.0) / total_inverse if total_inverse else 0.0
                    for symbol in symbols
                }
                if strategy == 'entropy_risk_parity':
                    # 可选地把逆波动率权重向等权组合收缩。
                    weights = _entropy_regularized_weights(weights, entropy_strength)
            else:
                # TSMOM：比较上一日收盘价与 lookback 期前收盘价；
                # 上涨记 +1，否则（包含持平）记 -1，属于多空方向判断。
                signals = {
                    symbol: 1 if closes[symbol][index - 1] > closes[symbol][index - lookback - 1] else -1
                    for symbol in symbols
                }
                # 多空权重按绝对值归一化：权重绝对值之和为 1，但净权重和可不为 1。
                absolute = sum(abs(value) for value in signals.values())
                weights = {symbol: signals[symbol] / absolute for symbol in symbols}
            # 以半数权重绝对变化估计换手；例如从全现金转成全仓时换手为 0.5。
            current_turnover = 0.5 * sum(abs(weights[symbol] - previous_weights[symbol]) for symbol in symbols)
            turnover.append(current_turnover)
            # 记录此次调仓日期和目标权重，供结果分析使用。
            weight_history.append({'date': dates[index].isoformat(), 'weights': weights.copy()})
        else:
            # lookback 尚未满足时不建仓，组合仍保持现金状态。
            current_turnover = 0.0
            turnover.append(current_turnover)
        # 冲击成本用“费率 × 换手率的指数次幂”近似；它不是盘口成交量模型。
        impact_rate = impact_bps / 10000
        impact_cost = impact_rate * current_turnover ** impact_exponent
        # 组合收益为各标的收益按权重加总，再扣除交易费和冲击成本代理值。
        net_return = (
            sum(weights[symbol] * returns[symbol] for symbol in symbols)
            - current_turnover * cost_rate
            - impact_cost
        )
        daily_returns.append(net_return)
        # 净值按每日收益复利滚动：今天净值 = 昨天净值 × (1 + 今日净收益)。
        equity.append(equity[-1] * (1 + net_return))

    return {
        'strategy': strategy,
        'parameters': {
            'lookback': lookback,
            'transaction_cost_bps': transaction_cost_bps,
            'entropy_strength': entropy_strength,
            'impact_bps': impact_bps,
            'impact_exponent': impact_exponent,
            'symbols': symbols,
        },
        'initial_cash': round(initial_cash, 2),
        'final_equity': round(equity[-1], 2),
        # 总收益率是期末净值相对初始资金的实际累计变化百分比。
        'total_return': round((equity[-1] / initial_cash - 1) * 100, 4),
        'metrics': _portfolio_metrics(equity, daily_returns, turnover),
        # 日期序列和净值序列一一对应；第一个点是初始资金。
        'equity_curve': [
            {'date': item.isoformat(), 'equity': round(value, 2)}
            for item, value in zip(dates, equity)
        ],
        'weight_history': weight_history,
    }


def run_sma_cross(
    bars: list[HistoricalBar],
    initial_cash: float,
    short_window: int,
    long_window: int,
    commission_rate: float = 0.0003,
    slippage_bps: float = 2,
) -> dict:
    """执行单标的短长均线交叉策略并返回交易记录与净值曲线。

    金叉买入、死叉卖出；成交价分别加入滑点，成交金额再扣除佣金。
    均线未形成前只保留现金，最终未平仓头寸按最后一根K线收盘价估值。
    """
    # 短均线至少为 2 日，且长均线必须长于短均线，否则交叉信号没有意义。
    if short_window < 2 or long_window <= short_window:
        raise ResearchError('均线参数必须满足 2 <= short_window < long_window')
    # 长均线需要 long_window 个收盘价；再多要求一根，确保首个信号之后至少有回测区间。
    if len(bars) <= long_window:
        raise ResearchError(f'历史数据不足，至少需要 {long_window + 1} 根K线')
    if initial_cash <= 0:
        raise ResearchError('初始资金必须大于0')

    cash = initial_cash
    shares = 0
    # 逐根积累收盘价，后续切片计算滚动简单移动平均线。
    closes: list[float] = []
    equity_curve = []
    trades = []
    # 初始假定未持仓、信号为空；用于识别状态由空转多或由多转空的变化。
    previous_signal = False
    # 将基点换为比例，例如 2 bps = 2/10000 = 0.0002。
    slip = slippage_bps / 10000

    for bar in bars:
        closes.append(bar.close)
        if len(closes) < long_window:
            # 长均线窗口未凑齐前无法判定趋势；账户保持现金并记录净值点。
            equity_curve.append({'date': bar.date.isoformat(), 'equity': round(cash, 2)})
            continue
        # SMA 是窗口内收盘价的算术平均；最近一天位于切片末尾。
        short_ma = sum(closes[-short_window:]) / short_window
        long_ma = sum(closes[-long_window:]) / long_window
        # 短均线在长均线上方定义为多头状态；这是状态条件而非单独的交叉检测。
        signal = short_ma > long_ma
        # 只在状态改变时下单：空仓转多头买入，多头转空头卖出；
        # 持续处于同一状态时不重复买卖。
        if signal and not previous_signal and shares == 0:
            # 买入滑点使模拟成交价高于当日收盘价。
            execution_price = bar.close * (1 + slip)
            # 按现金可承受数量向下取整，并预留比例佣金，避免现金不够支付成本。
            shares = int(cash / (execution_price * (1 + commission_rate)))
            if shares:
                amount = shares * execution_price
                fee = amount * commission_rate
                cash -= amount + fee
                # 保存成交价、数量及佣金，供前端展示逐笔交易。
                trades.append({'date': bar.date.isoformat(), 'side': 'BUY', 'price': round(execution_price, 4), 'quantity': shares, 'fee': round(fee, 4)})
        elif not signal and previous_signal and shares:
            # 卖出滑点使模拟成交价低于当日收盘价，并从卖出金额扣佣金。
            execution_price = bar.close * (1 - slip)
            amount = shares * execution_price
            fee = amount * commission_rate
            cash += amount - fee
            trades.append({'date': bar.date.isoformat(), 'side': 'SELL', 'price': round(execution_price, 4), 'quantity': shares, 'fee': round(fee, 4)})
            shares = 0
        # 更新上一个交易日的状态，供下一根 K 线判断是否发生状态切换。
        previous_signal = signal
        # 持仓按当日收盘价估值，现金保持可用余额，二者相加得到当日净值。
        equity_curve.append({'date': bar.date.isoformat(), 'equity': round(cash + shares * bar.close, 2)})

    # 若回测结束仍持仓，不强制平仓；以最后一根 K 线收盘价作为未实现持仓估值。
    final_equity = cash + shares * bars[-1].close
    values = [point['equity'] for point in equity_curve]
    # 从相邻净值计算简单日收益；排除前一日净值为 0 的情况以避免除零。
    returns = [(values[index] / values[index - 1] - 1) for index in range(1, len(values)) if values[index - 1]]
    average_return = sum(returns) / len(returns) if returns else 0
    # 样本方差，分母使用 n-1；样本不足时以 1 作保护，避免除零。
    variance = sum((item - average_return) ** 2 for item in returns) / max(len(returns) - 1, 1)
    # 年化夏普：平均日收益/日波动 × sqrt(252)，并假设无风险收益率为 0。
    sharpe = average_return / sqrt(variance) * sqrt(252) if variance > 0 else 0
    peak = values[0]
    max_drawdown = 0.0
    for value in values:
        # 用历史峰值作分母，取最严重的一次峰谷跌幅。
        peak = max(peak, value)
        max_drawdown = min(max_drawdown, value / peak - 1)

    return {
        'strategy': 'sma_cross',
        'parameters': {'short_window': short_window, 'long_window': long_window},
        'initial_cash': round(initial_cash, 2),
        'final_equity': round(final_equity, 2),
        'total_return': round((final_equity / initial_cash - 1) * 100, 4),
        'max_drawdown': round(max_drawdown * 100, 4),
        'sharpe_ratio': round(sharpe, 4),
        'trade_count': len(trades),
        'trades': trades,
        'equity_curve': equity_curve,
    }