# 全市场共享 LSTM 周度轮动（独立研究实验）

入口：[run_market_rotation.py](../tools/run_market_rotation.py)。
不替换原逐股分数差分实验，不下单、不覆盖行情数据库或原实验结果。

## 时间与数据

- 训练：2020-01-01 至 2023-12-31。
- 验证：2024-01-01 至 2025-12-31，选择 epoch 和入场门槛。
- 测试：2026-01-01 至本次冻结快照的有效末日；不参与梯度更新、标准化或选型。
- 预测未来 5 个交易日复权收盘收益；输入为 20 个连续交易日的收益、
  日内振幅、开收收益、20 日趋势和相对成交量。所有特征仅使用信号日及之前记录。
- 跨分区边界的 5 日标签剔除；特征标准化和目标缩放仅使用训练集。
  全市场共享同一日期边界，不随机拆分股票日样本。
- 使用 `ts_daily`、`ts_adj_factor`、`ts_stk_limit`、`ts_suspend_d`、
  `ts_trade_cal`、`ts_stock_basic`；不混合 Yahoo 日线与 Tushare 复权因子。
  包含沪深历史退市股票，不仅按当前上市名单筛选；按上市日期限制可用行情。
- 用单个 SQLite 只读事务冻结输入，并另存本地快照、日历和缩放参数。
  有效末日保守取日线、复权、涨跌停、停牌表最新日期的最小值；这不是数据完整性认证，
  尤其停牌表最新事件日期不等于已核验的全市场覆盖日期。
- 缺失涨跌停信息不猜测可成交，该行禁止交易，并在结果记录数量。
  行情或复权缺失/非法则显式失败，不填未来数据、不把缺失因子填 1。
- 原实验已看过部分 2026 数据，因此这里的测试隔离仅针对本次训练流程，
  不能宣称 2026 是整个研究过程从未观察过的独立留出期。

## 已确认的策略规则

每周首个交易日按前一交易日收盘后的预测调仓；新买候选为预测前 30，
原持仓在前 50 且超过门槛时保留，每周最多替换 6 只，首次建仓例外。
最多持有 30 只，每槽位目标权重为 95% / 30；不足时留现金，不强行满仓。
入场收益门槛在验证集比较 0、0.5%、1%、2%，按费用后验证总收益选择，
并保存所有候选值；不根据测试表现再次调参。

按用户确认：**不做 ST 过滤，不做行业 20% 上限**。
空更名表不表示股票不是 ST；组合可能包含 ST，可能有行业集中风险。
停牌持仓冻结、不虚构卖出；缺失报价持仓保留最后估值，因此退市残值仍有风险。
涨跌停判断只做开盘价保守限制，不能复现排队成交。
买入数量受剩余现金与 95% 目标总敞口约束；冻结持仓或价格上涨可能使实际敞口超过目标。

模拟使用复权连续单位，不是整数手真实成交，不重复加现金分红。
费用为买入 0.05%、卖出 0.1% 的研究假设，不声称历史真实费率。
5 日收盘预测与下次开盘执行、实际周长存在目标错配；周频不消除预测误差。
日线无法复现 TWAP/VWAP，相关状态固定标为日内数据不足，不生成虚假执行效果。

## 运行与实时图表

在 backend 目录执行（输出目录必须不存在）：

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'
& 'C:\Users\lrx14\anaconda3\python.exe' -m tools.run_market_rotation `
  --output-directory '.\research_charts\market-rotation-full-20261027'
```

`MKL_THREADING_LAYER=SEQUENTIAL` 仅影响该命令进程的 MKL 线程层，
避免本机两个 Intel OpenMP 运行时冲突；不设置不安全的重复加载绕过开关，
不修改共享 Python 安装。PyTorch 仍按 `--threads` 使用指定 CPU 线程。

先用 `--symbol-limit 12 --epochs 1` 做小规模流程验证；该结果必须标记为子样本，
不能当作全市场策略业绩。默认全市场 20 epoch、batch size 512、4 个 CPU 线程。
训练中每 100 批次/每个 epoch 写进度，保存验证误差最小的权重。

直接打开输出目录的 `index.html`，运行时每 15 秒刷新：

- 训练状态、批次进度、逐轮训练/验证 MSE。
- 训练完成后逐步显示验证/测试净值和回撤，不在模型训练时捏造金融收益。
- 数值指标包括 MAE、RMSE、方向准确率、总收益、最大回撤、夏普和累计费用。
- `progress.json` 保存当前状态，`results.json` 保存最终结果，
  `best-model.pt` 保存权重，`predictions.csv` 保存逐股票日预测。
  不要从不可信来源加载 pickle 行情快照。

失败会保存明确错误并以非零退出。没有自动续训；已有目录不会被覆盖。

### 本机 GPU 运行

本机 `qwen_env` 已安装 CUDA 12.1 版 PyTorch，且已验证 GPU LSTM 正反向计算。
使用独立输出目录，显式指定空闲的第二张显卡：

```powershell
& 'C:\Users\lrx14\anaconda3\envs\qwen_env\python.exe' -m tools.run_market_rotation `
  --device cuda:1 `
  --output-directory '.\research_charts\market-rotation-gpu-20261027'
```

`--device cuda:N` 请求失败时直接报错，不降级到 CPU；默认 `auto` 才允许自动选择。
数据读取、特征处理和回测仍在 CPU 上执行，模型与批次张量在指定 GPU 上训练。
进度报告记录 GPU 名称、设备索引、CUDA/PyTorch 版本及 Python 路径；
加载阶段每 100 只股票更新实际进度。
这里使用单张 GPU 训练一个共享模型，不冒称两张卡同时训练。

双卡共同训练同一个模型：

```powershell
& 'C:\Users\lrx14\anaconda3\envs\qwen_env\python.exe' -m tools.run_market_rotation `
  --gpu-ids 0 1 `
  --output-directory '.\research_charts\market-rotation-dual-gpu-20261027'
```

使用 Windows 支持的 `DataParallel` 按批次拆分数据，聚合梯度后更新一份共享权重，
训练、验证和预测都走同一并行模型。`--gpu-ids` 不与 `--device` 混用。
首批训练通过 LSTM 输出设备 hook 验证两卡实际计算，报告保存
`verified_training_devices`；权重保存为不带并行前缀的基础模型，可单卡加载。
小型 LSTM 的跨卡复制和通信可能抵消计算收益，不保证双卡比单卡更快；
全局 batch size 与时间切分不变，不通过增加 batch 偷换实验设置。

### 中文实时看板

新启动的实验默认生成中文看板，分离装载进度与训练轮次，原始诊断数据折叠显示。
未产生真实指标时显示等待状态，不补造曲线；完成训练和回测后展示净值、回撤及指标表。
对于已经运行、仍使用旧页面生成逻辑的进程，可不重启训练，单独渲染另一个页面：

```powershell
& 'C:\Users\lrx14\anaconda3\envs\qwen_env\python.exe' -m tools.market_rotation_dashboard `
  --source '.\research_charts\market-rotation-dual-gpu-20261027\progress.json' `
  --output '.\research_charts\market-rotation-dual-gpu-20261027\dashboard.html' `
  --watch --source-pid $trainingPid
```

运行前将 `$trainingPid` 设置为实际训练进程 PID；监视器只读进度、不写行情或训练状态，
终态时自动退出，训练进程消失时显示错误并退出。页面离线每 15 秒刷新，
监视器每 5 秒检查源进度。去掉 `--watch` 可对已完成结果生成静态页面。

## 双卡性能优化与复现

先等原始 20 轮实验以及验证、测试全部完成，再优化。原实验目录保留，不把性能调优
当作模型重新选型，也不根据测试收益挑选更快的配置。

CUDA 默认 `--batch-backend auto` 选择 `resident`，CPU 默认仍为 `legacy`。
可显式设置 `--batch-backend legacy` 复现原始路径。两者保持 FP32、全局 batch 512、
共享 LSTM 结构、Adam、梯度裁剪、打乱顺序、尾批和时间分区一致：

- 将紧凑特征行、样本终点与标签一次装入主卡显存，只在当前批次按索引取出 20 日序列，
  不在显存中展开整个全市场序列集。
- DataLoader 保留原随机数和顺序语义，但只传输少量样本索引，避免逐样本拼接特征、
  每批重新搬运完整输入；索引通过锁页内存传输。
- GPU 上累计训练/验证误差，只在进度更新和每轮结束时读回标量。
  流内异步断言检查非有限损失与梯度范数，不用取消校验换取速度。
- 两卡仍由 DataParallel 共同计算一份模型；没有自动放大模型、增大 batch 或启用混合精度。
  显存不足会明确报错，不偷偷降级或改变样本。

本机双 RTX 4080 SUPER，原冻结快照的完整 4,096,227 个训练样本与
2,429,104 个验证样本，交替顺序重复两次，实测中位数：

| 指标 | 原始 | 优化 |
| --- | ---: | ---: |
| 每轮训练＋验证 | 117.34 秒 | 73.67 秒 |
| 样本吞吐 | 约 5.56 万/秒 | 约 8.86 万/秒 |
| GPU 0 平均忙碌率 | 约 26.4% | 约 33.6% |
| GPU 1 平均忙碌率 | 约 21.5% | 约 28.9% |

吞吐约提升 59%，耗时约下降 37%；两次完整对照的最大权重绝对误差为 0。
损失累加顺序不同会产生微小浮点误差。这些是本机测量，不保证其他机器同样收益。
利用率为 `nvidia-smi` 采样的设备忙碌比例，不等于 SM occupancy 或每个 CUDA 核心占用率；
小模型及 Windows DataParallel 复制/通信仍限制满载，不能用空算力填充来伪造优化。
计时包含取批、传输、完整前后向、优化器和验证，不含一次性准备、网页渲染或金融回测。

复现全轮性能对照（只加载可信的本地行情快照；输出目录必须不存在）：

```powershell
& 'C:\Users\lrx14\anaconda3\envs\qwen_env\python.exe' -m tools.benchmark_rotation_training `
  --baseline-directory '.\research_charts\market-rotation-dual-gpu-20261027' `
  --output-directory '.\research_charts\gpu-performance-new-run' `
  --steps 0 --repeats 2 --sample-gpu
```

`--steps 300 --repeats 3 --profile` 可做较短的交替测量，并生成 PyTorch CPU/CUDA
trace 与热点汇总。本机 GPU 环境是 Python 3.10，不满足 Pylance CPU profiling 的
Python 3.15 要求，因此使用 PyTorch 自带 GPU profiler，不升级或污染共享环境。
性能采样和 profiler 不同时计入正式计时。结果保存为 `benchmark.json` 和中文 `index.html`。
可使用上一轮工具自动生成的 `panel-cache` 配合 `--cache-directory` 复用数值数组，
缓存检查对应的基准目录，不从未知来源加载快照。
