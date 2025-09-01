# API 接口文档

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

**文档版本**: v1.0.0  
**最后更新**: 2025-08-04  
**维护者**: 系统集成团队
