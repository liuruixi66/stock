/**
 * API 请求封装模块
 */

import axios, { AxiosRequestConfig, AxiosResponse } from 'axios'
import { dateToApiFormat } from './dateUtils'

// API 基础配置
const API_BASE_URL = '/api'

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    console.log('🚀 API请求:', config.method?.toUpperCase(), config.url, config.params || config.data)
    return config
  },
  (error) => {
    console.error('❌ 请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log('✅ API响应:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('❌ API错误响应:', error.response?.status, error.response?.data || error.message)
    return Promise.reject(error)
  }
)

/**
 * 股票数据相关API
 */
export const stockAPI = {
  /**
   * 获取股票现货数据
   */
  getStockSpot: (params?: { start_date?: string; end_date?: string; limit?: number }) => {
    const apiParams = { ...params }
    
    // 转换日期格式
    if (apiParams.start_date) {
      apiParams.start_date = dateToApiFormat(apiParams.start_date)
    }
    if (apiParams.end_date) {
      apiParams.end_date = dateToApiFormat(apiParams.end_date)
    }
    
    return apiClient.get('/stock-spot/', { params: apiParams })
  },

  /**
   * 获取股票实时数据
   */
  getStockRealtime: (codes: string[]) => {
    return apiClient.post('/stock-realtime/', { codes })
  },

  /**
   * 获取股票资金流向
   */
  getStockFundFlow: (params?: { date?: string }) => {
    return apiClient.get('/stock-fund-flow/', { params })
  },
}

/**
 * 技术指标相关API
 */
export const indicatorAPI = {
  /**
   * 计算MACD指标
   */
  calculateMACD: (params: {
    symbol: string
    start_date: string
    end_date: string
    fast_period?: number
    slow_period?: number
    signal_period?: number
  }) => {
    const apiParams = {
      ...params,
      start_date: dateToApiFormat(params.start_date),
      end_date: dateToApiFormat(params.end_date),
    }
    return apiClient.post('/calculate-macd/', apiParams)
  },

  /**
   * 获取市场MA指标
   */
  getMarketMA: (params: {
    index: string
    period: string
    short_ma: number
    long_ma: number
    start_date?: string
    end_date?: string
  }) => {
    const apiParams = { ...params }
    if (apiParams.start_date) {
      apiParams.start_date = dateToApiFormat(apiParams.start_date)
    }
    if (apiParams.end_date) {
      apiParams.end_date = dateToApiFormat(apiParams.end_date)
    }
    return apiClient.get('/market/ma/', { params: apiParams })
  },

  /**
   * 获取市场KDJ指标
   */
  getMarketKDJ: (params: {
    index: string
    period: string
    k_period: number
    d_period: number
    j_period: number
    start_date?: string
    end_date?: string
  }) => {
    const apiParams = { ...params }
    if (apiParams.start_date) {
      apiParams.start_date = dateToApiFormat(apiParams.start_date)
    }
    if (apiParams.end_date) {
      apiParams.end_date = dateToApiFormat(apiParams.end_date)
    }
    return apiClient.get('/market/kdj/', { params: apiParams })
  },
}

/**
 * 回测相关API
 */
export const backtestAPI = {
  /**
   * 运行回测
   */
  runBacktest: (params: {
    indicators?: string[]
    conditions?: Record<string, any>
    start_date?: string
    end_date?: string
    startDate?: string
    endDate?: string
    stockSelectionStartDate?: string
    stockSelectionEndDate?: string
    total_cash?: number
    strategy?: string
  }) => {
    const apiParams = { ...params }
    
    // 统一处理多种日期参数格式
    const startDate = params.start_date || params.startDate || params.stockSelectionStartDate
    const endDate = params.end_date || params.endDate || params.stockSelectionEndDate
    
    if (startDate) {
      apiParams.start_date = dateToApiFormat(startDate)
      apiParams.startDate = startDate
      apiParams.stockSelectionStartDate = startDate
    }
    if (endDate) {
      apiParams.end_date = dateToApiFormat(endDate)
      apiParams.endDate = endDate
      apiParams.stockSelectionEndDate = endDate
    }
    
    console.log('📊 回测API调用参数:', apiParams)
    return apiClient.post('/run-backtest/', apiParams)
  },

  /**
   * 获取回测配置
   */
  getBacktestConfig: () => {
    return apiClient.get('/backtest/config/')
  },

  /**
   * 获取交易详情
   */
  getTransactionDetails: () => {
    return apiClient.get('/transaction-details/')
  },
}

/**
 * 筛选相关API
 */
export const filterAPI = {
  /**
   * 筛选股票
   */
  filterStocks: (params: {
    indicators: string[]
    conditions: Record<string, any>
    start_date?: string
    end_date?: string
    limit?: number
  }) => {
    const apiParams = { ...params }
    if (apiParams.start_date) {
      apiParams.start_date = dateToApiFormat(apiParams.start_date)
    }
    if (apiParams.end_date) {
      apiParams.end_date = dateToApiFormat(apiParams.end_date)
    }
    return apiClient.post('/filter-stocks/', apiParams)
  },
}

/**
 * 收益概览相关API
 */
export const earningsAPI = {
  /**
   * 获取收益概览数据
   */
  getEarningsOverview: (params?: {
    start_date?: string
    end_date?: string
  }) => {
    const apiParams = { ...params }
    
    // 转换日期格式
    if (apiParams.start_date) {
      apiParams.start_date = dateToApiFormat(apiParams.start_date)
    }
    if (apiParams.end_date) {
      apiParams.end_date = dateToApiFormat(apiParams.end_date)
    }
    
    return apiClient.get('/earnings-overview/', { params: apiParams })
  },
}

/**
 * 统一的错误处理函数
 */
export const handleAPIError = (error: any) => {
  if (error.response) {
    // 服务器响应了错误状态码
    const { status, data } = error.response
    switch (status) {
      case 400:
        return `请求参数错误: ${data.message || data.error || '未知错误'}`
      case 401:
        return '未授权访问，请登录'
      case 403:
        return '访问被拒绝'
      case 404:
        return '请求的资源不存在'
      case 500:
        return `服务器内部错误: ${data.message || data.error || '请稍后重试'}`
      default:
        return `请求失败 (${status}): ${data.message || data.error || '未知错误'}`
    }
  } else if (error.request) {
    // 请求发送了但没有收到响应
    return '网络连接超时，请检查网络连接'
  } else {
    // 其他错误
    return `请求失败: ${error.message || '未知错误'}`
  }
}

/**
 * 通用API调用函数
 */
export const callAPI = async <T = any>(
  apiCall: () => Promise<AxiosResponse<T>>,
  errorHandler?: (error: any) => string
): Promise<{ success: boolean; data?: T; error?: string }> => {
  try {
    const response = await apiCall()
    return {
      success: true,
      data: response.data,
    }
  } catch (error) {
    const errorMessage = errorHandler ? errorHandler(error) : handleAPIError(error)
    console.error('API调用失败:', errorMessage, error)
    return {
      success: false,
      error: errorMessage,
    }
  }
}

export default apiClient
