# stock-clone 论文驱动实验设计与最新论文方向总结

生成日期：2026-09-22

本方案基于 `stock_clone_paper_analysis.md` 的 9 篇初始论文判断，并补充 `zotero-paper-lab/data/arxiv_fetch/seen_ids.json` 中新增的 12 篇 arXiv 条目。当前 `data/arxiv_fetch/pdfs/` 缓存为空，说明 PDF 大概率已导入 Zotero storage；新增论文判断主要依据 arXiv API 返回的标题、分类和摘要。

## 一句话结论

最值得在 `stock-clone` 中推进的主线是：**订单流状态识别 + 熵正则组合权重 + 动态冲击成本 + 执行不确定性敏感性分析**。前三项已经能接入现有组合回测框架，第四项来自最新论文，适合作为可发表的实证增强点。

如果目标是既实用又有论文潜力，建议选题为：

> 面向零售级行情数据的订单流状态过滤、稳健组合配置与执行不确定性联合回测框架

核心贡献不是声称收益率最高，而是证明：在数据字段受限、订单簿不完整或只具备 L1/L2 聚合数据时，如何做无未来函数、成本敏感、执行假设透明的策略评估。

## stock-clone 当前可承接能力

项目已有几个关键落点：

- `backend/market_data/providers.py` 已统一 `HistoricalBar`、`MinuteBar` 和行情 provider，可作为数据字段扩展入口。
- `backend/stockmarket/quant_research.py` 已有 `run_portfolio_baseline`，支持 `equal_weight`、`risk_parity`、`entropy_risk_parity`、`tsmom`，并已有 `transaction_cost_bps`、`impact_bps`、`impact_exponent` 参数。
- `backend/stockmarket/trading_views.py` 已有 `/research/portfolio-backtest/`，能直接跑多标的组合回测。
- `frontend/src/api/stock.ts` 已有 `runPortfolioBacktest` API 封装，但 `frontend/src/views/ResearchTerminal.vue` 当前主要展示单标的均线实验，组合实验还没有完整 UI。

这意味着第一阶段不用先做大模型或复杂训练，应该先把研究协议、分组统计、成本归因和前端展示补齐。

## 推荐实验主线

### 实验 A：订单流状态过滤是否改善策略质量

对应论文：2609.07989 `Regimes in the Order Flow`

目标：判断在不同订单流或成交量状态下，现有均线/动量/风险平价策略的收益、回撤、换手和成本后收益是否显著不同。

第一版可用字段：

- 日线：收益率、成交量变化、振幅、实体比例、量价背离、滚动波动率。
- 分钟线：分钟收益、分钟成交量、波动聚集、成交量冲击、日内趋势强度。
- 若无主动买卖方向、盘口不平衡、bid/ask spread，则状态标为 `unavailable`，不以 0 伪造。

建议状态标签：

- `calm_liquid`：低波动、正常成交量。
- `trend_accumulation`：价格同向移动且成交量放大。
- `stress_liquidity`：高波动、高振幅、成交量异常。
- `thin_noise`：低成交量、高噪声或数据不足。

验证方式：

- 基线：原策略不加状态过滤。
- 实验组 1：只在 `trend_accumulation` 做多，`stress_liquidity` 降权。
- 实验组 2：按状态动态调整仓位上限和换手阈值。
- 实验组 3：状态只用于风险分层，不改变交易信号，观察统计差异。

主要指标：年化收益、最大回撤、Sharpe、Sortino、换手率、成本后收益、状态内胜率、状态切换后的 1/5/20 日收益分布。

论文价值：如果能证明简单可解释状态标签在多个市场、多时间窗口中稳定改善成本后表现，比单纯堆复杂模型更容易写成可复现实证论文。

### 实验 B：熵正则组合权重是否降低样本外漂移

对应论文：2609.03552 `An Entropic Factor Model for Robust Portfolio Replication`

目标：比较等权、风险平价、动量组合、熵正则风险平价在样本外的集中度、回撤和稳定性。

当前代码已有 `entropy_risk_parity` 和 `entropy_strength`，第一阶段建议直接参数扫描：

- `entropy_strength`: 0.0, 0.1, 0.25, 0.5, 0.75, 1.0
- `lookback`: 20, 60, 120, 252
- 股票池：A 股核心资产、美股科技/防御混合、加密主流币，分别测试。

需要新增统计：

- 权重 Herfindahl 指数：衡量集中度。
- 单资产最大权重。
- 权重漂移率。
- 滚动样本外收益和回撤。

论文价值：可作为“约束越强不一定收益越高，但能降低组合不稳定性”的稳健配置实验。

### 实验 C：成交成本与价格冲击敏感性

对应论文：2609.04712 `Convex Modeling of Price Cross-Impact over Time`

目标：证明固定佣金不足以评估策略容量，加入凸冲击成本后，策略排序会变化。

当前代码已有：

- `transaction_cost_bps`
- `impact_bps`
- `impact_exponent`

建议扩展为三层成本：

- 固定成本：佣金、滑点。
- 自冲击成本：本组合换手率越高，成交越贵。
- 交叉冲击代理：同日高相关资产同时调仓时，额外放大成本。

第一版交叉冲击代理：

```text
cross_impact = impact_bps * portfolio_turnover^impact_exponent * avg_pairwise_corr_positive
```

其中相关性只用调仓日前的滚动收益率计算，避免未来函数。

论文价值：适合写成“零售回测系统中交易成本建模会如何改变策略选择”的工程实证论文。

### 实验 D：执行不确定性与 FIFO 敏感性

对应最新论文：2609.13597 `Same Book, Different Fills`

目标：当只有聚合订单簿或不完整盘口数据时，不再报告单一成交结果，而是报告成交区间。

这篇论文的关键启发是：同一条聚合订单簿路径，在不同撤单队列假设下，会产生不同的被动成交率和 implementation shortfall。

stock-clone 第一版可不需要真实逐笔订单：

- 对模拟盘限价单和被动成交回测增加三种成交假设：`front_cancel`、`random_cancel`、`back_cancel`。
- 输出 fill rate 区间、成本区间、最终净值区间。
- 对高流动性和低流动性标的分组比较。

论文价值很强：现有个人量化系统常给一个确定回测结果，但真实被动成交高度依赖队列假设。把“点估计回测”升级为“执行假设区间回测”，实用且有研究新意。

### 实验 E：模型无关被动执行基准

对应最新论文：2609.18019 `Model-Free Passive Execution via Order-Level Shadowing`

目标：为未来订单簿策略建立一个不依赖预测模型的被动执行基准。

受数据限制，stock-clone 可先做简化版：

- 若有分钟成交量：用成交量突增作为“第三方流动性出现”的代理。
- 若有 L2 数据：跟随新增挂单价位生成被动订单。
- 对比 aggressive POV、TWAP、简化 Shadow-POV。

第一阶段不要接实盘，只做离线回放。

论文价值：如果后续接入币安或其他加密交易所 order book websocket，这条线可以形成完整执行算法论文。

## 新增 12 篇论文应用判断

| arXiv ID | 方向 | 对 stock-clone 的价值 | 建议 |
| --- | --- | --- | --- |
| 2609.13402 | 动态隐含波动率曲面 diffusion 与对冲 | 需要期权 IVS 数据；当前股票/组合回测暂不具备 | 暂缓，未来期权模块可用 |
| 2609.13597 | 聚合订单簿下 FIFO 执行的部分识别 | 很适合把回测成交从点估计改为区间估计 | 高优先级，加入执行敏感性 |
| 2609.18019 | 模型无关被动执行 Shadow-PPOV | 适合作为被动限价单基准，但需要更细订单簿 | 中高优先级，先做简化回放 |
| 2609.18949 | 稳定币脱锚风险 Agentic Benchmark | 适合 CRYPTO 风控和稳定币 watchlist | 中优先级，可做风险监控实验 |
| 2609.18975 | Solana memecoin 生命周期分群 | 过于特定，除非项目扩展链上数据 | 暂缓 |
| 2609.20192 | 订单簿市场羊群、杠杆、流动性危机 | 可启发风险状态标签，但需要仿真市场 | 中优先级，作为压力场景生成 |
| 2609.20293 | GLE 解耦波动记忆和缩放 | 更偏随机波动理论，短期工程价值低 | 暂缓 |
| 2609.21291 | OU 随机波动期权模拟 | 期权定价方向，当前不优先 | 暂缓 |
| 2609.21301 | operator splitting 随机波动模拟 | 期权数值方法，当前不优先 | 暂缓 |
| 2609.22893 | 多股票隐含波动率曲面 diffusion | 需要期权 IVS 数据，未来期权风险模块可用 | 暂缓 |
| 2609.23378 | Leaky-integrator 递归差分预测修正 | 很适合任何一阶差分预测模型，接入成本低 | 中高优先级，做预测稳定性实验 |
| 2609.23598 | 日内电力市场买卖轨迹预测 | 市场不同，但 buy-sell 轨迹建模思想可借鉴 | 暂缓或作为订单流建模参考 |

## 最适合发论文的 3 个选题

### 选题 1：执行假设透明的个人量化回测框架

研究问题：当只有日线、分钟线、L1 或聚合 L2 数据时，策略回测结果对成交假设有多敏感？

创新点：

- 将 FIFO 不确定性、成本冲击和状态过滤放进统一回测协议。
- 输出收益区间而非单一收益点。
- 面向普通可获得数据，比高频专有数据更容易复现。

最小实验：A 股/美股/加密三类市场，各选 10 到 20 个高低流动性标的；比较单点成交、悲观成交、乐观成交、随机成交的净值差异。

### 选题 2：订单流状态条件下的稳健组合配置

研究问题：订单流状态能否改善熵正则组合的样本外表现？

创新点：

- 不追求黑盒预测，使用可解释状态标签。
- 把组合权重稳定性和交易成本同时纳入目标。
- 对不同市场状态给出策略适用边界。

最小实验：等权、风险平价、熵风险平价、状态过滤熵风险平价四组对比；做滚动样本外和成本压力测试。

### 选题 3：递归差分预测在金融时间序列中的误差泄漏修正

对应论文：2609.23378

研究问题：对收益/价格差分做一步预测再递归还原时，leaky integrator 是否能稳定长期预测和策略信号？

创新点：

- 方法简单，训练后处理即可。
- 可比较 `gamma=1.0` 累加还原与 `gamma<1` 泄漏还原。
- 能和交易结果挂钩：预测误差下降是否真的改善回测，而不是只改善 MAE。

最小实验：用简单 AR、线性模型、LightGBM 或现有指标信号预测未来 1 日差分，滚动生成 5/20/60 日路径，比较误差和策略表现。

第一版已落地到 `stock-clone`：

- 后端函数：`run_leaky_integrator_experiment`，位于 `backend/stockmarket/quant_research.py`。
- 还原算子：`reconstruct_differenced_forecast(anchor, predicted_differences, gamma)`，其中 `gamma=1.0` 是普通累加还原，`gamma<1` 是 leaky-integrator 还原。
- API 入口：`POST /api/research/leaky-forecast/`。
- 前端 API 封装：`researchApi.runLeakyForecastExperiment`。
- 当前预测器：滚动训练窗口内的一步差分均值。它不是最终模型，而是为了隔离“递归差分还原会不会累积误差”这个研究问题。

第一版请求示例：

```json
{
	"market": "US",
	"symbol": "AAPL",
	"start_date": "2024-01-01",
	"end_date": "2026-09-22",
	"train_window": 20,
	"horizon": 20,
	"gamma_values": [1.0, 0.95, 0.9, 0.8]
}
```

第一版输出重点：

- `recommended_gamma`：按平均 MAE/RMSE 排序后的最佳 gamma。
- `relative_mae_improvement`：相对普通累加还原的 MAE 改善幅度。
- `metrics_by_gamma`：每个 gamma 的 MAE、RMSE、最终误差、方向准确率和逐 horizon MAE。

下一步论文实验要把预测器从“差分均值”升级为多组模型：naive、AR/线性回归、技术指标回归、LightGBM 或其它可解释模型。关键评价不是只看 MAE，而是检验误差改善是否能稳定转化为更少错误信号、更低换手和更好的样本外成本后收益。

## 建议实施顺序

1. 补组合实验前端：暴露 `runPortfolioBacktest` 参数，包括策略、股票池、lookback、熵强度、固定成本、冲击成本。
2. 在 `quant_research.py` 增加研究输出：状态分组统计、成本归因、权重集中度、滚动样本外分段结果。
3. 新增订单流状态标签函数：先基于日线/分钟线可得字段，不可用字段返回 `unavailable`。
4. 新增执行敏感性模块：为限价/被动成交输出乐观、随机、悲观三种成交结果。
5. 建立实验配置 JSON：固定股票池、时间边界、成本参数和样本外切分，保证结果可复现。
6. 前端展示从“收益曲线”升级为“研究报告”：状态分布、成本前后收益、成交假设区间、样本外表现。

## 第一轮实验配置建议

市场与股票池：

- A 股：`000001, 600519, 601318, 600036, 000333, 300750, 600900, 601899, 000858, 600276`
- 美股：`AAPL, MSFT, NVDA, AMZN, GOOGL, META, JPM, XOM, UNH, COST`
- 加密：`BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, ZECUSDT`

时间切分：

- 训练/参数选择：前 60%。
- 验证：中间 20%。
- 样本外测试：最后 20%。
- 滚动窗口：每 6 个月或 12 个月滚动一次。

基线：

- `equal_weight`
- `risk_parity`
- `entropy_risk_parity`
- `tsmom`
- 现有单标的 `sma_cross`

成本压力：

- 固定成本：0、2、5、10 bps。
- 冲击成本：0、5、10、20 bps。
- 冲击指数：1.0、1.5、2.0。

判断标准：

- 不能只看累计收益。
- 必须同时看最大回撤、成本后收益、换手率、权重集中度、状态内稳定性和样本外结果。
- 若优势只出现在单个标的、单个时间段或单个成本假设下，不进入默认策略。

## 需要补的数据能力

短期必须补：

- 分钟 K 线稳定获取和缓存。
- 成交量异常、波动率、振幅、状态标签的统一计算。
- 每次研究运行的配置保存和结果导出。

中期再补：

- L1 bid/ask、spread、盘口不平衡。
- L2 聚合盘口快照。
- 限价单成交模拟和 FIFO 敏感性。

暂不建议补：

- 期权 IVS diffusion。
- 深度 BSDE。
- 量子波动率模型。
- 复杂 stochastic volatility 定价模拟。

这些方向有研究价值，但需要期权数据、定价基准和更强数值验证，短期不如订单流、成本和执行假设对 stock-clone 的核心回测能力有帮助。

## 下一步代码任务拆分

第一批最小可交付：

1. 在 `backend/stockmarket/quant_research.py` 增加 `calculate_market_regimes` 和状态分组指标。
2. 扩展 `run_portfolio_baseline` 返回 `cost_breakdown`、`concentration_metrics`、`regime_metrics`。
3. 在 `frontend/src/views/ResearchTerminal.vue` 增加组合实验面板，调用已有 `researchApi.runPortfolioBacktest`。
4. 新增后端测试，覆盖无未来函数、成本计算、熵强度边界和数据不足错误。

第二批：

1. 新增执行敏感性模块，输出 optimistic/base/pessimistic 三条成交路径。
2. 增加滚动样本外实验 runner，把实验配置与结果保存为 JSON。
3. 前端加入实验报告视图和下载功能。

第三批：

1. 做 leaky-integrator 预测后处理实验。
2. 接入加密或美股盘口数据，验证被动执行和订单簿状态。
3. 整理论文实验表格、消融实验和复现实验脚本。