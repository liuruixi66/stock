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

export const researchApi = {
    getQuotes: (market: 'A' | 'US', symbols: string) =>
        api.get('/market/quotes/', { params: { market, symbols } }),
    runBacktest: (data: any) => api.post('/research/backtest/', data),
}

export const paperTradingApi = {
    getAccounts: () => api.get('/paper/accounts/'),
    createAccount: (data: any) => api.post('/paper/accounts/', data),
    getSummary: (accountId: number) => api.get(`/paper/accounts/${accountId}/summary/`),
    getOrders: (accountId?: number) => api.get('/paper/orders/', { params: { account_id: accountId } }),
    submitOrder: (data: any) => api.post('/paper/orders/', data),
}