"""
前端接口文档 - 回测系统API
"""

API_DOCUMENTATION = """
# 西蒙斯量化回测系统 API 接口文档

## 1. 运行回测接口
**URL:** `/api/backtest/run/`
**方法:** POST
**描述:** 基于技术指标筛选股票并运行回测

### 请求参数:
```json
{
    "indicators": ["macd", "kdj", "ma"],
    "conditions": {
        "macd": {"op": ">", "value": 0},
        "kdj_k": {"op": "<", "value": 20}
    },
    "start_date": "20230101",
    "end_date": "20241231",
    "total_cash": 100000,
    "data_path": "/path/to/stock/data.csv"
}
```

### 响应示例:
```json
{
    "success": true,
    "filtered_stocks": ["000001", "000002", "600031"],
    "backtest_results": {
        "account_data": [
            {
                "date": "20230101",
                "total_assets": 100000,
                "stock_value": 0,
                "available_cash": 100000
            }
        ],
        "position_data": [],
        "trade_records": [
            {
                "stock_code": "000001",
                "action": "buy",
                "amount": 33333.33,
                "price": "market_price",
                "date": "20230101"
            }
        ],
        "performance_metrics": {
            "total_stocks": 3,
            "initial_cash": 100000,
            "strategy_type": "equal_weight_buy_hold",
            "backtest_period": "20230101 - 20241231"
        }
    },
    "strategy_info": {
        "indicators": ["macd", "kdj", "ma"],
        "conditions": {...},
        "period": "20230101 - 20241231",
        "total_cash": 100000
    }
}
```

## 2. 获取回测配置接口
**URL:** `/api/backtest/config/`
**方法:** GET
**描述:** 获取回测系统支持的配置选项

### 响应示例:
```json
{
    "success": true,
    "data": {
        "trader_tools": ["ths", "tdx", "qmt"],
        "data_apis": ["dfcf", "tushare", "akshare"],
        "data_types": ["1", "5", "15", "30", "60", "D", "W", "M"],
        "default_config": {
            "trader_tool": "ths",
            "data_api": "dfcf",
            "data_type": "D",
            "total_cash": 100000,
            "start_date": "20230101",
            "end_date": "20241231"
        }
    }
}
```

## 3. 使用示例

### JavaScript前端调用示例:
```javascript
// 运行回测
async function runBacktest() {
    const config = {
        indicators: ['macd_cross', 'kdj', 'four_ma_long'],
        conditions: {
            'macd_cross': {'op': '=', 'value': 0},  // MACD金叉
            'k': {'op': '<', 'value': 20},          // KDJ超卖
            'four_ma_long': {'op': '=', 'value': true}  // 四线多头
        },
        start_date: '20230101',
        end_date: '20241231',
        total_cash: 100000,
        data_path: '/home/liu/桌面/stock-main/backend/000001_10years.csv'
    };
    
    try {
        const response = await fetch('/api/backtest/run/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('回测成功:', result);
            displayBacktestResults(result);
        } else {
            console.error('回测失败:', result.error);
        }
    } catch (error) {
        console.error('请求失败:', error);
    }
}

// 获取配置选项
async function getBacktestConfig() {
    try {
        const response = await fetch('/api/backtest/config/');
        const result = await response.json();
        
        if (result.success) {
            console.log('配置选项:', result.data);
            return result.data;
        }
    } catch (error) {
        console.error('获取配置失败:', error);
    }
}
```

### Python调用示例:
```python
import requests
import json

# 运行回测
def run_backtest_python():
    url = 'http://localhost:8000/api/backtest/run/'
    config = {
        'indicators': ['macd_cross', 'kdj'],
        'conditions': {
            'macd_cross': {'op': '=', 'value': 0},
            'k': {'op': '<', 'value': 20}
        },
        'start_date': '20230101',
        'end_date': '20241231',
        'total_cash': 100000
    }
    
    response = requests.post(url, json=config)
    result = response.json()
    
    if result['success']:
        print("回测成功!")
        print(f"筛选股票: {result['filtered_stocks']}")
        print(f"交易记录: {len(result['backtest_results']['trade_records'])}条")
    else:
        print(f"回测失败: {result['error']}")

if __name__ == '__main__':
    run_backtest_python()
```

## 4. 支持的技术指标

### 基础指标:
- `ma`: 移动平均线
- `macd`: MACD指标
- `kdj`: KDJ指标
- `k`: KDJ中的K值
- `d`: KDJ中的D值  
- `j`: KDJ中的J值

### 复合指标:
- `macd_cross`: MACD金叉死叉信号 (0=金叉, 1=死叉)
- `four_ma_long`: 四周期均线多头排列

### 基本面指标:
- `net_profit`: 净利润
- `profit_yoy`: 利润同比增长率

### 市场信号:
- `holder_reduce`: 股东减持信号
- `holder_add`: 股东增持信号
- `holder_dividend`: 分红信号
- `new_listing`: 新上市信号
- `st`: ST股信号
- `delisting`: 退市信号

## 5. 条件操作符

支持的比较操作符:
- `>`: 大于
- `<`: 小于
- `>=`: 大于等于
- `<=`: 小于等于
- `=`: 等于

## 6. 错误处理

常见错误及解决方案:

1. **没有找到符合条件的股票**
   - 检查筛选条件是否过于严格
   - 确认数据源中有足够的股票数据

2. **数据路径错误**
   - 确认CSV文件路径正确
   - 检查文件格式是否符合要求

3. **指标计算失败**
   - 确认股票数据包含必要的字段(open, close, high, low, volume)
   - 检查数据格式和时间范围

4. **回测系统初始化失败**
   - 检查西蒙斯量化回测系统路径是否正确
   - 确认所有依赖模块已正确安装
"""

def get_api_documentation():
    """返回API文档"""
    return API_DOCUMENTATION

if __name__ == '__main__':
    print(get_api_documentation())
