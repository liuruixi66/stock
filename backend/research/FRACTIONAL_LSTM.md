# 基于数据库的分数差分 LSTM 研究实验

## 行业龙头固定股票池（仅研究）

新增独立的股票池准备命令，**不启动训练，不修改旧模型或删除旧数据**：

```powershell
python -m tools.select_industry_leaders
```

范围限定为沪深主板人民币 A 股；使用本地 `cn_info.industry` 细分行业，
不是申万分类。按同一已完成交易日的 `ts_daily_basic.total_mv` 从大到小，
每行业取 5 只，并列时按股票代码升序。市值单位为万元；不足 5 只的行业
保留实际数量。缺少行业、来源时间、当日市值或市值非正/非有限的股票，
以及当前可识别 ST/*ST、非上市和选股日停牌股票，均排除并记录原因。
当前名称过滤包含旧快照的 `SST`/`S*ST` 标识，不把英文名称 `Stock` 当作 ST。

默认取本地最近一个已完成交易日的市值；可显式指定
`--market-cap-date 2026-10-26`。不会拼接各股票不同日期的市值，也不会将
未完成的局部下载当作全市场排名。市值、停牌的整批下载进度和沪深交易日历
必须覆盖该日期；不满足时明确报错，不静默退回另一天。

输出沿用实验编号：

- `research_charts/runs/run-NNNNNN/results.json`：行业排名、全部入选代码、
  排除原因、快照日期、来源指纹及校验签名。
- 同目录 `industry-leaders.csv`：带 UTF-8 BOM 的完整名单，便于表格软件查看。
- `run.json` 的类型为 `portfolio-universe`，与训练结果分开；查询本类最新结果：
  `python -m tools.list_research_runs --latest --kind portfolio-universe`。

市值前五只是“龙头”的可复现代理，不代表经营质量认证。当前行业、名称及
上市快照用于过去区间会产生前视/幸存者偏差；当前非 ST 不证明历史全程非 ST。
用户接受该限制用于研究，但 `historical_st_verified`、
`point_in_time_verified` 和 `live_trading_eligible` 均固定为 `false`。
选股日停牌过滤也不替代历史回测中逐日停复牌检查。

该产物是**候选池，不是持仓清单或已训练模型**；候选股票数量与最多 30 个
持仓槽位分开。现有逐股训练入口不会自动切换到这个股票池；
共享组合训练接线与价格覆盖核验完成前，不能把旧 MAE 训练当作新组合训练。

### 新行业池的统一行情检查

行业池研究改用同库 `ts_daily` 和 `ts_adj_factor`，不对单只缺失股票回退到
Yahoo `cn_daily`，也不混用两套来源。研究价格为当日 OHLC 乘当日累积复权因子，
不按未来终点因子重新定锚；成交量由手乘 100 转为股。此协议单独标为
`tushare-factor-portfolio-research-v1`，不套用旧模型的供应商价格协议。

```powershell
python -m tools.audit_portfolio_history `
  .\research_charts\runs\run-000001\results.json `
  --start 2006-10-16 --end 2026-10-14 `
  --output .\research_charts\industry-price-audit-new.json
```

该命令只读数据库，检查全部入选证券，不训练、不清理。要求沪深完整交易日历
一致、全市场停牌下载覆盖对应交易日、每条行情有同日有效复权因子。
对已上市期间缺少的 K 线，只有有依据的停牌日才作为已解释缺口；
既无行情又无状态解释的日期全部列入阻断报告，不插入价格。
单股问题汇总到报告后以退出码 2 返回，不能把已检查的其他股票当作整池成功。
其他输入/数据库错误退出码 1，完整检查通过才返回 0；已有输出不覆盖。
`passed` 也只表示这些数据一致性检查通过，不认证原价、公司行动、历史 ST 或实盘成交。

## 统一价格口径（v1）

**当前数据仅供研究，不具备实盘认证。** 审阅本地数据下载程序后确认：日线来源是
Yahoo / yfinance，调用 `history(auto_adjust=False, actions=True)`，原样保存 OHLC、
Adj Close、Volume、Dividends 和 Stock Splits。关闭自动复权不等于 OHLC 一定是
历史不复权成交价，供应商可能已经做过拆股调整；不能把字段名 `close` 当作原价证据。
此外，下载程序把缺失公司行动填零，因此“0”不能证明历史上没有该事件。
每日增量更新只刷新最近重叠窗口，不会自动重刷整个历史的复权因子；
库内历史记录可能混合不同下载快照，重训前还需全历史一致性复核，不能仅凭指纹一致认定价格正确。

统一约定由 `market_data/price_basis.py` 定义：

| 环节 | 固定口径 |
| --- | --- |
| 模型输入 | OHLC × adj_close / close；成交量保持供应商原值 |
| 价格锚点 | 当前供应商快照，不冒称已认证前复权或后复权，不主动换锚点 |
| 预测目标 | 下一交易日复权收盘价简单收益率，不是原价涨跌幅或成交收益 |
| 模型选型 | 默认先做历史 Optuna 搜索并冻结配置；逐日用目标日前窗口的逆差分收益 MAE 选 epoch，再重训；legacy 保留标准化 MSE |
| 信号与成交时序 | t 日收盘后信号，最早 t+1 交易日开盘模拟执行；预测目标不等于成交收益 |
| 连续研究模拟 | 复权价格和连续数量；不另外加现金分红，避免双重记账 |
| 股数敏感性模拟 | 未核验供应商 OHLC；只做整手/费用敏感性，不声称实盘复现 |
| 真实成交要求 | 经核验不复权 OHLC + 当时可得公司行动 + 真实费用、交易日历与交易限制 |

前复权通常便于对照当前价格，后复权便于连续历史展示，但**名字本身不能保证因果性或原价真实性**。
若两种序列仅差固定正比例，简单/对数收益率相同；分数差分及含价格水平的特征不应据此认定完全等价。
本次不改变历史训练数值，也不把供应商字段重新命名为已认证前/后复权。
缺失、非正或非有限的复权价格现在必须报错；通用 SQLite 行情读取器不再退回原 close。
模型、数据溯源和实验顶层均写入 `fractional-price-policy-v1`，并明确标记实盘资格为 false。
训练输入与股数成交输入有价格类型标记；检测到复权行情进入股数模拟时直接拒绝。
类型标记是程序防误用措施，不替代数据来源核验。

新实验同时保存复权 OHLCV、供应商 OHLCV 和公司行动的独立 SHA256，
复算时全部核对，避免“复权价没变但原价或分红改了”仍通过。
旧版结果允许以明确警告进行研究敏感性复算；旧版缺少的指纹不会被当作已验证。
不同版本（含旧版未声明）的价格约定不允许直接跨实验汇总。
股票进度检查点版本升为 3，纳入搜索签名、结构和早停设置；旧检查点保留，但不能按新代码续跑，必须使用新输出文件名。
已经运行的进程不会自动加载代码修改；不要把其产物改标为新口径。

### 只读价格审计

```powershell
python -m tools.audit_fractional_prices `
  .\fractional-lstm-results-seed-42-current-fees-zh.json `
  --output .\research_charts\price-basis-audit-seed-42.json
```

该命令只检查结果指定的股票与历史区间，不写数据库、不训练模型，输出复权因子范围、
拆股/分红记录、非分币价格行数、独立指纹和实盘阻断项。新输出文件必须不存在。
“研究行情与历史结果一致”为 true 只代表研究数据检查通过，不等于原价、公司行动或实盘已认证。
`--require-live-ready` 会先写出审计报告，再以非零状态退出，因为当前快照缺少历史时点和原价认证。
只有经过外部数据核验并实现完整公司行动及交易约束后，才能另行设计实盘口径，不能手动翻转资格字段。

长时间重训前先做此审计，冻结数据快照与选型规则。现有 seed 45 旧版检查点不与新实验混用。
本次仍保持逐股逐日滚动模型，不改成全股票共用模型，也不按测试收益挑“最佳”模型。
若已看过测试结果再改策略，应留新的未使用时间区间或模拟盘作进一步验证。

### 外部原价与公司行动交叉核验

```powershell
python -m tools.verify_fractional_sources `
  .\fractional-lstm-results-seed-42-current-fees-zh.json `
  --output-directory .\research_charts\source-verification-seed-42
```

此命令只读数据库，按股票和每段不超过 730 个自然日向腾讯请求未指定前/后复权的
`day` 日线（每次上限 640 条），并分页读取东方财富已实施分红送转记录。
不使用系统代理；请求只有公开股票代码和日期，不发送账户或私有代码。
默认请求间隔 0.5 秒，可用 `--request-interval` 调整但不能低于 0.2 秒。
输出目录必须不存在。每只股票完成后保存比较结果和阶段汇总，保留输入快照、响应原文、
请求 URL、抓取时间及 SHA256。中断后已有证据保留，但当前工具不支持续传，
重跑请用新目录。证据中可能包含测试区间以外的公司行动，但只在指定区间内比较。
若某来源返回HTTP 429、501或503，本次运行会停止向该来源发送后续请求，
并逐项记录未发送请求的原因；不会切换代理或伪装绕过限制。

输出 `index.html` 可离线查看。完整日期按 stock/date 精确对齐；任何缺失参考日期都保留，
不自动填充、不推测停牌。OHLC 绝对差超过 0.0051 元记为差异（允许半分钱内舍入/浮点误差）；
参考成交量单位可能为手，因此不混入或覆盖原库成交量。价格差异按字段计数，不等于差异交易日数。
复权因子相邻变化超过 0.01% 且无已存或参考事件时，列为待核实异常，不自动修正。

分红与送转按供应商“每10股”的金额/比例换算；缺失字段保留未知，不能当零。
逐日核对现金分红和送转比例，列出库内存在、参考未找到的行动。
直接金额差异可能源于供应商拆股调整或公司行动错误，报告只记录差异，不擅自判定哪家正确。
任何 HTTP/解析错误都写明并使核验失败，不能用空响应冒充没有公司行动。
核验不通过命令返回非零，不启动训练、不覆盖数据库。
即使两家 OHLC 一致，也不能单凭此报告授予实盘资格：仍需核验交易所/券商原价、
公司行动到账日、历史时点可得性、配股股改和交易约束。

### 缺失数据的获取路径

不要用“把 Yahoo close 改名为原价”的方式补数据，也不要从价格差异反推出分红到账日。
可选择下列路径；任何新源都应另存快照、标明供应商和抓取时间，再做交叉核验，不覆盖旧研究库。

1. **券商 QMT / miniQMT 行情**：
   项目已包含 QMT 适配代码，但有适配代码不等于本机已有可用客户端或行情权限。
   在券商客户端具备历史行情权限后，用行情模块下载并读取日线：
   `get_market_data_ex(..., period='1d', dividend_type='none', fill_data=False)`。
   `none` 指不复权，`fill_data=False` 避免填充停牌时间戳；
   历史下载、交易日历和除权数据分别用 `download_history_data`、
   `get_trading_dates`、`get_divid_factors`。
   只使用行情模块，不创建交易账户订阅、不调用下单接口。券商提供的历史长度、成交量单位、
   原价定义和公司行动完整性仍需确认；除权因子不等于含派息到账日的完整公司行动。
   参考：[XtData 官方文档](https://dict.thinktrader.net/nativeApi/xtdata.html)。
2. **Tushare Pro 结构化补充**：
   [`daily`](https://tushare.pro/document/2?doc_id=27) 文档明确为不复权日线，
   停牌期间不提供数据，`vol` 单位为手、`amount` 单位为千元；
   `pre_close` 是除权昨收，不应直接当作前一交易日实际收盘价。
   [`dividend`](https://tushare.pro/document/2?doc_id=103) 提供每股税前分红、
   送股/转增比例、登记日、除息日、派息日、红股上市日和实施公告日；
   只用已实施记录，空日期保留未知。`cash_div_tax` 是每股税前分红，
   不能误按东方财富每10股的单位再除以10，也不能把供应商税后值当作所有账户的实际股息税。
   [`adj_factor`](https://tushare.pro/document/2?doc_id=28) 与
   [`trade_cal`](https://tushare.pro/document/2?doc_id=26) 可补复权因子和交易日历。
   截至 2026-10-23 查阅的文档，分红、因子、交易日历要求至少 2000 积分；
   日线的免费试用门槛和额度较低，但不代表上述完整数据集免费。
   权限、资费和历史覆盖以服务商实际账户为准；需用户自行注册/开通，不自动付费，
   token 仅在本地安全配置，不发送到聊天、不提交源码或报告。
   Tushare 因子由其自行生产，仍不是历史时点可得性的认证。
3. **交易所/公司公告复核**：
   在[上交所](https://www.sse.com.cn/)和
   [巨潮资讯公告查询](https://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice)
   查询权益分派实施公告及更正公告，核对登记、除权除息、派息和新增股份上市日期。
   公告证据适合核实事件，但网页公告不直接替代完整20年逐日 OHLCV 数据集。
   公开免费行情可继续做研究交叉核验，不应因缺少付费或券商权限就默认为实盘已认证。

   当前采用免费、仅研究路径，不自动开通付费服务，也不连接券商交易账户。
   首轮30只股票中，22只完成参考数据抓取，另8只存在HTTP 501等请求失败；
   已获得的参考日期中有35,704个股票交易日、139,081个OHLC字段差异，
   并发现129条现金分红和1条送转比例比较差异。这里的差异不自动判定某一供应商正确。
   之后对失败窗口做低频单次重试仍返回501，已停止继续请求，不切换代理或绕过服务限制。
   新训练数据尚未冻结，正式重训尚未启动。

   ### 免费公告证据采集（严格限定格式）

   ```powershell
   python -m tools.collect_fractional_announcement `
     --code 600055 --year 2017 `
     --output-directory .\research_charts\official-announcement-600055-2017
   ```

   该命令仅访问巨潮资讯公开发行人搜索、公告查询及公告PDF，保存响应、SHA256和
   标准化事实记录；不会复制PDF全文到报告，不写原数据库，不下单。PDF读取使用
   `requirements-research.txt` 中的 `pypdf`。输出目录必须不存在。
   当前只支持唯一匹配、明确“不差异化”、按每股列示现金红利与转增股份、完整A股日期表的
   简单权益分派公告。遇到多份匹配、特殊方案、代码不符、缺失日期或无法识别版式直接报错，
   不能用推测值补齐；这是格式受限的证据采集器，不是通用公司行动解析器。

   已采集万东医疗2016年度权益分派实施公告（2017-05-25披露）：
   每股税前现金红利0.15元、每股转增0.40股；
   登记日2017-06-01、除权除息及派息日2017-06-02、新增股份上市日2017-06-05。
   旧库同日分红字段为0.010714，不应直接用于当时实际股数的现金记账。
   此公告只验证这一个事件，不能推广成30只股票全部历史行动已经核验。
   后续仍需逐事件检查更正公告、送转到账和税务处理；公告派息日也不等于特定账户实际到账证明。
   来源：[公司实施公告](https://static.cninfo.com.cn/finalpage/2017-05-25/1203566326.PDF)。

在 `backend` 目录下运行数据库研究实验：

需要 Python 3.11+ 及 `requirements-research.txt` 的依赖（含 Optuna）。
本机股票项目使用独立 Conda 前缀 `stock\.venv312`（Python 3.12），
对应研究命令的解释器为 `..\.venv312\python.exe`。
原 `stock\.venv` 是保留的 Python 3.13 CPU 环境，不要混淆两个解释器。
CUDA 仅在兼容环境可用时自动选用，不以临时枚举补丁或
`KMP_DUPLICATE_LIB_OK` 绕过兼容性及 OpenMP 冲突检查。
这只是本机环境升级，不改变项目原有 Python 3.11+ 支持声明。

从 `backend` 目录安装或重建同类研究环境：

```powershell
conda create --prefix ..\.venv312 python=3.12 pip --no-default-packages --yes
..\.venv312\python.exe -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128
..\.venv312\python.exe -m pip install -r .\requirements.txt -r .\requirements-research.txt
..\.venv312\python.exe -m pip check
```

使用官方 CUDA wheel；不把 CPU 版 torch 或旧 Conda 数值计算包复制到新环境。
下面示例中的 `python` 应指向所选的 3.12 解释器；不激活终端时可始终使用上述完整相对路径。

```powershell
python -m tools.run_fractional_research --output .\research_charts\fractional-lstm-tuned.json
```

### 实验编号与最新结果

三个训练入口（`tools.run_fractional_research`、`tools.tune_fractional_lstm`、
`tools.run_market_rotation`）共用 `research_charts/runs/run-000001` 形式的递增编号。
不指定原来的输出参数时，自动为每次启动分配独立目录：

```powershell
python -m tools.run_fractional_research
python -m tools.tune_fractional_lstm
python -m tools.list_research_runs
python -m tools.list_research_runs --latest
python -m tools.list_research_runs --latest --kind fractional-training
```

`run.json` 保存编号、类型、状态、起止时间、结果绝对路径、参数与数据溯源。
默认训练结果、日志、搜索和模型权重都留在该次运行目录；旧目录不移动、不重新编号。
显式指定输出路径仍兼容，但同样登记编号及结果位置。
编号表示启动顺序；“最新”取**编号最大的成功完成项**，不是最近修改的任意文件。
失败、处理中、被中断的实验会列出状态，不冒充最新成功训练；没有成功项时明确提示。
未产生正式结果文件不能标记完成。强制终止进程可能留下 `running`，仍不会成为最新成功项。
同一输出断点续跑保留编号和累计尝试次数：fractional 继续传原 `--output`（须有 progress），
独立搜索继续传原 `--directory` 加 `--resume`；已成功完成项不可被重新标成新训练。
目录编号通过原子创建分配，支持多个独立任务并发启动。现有历史产物仍按原路径查看。
编号和图片是输出管理功能，并不改变训练数据或模型预测。

命令行工具会将 JSON 字段名和说明文字输出为中文；技术标识符、股票代码、GPU 名称和模型权重键保持原样。
现有模拟器按照每年 252 个交易日的口径计算年化收益率。样本比较报告还会汇总年化收益率的平均值、最小值和最大值。

默认 `--training-mode tuned`：训练从 2006-10-16 起，初始验证边界为 2014-10-14，
测试区间仍为 2025-01-01 至 2026-10-14。先执行下述一次性历史搜索，再冻结每个分支的模型配置。
测试期间采用逐日滚动训练：每个目标交易日都单独进行一次拟合。训练轮次根据此前最近 60 个已有标签的样本选择，
再使用截至目标日前的全部已标注样本重新拟合模型，最后预测下一个目标日。当天及之后的数据不会参与当天的训练或选型。
验证窗口长度可通过 `--walk-forward-validation-days` 调整。由于每天都要重新选型和训练，本实验的计算量会显著高于
“训练一次、批量预测整个测试区间”的方式。

### Optuna 搜索、早停和最佳模型

这三项并非同一算法：

- **Optuna / TPE** 搜索隐藏单元 16/32/64、层数 1/2、学习率 0.0003—0.003（对数采样）、
  batch size 32/64/128、轮数上限 30/60/90/120；双层 dropout 为 0/0.1/0.2，单层为 0。
- **Early Stopping** 默认 patience=15、min_delta=0.000001，以逆差分后简单收益 MAE 监测改善。
  `--epochs` 是上限而非强制训练次数；不足 min_delta 的真实改善仍保存，但不重置等待计数。
  patience=0 可显式关闭早停，仍保留最优 epoch。
- **Best Checkpoint** 原子保存真正的最优验证权重、epoch、缩放参数、差分权重、结构、日期、种子、
  价格约定和行情指纹；不把最后一轮或重拟合权重误称为最优验证权重。

默认抽取 6 只完整历史上海非 ETF 股票，使用 2012、2013、2014 三个逐年扩展的验证折；
每折的差分阶数和缩放只从该折训练期估计，所有搜索标签早于 2016。
总预算 **20 trial，两个分支各 10**，不是每个分支 20、也不是每个预测日 20。
每分支先包含 16单层30轮、32单层30轮、64单层90轮、32双层90轮四个对照，
其余 trial 使用 TPE（启动样本数 4，确保小预算内实际进入引导搜索）。
MedianPruner 可提前结束劣质候选；已失败、中断和剪枝的 trial 也占预算，不偷偷补跑。

目标为各股票/验证折 `模型收益 MAE / 零收益预测 MAE` 的等权平均；小于 1 才表示该验证目标优于零收益基线。
报告同时保存 MAE、RMSE、方向准确率、训练期多数方向基线和完整逐轮 loss。
若赢家仍不及零收益基线，会明确标记不合格并发出警告，但仍可用于研究，不会自动替换成别的模型。
选 epoch、选参数及评分使用同一验证集，结果存在选型偏差；不是独立测试，更不是实盘认证。
股票池仍有幸存者偏差，且本轮仅一个模型初始化种子。

先运行独立小试，不启动完整逐日回测：

```powershell
python -m tools.tune_fractional_lstm `
  --directory .\research_charts\lstm-tuning-new `
  --stocks 6 --trials 20 --max-epochs 120 --patience 15
```

输出目录必须全新；中断后用同一命令增加 `--resume`。本地 `study.sqlite3` 持久化所有 trial，
`manifest.json` 签名绑定数据库文件和价格指纹、时间边界及参数，`report.json` 记录最终赢家；
每次最优 epoch 改善即写 `方法\trial-NNN\fold-NN.pt`。恢复会先验证签名；配置或数据变化必须另开目录。
中断时已经 RUNNING 的 trial 显式标为 FAIL，并在研究元数据中记录 interrupted，不伪装成完整试验。
报告完成时会重新加载每个胜出检查点检查签名和覆盖范围。

完整 runner 默认另建输出路径旁的 `.search` 和 `.models` 目录，也可通过
`--search-directory`、`--model-directory` 指定。复用同一兼容搜索必须显式加 `--resume-search`；
其 `--test-start`、搜索股票数、预算及种子等也必须相同（独立搜索默认测试边界是 2016-10-14）。
每股每方法分别保留 `validation-best.pt`（最后预测日的验证选中状态）
和 `refit-latest.pt`（按选中 epoch 用全部已知历史重拟合的预测状态）。
它们与逐股票的 `.progress.jsonl` 进度文件用途不同，不覆盖历史正式结果。
将实验产物放在已忽略的 `research_charts` 中，避免提交大体积权重及 SQLite。
缩短训练历史不满足默认搜索前提时会报错，可明确选择 legacy，而不会用测试数据调参。

复现旧配置须显式选择：

```powershell
python -m tools.run_fractional_research --training-mode legacy `
  --output .\research_charts\fractional-lstm-legacy-new.json
```

legacy 默认训练起点为 2023-01-01、验证起点为 2024-01-01，隐藏16/32、固定30轮，
早停关闭、标准化验证 MSE 选型；测试日期不变。可用 `--epochs` 覆盖轮数。
历史输出及旧检查点不会被改写。

可用 `--parallel-gpus` 和 `--workers-per-gpu` 并行训练不同股票；单个小型 LSTM 不做多卡切分，以避免通信开销。
适当增加每张卡的进程数可能提升 GPU 利用率，但会增加显存占用，速度提升取决于硬件负载。示例：

```sh
python -m tools.run_fractional_research \
  --training-mode legacy \
  --parallel-gpus 2 \
  --seed 45 \
  --train-start 2006-10-16 \
  --validation-start 2014-10-14 \
  --test-start 2016-10-14 \
  --test-end 2026-10-14 \
  --walk-forward-validation-days 60 \
  --epochs 30 \
  --workers-per-gpu 2 \
  --parallel-gpus 2 \
  --output ./fractional-lstm-results-seed-45-current-fees-zh.json
```

运行时会显示每只股票、预测方法的逐100日进度、当前设备、耗时和当前股票方法的剩余时间估算，以及股票完成数量。
并行模式不会覆盖已有结果；如单卡内存不足，会明确报错，不会挪用另一张正用于并行训练的 GPU。
训练数据会在每个股票方法开始时一次性传入所选设备，避免每个 batch 重复从 CPU 复制。
每只股票的两种方法完成后，会把预测和模型元数据追加到输出文件旁的 `.progress.jsonl` 检查点；
使用完全相同的参数重新运行同一输出路径时，会验证数据库文件与实验参数签名，并跳过已完成股票。
默认 tuned 模式续跑时还必须加 `--resume-search`，以显式复用已冻结的搜索。
整个实验完成并成功写出正式结果后，检查点会自动删除。参数或数据库变化时拒绝错误续跑。
运行日志会同时显示在终端并写入 `backend/log/` 下带时间戳的日志文件；可通过 `--log-directory` 指定其他目录。

最终 JSON 的“模型效果评价”分为两个互不混淆的视角：

- “机器学习视角”在测试期逐股票、逐交易日汇总下一交易日复权收盘价简单收益率的 MAE、RMSE、MAPE、sMAPE 和方向准确率，并与始终预测零收益的基线比较。MAPE 排除实际收益恰好为零的样本，但仍可能被非常接近零的收益放大；应结合 MAE、RMSE 和 sMAPE 解读。
- “金融视角”汇报策略累计/年化收益、最大回撤、年化波动率、夏普比率、费用和成交笔数，并列出相对数据库随机股票池等额基准的差值。它衡量预测转成策略后的模拟表现，不等同于模型误差，也不代表真实交易表现。

机器学习指标是测试集预测质量，金融指标是交易模拟表现；两者应分别解读。评估不会重新训练模型，而是在已有逐日预测和价格数据上计算。

## 离线可视化

在 `backend` 下复用已完成的 JSON 生成中文 HTML 报告和可下载的 SVG 矢量图，无需新依赖、数据库或重新训练：

```powershell
python -m tools.plot_fractional_research `
  .\fractional-lstm-results-seed-42-current-fees-zh.json `
  .\fractional-lstm-results-seed-43-current-fees-zh.json `
  .\fractional-lstm-results-seed-44-current-fees-zh.json `
  --execution-results .\fractional-lstm-execution-current-fees-all-seeds-zh.json `
  --output-directory .\research_charts
```

默认以 Seaborn + Matplotlib 的非交互后端生成 PNG，不启动浏览器、不生成 HTML。
每个来源结果独立子目录保存 `chart-NN.png` 和 `charts.json`（标题、说明、来源绝对路径及限制）。
支持 `--format svg` / `--format pdf` 与 `--dpi 180`；图片渲染需要研究依赖中的
Matplotlib、Seaborn，以及微软雅黑、黑体或 Noto Sans CJK SC 字体。
显式指定 `--format html` 才保留原来的离线 HTML/SVG 报告。
输出目录必须不存在，以防覆盖；
可以指定新的目录再次生成。`--execution-results` 可省略，提供时必须与输入结果的绝对来源路径匹配。
尚在运行的 `.progress.jsonl` 不是完整回测结果，不能作为输入。

- 模型图：各股票最优验证 MSE、测试收益率 MAE、最佳 epoch、不同隐藏单元配置的最终验证 MSE。
- 金融图：全交易日净值、历史回撤、收益与风险、夏普比率、累计费用和成交笔数，附指标数值表。
- 费用复算单独展示筛选子样本控制组和有限交易约束组，不与完整股票池混为一组。
- 有整体机器学习评价的结果会额外展示 MAE/RMSE、方向准确率和 MAPE/sMAPE，并比较零收益基线。

旧结果没有保存逐轮 loss 或整体机器学习指标时，报告会明确说明缺失，绝不从 MAE 推测 RMSE 或捏造收敛曲线。
新训练会在候选试验中保存逐轮训练/验证 MSE；滚动训练仅保留最后一个预测日的逐轮记录以控制体积，
并保留原有逐日选型记录。报告为每种方法按代码排序选第一只具有逐轮记录的股票展示候选模型曲线。
训练 MSE 是各批次参数更新前损失按样本数加权的平均值，验证 MSE 在 epoch 结束后计算；
这些记录不参与选型或改变预测。逐日滚动验证误差与同一模型逐轮收敛是不同概念。

Optuna 的原始 `report.json` 也可直接绘图（只支持静态格式），不需要重新搜索或训练：

```powershell
python -m tools.plot_fractional_research `
  .\research_charts\lstm-tuning-tpe-20261028\report.json `
  --output-directory .\research_charts\lstm-search-images-new --format png
```

包括赢家相对 MAE、完整试验对比、每股每年验证折相对 MAE、最佳 epoch 与实际训练轮数，
以及每个赢家验证折的逐轮 MSE 和实际早停指标（逆差分后的收益 MAE）。
失败/剪枝试验不作为完整目标值比较；验证集既选型又评分，不能当独立测试或实盘表现。
静态图保留完整日期与缺失观测间断，不插值、不用零填补缺失指标。

## 交易费用敏感性复算

复用已保存的预测结果进行复算，无需重新训练：

```sh
python -m tools.replay_fractional_execution \
  ./fractional-lstm-results-seed-43-zh.json \
  ./fractional-lstm-results-seed-44-zh.json \
  --output ./fractional-lstm-execution-current-fees-zh.json
```

本次敏感性分析采用以下默认假设：

- 券商佣金：单边 0.03%，每笔最低 5 元。本次实验按用户确认的口径，视为佣金已包含交易所经手费和监管费，不重复收取经手费。实际费率以券商及账户协议为准。
- 沪市 A 股过户费：单边 0.001%。
- 股票印花税：仅卖出时收取 0.05%。
- 买入按 100 股一手，卖出数量不得超过已交收股数。

上述当前费用会统一应用于整个历史测试区间，并不代表各历史年份实际执行的费率。结果会分别列出佣金、过户费和印花税。
旧研究路径未接入经过核实的历史每日涨跌停价、ST 状态或股息到账日期。模拟器不模拟涨跌停成交，也不计算股息税；股息作为不可用于交易的应收款处理。
名义价格数据也尚未经过外部核验。因此，结果仅供费用敏感性研究，不应视为可直接执行的回测结果或实盘收益。

### 严格执行验证的数据门禁

旧研究路径只读取 `cn_daily`，上述限制不代表同一数据库永远没有其他来源的数据。
若库中已有 `ts_daily`、`ts_stk_limit`、`ts_dividend`、交易日历及停牌记录，
须分别检查实际股票/日期覆盖，不能因为存在表名就宣称可用于真实执行。
可对之前搜索中冻结的股票清单做只读检查：

```powershell
python -m tools.audit_fractional_execution_readiness `
  .\research_charts\lstm-tuning-tpe-20261028\report.json `
  --start 2025-01-01 --end 2026-10-28 --capital 200000 `
  --output .\research_charts\execution-readiness-new.json
```

报告列出交易日历缺口、每股原价/涨跌停/复权因子覆盖、停牌记录、
实施分红的关键日期缺失、两来源 OHLC 不一致和历史名称记录数量。
空分红/停牌查询不能证明无事件；缺失行情必须结合停牌核对，不前向填充。
目前两种 fractional 模拟器尚未接入这些执行字段，也缺少完整涨跌停成交、
税务批次、历史风险状态和流动性规则，故门禁明确返回 `blocked`、
`simulation_executed=false`，不计算或输出所谓实盘收益。
