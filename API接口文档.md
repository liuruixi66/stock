# API 接口文档

## 后端模块分层（2026-10-14）

后端按职责拆分，已有HTTP路径、数据库模型/迁移、管理命令名及ETF策略参数保持不变。

| 目录 | 职责 |
| --- | --- |
| [config](./backend/config/) | Django settings、总路由、ASGI/WSGI入口、统一文件路径 |
| [api](./backend/api/) | HTTP请求解析、响应和业务路由；不放策略算法 |
| [strategies](./backend/strategies/) | ETF规则、技术分析和信号计算，不初始化Django、不下券商订单 |
| [strategies/platforms](./backend/strategies/platforms/) | 聚宽、BigQuant平台回调与委托适配 |
| [research](./backend/research/) | 回测、组合研究、绩效统计、数据校验及旧筛选服务 |
| [execution](./backend/execution/) | 账户、订单、同步及模拟交易执行 |
| [execution/compat](./backend/execution/compat/) | 原系统的跨操作系统交易兼容实现；其中随机模拟数据不是实盘行情 |
| [brokers](./backend/brokers/) | QMT/FUTU/IB券商适配，仍与策略规则分开 |
| [market_data](./backend/market_data/) | 行情来源、下载和本地历史快照 |
| [stockmarket](./backend/stockmarket/) | Django应用身份、ORM模型、迁移、admin和管理命令 |
| [stockmarket/tests](./backend/stockmarket/tests/) | 策略、平台、API、执行及目录边界回归测试 |
| [tools](./backend/tools/) | 独立诊断/旧筛选CLI，按需运行，不随Web启动执行 |
| [trading_system](./backend/trading_system/) | 保留的旧交易系统及内置SDK边界，不由新Web入口自动启动 |

`backend/manage.py` 与 `backend/start_server.py` 仍是启动入口，`.env`、数据库和缓存仍位于后端根目录；配置模块由`myproject.settings`改为`config.settings`，外部部署若显式设置了旧模块路径需同步修改。应用名`stockmarket`不变，因此本次不需要新建或重做数据库迁移。内部Python导入路径已随目录迁移更新，不保留两套重复实现。

旧`filter_stocks.py`的HTTP函数已分离到[screening_views.py](./backend/api/screening_views.py)，数据库筛选/计算保留在[screening.py](./backend/research/screening.py)，命令行示例移至[screen_stocks.py](./backend/tools/screen_stocks.py)。服务模块不再自行初始化Django或切换工作目录，由Web/CLI入口负责初始化。原本未注册的旧筛选及mock股票接口没有因此新增到HTTP路由。

在`backend`目录下使用模块方式运行诊断工具：

```powershell
..\.venv\Scripts\python.exe -m tools.time_range_validator
..\.venv\Scripts\python.exe -m tools.trade_analysis
```

两者使用统一`backend/cache`路径，不再依赖旧Linux桌面目录。时间验证工具里的前端日期仍是历史硬编码样例，不能把它的报告当成实时前端扫描结果。旧筛选服务仍依赖原有`indicators`模块；当前仓库中该模块缺失，本次结构整理不补造指标实现，也不宣称旧筛选CLI已可用。旧交易系统的SDK、策略配置和相对路径约定保留，未执行实盘或旧调度器。

## BigQuant ETF 研究策略导出与平台接口（2026-10-14）

本节描述独立的平台适配，不新增本系统HTTP接口，不连接券商实盘。完整代码文件为 [bigquant_etf_rotation_v1.py](./bigquant_etf_rotation_v1.py)，适配源代码为 [bigquant_etf_rotation.py](./backend/strategies/platforms/bigquant_etf_rotation.py)，复用项目的 [ETF规则核心](./backend/strategies/etf_rotation.py)。原MACD/KDJ功能不变。

### 导出与运行

在项目根目录 PowerShell 中执行，已存在的输出文件会拒绝覆盖：

```powershell
.\.venv\Scripts\python.exe backend\manage.py export_bigquant_etf --output .\bigquant_etf_rotation_v1.py
```

1. 登录 BigQuant 的 AIStudio/策略开发，新建Python策略代码或Notebook代码单元，将生成文件**全部内容**粘贴进去，不仅复制交易函数。
2. 运行默认入口 `performance = run_backtest()`。默认10万元是**模拟资金**，不要求真实入金；起始日期2024-01-01，结束日期为运行当天前一天。
3. 为固定实验区间，可改为 `performance = run_backtest("2024-01-01", "2026-10-13", 100000)`。检查基金行情权限、预热数据和成交日志，再观察净费后收益、最大回撤、Sharpe、费用和现金比例；不只看总收益。
4. 回测正常后，核对平台模拟部署入口是否支持新版`bigquant.bigtrader.run`，再部署，保持日线频率与相同参数。新版回测可运行不等于旧编辑器的“提交模拟”按钮已经兼容；不要改回`M.bigtrader.v30`以便提交。若当前编辑器只有单个函数槽，应使用AIStudio完整Python策略方式，不把整个启动脚本填入函数槽。
5. 首周检查跨日卖出/买入、拒单及部分成交、每日重启状态保持、基金佣金和调仓日。**不要绑定实盘账号**，代码没有实盘开户/认证功能，但平台可能允许另行将模拟策略信号绑定实盘。

本地验证命令：

```powershell
Push-Location backend
..\.venv\Scripts\python.exe manage.py test stockmarket --noinput
Pop-Location
```

### 已核对的官方接口

- [BigTrader API](https://bigquant.com/wiki/doc/nxDOuIdhm2)：`context.order`返回整数；负数表示发送失败，非负数**不代表成交**。当前日线Bar下单在下一Bar撮合。模拟盘每天重新初始化，`context.user_store.init_once`用于跨日保持状态。
- 启动入口使用新版 `bigquant.bigtrader.run`，市场 `Market.CN_FUND`、频率 `Frequency.DAILY`，与上述新版API保持一致。不要用旧教程的 `M.bigtrader.v30`：已收到平台实际运行证据，该模块启动 `bigtraderv1`，其 `StrategyContext` 没有 `user_store`，不能混用新旧接口。缺少持久化存储时明确报错，不创建普通字典冒充模拟盘跨日存储。
- [基金后复权日行情](https://bigquant.com/data/datasources/cn_fund_bar1d)：使用日期、基金代码、`close/high/low/volume/amount`，`amount`是真实成交额，历史价格是供应商后复权口径。

平台运行时延迟加载官方 `dai`、`bigquant.bigtrader`；不使用旧`bigmodule`启动入口，也不使用聚宽的 `jqdata/g/log`。普通本地Python无法直接执行平台回测，不需要为本地测试安装平台私有SDK，也不屏蔽Pylance诊断。

### 策略与执行约束

- 池：510300.SH、510500.SH、159915.SZ、588000.SH、512100.SH、512880.SH、512010.SH、512660.SH、515050.SH、518880.SH。
- 截至信号日查询600自然日历史，返回结果再剔除未来日期。数据需有至少120根K线和180自然日**可见历史跨度**；这是上市成熟度的代理，不是精确上市日期检查。近20日平均成交额需≥2000万元。
- 仅在收盘高于MA120且20/60日动量均为正、无压力/稀薄状态时参与排名。分数为 `(0.4*M20+0.6*M60)/max(20日年化波动, 3%)`，选前三。
- 压力状态：20日年化波动>45%，或>2倍 `max(60日年化波动,3%)`，或最新日跌幅≥4%，或日振幅>8%且量比>2；量比<0.3为稀薄状态。量比用最新成交量/此前20日平均成交量。不是订单簿或真实主动买卖订单流。
- 波动率倒数权重向等权收缩50%，单标的最多40%、总仓位最多95%；总暴露另受15%保守波动预算限制，剩余现金不重新分配。这不是熵优化求解器或协方差风险平价，也不保证未来真实波动。
- 每个ISO周第一个实际到达的日线收盘Bar产生信号、下一Bar开盘撮合，**不同于聚宽周一10:00调仓，也不同于旧版v30的提前调仓信号日**。周一假期时可在周二或随后首个交易日产生信号，回测起点在周中也会先产生一个初始化信号。周标记持久化，跨年使用ISO年和周，不要求新版引擎提供旧版`rebalance_period`属性。先减仓，后续日线确认持仓变化后才买入，换仓可能多空仓一个交易日。
- 状态用`user_store`保存，同日不重复委托，有未完成订单不加单；旧目标超过7自然日失效，新周信号替换旧目标。失败或部分成交未被当作成功，不在回调内阻塞等待。
- 退出不受3%净资产调仓阈值限制；其他微小调整跳过。每次买入用当前可用资金并本地预留已发买单的资金，按100份整手，预留5元最低佣金和0.5%预算缓冲。100元本金通常不足以执行该多ETF组合。
- 零成交量、无效价格不发单；可卖数量使用`avail_qty`，未来开盘停牌、涨跌停和成交量上限由平台撮合处理，不能保证成交。
- 双边佣金0.0003、最低5元、基金印花税0，百分比滑点0.002，单Bar成交量占比上限2.5%；这些只是研究假设，请核对平台费用与成交报告。
- 缺字段、重复日期、非法成交额及全部行情无效显式失败，不假装成功；当前持有ETF的历史缺失时停止调仓，不当成清仓信号。专用策略组合中出现池外持仓时报错，不擅自卖出其他股票。

研究灵感来自用户桌面模型生成的论文综述，不是已经核验的论文原文或论文复现。固定ETF池有选择/幸存者偏差，ETF间存在高度相关性。应与同池等权、沪深300买入持有、无过滤/无收缩版本在相同区间和费用下对比。

**验证边界**：63项本地回归测试通过，导出文件与源代码一致，Pylance无诊断。首次用户平台运行发现v30旧引擎与新版状态接口不兼容，已切换为官方新版`bigtrader.run`，并新增旧引擎拒绝和跨周/重启回归测试。在用户AIStudio环境执行了2026-10-12至2026-10-13、510300.SH、不下单的两天新版引擎检查：运行完成，实际上下文具有`user_store`及`init_once`、`logger`、`get_positions`、`get_available_cash`、`get_open_orders`、`get_last_price`，两个日线回调均在15:00触发。这只是平台接口/启动验证，尚未运行完整策略回测或创建模拟盘，没有策略收益结果；所有ETF行情权限、报价/复权口径和模拟部署入口仍需平台核验。出现错误时保留完整异常和版本信息，不通过忽略异常“跑通”。直接调用 `/opt/pyenv/versions/3.11.8/bin/python` 已指定解释器，不依赖 `pyenv shell` 的shell集成。

## 📋 接口概览

### 基本信息
- **Base URL**: `http://127.0.0.1:8002`
- **协议**: HTTP/1.1
- **数据格式**: JSON
- **字符编码**: UTF-8
- **CORS**: 支持跨域请求

### 认证方式
目前接口无需认证，生产环境建议添加 API Key 或 JWT Token 认证。

## 🔗 接口列表

### 1. 获取回测配置

获取系统可用的回测配置信息，包括可用股票、策略类型等。

**接口地址**
```http
GET /api/backtest/config/
```

**请求参数**
无

**请求示例**
```bash
curl -X GET "http://127.0.0.1:8002/api/backtest/config/" \
  -H "Accept: application/json"
```

**响应参数**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 响应状态：success/error |
| message | string | 响应消息 |
| data | object | 配置数据 |

**data 对象结构**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| available_stocks | array | 可用股票代码列表 |
| strategies | array | 可用策略列表 |
| default_balance | number | 默认初始资金 |
| commission_rate | number | 手续费率 |
| stamp_tax_rate | number | 印花税率 |
| min_commission | number | 最低手续费 |

**strategies 数组说明**

| 策略代码 | 策略名称 | 说明 |
|----------|----------|------|
| basic | 基础策略 | 基于价格突破的简单策略 |
| macd_golden | MACD金叉 | 基于MACD金叉买入信号 |
| macd_death | MACD死叉 | 基于MACD死叉卖出信号 |
| ma_bullish | 均线多头 | 基于均线多头排列 |
| ma_bearish | 均线空头 | 基于均线空头排列 |
| smart | 智能策略 | 多指标组合策略 |

**响应示例**
```json
{
  "status": "success",
  "message": "配置获取成功",
  "data": {
    "available_stocks": [
      "000001",
      "000002", 
      "000063",
      "000568"
    ],
    "strategies": [
      {
        "code": "basic",
        "name": "基础策略",
        "description": "基于价格突破的简单买卖策略"
      },
      {
        "code": "macd_golden",
        "name": "MACD金叉策略", 
        "description": "基于MACD指标金叉信号买入"
      },
      {
        "code": "smart",
        "name": "智能组合策略",
        "description": "多技术指标组合判断"
      }
    ],
    "default_balance": 100000,
    "commission_rate": 0.0003,
    "stamp_tax_rate": 0.001,
    "min_commission": 5.0
  }
}
```

**错误响应示例**
```json
{
  "status": "error",
  "message": "系统配置读取失败",
  "error_code": "CONFIG_READ_ERROR"
}
```

---

### 2. 执行回测

根据指定参数执行股票回测，返回详细的回测结果。

**接口地址**
```http
POST /api/backtest/run/
```

**请求头**
```
Content-Type: application/json
```

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| stocks | array | 是 | 股票代码列表 |
| strategy | string | 否 | 策略类型，默认 'smart' |
| start_date | string | 否 | 开始日期 YYYY-MM-DD |
| end_date | string | 否 | 结束日期 YYYY-MM-DD |
| initial_balance | number | 否 | 初始资金，默认 100000 |
| buy_strategy | string | 否 | 买入策略，默认与 strategy 相同 |
| sell_strategy | string | 否 | 卖出策略，默认与 strategy 相同 |
| price_threshold | number | 否 | 价格阈值 (basic策略) |
| macd_params | object | 否 | MACD参数配置 |
| ma_params | object | 否 | 均线参数配置 |

**macd_params 对象结构**

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| fast | number | 12 | 快速EMA周期 |
| slow | number | 26 | 慢速EMA周期 |
| signal | number | 9 | 信号线周期 |

**ma_params 对象结构**

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| short_ma | number | 5 | 短期均线周期 |
| long_ma | number | 20 | 长期均线周期 |

**请求示例**

```bash
curl -X POST "http://127.0.0.1:8002/api/backtest/run/" \
  -H "Content-Type: application/json" \
  -d '{
    "stocks": ["000001", "000002"],
    "strategy": "smart",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_balance": 100000,
    "macd_params": {
      "fast": 12,
      "slow": 26,
      "signal": 9
    },
    "ma_params": {
      "short_ma": 5,
      "long_ma": 20
    }
  }'
```

**简单请求示例**
```bash
curl -X POST "http://127.0.0.1:8002/api/backtest/run/" \
  -H "Content-Type: application/json" \
  -d '{
    "stocks": ["000001"],
    "strategy": "macd_golden"
  }'
```

**响应参数**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 响应状态：success/error |
| message | string | 响应消息 |
| data | object | 回测结果数据 |
| execution_time | number | 执行耗时(秒) |

**data 对象结构**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_summary | object | 账户总结 |
| trading_summary | object | 交易统计 |
| signal_history | array | 信号历史记录 |
| performance_metrics | object | 性能指标 |
| stock_details | object | 各股票详细结果 |

**account_summary 对象**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| initial_balance | number | 初始资金 |
| current_balance | number | 当前余额 |
| total_value | number | 总资产 |
| total_profit_loss | number | 总盈亏 |
| return_rate | number | 收益率(%) |
| positions | object | 当前持仓 |
| total_trades | number | 总交易数 |

**trading_summary 对象**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| total_trades | number | 总交易数 |
| buy_trades | number | 买入交易数 |
| sell_trades | number | 卖出交易数 |
| total_buy_amount | number | 总买入金额 |
| total_sell_amount | number | 总卖出金额 |
| total_commission | number | 总手续费 |
| total_stamp_tax | number | 总印花税 |
| total_fees | number | 总费用 |
| total_profit_loss | number | 总盈亏 |
| profit_rate | number | 盈利率(%) |
| win_rate | number | 胜率(%) |

**signal_history 数组元素**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| timestamp | string | 信号生成时间 |
| trade_date | string | 交易日期 |
| stock_code | string | 股票代码 |
| action | string | 操作类型：buy/sell |
| signal_type | string | 信号类型 |
| price | number | 交易价格 |
| shares | number | 交易股数 |
| total_amount | number | 交易金额 |
| commission | number | 手续费 |
| stamp_tax | number | 印花税 |
| total_cost | number | 总成本 |
| balance_after | number | 交易后余额 |
| position_shares | number | 持仓股数 |
| position_avg_price | number | 持仓均价 |
| profit_loss | number | 盈亏金额 (仅卖出) |

**performance_metrics 对象**

| 参数名 | 类型 | 说明 |
|--------|------|------|
| sharpe_ratio | number | 夏普比率 |
| max_drawdown | number | 最大回撤(%) |
| volatility | number | 波动率(%) |
| win_rate | number | 胜率(%) |
| profit_factor | number | 盈利因子 |
| avg_win | number | 平均盈利 |
| avg_loss | number | 平均亏损 |

**响应示例**
```json
{
  "status": "success",
  "message": "回测执行成功",
  "execution_time": 2.35,
  "data": {
    "account_summary": {
      "initial_balance": 100000,
      "current_balance": 95432.18,
      "total_value": 108750.50,
      "total_profit_loss": 8750.50,
      "return_rate": 8.75,
      "positions": {
        "000001": {
          "shares": 500,
          "avg_price": 26.64
        }
      },
      "total_trades": 12
    },
    "trading_summary": {
      "total_trades": 12,
      "buy_trades": 6,
      "sell_trades": 6,
      "total_buy_amount": 159875.20,
      "total_sell_amount": 164568.80,
      "total_commission": 156.45,
      "total_stamp_tax": 164.57,
      "total_fees": 321.02,
      "total_profit_loss": 4372.58,
      "profit_rate": 2.74,
      "win_rate": 66.67
    },
    "signal_history": [
      {
        "timestamp": "2025-08-04T10:30:15",
        "trade_date": "2023-03-15",
        "stock_code": "000001",
        "action": "buy",
        "signal_type": "macd_golden",
        "price": 18.39,
        "shares": 5400,
        "total_amount": 99306.00,
        "commission": 29.79,
        "stamp_tax": 0,
        "total_cost": 29.79,
        "balance_after": 70664.21,
        "position_shares": 5400,
        "position_avg_price": 18.39
      },
      {
        "timestamp": "2025-08-04T10:30:15", 
        "trade_date": "2023-04-20",
        "stock_code": "000001",
        "action": "sell",
        "signal_type": "macd_death",
        "price": 20.15,
        "shares": 5400,
        "total_amount": 108810.00,
        "commission": 32.64,
        "stamp_tax": 108.81,
        "total_cost": 141.45,
        "balance_after": 179332.76,
        "position_shares": 0,
        "position_avg_price": 0,
        "profit_loss": 9362.76
      }
    ],
    "performance_metrics": {
      "sharpe_ratio": 1.45,
      "max_drawdown": -8.2,
      "volatility": 15.6,
      "win_rate": 66.67,
      "profit_factor": 1.8,
      "avg_win": 2850.45,
      "avg_loss": -1580.22
    },
    "stock_details": {
      "000001": {
        "trades": 4,
        "profit_loss": 3250.80,
        "return_rate": 5.2
      },
      "000002": {
        "trades": 8,
        "profit_loss": 1121.78,
        "return_rate": 2.1
      }
    }
  }
}
```

**错误响应示例**

```json
{
  "status": "error",
  "message": "回测执行失败",
  "error_code": "BACKTEST_EXECUTION_ERROR",
  "details": {
    "error_type": "DATA_NOT_FOUND",
    "description": "股票代码 000999 的数据文件不存在",
    "suggestion": "请检查股票代码是否正确，或联系管理员添加数据文件"
  }
}
```

---

## 📊 错误码说明

### 通用错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|------------|------|
| SUCCESS | 200 | 请求成功 |
| INVALID_REQUEST | 400 | 请求参数错误 |
| UNAUTHORIZED | 401 | 未授权访问 |
| FORBIDDEN | 403 | 禁止访问 |
| NOT_FOUND | 404 | 资源不存在 |
| METHOD_NOT_ALLOWED | 405 | 请求方法不被允许 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

### 业务错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| CONFIG_READ_ERROR | 配置读取失败 | 检查系统配置文件 |
| DATA_NOT_FOUND | 数据文件不存在 | 检查股票代码或添加数据文件 |
| INVALID_STOCK_CODE | 无效的股票代码 | 使用正确的6位股票代码 |
| INVALID_DATE_RANGE | 无效的日期范围 | 确保开始日期小于结束日期 |
| INSUFFICIENT_DATA | 数据不足 | 确保数据包含足够的历史记录 |
| STRATEGY_NOT_FOUND | 策略不存在 | 使用支持的策略类型 |
| CALCULATION_ERROR | 计算过程错误 | 检查数据格式和计算参数 |
| BACKTEST_EXECUTION_ERROR | 回测执行失败 | 检查参数设置和数据完整性 |

---

## 🔍 调试指南

### 1. 接口测试工具

**使用 curl 测试**
```bash
# 测试配置接口
curl -v -X GET "http://127.0.0.1:8002/api/backtest/config/"

# 测试回测接口
curl -v -X POST "http://127.0.0.1:8002/api/backtest/run/" \
  -H "Content-Type: application/json" \
  -d '{"stocks": ["000001"], "strategy": "basic"}'
```

**使用 Python requests 测试**
```python
import requests
import json

# 配置接口
response = requests.get('http://127.0.0.1:8002/api/backtest/config/')
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# 回测接口
data = {
    "stocks": ["000001"],
    "strategy": "smart",
    "initial_balance": 100000
}
response = requests.post(
    'http://127.0.0.1:8002/api/backtest/run/',
    headers={'Content-Type': 'application/json'},
    data=json.dumps(data)
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

**使用 Postman 测试**

1. **获取配置**
   - Method: GET
   - URL: http://127.0.0.1:8002/api/backtest/config/
   - Headers: Accept: application/json

2. **执行回测**
   - Method: POST
   - URL: http://127.0.0.1:8002/api/backtest/run/
   - Headers: Content-Type: application/json
   - Body (raw JSON):
     ```json
     {
       "stocks": ["000001"],
       "strategy": "smart"
     }
     ```

### 2. 常见问题排查

**问题1: 服务器无响应**
```bash
# 检查服务器是否启动
curl -I http://127.0.0.1:8002/

# 检查端口是否被占用
lsof -i :8002

# 检查 Django 进程
ps aux | grep python
```

**问题2: CORS 错误**
```
错误信息: Access to fetch at 'http://127.0.0.1:8002/api/...' from origin 'http://127.0.0.1:5500' has been blocked by CORS policy

解决方案:
1. 确认 Django settings.py 中 CORS 配置正确
2. 检查 CORS_ALLOWED_ORIGINS 包含前端域名
3. 确认 django-cors-headers 已安装并配置
```

**问题3: 数据文件缺失**
```
错误信息: 股票代码 000001 的数据文件不存在

解决方案:
1. 检查 backend/ 目录下是否有对应的 CSV 文件
2. 确认文件名格式: XXXXXX_10years.csv
3. 验证文件内容格式是否正确
```

**问题4: JSON 解析错误**
```
错误信息: JSON decode error

解决方案:
1. 确认请求头包含 Content-Type: application/json
2. 检查 JSON 格式是否正确
3. 验证参数类型和字段名
```

### 3. 调试模式

**启用 Django 调试模式**
```python
# settings.py
DEBUG = True

# 查看详细错误信息
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

**添加调试输出**
```python
# backtest_integration.py
import logging
logger = logging.getLogger(__name__)

def run_backtest_api(request):
    logger.debug(f"收到回测请求: {request.body}")
    
    try:
        data = json.loads(request.body)
        logger.debug(f"解析后的参数: {data}")
        
        result = run_backtest(data)
        logger.debug(f"回测结果: {result}")
        
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"回测执行异常: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
```

---

## 📝 版本更新记录

### v1.0.0 (2025-08-04)
- ✅ 初始版本发布
- ✅ 实现基础配置和回测接口
- ✅ 支持多种交易策略
- ✅ 完整的交易记录和统计

### 计划更新

#### v1.1.0 (计划中)
- 🔄 添加实时数据接口
- 🔄 支持自定义时间范围回测
- 🔄 增加更多技术指标策略

#### v1.2.0 (计划中)  
- 🔄 添加用户认证和权限管理
- 🔄 支持批量回测和任务队列
- 🔄 增加回测结果缓存

---

## 📞 技术支持

### 联系方式
- **技术文档**: [项目 README.md](./README.md)
- **问题反馈**: GitHub Issues
- **API 更新**: 关注项目 Release

### 最佳实践
1. **请求频率**: 建议每秒不超过 10 次请求
2. **数据缓存**: 配置信息建议缓存 1 小时
3. **错误处理**: 实现完整的错误处理和重试机制
4. **参数验证**: 前端应验证参数格式和范围

### 性能优化建议
1. **并发请求**: 避免同时发起多个回测请求
2. **数据量**: 单次回测建议不超过 10 只股票
3. **时间范围**: 回测时间跨度建议不超过 5 年
4. **网络超时**: 设置合理的请求超时时间 (30-60秒)

---

## 上证50历史前30：差分与LSTM离线研究

本研究与Web接口、ETF轮动及实盘执行分离，不会启动交易或下单。
来源：<https://arxiv.org/abs/2505.19243>。实现一阶对数差分对照和
De Prado分数阶差分 + LSTM；不是论文完整复现，也没有实现R的
ARFIMA/ARTFIMA参数估计。温和化差分递推仅有数学核心及测试。

- 核心：`backend/research/fractional_forecast.py`。
- 训练：`backend/research/fractional_lstm.py`。
- 低频下载：`backend/tools/download_fractional_prices.py`。
- 离线运行：`backend/tools/run_fractional_research.py`。
- 可选研究依赖：`backend/requirements-research.txt`；没有添加到Web依赖。

### 历史数据约束

指数是**上证50（000016.SHI）**，不是中证A50或A500。按信号日前最近
完整权重快照取前30，不能用今天的成分倒推过去。权重CSV必须包含：

```text
date,instrument,member_code,weight
2024-03-29,000016.SHI,600000.SH,2.0
```

示例只展示一行格式，不是有效权重数据；每个快照需完整50只、不重复、
正权重且总和为100或1。默认拒绝超过35天的陈旧快照；缺失或无权限
必须补授权数据，不能回退到当前成分。供应商快照日期是否对应实际可获知日期，
仍需由数据使用者核实，程序不能凭日期证明这一点。

行情CSV包含`date,instrument,open,high,low,close,volume`，股票代码如
`600000.SH`。使用后复权日线，且训练和验证历史不能只提供回测期间。
AKShare可获取日线，但不自动解决完整历史权重与发布时间问题。

下载器按目标回测区间的历史前30并集串行下载，每次调用起点间隔默认
至少6秒（可调但不得低于3秒），无并发、无自动重试、不更换代理或绕过封禁。
失败立即停止；恢复时使用校验过SHA256的逐股票缓存，不重新下载。
AKShare内部可能发起不止一次HTTP请求，因此这不保证供应商永远不触发限流；
遇到限流应停止并等待，不能反复启动。后复权成交量单位按来源记录为“手”。
缓存、下载时间、实际覆盖日期、来源版本、调整方式及文件哈希共同保存。
仅全部成功后输出合并行情及同名`.metadata.json`；发现残缺缓存会明确失败。

### 运行方式

在`backend`目录运行，先安装可选研究依赖到独立研究环境。
不要在Web环境盲目升级依赖。Windows当前继承Conda的环境已验证可用
`MKL_THREADING_LAYER=SEQUENTIAL`避免PyTorch与MKL的重复OpenMP初始化；
这是进程级配置，不使用不安全的`KMP_DUPLICATE_LIB_OK`。

```powershell
$env:MKL_THREADING_LAYER='SEQUENTIAL'
python -m tools.download_fractional_prices --weights E:\data\sse50_weights.csv --cache E:\data\akshare_cache --output E:\data\prices.csv --interval 6
python -m tools.run_fractional_research --prices E:\data\prices.csv --weights E:\data\sse50_weights.csv --metadata E:\data\prices.metadata.json --output E:\data\fractional_result.json
```

目录需事先存在。输出文件不覆盖已有实验。非下载器提供的行情也需metadata JSON，
包含真实`source`、`adjustment: "hfq"`及`prices_sha256`、`weights_sha256`；
不得通过改声明掩盖不同复权方式或未知来源。

### 当前成分随机30只：探索模式

如暂时没有历史权重，可显式选择当前上证50随机30只。随机种子默认42，
先保存完整50只来源名单与选出的30只；重启复用该名单，不重新抽样。
此模式**存在幸存者偏差和成分选择前视偏差**，不能称为历史权重前30回测。
程序通过独立JSON和结果标记区分两种模式，不伪造历史权重。

```powershell
python -m tools.download_fractional_prices --fixed-universe E:\data\random30.json --create-random-universe --cache E:\data\akshare_cache --output E:\data\prices.csv --interval 15
python -m tools.run_fractional_research --fixed-universe E:\data\random30.json --prices E:\data\prices.csv --metadata E:\data\prices.metadata.json --output E:\data\random30_result.json
```

仅首次需要`--create-random-universe`；也可保留该参数复用已有JSON。
下载仍从2014年开始以满足训练；上市较晚的股票可能没有足够训练历史，
不应为追求收益而重新挑选股票。下载失败即停止，无限流重试。

### Yahoo行情备选

下载器增加`--source yahoo`，沿用保存的随机名单，上海代码转换为`.SS`。
必须用独立缓存和合并输出，不混入AKShare行情：

```powershell
python -m tools.download_fractional_prices --source yahoo --fixed-universe E:\data\random30.json --cache E:\data\yahoo_cache --output E:\data\yahoo_prices.csv --interval 30
python -m tools.run_fractional_research --fixed-universe E:\data\random30.json --prices E:\data\yahoo_prices.csv --metadata E:\data\yahoo_prices.metadata.json --output E:\data\yahoo_result.json
```

Yahoo通过日线chart接口一次请求一只股票，设连接/读取超时10/60秒，
不自动重试。将每行`Adj Close / Close`因子统一乘到原始OHLC，
记录为`yahoo_adjclose_ratio`，**不是AKShare的hfq**；成交量保留来源股数。
复权数据按下载时的供应商口径计算，不是逐历史时点可用的复权快照。
回测接受此独立复权模式并保留来源信息，仍属连续复权价格研究，非真实撮合。
缺失日线或复权值、接口错误均停止，不能补零或静默删除。
Yahoo也可能限流；若失败保留缓存并停止，不更换代理绕过限流。

Yahoo三一重工两行数据已于2026-10-14使用腾讯未复权日线独立核验：
2019-01-07开盘7.87修正为8.12；2020-09-08开盘22.56修正为22.60、
最高23.36修正为23.38、成交量72894073修正为74171473股。
仅当Yahoo原行精确匹配已核验值（浮点容差0.00001）时应用；
源行变化必须重新核验。修正在复权前进行，收盘未改，保留Yahoo复权因子。
每股票缓存元数据的`verified_corrections`包含原值、替换值、腾讯原始行、
查询地址/参数和核验日期；合并元数据与研究结果亦保留记录。
这不是通用自动清洗，不对其他异常夹紧价格、填零或删除数据。

Yahoo下载可显式增加`--quarantine-invalid`，先保存原始响应（`.raw.json`），
将价格校验异常记录为`.quarantine.json`，继续采集其他股票。恢复时复用原始
响应，不重复请求异常股票。隔离记录包含原始响应路径、SHA256和异常原因；
原始响应仅用于核验，不能用于训练。若任一股票仍被隔离，最终明确失败且不生成
合并行情，不重抽股票、不按剩余股票偷偷回测。网络错误、HTTP限流仍立即停止。

### 切分、模型及判断边界

- 训练2014-01-01至2022-03-31；验证2022-04-01至2024-03-31；
  样本外2024-04-01至2026-04-30。日期可通过显式CLI参数修改。
- 序列长度20，ADF网格步长0.05、5%检验、AIC选择滞后，
  固定宽度权重阈值0.001、上限1000。这些是迁移研究假设，不是论文完整配置。
- 每股票、每分支独立CPU单层LSTM；hidden16/32、学习率0.001、batch64、
  默认30 epochs；仅验证损失选择试验和epoch，不用测试收益挑模型。
  标签按次日日期切分，scaler与差分阶数只用训练期。
- 特征为因果差分、SMA5/10/20、RSI9/14/21、Bollinger10/2、
  MACD12/26/9；RSI使用滚动均值、布林方差ddof0、EMA adjust=False。
  成本带内保留原持仓，是本实现明确的交易约定。
- 任一需要交易的历史成员缺价、模型历史不足、ADF无合格阶数、
  预测覆盖不足或持仓无法交易都会明确停止，不以空仓伪装成功。
- 输出两个研究组合、同池前30固定槽位基线、逐日净值/交易/选股、
  模型参数/scaler/差分权重/数据哈希。默认资金100000、最多95%仓位，
  每股票一个1/30槽位，空槽不分给其他股票。
- 默认买成本0.05%、卖成本0.1%、信号带0.2%，均为研究假设。
  前日收盘信号最早次日开盘执行。最后持仓按收盘估值、不强制清仓。

**这是后复权价格、连续份额的研究模拟，不是A股真实撮合。**
未处理100股整数手、最低佣金、T+1、涨跌停、公司行动现金/股份记账及
税费历史变动，不能拿研究收益直接指导实盘或100元账户。停牌等情况需
交给平台真实规则验证。即使研究效果好，也需再做BigQuant股票回测，
当前没有宣称该LSTM策略已部署到BigQuant。

当前功能证据来自合成数据训练、因果/无泄漏/缓存与执行测试，不代表市场盈利。
历史权重数据仍待补齐；尚未生成2024-2026真实股票收益。

**文档版本**: v1.0.0  
**最后更新**: 2025-08-04  
**维护者**: 系统集成团队
