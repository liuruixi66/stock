import axios from 'axios'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    }
})

// 响应拦截器
api.interceptors.response.use(
    response => response,
    error => {
        console.error('API请求错误:', error)
        return Promise.reject(error)
    }
)

// 股票相关API
export const stockApi = {
    // 获取股票现货数据
    getStockSpot: (params?: any) => api.get('/stock-spot/', { params }),

    // 获取股票资金流向
    getStockFundFlow: (params?: any) => api.get('/stock-fund-flow/', { params }),

    // 获取股票分红配送
    getStockBonus: (params?: any) => api.get('/stock-bonus/', { params }),

    // 获取股票龙虎榜
    getStockTop: (params?: any) => api.get('/stock-top/', { params }),

    // 获取股票大宗交易
    getStockBlocktrade: (params?: any) => api.get('/stock-blocktrade/', { params }),

    // 获取行业资金流向
    getIndustryFundFlow: (params?: any) => api.get('/industry-fund-flow/', { params }),

    // 获取概念资金流向
    getConceptFundFlow: (params?: any) => api.get('/concept-fund-flow/', { params }),

    // 获取ETF现货数据
    getEtfSpot: (params?: any) => api.get('/etf-spot/', { params }),

    // 获取实时股票数据
    getStockRealtime: () => api.get('/stock-realtime/'),

    // 股票筛选
    filterStocks: (data: any) => api.post('/filter_stocks/', data),
}

// 技术指标API
export const indicatorApi = {
    // 计算MACD
    calculateMacd: (data: any) => api.post('/calculate-macd/', data),

    // 获取市场MA数据
    getMarketMa: (params?: any) => api.get('/market/ma/', { params }),

    // 获取市场KDJ数据
    getMarketKdj: (data: any) => api.post('/market/kdj/', data),
}

// 回测API
export const backtestApi = {
    // 运行回测
    runBacktest: (data: any) => api.post('/backtest/run/', data),

    // 获取回测配置
    getBacktestConfig: () => api.get('/backtest/config/'),
}

// 兼容旧版本的API（用于向后兼容）
export const getStockData = (name: string, date: string) => {
    return stockApi.getStockSpot({ name, date })
}

export const getIndicatorsData = (code: string, date: string, name: string) => {
    return indicatorApi.calculateMacd({ code, date, name })
}

export const getStockRealtime = () => {
    return stockApi.getStockRealtime()
}

// 导出默认API实例
export default api