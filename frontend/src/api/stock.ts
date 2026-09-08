import axios from 'axios'

export type Market = 'A' | 'US' | 'CRYPTO'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 30000,
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
    getQuotes: (market: Market, symbols: string) =>
        api.get('/market/quotes/', { params: { market, symbols } }),
    getHistory: (market: Market, symbol: string, start_date?: string, end_date?: string) =>
        api.get('/market/history/', {
            params: { market, symbol, start_date, end_date },
            timeout: 120000,
        }),
    runBacktest: (data: any) => api.post('/research/backtest/', data, { timeout: 120000 }),
    runPortfolioBacktest: (data: any) => api.post('/research/portfolio-backtest/', data, { timeout: 120000 }),
    getRuns: (market?: Market) => api.get('/research/runs/', { params: { market } }),
    getRun: (runId: number) => api.get(`/research/runs/${runId}/`),
}

export const watchlistApi = {
    list: (market?: Market) => api.get('/watchlist/', { params: { market } }),
    add: (data: { market: Market; symbol: string; name?: string; note?: string }) =>
        api.post('/watchlist/', data),
    remove: (itemId: number) => api.delete(`/watchlist/${itemId}/`),
}

export const paperTradingApi = {
    getAccounts: () => api.get('/paper/accounts/'),
    createAccount: (data: any) => api.post('/paper/accounts/', data),
    getSummary: (accountId: number) => api.get(`/paper/accounts/${accountId}/summary/`),
    getAnalytics: (accountId: number) => api.get(`/paper/accounts/${accountId}/analytics/`),
    submitOrder: (data: any) => api.post('/paper/orders/', data),
}