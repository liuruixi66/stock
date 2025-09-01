# 股票量化系统前后端API连接文档

## 系统架构概述

本系统采用前后端分离的架构：
- **后端**: Django 框架，运行在 `http://localhost:8002`
- **前端**: Vue 3 + Vite，运行在 `http://localhost:3000`

## 核心连接文件

### 后端核心文件

#### 1. URL路由配置
- **主路由**: `/backend/myproject/urls.py`
- **应用路由**: `/backend/stockmarket/urls.py`

#### 2. 视图层
- **主视图文件**: `/backend/stockmarket/views.py`
- **回测集成**: `/backend/backtest_integration.py`

#### 3. 数据模型
- **模型定义**: `/backend/stockmarket/models.py`

### 前端核心文件

#### 1. API接口层
- **主API文件**: `/frontend/src/api/stock.ts`
- **Axios配置**: `/frontend/src/main.js`

#### 2. 路由配置
- **Vue路由**: `/frontend/src/router/index.ts`

#### 3. 组件页面
- **表格组件**: `/frontend/src/components/BaseTable.vue`
- **各种数据页面**: `/frontend/src/views/tables/`

## API端点映射

### 1. 股票基础数据API

| 功能 | 前端路由 | 后端API端点 | 视图函数 | 说明 |
|------|----------|-------------|----------|------|
| 每日股票数据 | `/tables/stock-spot` | `/api/stock-spot/` | `get_stock_spot` | 获取股票每日行情数据 |
| 股票资金流向 | `/tables/stock-fund-flow` | `/api/stock-fund-flow/` | `get_stock_fund_flow` | 获取个股资金流向数据 |
| 股票分红配送 | `/tables/stock-bonus` | `/api/stock-bonus/` | `get_stock_bonus` | 获取股票分红配送信息 |
| 龙虎榜数据 | `/tables/stock-top` | `/api/stock-top/` | `get_stock_top` | 获取龙虎榜交易数据 |
| 大宗交易 | `/tables/stock-blocktrade` | `/api/stock-blocktrade/` | `get_stock_blocktrade` | 获取大宗交易数据 |
| 行业资金流向 | `/tables/industry-fund-flow` | `/api/industry-fund-flow/` | `get_stock_fund_flow_industry` | 获取行业资金流向 |
| 概念资金流向 | `/tables/concept-fund-flow` | `/api/concept-fund-flow/` | `get_stock_fund_flow_concept` | 获取概念板块资金流向 |
| ETF数据 | `/tables/etf-spot` | `/api/etf-spot/` | `get_etf_spot` | 获取ETF基金数据 |

### 2. 技术指标API

| 功能 | 前端API调用 | 后端API端点 | 视图函数 | 说明 |
|------|-------------|-------------|----------|------|
| MACD计算 | `indicatorApi.calculateMacd()` | `/api/calculate-macd/` | `calculate_macd` | 计算MACD技术指标 |
| 市场均线 | `indicatorApi.getMarketMa()` | `/api/market/ma/` | `get_market_ma` | 获取市场均线数据 |
| KDJ指标 | `indicatorApi.getMarketKdj()` | `/api/market/kdj/` | `get_market_kdj` | 计算KDJ技术指标 |

### 3. 股票筛选与回测API

| 功能 | 前端API调用 | 后端API端点 | 视图函数 | 说明 |
|------|-------------|-------------|----------|------|
| 股票筛选 | `stockApi.filterStocks()` | `/api/filter-stocks/` | `filter_stocks_api` | 根据技术指标筛选股票 |
| 运行回测 | `backtestApi.runBacktest()` | `/api/run-backtest/` | `run_backtest_api` | 执行量化回测 |
| 回测配置 | `backtestApi.getBacktestConfig()` | `/api/backtest-config/` | `get_backtest_config_api` | 获取回测参数配置 |
| 交易明细 | - | `/api/transaction-details/` | `get_transaction_details_api` | 获取回测交易明细 |
| 收益概览 | - | `/api/earnings-overview/` | `get_earnings_overview_api` | 获取回测收益统计 |

### 4. 实时数据API

| 功能 | 前端API调用 | 后端API端点 | 视图函数 | 说明 |
|------|-------------|-------------|----------|------|
| 实时股票数据 | `stockApi.getStockRealtime()` | `/api/stock-realtime/` | `get_stock_realtime` | 获取实时股票行情 |
| 热门策略 | - | `/api/hot-strategy/` | `get_hot_strategy` | 获取热门量化策略 |

## 网络配置

### 1. 前端代理配置 (`vite.config.js`)

```javascript
export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8002',  // 后端服务地址
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
```

### 2. 前端Axios配置 (`main.js`)

```javascript
import axios from 'axios'

// 配置axios默认值
axios.defaults.baseURL = 'http://localhost:8002'
axios.defaults.headers.common['Content-Type'] = 'application/json'
```

### 3. 环境变量配置 (`.env.development`)

```bash
# API基础URL
VITE_API_BASE_URL=http://localhost:8002/api

# 后端服务地址
VITE_BACKEND_URL=http://localhost:8002
```

### 4. 后端CORS配置 (`settings.py`)

```python
# CORS设置
CORS_ALLOW_ALL_ORIGINS = True  # 开发环境下允许所有源
CORS_ALLOW_CREDENTIALS = True

# 允许的请求方法
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']

# 允许的请求头
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type',
    'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
]
```


## 数据流向图

```
前端组件 → API调用 → Vite代理 → Django视图 → 数据库查询 → 返回JSON → 前端渲染
  ↓           ↓         ↓          ↓           ↓            ↓         ↓
StockSpot.vue → stockApi → /api/stock-spot/ → get_stock_spot → MySQL → response → 表格显示
```

---

## 回测完整流程说明

### 1. 前端发起回测请求

- 用户在前端页面（如“回测”界面）填写参数（如股票池、起止日期、资金等），点击“开始回测”。
- 前端通过 `backtestApi.runBacktest(data)` 方法发起 POST 请求，data 为回测参数。

```typescript
runBacktest: (data: any) => api.post('/backtest/run/', data)
```

### 2. 请求通过Vite代理转发

- 前端请求 `/api/backtest/run/` 实际被 Vite 代理转发到后端 Django 的 `/api/backtest/run/`。

### 3. 后端接收并处理请求

- Django 路由 `myproject/urls.py` 中 `/api/backtest/run/` 路径指向 `run_backtest_api` 视图函数（通常在 `backtest_integration.py`）。
- 该函数解析前端传来的参数，调用回测引擎（如 pandas、backtrader、自研逻辑等）进行回测计算。

### 4. 回测结果生成

- 后端回测逻辑会读取历史数据、模拟买卖、计算收益、风险等指标，生成回测报告和明细。
- 结果通常以 JSON 格式返回给前端，包括收益曲线、交易明细、统计指标等。

### 5. 前端展示回测结果

- 前端收到回测结果后，渲染到页面上（如图表、表格、统计卡片等），供用户分析。

### 回测流程图

```
用户操作前端页面
  ↓
前端调用 backtestApi.runBacktest(data)
  ↓
POST /api/backtest/run/（Vite代理转发）
  ↓
Django 路由到 run_backtest_api
  ↓
后端执行回测逻辑
  ↓
返回回测结果（JSON）
  ↓
前端展示回测报告
```

---

## 典型API前后端交互详细举例

### 以“股票现货数据”为例

#### 前端如何请求数据

- 前端页面如 `StockSpot.vue` 通过 `stockApi.getStockSpot()` 方法获取数据。
- 该方法定义在 `frontend/src/api/stock.ts`：

```typescript
getStockSpot: (params?: any) => api.get('/stock-spot/', { params }),
```

- 实际请求的URL为 `/api/stock-spot/`，参数如 `date`、`keyword` 由前端传递。

#### 前端调用流程

1. 用户在页面选择日期或输入关键词，触发查询。
2. 组件调用 `stockApi.getStockSpot({ date, keyword })`。
3. 通过 axios 发送 GET 请求到 `/api/stock-spot/`。

#### Vite 代理

- `vite.config.js` 配置了 `/api` 代理到 `http://localhost:8002`，即Django后端。

#### 后端如何处理

- Django 路由 `myproject/urls.py` 和 `stockmarket/urls.py` 都有 `/api/stock-spot/` 路径，指向 `stockmarket/views.py` 的 `get_stock_spot` 函数。
- 该函数从数据库查询数据，并返回 JSON 响应。

```python
@require_http_methods(["GET"])
def get_stock_spot(request):
   # ...解析参数，查询数据库...
   return JsonResponse({'status': 'success', 'data': list(stocks)})
```

---

### 其它典型API交互举例

| 前端API方法                      | 请求URL                | 后端视图函数                | 说明                   |
|----------------------------------|------------------------|-----------------------------|------------------------|
| stockApi.getStockFundFlow        | /api/stock-fund-flow/  | get_stock_fund_flow         | 获取股票资金流向        |
| stockApi.getStockBonus           | /api/stock-bonus/      | get_stock_bonus             | 获取分红数据           |
| stockApi.filterStocks            | /api/filter_stocks/    | filter_stocks_api           | POST方式，股票筛选     |
| indicatorApi.calculateMacd       | /api/calculate-macd/   | calculate_macd              | POST方式，计算MACD     |
| backtestApi.runBacktest          | /api/backtest/run/     | run_backtest_api            | POST方式，运行回测     |

---

## API是后端提供，前端调用

API（接口）是后端（Django）实现和提供的，前端只是“调用”这些API。

- 后端实现所有API接口（如 /api/stock-spot/），负责处理请求、查询数据库、返回数据。
- 前端通过 axios 或 fetch 等方式“请求”这些API，把数据拿来展示。
- 前端的 `src/api/stock.ts` 只是把后端API的地址和调用方式封装成函数，方便页面调用，本质上数据和接口都来自后端。


## 关键组件详解

### 1. BaseTable.vue 通用表格组件

这是前端的核心表格组件，所有数据页面都使用它：

```vue
<BaseTable
    :api-url="'/api/stock-spot/'"        <!-- 后端API端点 -->
    :column-types="columnTypes"           <!-- 列类型定义 -->
    :formatters="formatters"              <!-- 数据格式化器 -->
    :query-params="queryParams"           <!-- 查询参数 -->
    ref="baseTableRef"
/>
```

### 2. 统一的API请求流程

1. **前端发起请求**: 通过 `stockApi.getStockSpot()` 等方法
2. **Vite代理转发**: 将 `/api/*` 请求转发到 `http://localhost:8002`
3. **Django URL路由**: 根据 `urls.py` 配置匹配视图函数
4. **视图处理**: 执行数据库查询和业务逻辑
5. **返回JSON响应**: 标准化的JSON格式响应
6. **前端处理**: 更新组件状态和页面显示

## 数据格式标准

### 1. 成功响应格式

```json
{
    "status": "success",
    "data": [
        {
            "date": "2024-01-01",
            "code": "000001",
            "name": "平安银行",
            "new_price": 12.50,
            "change_rate": 2.45
        }
    ]
}
```

### 2. 错误响应格式

```json
{
    "status": "error",
    "message": "具体错误信息",
    "error_code": "ERROR_001"
}
```

## 常见查询参数

### 1. 分页参数
- `page`: 页码
- `page_size`: 每页条数

### 2. 过滤参数
- `date`: 日期过滤
- `keyword`: 关键词搜索
- `sort_by`: 排序字段
- `sort_order`: 排序方向

### 3. 导出参数
- `export=true`: 触发CSV导出

## 启动流程

### 1. 后端启动
```bash
cd /home/liu/桌面/stock-20250730_update./backend
python manage.py runserver 8002
```

### 2. 前端启动
```bash
cd /home/liu/桌面/stock-20250730_update./frontend
npm run dev
```

### 3. 访问地址
- 前端: `http://localhost:3000`
- 后端API: `http://localhost:8002/api/`
- 后端管理: `http://localhost:8002/admin/`

## 调试方法

### 1. 前端调试
- 浏览器开发者工具 → Network 选项卡
- 查看API请求和响应
- Console 查看错误日志

### 2. 后端调试
- Django Debug Toolbar
- 服务器日志: `python manage.py runserver --verbosity=2`
- 数据库查询日志

### 3. 网络调试
- 检查Vite代理配置
- 验证CORS设置
- 测试API端点可达性

## 常见问题排查

### 1. CORS错误
- 检查 `settings.py` 中的CORS配置
- 确认 `corsheaders` 中间件已添加

### 2. 404错误
- 检查URL路由配置
- 验证API端点拼写

### 3. 500错误
- 查看Django服务器日志
- 检查数据库连接
- 验证视图函数逻辑

### 4. 数据加载慢
- 检查数据库查询效率
- 添加数据库索引
- 实现分页和缓存

## 性能优化建议

### 1. 前端优化
- 使用虚拟滚动处理大数据集
- 实现数据缓存机制
- 异步加载非关键数据

### 2. 后端优化
- 数据库查询优化
- 添加Redis缓存
- 实现API限流

### 3. 网络优化
- 启用gzip压缩
- 使用CDN加速
- 优化图片和静态资源

---

*文档更新日期: 2025年8月11日*
*版本: v1.0.0*
