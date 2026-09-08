<template>
  <main class="terminal-page">
    <header class="terminal-header">
      <div>
        <span class="eyebrow">QUANT RESEARCH DESK</span>
        <h1>多市场研究交易台</h1>
      </div>
      <div class="market-toggle" role="group" aria-label="市场">
        <button :class="{ active: market === 'A' }" @click="switchMarket('A')">A股</button>
        <button :class="{ active: market === 'US' }" @click="switchMarket('US')">美股</button>
        <button :class="{ active: market === 'CRYPTO' }" @click="switchMarket('CRYPTO')">虚拟货币</button>
      </div>
    </header>

    <section class="ticker-strip">
      <label>
        <span>观察代码</span>
        <input v-model="symbols" @keyup.enter="loadQuotes" placeholder="000001,600519" />
      </label>
      <button class="command" :disabled="loadingQuotes" @click="loadQuotes">
        <i class="fa fa-refresh"></i>{{ loadingQuotes ? '更新中' : '更新行情' }}
      </button>
      <div v-for="quote in quotes" :key="quote.symbol" class="quote">
        <strong>{{ quote.symbol }}</strong>
        <span>{{ quote.price.toFixed(2) }} {{ quote.currency }}</span>
        <em :class="quote.change >= 0 ? 'up' : 'down'">
          {{ quote.change >= 0 ? '+' : '' }}{{ quote.change_percent.toFixed(2) }}%
        </em>
      </div>
    </section>

    <p v-if="error" class="error-banner">{{ error }}</p>

    <section class="watchlist-strip">
      <span class="strip-title">自选股</span>
      <button v-for="item in marketWatchlist" :key="item.id" class="watch-chip" @click="useWatchSymbol(item.symbol)">
        {{ item.symbol }}<em v-if="item.name">{{ item.name }}</em>
        <i class="remove" title="移除自选" @click.stop="removeWatch(item.id)">×</i>
      </button>
      <span v-if="!marketWatchlist.length" class="strip-empty">暂无自选股，先添加一个</span>
      <input v-model="newWatchSymbol" class="watch-input" placeholder="添加代码" @keyup.enter="addWatch" />
      <button class="command ghost" @click="addWatch">加入自选</button>
    </section>

    <div class="workspace-grid">
      <section class="research-panel">
        <div class="panel-heading">
          <div><span>STRATEGY LAB</span><h2>双均线参数研究</h2></div>
          <button class="command" :disabled="runningBacktest" @click="runBacktest">
            <i class="fa fa-play"></i>{{ runningBacktest ? '计算中' : '运行回测' }}
          </button>
        </div>
        <div class="parameter-grid">
          <label>股票代码<input v-model="research.symbol" /></label>
          <label>短周期<input v-model.number="research.short_window" type="number" min="2" /></label>
          <label>长周期<input v-model.number="research.long_window" type="number" min="3" /></label>
          <label>初始资金<input v-model.number="research.initial_cash" type="number" min="1000" /></label>
        </div>
        <div v-if="backtest" class="metric-grid">
          <article><span>总收益</span><strong :class="backtest.total_return >= 0 ? 'up' : 'down'">{{ backtest.total_return }}%</strong></article>
          <article><span>最大回撤</span><strong class="down">{{ backtest.max_drawdown }}%</strong></article>
          <article><span>夏普比率</span><strong>{{ backtest.sharpe_ratio }}</strong></article>
          <article><span>成交次数</span><strong>{{ backtest.trade_count }}</strong></article>
        </div>
        <details v-if="backtest?.historical_data" class="raw-data">
          <summary>查看回测原始数据（{{ backtest.historical_data.length }} 条）</summary>
          <div class="raw-data-meta">
            <span>来源：{{ backtest.data_source }}</span>
            <span>字段：date / open / high / low / close / volume</span>
          </div>
          <pre>{{ formatJson(backtest.historical_data) }}</pre>
        </details>
        <div ref="chartElement" class="equity-chart"></div>
      </section>

      <aside class="trade-panel">
        <div class="panel-heading"><div><span>PAPER EXECUTION</span><h2>模拟盘</h2></div></div>
        <div v-if="!accounts.length" class="empty-account">
          <input v-model="newAccountName" placeholder="研究账户名称" />
          <button class="command" @click="createAccount">创建 {{ accountCurrency }} 账户</button>
        </div>
        <template v-else>
          <label class="account-select">模拟账户
            <select v-model.number="selectedAccountId" @change="loadAccount">
              <option v-for="account in marketAccounts" :key="account.id" :value="account.id">{{ account.name }}</option>
            </select>
          </label>
          <div v-if="summary" class="account-summary">
            <div><span>总资产</span><strong>{{ summary.total_assets.toFixed(2) }} {{ summary.currency }}</strong></div>
            <div><span>可用资金</span><strong>{{ summary.cash.toFixed(2) }}</strong></div>
            <div><span>累计收益</span><strong :class="summary.total_return >= 0 ? 'up' : 'down'">{{ summary.total_return.toFixed(2) }}%</strong></div>
          </div>
          <div class="order-ticket">
            <div class="side-toggle"><button :class="{ active: order.side === 'BUY' }" @click="order.side = 'BUY'">买入</button><button :class="{ active: order.side === 'SELL' }" @click="order.side = 'SELL'">卖出</button></div>
            <label>代码<input v-model="order.symbol" /></label>
            <label>数量<input v-model.number="order.quantity" type="number" :step="market === 'A' ? 100 : market === 'CRYPTO' ? 0.0001 : 1" :min="market === 'CRYPTO' ? 0.00000001 : 1" /></label>
            <label>订单类型<select v-model="order.order_type"><option value="MARKET">市价单</option><option value="LIMIT">限价单</option></select></label>
            <label v-if="order.order_type === 'LIMIT'">限价<input v-model.number="order.price" type="number" step="0.01" /></label>
            <button class="submit-order" @click="submitOrder">提交模拟订单</button>
          </div>
        </template>
      </aside>
    </div>

    <section v-if="summary?.positions?.length" class="positions-section">
      <div class="panel-heading"><div><span>POSITIONS</span><h2>当前持仓</h2></div></div>
      <table><thead><tr><th>代码</th><th>数量</th><th>成本</th><th>现价</th><th>市值</th><th>浮动盈亏</th></tr></thead>
        <tbody><tr v-for="position in summary.positions" :key="position.symbol"><td>{{ position.symbol }}</td><td>{{ position.quantity }}</td><td>{{ position.average_price.toFixed(2) }}</td><td>{{ position.current_price.toFixed(2) }}</td><td>{{ position.market_value.toFixed(2) }}</td><td :class="position.unrealized_pnl >= 0 ? 'up' : 'down'">{{ position.unrealized_pnl.toFixed(2) }}</td></tr></tbody>
      </table>
    </section>

    <section class="positions-section">
      <div class="panel-heading">
        <div><span>RESEARCH JOURNAL</span><h2>量化研究过程记录</h2></div>
        <div class="heading-actions">
          <RouterLink class="command ghost" to="/transaction-details">交易记录</RouterLink>
          <RouterLink class="command ghost" to="/earnings-overview">分析报告</RouterLink>
          <button class="command ghost" @click="loadRuns">刷新</button>
        </div>
      </div>
      <table v-if="runs.length">
        <thead><tr><th>时间</th><th>标的</th><th>策略</th><th>参数</th><th>区间</th><th>总收益</th><th>最大回撤</th><th>夏普</th><th>成交次数</th><th></th></tr></thead>
        <tbody>
          <template v-for="run in runs" :key="run.id">
            <tr>
              <td>{{ formatTime(run.created_at) }}</td>
              <td>{{ run.market }} {{ run.symbol }}</td>
              <td>{{ run.strategy }}</td>
              <td class="memo">MA{{ run.parameters.short_window }}/{{ run.parameters.long_window }}，本金 {{ run.parameters.initial_cash }}</td>
              <td class="memo">{{ run.start_date }} ~ {{ run.end_date }}</td>
              <td :class="run.total_return >= 0 ? 'up' : 'down'">{{ run.total_return }}%</td>
              <td class="down">{{ run.max_drawdown }}%</td>
              <td>{{ run.sharpe_ratio }}</td>
              <td>{{ run.trade_count }}</td>
              <td><button class="link-button" @click="toggleRun(run.id)">{{ expandedRunId === run.id ? '收起' : '明细' }}</button></td>
            </tr>
            <tr v-if="expandedRunId === run.id">
              <td colspan="10" class="run-detail">
                <div v-if="run.trades.length" class="trade-lines">
                  <div v-for="(trade, index) in run.trades" :key="index">
                    {{ trade.date }} · {{ trade.side === 'BUY' ? '买入' : '卖出' }} · 价格 {{ trade.price }} · 数量 {{ trade.quantity }}
                  </div>
                </div>
                <span v-else>该次研究没有触发交易信号</span>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
      <p v-else class="empty-hint">运行一次回测，这里会记录参数、绩效与信号明细。</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import * as echarts from 'echarts'
import { paperTradingApi, researchApi, watchlistApi } from '@/api/stock'

type Market = 'A' | 'US' | 'CRYPTO'
interface PaperAccount { id: number; name: string; market: Market; currency: string }
interface WatchItem { id: number; market: Market; symbol: string; name: string }
const market = ref<Market>('A')
const symbols = ref('000001,600519')
const quotes = ref<any[]>([])
const accounts = ref<PaperAccount[]>([])
const selectedAccountId = ref<number>()
const summary = ref<any>()
const backtest = ref<any>()
const error = ref('')
const loadingQuotes = ref(false)
const runningBacktest = ref(false)
const newAccountName = ref('A股研究账户')
const chartElement = ref<HTMLElement>()
let chart: echarts.ECharts | undefined

const watchlist = ref<WatchItem[]>([])
const marketWatchlist = ref<WatchItem[]>([])
const newWatchSymbol = ref('')
const runs = ref<any[]>([])
const expandedRunId = ref<number>()

const research = reactive({ symbol: '000001', short_window: 5, long_window: 20, initial_cash: 100000 })
const order = reactive<any>({ symbol: '000001', side: 'BUY', quantity: 100, order_type: 'MARKET', price: null })
const marketAccounts = ref<PaperAccount[]>([])

function showError(value: any) {
  error.value = value?.response?.data?.error || value?.message || '请求失败'
}
function formatTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}
function formatJson(value: unknown) {
  return JSON.stringify(value, null, 2)
}
function switchMarket(value: Market) {
  market.value = value
  symbols.value = value === 'A' ? '000001,600519' : value === 'US' ? 'AAPL,MSFT' : 'BTCUSDT,ETHUSDT'
  research.symbol = value === 'A' ? '000001' : value === 'US' ? 'AAPL' : 'BTCUSDT'
  order.symbol = research.symbol
  order.quantity = value === 'A' ? 100 : value === 'US' ? 10 : 0.01
  newAccountName.value = value === 'A' ? 'A股研究账户' : value === 'US' ? '美股研究账户' : '虚拟货币研究账户'
  syncMarketAccounts()
  syncMarketWatchlist()
  loadQuotes()
  loadRuns()
}
const accountCurrency = computed(() => market.value === 'A' ? 'CNY' : market.value === 'US' ? 'USD' : 'USDT')
async function loadWatchlist() {
  try { watchlist.value = (await watchlistApi.list()).data.data; syncMarketWatchlist() }
  catch (value) { showError(value) }
}
function syncMarketWatchlist() {
  marketWatchlist.value = watchlist.value.filter((item) => item.market === market.value)
  if (marketWatchlist.value.length) symbols.value = marketWatchlist.value.map((item) => item.symbol).join(',')
}
async function addWatch() {
  const symbol = newWatchSymbol.value.trim()
  if (!symbol) return
  try { await watchlistApi.add({ market: market.value, symbol }); newWatchSymbol.value = ''; await loadWatchlist(); loadQuotes() }
  catch (value) { showError(value) }
}
async function removeWatch(itemId: number) {
  try { await watchlistApi.remove(itemId); await loadWatchlist() }
  catch (value) { showError(value) }
}
function useWatchSymbol(symbol: string) {
  research.symbol = symbol
  order.symbol = symbol
}
async function loadQuotes() {
  loadingQuotes.value = true; error.value = ''
  try { quotes.value = (await researchApi.getQuotes(market.value, symbols.value)).data.data }
  catch (value) { showError(value) }
  finally { loadingQuotes.value = false }
}
async function loadRuns() {
  try { runs.value = (await researchApi.getRuns(market.value)).data.data }
  catch (value) { showError(value) }
}
function toggleRun(runId: number) {
  expandedRunId.value = expandedRunId.value === runId ? undefined : runId
}
async function runBacktest() {
  runningBacktest.value = true; error.value = ''
  try {
    backtest.value = (await researchApi.runBacktest({ ...research, market: market.value })).data.data
    await nextTick(); drawChart(); await loadRuns()
  } catch (value) { showError(value) }
  finally { runningBacktest.value = false }
}
function drawChart() {
  if (!chartElement.value || !backtest.value) return
  chart ||= echarts.init(chartElement.value)
  chart.setOption({ grid: { left: 56, right: 20, top: 24, bottom: 38 }, tooltip: { trigger: 'axis' }, xAxis: { type: 'category', data: backtest.value.equity_curve.map((item: any) => item.date), axisLabel: { color: '#718096' } }, yAxis: { type: 'value', scale: true, axisLabel: { color: '#718096' }, splitLine: { lineStyle: { color: '#e8edf2' } } }, series: [{ type: 'line', showSymbol: false, smooth: true, data: backtest.value.equity_curve.map((item: any) => item.equity), lineStyle: { color: '#006d5b', width: 2 }, areaStyle: { color: 'rgba(0,109,91,.09)' } }] })
}
async function loadAccounts() { accounts.value = (await paperTradingApi.getAccounts()).data.data; syncMarketAccounts() }
function syncMarketAccounts() {
  marketAccounts.value = accounts.value.filter((item: PaperAccount) => item.market === market.value)
  selectedAccountId.value = marketAccounts.value[0]?.id
  summary.value = undefined
  if (selectedAccountId.value) loadAccount()
}
async function createAccount() {
  try { await paperTradingApi.createAccount({ name: newAccountName.value, market: market.value, initial_cash: 100000 }); await loadAccounts() }
  catch (value) { showError(value) }
}
async function loadAccount() {
  if (!selectedAccountId.value) return
  summary.value = (await paperTradingApi.getSummary(selectedAccountId.value)).data.data
}
async function submitOrder() {
  if (!selectedAccountId.value) return
  try { await paperTradingApi.submitOrder({ ...order, account_id: selectedAccountId.value }); await loadAccount() }
  catch (value) { showError(value) }
}
function resizeChart() { chart?.resize() }
onMounted(() => { loadWatchlist(); loadQuotes(); loadAccounts(); loadRuns(); window.addEventListener('resize', resizeChart) })
onUnmounted(() => { window.removeEventListener('resize', resizeChart); chart?.dispose() })
</script>

<style scoped>
.terminal-page{min-height:100vh;padding:34px;background:#f4f6f7;color:#14201f;font-family:"Avenir Next","Helvetica Neue",sans-serif}.terminal-header{display:flex;justify-content:space-between;align-items:end;padding-bottom:22px;border-bottom:1px solid #ccd5d3}.eyebrow,.panel-heading span{font-size:11px;font-weight:700;letter-spacing:1.8px;color:#657570}.terminal-header h1{margin:5px 0 0;font-family:Georgia,serif;font-size:36px;font-weight:500;letter-spacing:0}.market-toggle,.side-toggle{display:flex;border:1px solid #aebbb8}.market-toggle button,.side-toggle button{border:0;background:#fff;padding:10px 22px;cursor:pointer}.market-toggle .active,.side-toggle .active{background:#123c35;color:#fff}.ticker-strip{display:flex;align-items:end;gap:14px;padding:18px 0;overflow:auto}.ticker-strip label{min-width:220px}.ticker-strip label span{display:block;font-size:12px;margin-bottom:5px;color:#657570}.ticker-strip input,input,select{box-sizing:border-box;width:100%;border:1px solid #b9c5c2;background:#fff;padding:10px 12px;font:inherit}.command{display:flex;align-items:center;gap:8px;border:0;background:#006d5b;color:white;padding:11px 16px;cursor:pointer;white-space:nowrap}.command:disabled{opacity:.55}.quote{min-width:142px;border-left:2px solid #d2dad8;padding:3px 12px}.quote span,.quote em{display:block}.quote em{font-style:normal;font-size:12px}.up{color:#b42318!important}.down{color:#087a65!important}.error-banner{padding:10px 14px;background:#fff0ed;border-left:3px solid #b42318}.workspace-grid{display:grid;grid-template-columns:minmax(0,2fr) minmax(300px,1fr);gap:18px}.research-panel,.trade-panel,.positions-section{background:#fff;border:1px solid #dbe2e0;padding:22px}.panel-heading{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}.panel-heading h2{margin:3px 0 0;font-family:Georgia,serif;font-size:23px;font-weight:500}.parameter-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.parameter-grid label,.order-ticket label,.account-select{font-size:12px;color:#596a66}.parameter-grid input,.order-ticket input,.order-ticket select,.account-select select{margin-top:6px}.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);margin-top:18px;border-block:1px solid #e2e7e6}.metric-grid article{padding:14px;border-right:1px solid #e2e7e6}.metric-grid article:last-child{border:0}.metric-grid span,.account-summary span{display:block;font-size:11px;color:#71807c}.metric-grid strong{font-size:22px}.equity-chart{height:310px}.empty-account{display:grid;gap:10px}.account-summary{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:16px 0;border-bottom:1px solid #e2e7e6}.account-summary div:first-child{grid-column:1/-1}.account-summary strong{display:block;margin-top:3px;font-size:20px}.order-ticket{display:grid;gap:12px;margin-top:18px}.side-toggle button{width:50%}.submit-order{border:0;background:#b89136;color:#151912;padding:12px;font-weight:700;cursor:pointer}.positions-section{margin-top:18px}table{width:100%;border-collapse:collapse}th,td{text-align:right;padding:11px;border-bottom:1px solid #e5e9e8}th:first-child,td:first-child{text-align:left}.watchlist-strip{display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding:14px 0}.strip-title{font-size:11px;font-weight:700;letter-spacing:1.8px;color:#657570}.watch-chip{display:inline-flex;align-items:center;gap:8px;border:1px solid #b9c5c2;background:#fff;padding:7px 11px;cursor:pointer;font:inherit}.watch-chip em{font-style:normal;font-size:12px;color:#71807c}.watch-chip .remove{font-style:normal;color:#b42318}.strip-empty{font-size:12px;color:#8a9793}.watch-input{width:140px}.command.ghost{background:#fff;color:#123c35;border:1px solid #123c35}.empty-hint{margin:0;font-size:13px;color:#8a9793}.heading-actions{display:flex;gap:8px}.command.ghost{text-decoration:none}.link-button{border:0;background:none;color:#006d5b;cursor:pointer;text-decoration:underline}.memo{font-size:12px;color:#5d6c68}.run-detail{text-align:left;background:#f7f9f9;font-size:12px}.trade-lines{display:grid;gap:4px}@media(max-width:900px){.terminal-page{padding:20px}.terminal-header{align-items:start;gap:18px}.terminal-header h1{font-size:29px}.workspace-grid{grid-template-columns:1fr}.parameter-grid,.metric-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:540px){.terminal-header{display:grid}.parameter-grid{grid-template-columns:1fr}.positions-section{overflow:auto}}
</style>