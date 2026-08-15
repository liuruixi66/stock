import axios from 'axios'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 45000,
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
    getRuns: (market?: 'A' | 'US') => api.get('/research/runs/', { params: { market } }),
    getRun: (runId: number) => api.get(`/research/runs/${runId}/`),
}

export const watchlistApi = {
    list: (market?: 'A' | 'US') => api.get('/watchlist/', { params: { market } }),
    add: (data: { market: 'A' | 'US'; symbol: string; name?: string; note?: string }) =>
        api.post('/watchlist/', data),
    remove: (itemId: number) => api.delete(`/watchlist/${itemId}/`),
}

export const paperTradingApi = {
    getAccounts: () => api.get('/paper/accounts/'),
    createAccount: (data: any) => api.post('/paper/accounts/', data),
    getSummary: (accountId: number) => api.get(`/paper/accounts/${accountId}/summary/`),
    getAnalytics: (accountId: number) => api.get(`/paper/accounts/${accountId}/analytics/`),
    getOrders: (accountId?: number) => api.get('/paper/orders/', { params: { account_id: accountId } }),
    submitOrder: (data: any) => api.post('/paper/orders/', data),
}