// 股票基础类型
export interface StockBase {
    date: string
    code: string
    name: string
}

// 股票现货数据
export interface StockSpot extends StockBase {
    new_price: number
    change_rate: number
    ups_downs: number
    volume: number
    deal_amount: number
    amplitude: number
    turnoverrate: number
    volume_ratio: number
    open_price: number
    high_price: number
    low_price: number
    pre_close_price: number
    speed_increase: number
    speed_increase_5: number
    speed_increase_60: number
    speed_increase_all: number
    dtsyl: number
    pe9: number
    pe: number
    pbnewmrq: number
    basic_eps: number
    bvps: number
    per_capital_reserve: number
    per_unassign_profit: number
    roe_weight: number
    sale_gpr: number
    debt_asset_ratio: number
    total_operate_income: number
    toi_yoy_ratio: number
    parent_netprofit: number
    netprofit_yoy_ratio: number
    report_date: string
    total_shares: number
    free_shares: number
    total_market_cap: number
    free_cap: number
    industry: string
    listing_date: string
}

// ETF现货数据
export interface EtfSpot extends StockBase {
    new_price: number
    change_rate: number
    ups_downs: number
    volume: number
    deal_amount: number
    open_price: number
    high_price: number
    low_price: number
    pre_close_price: number
    turnoverrate: number
    total_market_cap: number
    free_cap: number
}

// 股票资金流向
export interface StockFundFlow extends StockBase {
    new_price: number
    change_rate: number
    fund_amount: number
    fund_rate: number
    fund_amount_super: number
    fund_rate_super: number
    fund_amount_large: number
    fund_rate_large: number
    fund_amount_medium: number
    fund_rate_medium: number
    fund_amount_small: number
    fund_rate_small: number
    change_rate_3: number
    fund_amount_3: number
    fund_rate_3: number
    fund_amount_super_3: number
    fund_rate_super_3: number
    fund_amount_large_3: number
    fund_rate_large_3: number
    fund_amount_medium_3: number
    fund_rate_medium_3: number
    fund_amount_small_3: number
    fund_rate_small_3: number
    change_rate_5: number
    fund_amount_5: number
    fund_rate_5: number
    fund_amount_super_5: number
    fund_rate_super_5: number
    fund_amount_large_5: number
    fund_rate_large_5: number
    fund_amount_medium_5: number
    fund_rate_medium_5: number
    fund_amount_small_5: number
    fund_rate_small_5: number
    change_rate_10: number
    fund_amount_10: number
    fund_rate_10: number
    fund_amount_super_10: number
    fund_rate_super_10: number
    fund_amount_large_10: number
    fund_rate_large_10: number
    fund_amount_medium_10: number
    fund_rate_medium_10: number
    fund_amount_small_10: number
    fund_rate_small_10: number
}

// 行业/概念资金流向
export interface IndustryFundFlow {
    date: string
    name: string
    change_rate: number
    fund_amount: number
    fund_rate: number
    fund_amount_super: number
    fund_rate_super: number
    fund_amount_large: number
    fund_rate_large: number
    fund_amount_medium: number
    fund_rate_medium: number
    fund_amount_small: number
    fund_rate_small: number
    stock_name: string
    change_rate_5: number
    fund_amount_5: number
    fund_rate_5: number
    fund_amount_super_5: number
    fund_rate_super_5: number
    fund_amount_large_5: number
    fund_rate_large_5: number
    fund_amount_medium_5: number
    fund_rate_medium_5: number
    fund_amount_small_5: number
    fund_rate_small_5: number
    stock_name_5: string
    change_rate_10: number
    fund_amount_10: number
    fund_rate_10: number
    fund_amount_super_10: number
    fund_rate_super_10: number
    fund_amount_large_10: number
    fund_rate_large_10: number
    fund_amount_medium_10: number
    fund_rate_medium_10: number
    fund_amount_small_10: number
    fund_rate_small_10: number
    stock_name_10: string
}

// 股票分红配送
export interface StockBonus extends StockBase {
    convertible_total_rate: number
    convertible_rate: number
    convertible_transfer_rate: number
    bonusaward_rate: number
    bonusaward_yield: number
    basic_eps: number
    bvps: number
    per_capital_reserve: number
    per_unassign_profit: number
    netprofit_yoy_ratio: number
    total_shares: number
    plan_date: string
    record_date: string
    ex_dividend_date: string
    progress: string
    report_date: string
}

// 股票龙虎榜
export interface StockTop extends StockBase {
    ranking_times: number
    sum_buy: number
    sum_sell: number
    net_amount: number
    buy_seat: number
    sell_seat: number
}

// 股票大宗交易
export interface StockBlocktrade extends StockBase {
    new_price: number
    change_rate: number
    average_price: number
    overflow_rate: number
    trade_number: number
    sum_volume: number
    sum_turnover: number
    turnover_market_rate: number
}

// 技术指标相关类型
export interface MacdData {
    DIF: number[]
    DEA: number[]
    MACD: number[]
    dates?: string[]
}

export interface KdjData {
    K: number[]
    D: number[]
    J: number[]
    dates?: string[]
}

export interface MaData {
    ma5: number[]
    ma10: number[]
    ma20: number[]
    ma60: number[]
    dates?: string[]
}

// 回测相关类型
export interface BacktestConfig {
    initial_capital: number
    start_date: string
    end_date: string
    stock_codes: string[]
    strategy_name: string
    commission_rate: number
    min_commission: number
    stamp_tax_rate: number
}

export interface BacktestResult {
    total_return: number
    annual_return: number
    sharpe_ratio: number
    max_drawdown: number
    win_rate: number
    total_trades: number
    strategy_value: number[]
    benchmark_value: number[]
    dates: string[]
    trades: TradeRecord[]
}

export interface TradeRecord {
    date: string
    code: string
    name: string
    action: 'buy' | 'sell'
    price: number
    quantity: number
    amount: number
    commission: number
    reason: string
}

// API响应类型
export interface ApiResponse<T = any> {
    success: boolean
    data?: T
    error?: string
    message?: string
}

// 筛选参数类型
export interface StockFilterParams {
    pe_min?: number
    pe_max?: number
    pb_min?: number
    pb_max?: number
    roe_min?: number
    market_cap_min?: number
    market_cap_max?: number
    change_rate_min?: number
    change_rate_max?: number
    industry?: string
    date?: string
}
