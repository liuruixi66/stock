<template>
  <div class="transaction-details">
    <div class="page-header">
      <div>
        <h1>模拟盘交易记录</h1>
        <p class="subtitle">每一笔模拟委托的成交价、费用与平仓盈亏，按 FIFO 口径逐笔配对。</p>
      </div>
      <div class="header-actions">
        <select v-model.number="accountId" @change="loadAnalytics">
          <option v-for="item in accounts" :key="item.id" :value="item.id">
            {{ item.name }}（{{ item.market === 'A' ? 'A股' : '美股' }}）
          </option>
        </select>
        <button class="ghost-btn" :disabled="loading" @click="loadAnalytics">
          {{ loading ? '加载中' : '刷新' }}
        </button>
        <RouterLink class="ghost-btn" to="/research-terminal">去交易台下单</RouterLink>
      </div>
    </div>

    <p v-if="error" class="error-banner">{{ error }}</p>

    <div v-if="!accounts.length" class="empty-card">
      还没有模拟账户，先到量化研究交易台创建一个并提交订单。
    </div>

    <template v-else>
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
          <span>交易费用</span>
          <strong>{{ money(summary.total_fees) }}</strong>
          <em>佣金与印花税合计</em>
        </div>
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
              <td>{{ trade.side === 'BUY' ? '+' : '-' }}{{ trade.quantity }}</td>
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

interface PaperAccount { id: number; name: string; market: 'A' | 'US' }

const accounts = ref<PaperAccount[]>([])
const accountId = ref<number>()
const currency = ref('CNY')
const summary = ref<any>({
  trade_count: 0, buy_count: 0, sell_count: 0, closed_count: 0,
  realized_pnl: 0, unrealized_pnl: 0, market_value: 0, total_fees: 0,
})
const trades = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const symbolFilter = ref('')
const sideFilter = ref('ALL')
const sideOptions = [
  { value: 'ALL', label: '全部' },
  { value: 'BUY', label: '买入' },
  { value: 'SELL', label: '卖出' },
]

const filteredTrades = computed(() => trades.value.filter((trade) => {
  const symbolMatched = !symbolFilter.value || trade.symbol.includes(symbolFilter.value.trim().toUpperCase())
  return symbolMatched && (sideFilter.value === 'ALL' || trade.side === sideFilter.value)
}))

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

async function loadAnalytics() {
  if (!accountId.value) return
  loading.value = true
  error.value = ''
  try {
    const data = (await paperTradingApi.getAnalytics(accountId.value)).data.data
    currency.value = data.account.currency
    summary.value = data.summary
    trades.value = data.trades
  } catch (value: any) {
    error.value = value?.response?.data?.error || '交易记录加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    accounts.value = (await paperTradingApi.getAccounts()).data.data
    accountId.value = accounts.value[0]?.id
    await loadAnalytics()
  } catch (value: any) {
    error.value = value?.response?.data?.error || '账户加载失败'
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
.memo { font-size: 12px; color: #6a7a76; }

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
