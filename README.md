# 股票交易系统 - 项目文档

## 📋 项目概述

这是一个基于 Django + 前端 + 量化回测的完整股票交易系统，集成了信号生成、回测分析、API 服务等功能模块。

### 🎯 主要功能
- **交易信号生成**: 基于技术指标的买入/卖出信号
- **量化回测**: 完整的交易回测系统，支持策略验证
- **REST API**: 提供 HTTP API 接口供前端调用
- **数据管理**: 股票数据获取、存储和处理
- **风险控制**: 手续费、印花税、资金管理等

## 🏗️ 项目结构

```
stock-main/
├── backend/                    # 后端核心代码
│   ├── myproject/             # Django 项目配置
│   │   ├── __init__.py
│   │   ├── settings.py        # Django 设置
│   │   ├── urls.py           # URL 路由
│   │   └── wsgi.py           # WSGI 配置
│   ├── indicators/            # 技术指标库
│   │   ├── ma.py             # 移动平均线
│   │   ├── macd.py           # MACD 指标
│   │   ├── kdj.py            # KDJ 指标
│   │   └── ...               # 其他技术指标
│   ├── 西蒙斯量化回测系统3/       # XMS 量化回测核心
│   │   ├── xms_quant_backtrader.py  # 回测引擎
│   │   └── ...               # 回测相关文件
│   ├── signal_library.py      # 交易信号库 (核心)
│   ├── backtest_integration.py # 回测集成模块
│   ├── filter_stocks.py       # 股票筛选模块
│   ├── tushare_huoqu.py      # 数据获取模块
│   ├── manage.py             # Django 管理脚本
│   ├── start_server.py       # 服务器启动脚本
│   └── *.csv                 # 股票历史数据
├── frontend/                  # 前端代码
│   ├── src/                  # 源代码
│   ├── index.html            # 主页面
│   ├── backtest.html         # 回测页面
│   ├── stock-analysis.html   # 股票分析页面
│   └── package.json          # 前端依赖
└── README.md                 # 项目文档
```

## 🔧 核心模块详解

### 1. 交易信号库 (signal_library.py)

这是系统的核心模块，负责生成交易信号并执行模拟交易。

#### 主要功能:
- **信号生成**: 支持多种策略 (基础、MACD、均线、智能组合)
- **交易执行**: 模拟买入/卖出操作，包含费用计算
- **资金管理**: 账户余额、持仓管理
- **历史记录**: 完整的交易记录和统计

#### 关键类:
```python
class SignalLibrary:
    def __init__(self, initial_balance: float = 100000.0)
    def generate_buy_signal(stock_code, df, signal_type='basic')
    def generate_sell_signal(stock_code, df, signal_type='basic') 
    def execute_buy_trade(stock_code, price, shares, trade_date)
    def execute_sell_trade(stock_code, price, shares, trade_date)
```

#### 支持的信号类型:
- `basic`: 基于价格突破
- `macd_golden/death`: MACD 金叉/死叉
- `ma_bullish/bearish`: 均线多头/空头
- `smart`: 多指标组合策略

### 2. 回测集成模块 (backtest_integration.py)

提供 API 接口，连接前端和后端回测功能。

#### API 端点:
- `GET /api/backtest/config/` - 获取回测配置
- `POST /api/backtest/run/` - 执行回测

#### 关键函数:
```python
def run_backtest_api(request)      # 执行回测的 API 接口
def get_backtest_config_api(request) # 获取配置的 API 接口
```

### 3. 技术指标库 (indicators/)

包含各种技术分析指标的实现:

- **移动平均线 (MA)**: 简单移动平均、指数移动平均
- **MACD**: 指数平滑移动平均收敛散度
- **KDJ**: 随机指标
- **其他指标**: RSI, BOLL, CCI 等 50+ 技术指标

### 4. 数据管理模块

- **tushare_huoqu.py**: 从 Tushare API 获取股票数据
- **filter_stocks.py**: 股票筛选和过滤
- **CSV 数据文件**: 存储历史价格数据

## 🚀 快速开始

### 环境要求

```bash
Python 3.8+
Django 5.2.4
pandas
numpy
requests
其他依赖见 requirements.txt
```

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd stock-main
```

2. **安装依赖**
```bash
cd backend
pip install -r requirements.txt
```

3. **配置数据库**
```bash
# 在 myproject/settings.py 中配置数据库
python manage.py migrate
```

4. **启动服务器**
```bash
python start_server.py
# 或者
python manage.py runserver 8002
```

5. **访问服务**
- API 服务: http://127.0.0.1:8002
- 前端页面: 打开 frontend/index.html

### 快速测试

```bash
# 测试信号库
python signal_library.py

# 测试回测功能
python test_complete_workflow.py

# 测试 API 接口
curl http://127.0.0.1:8002/api/backtest/config/
```

## 📊 使用示例

### 1. 生成交易信号

```python
from signal_library import SignalLibrary
import pandas as pd

# 创建信号库实例
signal_lib = SignalLibrary(initial_balance=100000)

# 加载股票数据
df = pd.read_csv('000001_10years.csv')

# 生成买入信号
buy_signals = signal_lib.generate_buy_signal('000001', df, 'macd_golden')

# 生成卖出信号  
sell_signals = signal_lib.generate_sell_signal('000001', df, 'macd_death')

# 查看信号历史
history = signal_lib.get_signal_history('000001')
print(f"生成了 {len(history)} 个交易信号")
```

### 2. 执行回测

```python
from backtest_integration import run_backtest

# 配置回测参数
config = {
    'stocks': ['000001', '000002'],
    'start_date': '2023-01-01',
    'end_date': '2023-12-31',
    'initial_balance': 100000,
    'strategy': 'smart'
}

# 执行回测
result = run_backtest(config)
print(f"回测收益率: {result['return_rate']:.2f}%")
```

### 3. API 调用

```bash
# 获取回测配置
curl -X GET "http://127.0.0.1:8002/api/backtest/config/"

# 执行回测
curl -X POST "http://127.0.0.1:8002/api/backtest/run/" \
  -H "Content-Type: application/json" \
  -d '{"stocks": ["000001"], "strategy": "smart"}'
```

## 🔍 交易详情说明

系统会记录每笔交易的详细信息:

### 买入交易
- **交易时间**: 具体的交易日期和时间
- **股票数量**: 实际买入的股票数量
- **交易价格**: 买入时的股票价格
- **交易金额**: 总交易金额 (价格 × 数量)
- **手续费**: 0.03% 佣金费用 (最低5元)
- **剩余资金**: 交易后的账户余额

### 卖出交易
- **交易时间**: 具体的交易日期和时间
- **股票数量**: 实际卖出的股票数量
- **交易价格**: 卖出时的股票价格
- **交易金额**: 总交易金额 (价格 × 数量)
- **手续费**: 0.03% 佣金费用
- **印花税**: 0.1% 印花税 (仅卖出收取)
- **净收入**: 扣除所有费用后的实际收入
- **盈亏情况**: 相对于买入成本的盈亏金额

### 费用计算
- **佣金**: 交易金额 × 0.03% (最低5元)
- **印花税**: 卖出金额 × 0.1% (仅卖出时收取)
- **总费用**: 佣金 + 印花税

## 📈 性能监控

### 账户摘要
```python
summary = signal_lib.get_account_summary()
print(f"总资产: ¥{summary['total_value']:,.2f}")
print(f"收益率: {summary['return_rate']:.2f}%")
```

### 交易统计
```python
trading_summary = signal_lib.get_trading_summary('000001')
print(f"总交易: {trading_summary['total_trades']}笔")
print(f"盈利率: {trading_summary['profit_rate']:.2f}%")
```

## 🛠️ 开发指南

### 添加新的技术指标

1. 在 `indicators/` 目录下创建新文件
2. 实现指标计算函数
3. 在 `signal_library.py` 中导入并使用

### 添加新的交易策略

1. 在 `SignalLibrary` 类中添加新的信号方法
2. 更新 `generate_buy_signal` 和 `generate_sell_signal` 方法
3. 添加相应的测试用例

### 扩展 API 接口

1. 在 `backtest_integration.py` 中添加新的视图函数
2. 在 `myproject/urls.py` 中添加 URL 路由
3. 更新前端调用代码

## 🔧 配置说明

### Django 设置 (myproject/settings.py)

```python
# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'stockdb',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# CORS 配置
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]
```

### 信号库配置

```python
# 初始资金配置
signal_lib = SignalLibrary(initial_balance=100000.0)

# 费用配置
signal_lib.commission_rate = 0.0003    # 手续费率 0.03%
signal_lib.min_commission = 5.0        # 最低手续费 5元
signal_lib.stamp_tax_rate = 0.001      # 印花税率 0.1%
```

## 🚨 故障排除

### 常见问题

1. **Django 配置错误**
   ```
   错误: settings are not configured
   解决: 确保 DJANGO_SETTINGS_MODULE 环境变量正确设置
   ```

2. **数据库连接失败**
   ```
   错误: Access denied for user
   解决: 检查数据库用户名、密码和权限
   ```

3. **技术指标计算错误**
   ```
   错误: 数据不足或格式错误
   解决: 确保数据包含必要的列 (OPEN, HIGH, LOW, CLOSE, VOLUME)
   ```

4. **API 请求失败**
   ```
   错误: CORS 策略阻止
   解决: 检查 CORS 配置和允许的域名
   ```

### 调试技巧

1. **查看信号历史**
   ```python
   history = signal_lib.get_signal_history()
   for record in history[-5:]:
       print(record)
   ```

2. **检查账户状态**
   ```python
   summary = signal_lib.get_account_summary()
   print(summary)
   ```

3. **验证 API 响应**
   ```bash
   curl -v http://127.0.0.1:8002/api/backtest/config/
   ```

## 📝 更新日志

### v1.0.0 (2025-08-04)
- ✅ 完成交易信号库核心功能
- ✅ 集成 Django API 服务
- ✅ 实现详细交易记录和费用计算
- ✅ 支持多种技术指标策略
- ✅ 完成前后端 API 对接

### 待开发功能
- 🔄 实时数据接入
- 🔄 更多技术指标支持
- 🔄 策略优化和参数调节
- 🔄 风险控制模块增强
- 🔄 可视化报表功能

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目维护者: 系统集成团队
- 技术支持: 请通过 Issues 提交问题
- 文档更新: 欢迎提交文档改进建议

---

**注意**: 本系统仅用于学习和研究目的，实际投资请谨慎操作并遵守相关法律法规。
