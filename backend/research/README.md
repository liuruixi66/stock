# Research 目录导航

这个目录里有几组名称相似、但负责不同步骤的模块。先按你要做的事情找入口，不要只凭文件名判断是否重复。

## 按用途找文件

| 文件 | 负责什么 | 什么时候看它 |
| --- | --- | --- |
| [quant_research.py](quant_research.py) | 通用量化实验：差分递归预测、组合基准、SMA 均线回测 | 想改普通策略或组合回测公式 |
| [fractional_forecast.py](fractional_forecast.py) | 分数阶差分核心、特征、时间区间配置、股票池和多空模拟 | 想改分数差分数学处理、预测数据或模拟规则 |
| [fractional_lstm.py](fractional_lstm.py) | 组装 LSTM 序列、训练、验证选型、测试期预测 | 想改模型结构或训练/验证/测试流程 |
| [database_fractional.py](database_fractional.py) | 从 `stocks.db` 读取并筛选分数差分实验所需股票和行情 | 想改数据库样本、股票池或历史数据筛选 |
| [fractional_execution.py](fractional_execution.py) | 对已保存预测做有限交易约束和费用敏感性模拟 | 想检查佣金、整手、现金或执行约束的影响 |
| [fractional_results.py](fractional_results.py) | 将实验结果字段和说明翻译成中文 | 想改结果展示文案，不改模型计算 |
| [analytics.py](analytics.py) | 模拟账户成交订单的 FIFO 配对和账户绩效分析 | 想改账户订单、已实现盈亏或账户统计 |
| [advanced_metrics.py](advanced_metrics.py) | 根据通用交易记录计算回测指标；缺少日收益时会使用简化估算 | 需要兼容这个通用指标输入格式时；不要把估算回撤当成完整净值回撤 |
| [data_quality_validator.py](data_quality_validator.py) | 检查并修复 OHLCV 数据结构问题 | 想改行情数据质量检查规则 |
| [screening.py](screening.py) | 旧版数据库选股和技术指标筛选逻辑 | 只在维护旧筛选流程时使用；新研究 API 不一定走这里 |

## 最容易混淆的几组

- `quant_research.py` 与 `fractional_forecast.py`：前者放通用策略实验；后者服务于分数阶差分实验，还包含该实验的配置、股票池和模拟器。
- `fractional_forecast.py` 与 `fractional_lstm.py`：前者处理差分、特征及预测/回测数据；后者负责把这些数据送入 LSTM 训练和预测。
- `database_fractional.py` 与 `fractional_execution.py`：前者准备实验输入数据；后者对预测结果做交易费用和执行限制模拟。
- `analytics.py` 与 `advanced_metrics.py`：前者分析本项目模拟账户的订单与 FIFO 盈亏；后者是接收通用交易记录的回测指标工具。

## 常用调用链

分数差分 LSTM 主实验从 [../tools/run_fractional_research.py](../tools/run_fractional_research.py) 开始：

`run_fractional_research.py` → `database_fractional.py` → `fractional_forecast.py` / `fractional_lstm.py` → `fractional_results.py`

已保存预测的交易约束复算从 [../tools/replay_fractional_execution.py](../tools/replay_fractional_execution.py) 开始，主要使用 `fractional_execution.py` 和 `fractional_forecast.py`。

通用研究 API 的策略逻辑位于 [../stockmarket/services/research.py](../stockmarket/services/research.py)，它调用 `quant_research.py`。旧选股 API 位于 [../api/screening_views.py](../api/screening_views.py)，调用 `screening.py`。

目前保留原有文件名和导入路径，避免重命名影响 API、工具脚本和测试。新增逻辑时优先放进职责最接近的模块；确认调用方后再考虑合并或删除旧模块。