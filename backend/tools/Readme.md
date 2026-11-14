
# Tools 目录说明

本目录包含命令行工具、研究脚本及辅助文档。以下说明根据当前代码整理；
功能相近不代表可以直接删除或合并。

## 按用途导航

- **训练与搜索**：[run_fractional_research.py](run_fractional_research.py)、
  [tune_fractional_lstm.py](tune_fractional_lstm.py)。
- **实验结果与图表**：[list_research_runs.py](list_research_runs.py)、
  [compare_fractional_experiments.py](compare_fractional_experiments.py)、
  [plot_fractional_research.py](plot_fractional_research.py)。
- **数据审计与证据**：[audit_fractional_prices.py](audit_fractional_prices.py)、
  [audit_fractional_execution_readiness.py](audit_fractional_execution_readiness.py)、
  [audit_portfolio_history.py](audit_portfolio_history.py)、
  [verify_fractional_sources.py](verify_fractional_sources.py)、
  [collect_fractional_announcement.py](collect_fractional_announcement.py)。
- **交易与选股**：[replay_fractional_execution.py](replay_fractional_execution.py)、
  [trade_analysis.py](trade_analysis.py)、[screen_stocks.py](screen_stocks.py)、
  [select_industry_leaders.py](select_industry_leaders.py)。
- **辅助工具**：[time_range_validator.py](time_range_validator.py)、
  [api_documentation.py](api_documentation.py)。

## 调用方式

在 `backend` 目录下，可以通过模块名运行支持命令行参数的工具，例如：

```powershell
python -m tools.list_research_runs
python -m tools.plot_fractional_research --help
```

也可以在 Python 代码中直接导入工具文件中的函数，例如：

```python
from tools.plot_fractional_research import generate
from tools.compare_fractional_experiments import compare
```

导入后仍需按各函数的参数要求调用；上述示例不会自动执行绘图或比较。
运行时需要让 `backend` 目录位于 Python 的模块搜索路径中。
[__init__.py](__init__.py) 可以为空；若希望使用 `from tools import generate`，
则需要在其中显式导出该函数。部分脚本只有解析命令行参数的 `main()`，
不应将其当作接受普通业务参数的函数。

## 文件清单

| 文件 | 主要职责 | 与其他工具的关系 |
| --- | --- | --- |
| [api_documentation.py](api_documentation.py) | 提供回测 API 文档和调用示例。 | 文档用途，不是训练工具。 |
| [audit_fractional_execution_readiness.py](audit_fractional_execution_readiness.py) | 检查停牌、涨跌停、分红等执行数据的覆盖情况。 | 与其他审计工具有数据检查重叠，但目的不同。 |
| [audit_fractional_prices.py](audit_fractional_prices.py) | 检查实验行情、复权口径和数据指纹。 | 与交易回放工具的部分行情读取和复权流程相似。 |
| [audit_portfolio_history.py](audit_portfolio_history.py) | 审计冻结行业股票池的历史行情。 | 使用的股票池和审计范围与逐股实验不同。 |
| [collect_fractional_announcement.py](collect_fractional_announcement.py) | 收集并解析分红公告证据。 | 与外部数据核验相关，但数据来源和用途不同。 |
| [compare_fractional_experiments.py](compare_fractional_experiments.py) | 汇总比较多个已完成实验。 | 不训练模型，也不重新画图。 |
| [list_research_runs.py](list_research_runs.py) | 列出实验编号、状态和结果位置。 | 独立的实验记录查询入口。 |
| [plot_fractional_research.py](plot_fractional_research.py) | 读取已保存结果，绘制训练、预测和回测图表。 | 文件内存在可整理的重复导入。 |
| [replay_fractional_execution.py](replay_fractional_execution.py) | 使用已保存预测，重新模拟交易约束与费用。 | 与价格审计的部分行情读取流程相似。 |
| [run_fractional_research.py](run_fractional_research.py) | 运行逐股 LSTM 搜索、训练、预测和研究回测。 | `tuned` 模式下也会调用参数搜索。 |
| [screen_stocks.py](screen_stocks.py) | 旧版指标条件筛股命令。 | 和行业选股都涉及选股，但规则不同。 |
| [select_industry_leaders.py](select_industry_leaders.py) | 按行业和市值生成冻结股票池。 | 与旧版指标筛股不是相同功能。 |
| [time_range_validator.py](time_range_validator.py) | 排查缓存、API 和前端日期范围。 | 与交易分析都读取缓存，但检查内容不同。 |
| [trade_analysis.py](trade_analysis.py) | 分析交易记录、现金流和等权调仓。 | 与日期校验不是重复功能。 |
| [tune_fractional_lstm.py](tune_fractional_lstm.py) | 单独运行 LSTM 参数搜索。 | 与完整研究入口的搜索阶段共用搜索实现。 |
| [verify_fractional_sources.py](verify_fractional_sources.py) | 使用外部数据核对行情和公司行动。 | 与本地审计互补，不是完全重复。 |
| [__init__.py](__init__.py) | Python 包标识文件。 | 空文件，无业务逻辑。 |
| `__pycache__` | Python 运行生成的字节码缓存。 | 不是源码工具。 |

## 主要重叠

- **参数搜索入口**：`tune_fractional_lstm.py` 可以单独启动搜索；
  `run_fractional_research.py` 在 `tuned` 模式下也调用同一套搜索逻辑。
  这是两个入口共用实现，不是两份独立的搜索算法。
- **行情读取流程**：价格审计与交易回放都会查询行情、处理复权并核对指纹。
  两者的日期范围和检查要求不同；如需提取公共步骤，应先核对输入输出和校验口径。
- **绘图依赖导入**：`plot_fractional_research.py` 在文件顶部及类内部重复导入
  Matplotlib、Pandas、Seaborn，并重复设置 `Agg` 后端，可考虑统一导入方式。

审计、选股和回测工具可能处理相同数据，但业务规则不同；不应仅因名称或数据来源
相似就删除或合并。重构前还应检查调用方并验证原有行为。
