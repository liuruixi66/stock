<template>
  <div class="transaction-details">
    <div class="page-header">
      <div>
        <h1>交易记录</h1>
        <p class="subtitle">内置模拟盘与券商账户（模拟 / 实盘）的委托状态、成交明细与 FIFO 平仓盈亏。</p>
      </div>
      <div class="header-actions">
        <select v-model.number="accountId" @change="switchAccount">
          <option v-for="item in accounts" :key="item.id" :value="item.id">
            {{ item.name }}（{{ marketLabel(item.market) }} · {{ item.broker_label }}{{ item.trading_mode === 'LIVE' ? ' · 实盘' : '' }}）
          </option>
        </select>
        <button v-if="selectedAccount?.is_external" class="ghost-btn" :disabled="syncing" @click="syncAndReload">
          {{ syncing ? '同步中' : '同步券商' }}
        </button>
        <button class="ghost-btn" :disabled="loading" @click="loadAll">
          {{ loading ? '加载中' : '刷新' }}
        </button>
        <RouterLink class="ghost-btn" to="/research-terminal">去交易台下单</RouterLink>
      </div>
    </div>

    <p v-if="error" class="error-banner">{{ error }}</p>
    <p v-if="syncError" class="error-banner warn">券商同步失败，以下为最近一次同步的本地数据：{{ syncError }}</p>

    <div v-if="!accounts.length" class="empty-card">
      还没有账户，先到量化研究交易台创建一个（内置模拟或券商模拟盘）并提交订单。
    </div>

    <template v-else>
      <div v-if="selectedAccount" class="account-meta">
        <span :class="['mode-tag', selectedAccount.trading_mode.toLowerCase()]">{{ selectedAccount.trading_mode === 'LIVE' ? '实盘' : '模拟盘' }}</span>
        <span>{{ selectedAccount.broker_label }}</span>
        <span v-if="selectedAccount.broker_account_id">券商账号 {{ selectedAccount.broker_account_id }}</span>
        <span v-if="selectedAccount.is_external">最近同步 {{ selectedAccount.last_synced_at ? formatTime(selectedAccount.last_synced_at) : '--' }}</span>
        <span v-else>本地即时撮合，无需同步</span>
      </div>

      <div class="summary-grid">
        <div class="summary-card">
          <span>成交笔数</span>
          <strong>{{ summary.trade_count }}</strong>
          <em>买入 {{ summary.buy_count }} / 卖出 {{ summary.sell_count }}</em>
        </div>
        <div class="summary-card">
          <span>已实现盈亏</span>
          <strong :class="pnlClass(summary.realized_pnl)">{{ money(summary.realized_pnl) }}</strong>
          <em>{{ summary.closed_count }} 笔平仓</em>
        </div>
        <div class="summary-card">
          <span>浮动盈亏</span>
          <strong :class="pnlClass(summary.unrealized_pnl)">{{ money(summary.unrealized_pnl) }}</strong>
          <em>持仓市值 {{ money(summary.market_value) }}</em>
        </div>
        <div class="summary-card">
          <span>未完成委托</span>
          <strong>{{ openOrders.length }}</strong>
          <em>交易费用 {{ money(summary.total_fees) }}</em>
        </div>
      </div>

      <div class="section-heading">
        <h2>委托记录</h2>
        <div class="side-filter">
          <button v-for="option in statusOptions" :key="option.value"
                  :class="{ active: statusFilter === option.value }"
                  @click="statusFilter = option.value">{{ option.label }}<em>{{ option.count }}</em></button>
        </div>
      </div>
      <div class="table-card">
        <table v-if="filteredOrders.length">
          <thead>
            <tr>
              <th>委托时间</th>
              <th>标的</th>
              <th>方向</th>
              <th>类型</th>
              <th>委托量</th>
              <th>已成交</th>
              <th>委托价</th>
              <th>成交价</th>
              <th>状态</th>
              <th>券商委托号</th>
              <th>说明</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in filteredOrders" :key="order.id">
              <td>{{ formatTime(order.created_at) }}</td>
              <td>{{ order.symbol }}</td>
              <td><span :class="['side-tag', order.side.toLowerCase()]">{{ order.side === 'BUY' ? '买入' : '卖出' }}</span></td>
              <td>{{ order.order_type === 'MARKET' ? '市价' : '限价' }}</td>
              <td>{{ qty(order.quantity) }}</td>
              <td>{{ qty(order.filled_quantity) }}</td>
              <td>{{ order.requested_price === null ? '--' : order.requested_price.toFixed(2) }}</td>
              <td>{{ order.executed_price === null ? '--' : order.executed_price.toFixed(2) }}</td>
              <td><span :class="['status-tag', order.status.toLowerCase()]">{{ statusLabel(order.status) }}</span></td>
              <td class="memo">{{ order.broker_order_id || '--' }}</td>
              <td class="memo">{{ order.message || '--' }}</td>
              <td>
                <button v-if="isOpen(order.status)" class="link-btn" :disabled="cancelling === order.id" @click="cancel(order)">
                  {{ cancelling === order.id ? '撤单中' : '撤单' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty-card">没有符合条件的委托。</p>
      </div>

      <div class="section-heading">
        <h2>成交明细</h2>
        <span class="hint">已成交订单按 FIFO 逐笔配对计算平仓盈亏</span>
      </div>
      <div class="filter-bar">
        <label>标的<input v-model="symbolFilter" placeholder="全部" /></label>
        <div class="side-filter">
          <button v-for="option in sideOptions" :key="option.value"
                  :class="{ active: sideFilter === option.value }"
                  @click="sideFilter = option.value">{{ option.label }}</button>
        </div>
        <span class="filter-count">共 {{ filteredTrades.length }} 条</span>
      </div>

      <div class="table-card">
        <table v-if="filteredTrades.length">
          <thead>
            <tr>
              <th>成交时间</th>
              <th>标的</th>
              <th>方向</th>
              <th>下单类型</th>
              <th>数量</th>
              <th>成交价</th>
              <th>成交额</th>
              <th>手续费</th>
              <th>平仓盈亏</th>
              <th>成交来源</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="trade in filteredTrades" :key="trade.id">
              <td>{{ formatTime(trade.created_at) }}</td>
              <td>{{ trade.symbol }}</td>
              <td><span :class="['side-tag', trade.side.toLowerCase()]">{{ trade.side === 'BUY' ? '买入' : '卖出' }}</span></td>
              <td>{{ trade.order_type === 'MARKET' ? '市价单' : '限价单' }}</td>
              <td>{{ trade.side === 'BUY' ? '+' : '-' }}{{ qty(trade.quantity) }}</td>
              <td>{{ money(trade.executed_price) }}</td>
              <td>{{ money(trade.amount) }}</td>
              <td>{{ money(trade.fee) }}</td>
              <td :class="pnlClass(trade.realized_pnl)">
                {{ trade.realized_pnl === null ? '--' : money(trade.realized_pnl) }}
              </td>
              <td class="memo">{{ trade.message || '--' }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty-card">该账户还没有成交记录。</p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { paperTradingApi } from '@/api/stock'

type Market = 'A' | 'US' | 'CRYPTO'
interface PaperAccount {
  id: number; name: string; market: Market; currency: string
  broker: string; broker_label: string; broker_account_id: string
  trading_mode: 'PAPER' | 'LIVE'; is_external: boolean; last_synced_at: string | null
}
interface PaperOrder {
  id: number; symbol: string; side: 'BUY' | 'SELL'; order_type: 'MARKET' | 'LIMIT'
  quantity: number | string; filled_quantity: number
  requested_price: number | null; executed_price: number | null
  status: string; broker_order_id: string; message: string; created_at: string
}

const OPEN_STATUSES = ['PENDING', 'SUBMITTED', 'PARTIAL']
const STATUS_LABELS: Record<string, string> = {
  PENDING: '待成交', SUBMITTED: '已报', PARTIAL: '部分成交', FILLED: '已成交', CANCELLED: '已撤销', REJECTED: '已拒绝',
}

const accounts = ref<PaperAccount[]>([])
const accountId = ref<number>()
const currency = ref('CNY')
const summary = ref<any>({
  trade_count: 0, buy_count: 0, sell_count: 0, closed_count: 0,
  realized_pnl: 0, unrealized_pnl: 0, market_value: 0, total_fees: 0,
})
const trades = ref<any[]>([])
const orders = ref<PaperOrder[]>([])
const loading = ref(false)
const syncing = ref(false)
const cancelling = ref<number>()
const error = ref('')
const syncError = ref('')
const symbolFilter = ref('')
const sideFilter = ref('ALL')
const statusFilter = ref('ALL')
const sideOptions = [
  { value: 'ALL', label: '全部' },
  { value: 'BUY', label: '买入' },
  { value: 'SELL', label: '卖出' },
]

const selectedAccount = computed(() => accounts.value.find((item) => item.id === accountId.value))
const openOrders = computed(() => orders.value.filter((order) => isOpen(order.status)))
const statusOptions = computed(() => [
  { value: 'ALL', label: '全部', count: orders.value.length },
  { value: 'OPEN', label: '未完成', count: openOrders.value.length },
  { value: 'FILLED', label: '已成交', count: orders.value.filter((order) => order.status === 'FILLED').length },
  { value: 'CANCELLED', label: '已撤销', count: orders.value.filter((order) => order.status === 'CANCELLED').length },
  { value: 'REJECTED', label: '已拒绝', count: orders.value.filter((order) => order.status === 'REJECTED').length },
])
const filteredOrders = computed(() => orders.value.filter((order) => {
  if (statusFilter.value === 'ALL') return true
  if (statusFilter.value === 'OPEN') return isOpen(order.status)
  return order.status === statusFilter.value
}))
const filteredTrades = computed(() => trades.value.filter((trade) => {
  const symbolMatched = !symbolFilter.value || trade.symbol.includes(symbolFilter.value.trim().toUpperCase())
  return symbolMatched && (sideFilter.value === 'ALL' || trade.side === sideFilter.value)
}))

function isOpen(status: string) {
  return OPEN_STATUSES.includes(status)
}
function statusLabel(status: string) {
  return STATUS_LABELS[status] ?? status
}
function marketLabel(market: Market) {
  return market === 'A' ? 'A股' : market === 'US' ? '美股' : '虚拟货币'
}
function qty(value: number | string) {
  return Number(value).toString()
}
function money(value: number | null) {
  if (value === null || value === undefined) return '--'
  return `${value.toFixed(2)} ${currency.value}`
}
function pnlClass(value: number | null) {
  if (!value) return ''
  return value > 0 ? 'positive' : 'negative'
}
function formatTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}
function showError(value: any, fallback: string) {
  error.value = value?.response?.data?.error || fallback
}

async function loadAccounts(keepId?: number) {
  accounts.value = (await paperTradingApi.getAccounts()).data.data
  accountId.value = accounts.value.find((item) => item.id === keepId)?.id ?? accounts.value[0]?.id
}
async function loadAll() {
  if (!accountId.value) return
  loading.value = true
  error.value = ''
  try {
    const [analytics, orderList] = await Promise.all([
      paperTradingApi.getAnalytics(accountId.value),
      paperTradingApi.getOrders(accountId.value),
    ])
    const data = analytics.data.data
    currency.value = data.account.currency
    summary.value = data.summary
    trades.value = data.trades
    orders.value = orderList.data.data
  } catch (value: any) {
    showError(value, '交易记录加载失败')
  } finally {
    loading.value = false
  }
}
async function syncAndReload() {
  if (!accountId.value) return
  syncing.value = true
  syncError.value = ''
  try {
    await paperTradingApi.syncAccount(accountId.value)
    await loadAccounts(accountId.value)
  } catch (value: any) {
    syncError.value = value?.response?.data?.error || value?.message || '同步失败'
  } finally {
    syncing.value = false
  }
  await loadAll()
}
async function switchAccount() {
  syncError.value = ''
  if (selectedAccount.value?.is_external) await syncAndReload()
  else await loadAll()
}
async function cancel(order: PaperOrder) {
  cancelling.value = order.id
  error.value = ''
  try {
    await paperTradingApi.cancelOrder(order.id)
    await loadAll()
  } catch (value: any) {
    showError(value, '撤单失败')
  } finally {
    cancelling.value = undefined
  }
}

onMounted(async () => {
  try {
    await loadAccounts()
    await switchAccount()
  } catch (value: any) {
    showError(value, '账户加载失败')
  }
})
</script>

<style scoped>
.transaction-details {
  padding: 24px;
  min-height: 100vh;
  background: #f5f6f7;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: #1f2a28;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 14px;
  padding-bottom: 18px;
  border-bottom: 1px solid #dfe5e4;
}

.page-header h1 { margin: 0; font-size: 24px; font-weight: 600; }
.subtitle { margin: 6px 0 0; font-size: 13px; color: #6a7a76; }
.header-actions { display: flex; align-items: center; gap: 10px; }

.header-actions select,
.filter-bar input {
  padding: 9px 12px;
  border: 1px solid #c4cecc;
  background: #fff;
  font: inherit;
}

.ghost-btn {
  padding: 9px 16px;
  border: 1px solid #123c35;
  background: #fff;
  color: #123c35;
  cursor: pointer;
  text-decoration: none;
  font: inherit;
}

.ghost-btn:disabled { opacity: .55; cursor: not-allowed; }

.error-banner {
  margin: 16px 0 0;
  padding: 10px 14px;
  background: #fff0ed;
  border-left: 3px solid #b42318;
}

.error-banner.warn { background: #fff7e6; border-left-color: #9a6b00; }

.account-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
  margin-top: 14px;
  font-size: 12px;
  color: #6a7a76;
}

.mode-tag { padding: 2px 8px; font-size: 12px; background: #e7f5f1; color: #087a65; }
.mode-tag.live { background: #fdeceb; color: #b42318; }

.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 26px;
}

.section-heading h2 { margin: 0; font-size: 16px; font-weight: 600; }
.section-heading .hint { font-size: 12px; color: #8a9793; }

.status-tag { padding: 2px 8px; font-size: 12px; background: #eef1f0; color: #4a5a56; }
.status-tag.filled { background: #e7f5f1; color: #087a65; }
.status-tag.rejected { background: #fdeceb; color: #b42318; }
.status-tag.pending, .status-tag.submitted, .status-tag.partial { background: #fff7e6; color: #9a6b00; }
.status-tag.cancelled { background: #eef1f0; color: #71807c; }

.link-btn {
  border: 0;
  background: none;
  color: #b42318;
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  text-decoration: underline;
}

.link-btn:disabled { opacity: .5; cursor: not-allowed; }

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 20px;
}

.summary-card { background: #fff; border: 1px solid #e2e7e6; padding: 18px; }
.summary-card span { display: block; font-size: 12px; color: #71807c; }
.summary-card strong { display: block; margin: 8px 0 4px; font-size: 22px; }
.summary-card em { font-style: normal; font-size: 12px; color: #8a9793; }

.filter-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 20px;
  font-size: 12px;
  color: #6a7a76;
}

.side-filter { display: flex; border: 1px solid #c4cecc; }

.side-filter button {
  border: 0;
  background: #fff;
  padding: 9px 18px;
  cursor: pointer;
  font: inherit;
}

.side-filter .active { background: #123c35; color: #fff; }
.side-filter button em { margin-left: 6px; font-style: normal; font-size: 11px; opacity: .7; }
.filter-count { margin-left: auto; }

.table-card {
  margin-top: 12px;
  background: #fff;
  border: 1px solid #e2e7e6;
  padding: 8px 18px 18px;
  overflow-x: auto;
}

table { width: 100%; border-collapse: collapse; }

th, td {
  padding: 11px;
  text-align: right;
  border-bottom: 1px solid #eef1f0;
  font-size: 13px;
  white-space: nowrap;
}

th { color: #71807c; font-weight: 500; }
th:first-child, td:first-child, th:last-child, td:last-child { text-align: left; }

.side-tag { padding: 2px 8px; font-size: 12px; }
.side-tag.buy { background: #fdeceb; color: #b42318; }
.side-tag.sell { background: #e7f5f1; color: #087a65; }

.positive { color: #b42318; }
.negative { color: #087a65; }
.memo { font-size: 12px; color: #6a7a76; white-space: normal; max-width: 260px; }

.empty-card {
  margin-top: 20px;
  padding: 26px;
  background: #fff;
  border: 1px solid #e2e7e6;
  color: #8a9793;
  text-align: center;
}

@media (max-width: 900px) {
  .summary-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
