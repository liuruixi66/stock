"""实现因果约束下的分数阶差分预测研究流程。

这里采用论文中的部分方法并明确保留本项目的实验设定，不声称完整复现论文。
关键约束是训练阶段估计差分阶数、按时间切分训练/验证/测试集，并在每个预测
起点只使用当时可获得的历史数据；调用方不应把研究结果直接视作实盘信号。
"""

from dataclasses import dataclass
from datetime import date, timedelta
from math import exp, isfinite
from typing import Mapping, Sequence

import numpy as np
from numpy.typing import NDArray
import pandas as pd


class DifferencingError(ValueError):
    pass


@dataclass(frozen=True)
class ForecastConfig:
    train_start: date = date(2023, 1, 1)
    validation_start: date = date(2024, 1, 1)
    test_start: date = date(2025, 1, 1)
    test_end: date = date(2026, 10, 14)
    sequence_length: int = 20
    weight_threshold: float = 0.001
    max_lags: int = 1000
    minimum_train_samples: int = 252
    minimum_validation_samples: int = 60

    def validate(self) -> None:
        if not self.train_start < self.validation_start < self.test_start <= self.test_end:
            raise DifferencingError('Require train_start < validation_start < test_start <= test_end')
        if self.test_end >= date.today():
            raise DifferencingError('Test end must be a completed past date')
        for value in (self.sequence_length, self.max_lags,
                      self.minimum_train_samples, self.minimum_validation_samples):
            if isinstance(value, bool) or not isinstance(value, int) or value < 2:
                raise DifferencingError('Sample counts and sequence length must be integers >= 2')
        if not isfinite(self.weight_threshold) or not 0 < self.weight_threshold < 1:
            raise DifferencingError('weight_threshold must be finite and in (0, 1)')


def fractional_weights(
    order: float, threshold: float = 0.001, max_lags: int = 1000, tempering: float = 0.0,
) -> np.ndarray:
    """按论文公式递推有限长度的分数阶差分权重。

    从滞后 0 的单位权重开始递推；遇到绝对值小于阈值的权重时截断。
    若达到最大滞后仍未截断则报错，避免悄悄使用不完整的滤波器。
    """
    if (not isfinite(order) or not 0 <= order <= 1
            or not isfinite(tempering) or tempering < 0
            or not isfinite(threshold) or not 0 < threshold < 1
            or isinstance(max_lags, bool) or not isinstance(max_lags, int) or max_lags < 2):
        raise DifferencingError('Invalid differencing order, threshold, tempering or lag limit')
    weights = [1.0]
    for lag in range(1, max_lags):
        value = -weights[-1] * (order - lag + 1) / lag * exp(-tempering)
        if abs(value) < threshold:
            return np.asarray(weights, dtype=float)
        weights.append(value)
    raise DifferencingError('Differencing weights did not truncate; increase max_lags')


def fractional_difference(
    values: Sequence[float] | NDArray[np.float64], weights: np.ndarray,
) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if (values.ndim != 1 or weights.ndim != 1 or not len(weights)
            or weights[0] != 1 or not np.isfinite(values).all()
            or not np.isfinite(weights).all()):
        raise DifferencingError('Differencing requires finite vectors and lag-zero weight 1')
    result = np.full(len(values), np.nan)
    if len(values) >= len(weights):
        result[len(weights) - 1:] = np.convolve(values, weights, mode='valid')
    return result


def invert_one_step(predicted_difference: float, past_log_prices: Sequence[float] | NDArray[np.float64],
                    weights: np.ndarray) -> float:
    """用预测起点之前的对数价格逆转有限长差分滤波。

    逆变换仅读取预测时点已经可见的历史值，避免把未来价格泄漏回预测结果；
    输入历史长度不足或含非有限值时明确失败。
    """
    if (not isfinite(predicted_difference) or len(past_log_prices) < len(weights) - 1
            or len(weights) == 0 or weights[0] != 1 or not np.isfinite(weights).all()):
        raise DifferencingError('Invalid inverse prediction or insufficient history')
    if len(weights) == 1:
        return float(predicted_difference)
    history = np.asarray(past_log_prices[-(len(weights) - 1):], dtype=float)[::-1]
    if not np.isfinite(history).all():
        raise DifferencingError('Inverse history must be finite')
    return float(predicted_difference - np.dot(weights[1:], history))


def estimate_order(
    training_log_prices: Sequence[float] | NDArray[np.float64], config: ForecastConfig,
) -> dict:
    """只用训练期数据，在候选网格中选取最小的 ADF 平稳差分阶数。

    每个阶数的检验状态和统计量都会保留在返回结果中；若没有候选阶数同时满足
    5% 显著性与临界值条件，则报错，不会根据验证集或测试集补选阶数。
    """
    from statsmodels.tsa.stattools import adfuller

    config.validate()
    values = np.asarray(training_log_prices, dtype=float)
    if not np.isfinite(values).all() or len(values) < config.minimum_train_samples:
        raise DifferencingError('Insufficient or non-finite training data for ADF')
    trials = []
    for order in np.linspace(0, 1, 21):
        weights = fractional_weights(float(order), config.weight_threshold, config.max_lags)
        transformed = fractional_difference(values, weights)
        transformed = transformed[np.isfinite(transformed)]
        if len(transformed) < config.minimum_train_samples:
            trials.append({'order': float(order), 'status': 'insufficient_after_truncation'})
            continue
        if np.ptp(transformed) <= 1e-12:
            trials.append({'order': float(order), 'status': 'constant_series'})
            continue
        result = adfuller(
            transformed, regression='c', autolag='AIC',
        )
        if len(result) != 6:
            raise DifferencingError('Unexpected ADF result schema')
        statistic, pvalue = float(result[0]), float(result[1])
        observations, critical = result[3], result[4]
        if not isinstance(observations, (int, np.integer)) or not isinstance(critical, dict):
            raise DifferencingError('Unexpected ADF observations or critical values')
        trial = {
            'order': float(order), 'status': 'tested', 'statistic': float(statistic),
            'pvalue': float(pvalue), 'observations': int(observations),
            'critical_5pct': float(critical['5%']), 'lags': len(weights),
        }
        trials.append(trial)
        if pvalue < 0.05 and statistic < critical['5%']:
            return {'order': float(order), 'trials': trials}
    raise DifferencingError('No order in [0, 1] passed training-only ADF; do not invent an order')


def forecast_features(closes: pd.Series, transformed: np.ndarray) -> pd.DataFrame:
    """生成价格预测特征：均线、RSI、布林带和 MACD。

    参数窗口分别为 SMA(5/10/20)、RSI(9/14/21)、布林带(10, 2 倍标准差)
    和 MACD(12/26/9)；同时保留分数阶差分序列作为输入特征。
    """
    if not np.isfinite(closes).all() or (closes <= 0).any():
        raise DifferencingError('Features require finite positive adjusted closes')
    frame = pd.DataFrame({'differenced': transformed}, index=closes.index)
    for window in (5, 10, 20):
        frame[f'sma_{window}'] = closes.rolling(window).mean()
    change = closes.diff()
    for window in (9, 14, 21):
        gain = change.clip(lower=0).rolling(window).mean()
        loss = (-change.clip(upper=0)).rolling(window).mean()
        denominator = gain + loss
        frame[f'rsi_{window}'] = (100 * gain / denominator).where(
            denominator > 0, 50.0,
        ).where(denominator.notna())
    average = closes.rolling(10).mean()
    deviation = closes.rolling(10).std(ddof=0)
    frame['bollinger_upper'] = average + 2 * deviation
    frame['bollinger_lower'] = average - 2 * deviation
    macd = closes.ewm(span=12, adjust=False).mean() - closes.ewm(span=26, adjust=False).mean()
    frame['macd'] = macd
    frame['macd_signal'] = macd.ewm(span=9, adjust=False).mean()
    return frame


class HistoricalTopThirty:
    """按信号日前最近一份完整的上证 50 权重快照确定历史前 30 成分股。

    快照必须包含 50 个有效成分且权重合计符合百分比或小数表示；查询时只接受
    严格早于信号日、并且没有超过允许最大时效的快照，避免使用当日收盘后才
    发布的数据产生前视偏差。
    """

    def __init__(self, frame: pd.DataFrame, maximum_age_days: int = 35):
        required = {'date', 'instrument', 'member_code', 'weight'}
        if not required <= set(frame.columns):
            raise DifferencingError(f'Historical weights need columns {sorted(required)}')
        if maximum_age_days < 1:
            raise DifferencingError('maximum_age_days must be positive')
        frame = frame.copy()
        frame['date'] = pd.to_datetime(frame['date'], errors='raise').dt.date
        if frame['date'].isna().any():
            raise DifferencingError('Missing weight snapshot dates')
        if set(frame['instrument']) != {'000016.SHI'}:
            raise DifferencingError('Expected only historical SSE50 weights: 000016.SHI')
        if frame.duplicated(['date', 'member_code']).any():
            raise DifferencingError('Duplicate historical constituent weights')
        if not frame['member_code'].str.fullmatch(r'\d{6}\.SH').all():
            raise DifferencingError('Invalid Shanghai constituent code')
        frame['weight'] = pd.to_numeric(frame['weight'], errors='raise')
        if not np.isfinite(frame['weight']).all() or (frame['weight'] <= 0).any():
            raise DifferencingError('Historical weights must be finite and positive')
        self.snapshots = {}
        for day, rows in frame.groupby('date'):
            if len(rows) != 50:
                raise DifferencingError(f'Incomplete SSE50 snapshot on {day}: expected 50 members')
            total = float(rows['weight'].sum())
            if not (abs(total - 100) < 0.1 or abs(total - 1) < 0.001):
                raise DifferencingError(f'Historical snapshot weights do not sum to 100% on {day}')
            selected = rows.sort_values(['weight', 'member_code'], ascending=[False, True]).head(30)
            self.snapshots[day] = tuple(selected['member_code'])
        self.days = sorted(self.snapshots)
        self.maximum_age_days = maximum_age_days
        if not self.days:
            raise DifferencingError('Historical weight snapshots are empty')

    def at(self, signal_day: date) -> tuple[date, tuple[str, ...]]:
        from bisect import bisect_left

        position = bisect_left(self.days, signal_day) - 1
        if position < 0:
            raise DifferencingError(f'No weight snapshot strictly before {signal_day}')
        day = self.days[position]
        if (signal_day - day).days > self.maximum_age_days:
            raise DifferencingError(f'Stale historical weight snapshot {day} for {signal_day}')
        return day, self.snapshots[day]

    def members_between(self, start: date, end: date) -> tuple[str, ...]:
        if start > end:
            raise DifferencingError('Universe start must not exceed end')
        members = set(self.at(start)[1])
        for snapshot_day in self.days:
            first_usable = snapshot_day + timedelta(days=1)
            if start <= first_usable <= end:
                members.update(self.at(first_usable)[1])
        return tuple(sorted(members))


class FixedRandomThirty:
    """将当前成分股随机抽样后回投历史的探索性样本。

    该方法存在明显幸存者偏差，只能用于实验对照，不能用于证明历史策略可交易。
    类会校验清单中的种子和抽样结果，确保同一清单可复现。
    """

    def __init__(self, manifest: dict):
        if (manifest.get('mode') != 'current_sse50_random30'
                or manifest.get('index') != '000016.SHI'
                or manifest.get('survivorship_bias') is not True):
            raise DifferencingError('Invalid fixed random universe provenance')
        self.selection_date = date.fromisoformat(manifest['selection_date'])
        members = manifest['members']
        selected = manifest['selected']
        import random
        import re

        if (len(members) != 50 or len(set(members)) != 50
                or any(not isinstance(code, str) or not re.fullmatch(r'\d{6}\.SH', code)
                       for code in members)
                or not isinstance(manifest['seed'], int)):
            raise DifferencingError('Random universe requires 50 unique Shanghai constituents and seed')
        expected = sorted(random.Random(manifest['seed']).sample(sorted(members), 30))
        if selected != expected:
            raise DifferencingError('Selected stocks do not match the saved random seed')
        self.selected = tuple(selected)

    def at(self, signal_day: date) -> tuple[date, tuple[str, ...]]:
        return self.selection_date, self.selected

    def members_between(self, start: date, end: date) -> tuple[str, ...]:
        if start > end:
            raise DifferencingError('Universe start must not exceed end')
        return self.selected


class DatabaseRandomUniverse:
    """将数据库筛选出的随机股票样本固定用于测试期的可复现实验宇宙。

    成分不会随日期变化，因此该样本适合固定条件的算法比较；它不等同于按历史
    成分变化重建的真实指数，也不能消除数据库样本构造产生的幸存者偏差。
    """

    def __init__(
        self, selected: Sequence[str], selection_date: date, seed: int, eligible_count: int,
    ):
        import re

        if (not selected or len(selected) != len(set(selected))
                or any(not isinstance(code, str) or not re.fullmatch(r'\d{6}\.SH', code)
                       for code in selected)
                or isinstance(seed, bool) or not isinstance(seed, int) or seed < 0
                or eligible_count < len(selected)):
            raise DifferencingError('Invalid database random-universe selection')
        self.selected = tuple(sorted(selected))
        self.selection_date = selection_date
        self.seed = seed
        self.eligible_count = eligible_count

    def at(self, signal_day: date) -> tuple[date, tuple[str, ...]]:
        return self.selection_date, self.selected

    def members_between(self, start: date, end: date) -> tuple[str, ...]:
        if start > end:
            raise DifferencingError('Universe start must not exceed end')
        return self.selected


def long_only_signal(predicted_return: float, previous: bool, threshold: float) -> bool:
    """根据预测收益和成本阈值产生多头/空仓状态。

    预测收益高于正阈值时持有，低于负阈值时退出；落在交易成本带内时沿用
    上一期状态，避免因微小预测波动频繁换手。
    """
    if (not isfinite(predicted_return) or not isfinite(threshold)
            or not 0 < threshold < 1):
        raise DifferencingError('Invalid forecast return or cost threshold')
    if predicted_return > threshold:
        return True
    if predicted_return < -threshold:
        return False
    return previous


def validate_prices(frame: pd.DataFrame) -> pd.DataFrame:
    required = {'date', 'instrument', 'open', 'high', 'low', 'close', 'volume'}
    if not required <= set(frame.columns) or frame.empty:
        raise DifferencingError(f'Prices need nonempty adjusted OHLCV columns {sorted(required)}')
    frame = frame.copy()
    frame['date'] = pd.to_datetime(frame['date'], errors='raise').dt.date
    if frame['date'].isna().any() or frame.duplicated(['date', 'instrument']).any():
        raise DifferencingError('Missing or duplicate price dates')
    if not frame['instrument'].str.fullmatch(r'\d{6}\.SH').all():
        raise DifferencingError('Expected Shanghai stock instruments')
    for name in ('open', 'high', 'low', 'close', 'volume'):
        frame[name] = pd.to_numeric(frame[name], errors='raise')
    if (not np.isfinite(frame[list(required - {'date', 'instrument'})]).all().all()
            or (frame[['open', 'high', 'low', 'close']] <= 0).any().any()
            or (frame['volume'] < 0).any()
            or (frame['low'] > frame[['open', 'close']].min(axis=1)).any()
            or (frame['high'] < frame[['open', 'close']].max(axis=1)).any()):
        raise DifferencingError('Invalid adjusted OHLCV')
    return frame.sort_values(['instrument', 'date']).reset_index(drop=True)


def simulate_long_only(
    prices: pd.DataFrame, predictions: Mapping[tuple[date, str], float],
    universe: HistoricalTopThirty | FixedRandomThirty | DatabaseRandomUniverse,
    start: date, end: date,
    initial_capital: float = 100000, exposure: float = 0.95,
    buy_cost: float = 0.0005, sell_cost: float = 0.001,
    signal_threshold: float = 0.002, benchmark: bool = False,
) -> dict:
    """构造连续复权价格研究组合，不是 A 股真实成交模拟器。

    收盘后产生的信号最早只能在输入数据中的下一交易日开盘执行；组合最多使用
    30 个固定配置槽位，未启用槽位保留为现金。持仓行情缺失或不可交易时停止实验，
    不伪造成交价。该模型没有模拟整数手、T+1、涨跌停和实际券商撮合。
    """
    prices = validate_prices(prices)
    if (not start <= end or not isfinite(initial_capital) or initial_capital <= 0
            or not isfinite(exposure) or not 0 < exposure <= 1
            or any(not isfinite(c) or not 0 <= c < 1 for c in (buy_cost, sell_cost))):
        raise DifferencingError('Invalid simulation dates, capital, exposure or costs')
    if not isfinite(signal_threshold) or not 0 < signal_threshold < 1:
        raise DifferencingError('Invalid signal threshold')
    frame = prices[prices['date'] <= end]
    days = sorted(day for day in frame['date'].unique() if start <= day <= end)
    if len(days) < 2:
        raise DifferencingError('At least two test trading days are required')
    database_universe = isinstance(universe, DatabaseRandomUniverse)
    daily = {
        day: rows.set_index('instrument').to_dict('index')
        for day, rows in frame.groupby('date')
    }
    cash = initial_capital
    units: dict[str, float] = {}
    last_prices: dict[str, float] = {}
    pending = None
    curve, trades, selections = [], [], []
    fees = 0.0
    missing_predictions = 0
    for day in days:
        rows = daily[day]
        last_prices.update({
            symbol: item['close'] for symbol, item in rows.items()
        })
        for symbol in units:
            if symbol not in rows or rows[symbol]['volume'] <= 0:
                if not database_universe:
                    raise DifferencingError(f'No tradeable held price {symbol} on {day}; cannot simulate')
        if pending is not None:
            origin, targets = pending
            equity_open = cash + sum(quantity * rows[symbol]['open']
                                     if symbol in rows and rows[symbol]['volume'] > 0
                                     else quantity * last_prices[symbol]
                                     for symbol, quantity in units.items())
            for symbol in sorted(units):
                if symbol not in rows or rows[symbol]['volume'] <= 0:
                    continue
                target = targets.get(symbol, 0.0) * equity_open
                value = units[symbol] * rows[symbol]['open']
                reduction = max(0.0, value - target)
                if reduction > 1e-8:
                    units[symbol] -= reduction / rows[symbol]['open']
                    cost = reduction * sell_cost
                    cash += reduction - cost
                    fees += cost
                    trades.append({'signal_date': origin.isoformat(), 'date': day.isoformat(),
                                   'instrument': symbol, 'side': 'SELL', 'value': reduction,
                                   'cost': cost})
            units = {symbol: quantity for symbol, quantity in units.items() if quantity > 1e-10}
            for symbol, weight in sorted(targets.items()):
                if weight <= 0:
                    continue
                if symbol not in rows or rows[symbol]['volume'] <= 0:
                    if database_universe:
                        continue
                    raise DifferencingError(f'No tradeable target price {symbol} on {day}')
                value = units.get(symbol, 0.0) * rows[symbol]['open']
                increase = min(max(0.0, weight * equity_open - value),
                               max(0.0, cash) / (1 + buy_cost))
                if increase > 1e-8:
                    units[symbol] = units.get(symbol, 0.0) + increase / rows[symbol]['open']
                    cost = increase * buy_cost
                    cash -= increase + cost
                    fees += cost
                    trades.append({'signal_date': origin.isoformat(), 'date': day.isoformat(),
                                   'instrument': symbol, 'side': 'BUY', 'value': increase,
                                   'cost': cost})
        equity = cash + sum(
            quantity * rows[symbol]['close'] if symbol in rows else quantity * last_prices[symbol]
            for symbol, quantity in units.items()
        )
        snapshot_day, candidates = universe.at(day)
        targets = {}
        for symbol in candidates:
            if symbol not in rows:
                if not database_universe:
                    raise DifferencingError(
                        f'No signal-day data for historical top30 member {symbol} on {day}',
                    )
                missing_predictions += 1
                active = symbol in units
            elif benchmark:
                active = True
            elif day == days[-1]:
                active = symbol in units
            elif (day, symbol) not in predictions:
                missing_predictions += 1
                active = symbol in units
            else:
                active = long_only_signal(predictions[(day, symbol)], symbol in units, signal_threshold)
            if active:
                targets[symbol] = exposure / len(candidates)
        pending = (day, targets)
        selections.append({'date': day.isoformat(), 'weight_date': snapshot_day.isoformat(),
                           'candidates': list(candidates), 'active': list(targets)})
        curve.append({'date': day.isoformat(), 'equity': equity, 'cash': cash})
    equity = np.asarray([initial_capital] + [point['equity'] for point in curve])
    returns = equity[1:] / equity[:-1] - 1
    running = np.maximum.accumulate(equity)
    volatility = float(np.std(returns) * np.sqrt(252))
    return {
        'simulation': 'continuous_adjusted_price_next_open_research_only',
        'universe_mode': (
            'database_random_survivorship_biased' if database_universe else
            'current_sse50_random30_survivorship_biased'
            if isinstance(universe, FixedRandomThirty) else 'historical_weight_top30'
        ),
        'total_return': float(equity[-1] / initial_capital - 1),
        'annualized_return': float((equity[-1] / initial_capital) ** (252 / len(days)) - 1),
        'max_drawdown': float(np.min(equity / running - 1)),
        'annualized_volatility': volatility,
        'sharpe_zero_risk_free': float(np.mean(returns) * 252 / volatility) if volatility > 0 else None,
        'costs': fees, 'order_count': len(trades), 'missing_forecasts': missing_predictions,
        'equity_curve': curve, 'trades': trades, 'selection_history': selections,
        'limitations': [
            'No integer lots, minimum commission, T+1 or limit-up/down fill simulation.',
            'Adjusted-price continuous units, not raw-price cash/share corporate-action accounting.',
            'Missing active-market prices stop the run; suspensions require a platform fill model.',
            'Last close signal remains unexecuted; terminal holdings are marked, not liquidated.',
            'Historical snapshot dates must be verified as available at their stated date.',
        ],
    }
