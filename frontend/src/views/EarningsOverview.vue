<template>
  <div class="earnings-overview">
    <div class="page-header">
      <div>
        <h1>分析报告</h1>
        <p class="subtitle">模拟盘绩效与量化研究成果的统一复盘视图。</p>
      </div>
      <div class="header-actions">
        <select v-model.number="accountId" @change="loadAll">
          <option v-for="item in accounts" :key="item.id" :value="item.id">
            {{ item.name }}（{{ item.market === 'A' ? 'A股' : item.market === 'US' ? '美股' : '虚拟货币' }}）
          </option>
        </select>
        <button class="ghost-btn" :disabled="loading" @click="loadAll">{{ loading ? '加载中' : '刷新' }}</button>
        <RouterLink class="ghost-btn" to="/transaction-details">查看逐笔记录</RouterLink>
      </div>
    </div>

    <p v-if="error" class="error-banner">{{ error }}</p>

    <div v-if="!accounts.length" class="empty-card">
      还没有模拟账户，先到量化研究交易台创建一个并提交订单。
    </div>

    <template v-else>
      <section class="metrics-panel">
        <h2>账户绩效</h2>
        <div class="metrics-grid">
          <div v-for="metric in accountMetrics" :key="metric.label" class="metric-item">
            <span class="metric-label">{{ metric.label }}</span>
            <span class="metric-value" :class="metric.tone">{{ metric.value }}</span>
          </div>
        </div>
      </section>

      <section class="chart-panel">
        <div class="panel-heading">
          <h2>已实现盈亏走势</h2>
          <span class="hint">按平仓时点累计，单位 {{ currency }}</span>
        </div>
        <div v-show="realizedCurve.length" ref="pnlChartElement" class="chart"></div>
        <p v-if="!realizedCurve.length" class="empty-card inline">尚无平仓交易，卖出后即可生成盈亏曲线。</p>
      </section>

      <section class="chart-panel">
        <div class="panel-heading">
          <h2>持仓结构</h2>
          <span class="hint">按当前市值占比</span>
        </div>
        <div class="holdings-layout">
          <div v-show="positions.length" ref="holdingChartElement" class="chart holding-chart"></div>
          <table v-if="positions.length" class="holding-table">
            <thead><tr><th>标的</th><th>数量</th><th>成本</th><th>现价</th><th>市值</th><th>浮动盈亏</th></tr></thead>
            <tbody>
              <tr v-for="position in positions" :key="position.symbol">
                <td>{{ position.symbol }}</td>
                <td>{{ position.quantity }}</td>
                <td>{{ position.average_price.toFixed(2) }}</td>
                <td>{{ position.current_price.toFixed(2) }}</td>
                <td>{{ position.market_value.toFixed(2) }}</td>
                <td :class="pnlClass(position.unrealized_pnl)">{{ position.unrealized_pnl.toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else class="empty-card inline">当前空仓。</p>
        </div>
      </section>

      <section class="chart-panel">
        <div class="panel-heading">
          <h2>研究策略绩效对比</h2>
          <span class="hint">来自量化研究交易台的历史回测</span>
        </div>
        <table v-if="runs.length" class="research-table">
          <thead>
            <tr><th>时间</th><th>标的</th><th>参数</th><th>区间</th><th>总收益</th><th>最大回撤</th><th>夏普</th><th>成交次数</th></tr>
          </thead>
          <tbody>
            <tr v-for="run in runs" :key="run.id">
              <td>{{ formatTime(run.created_at) }}</td>
              <td>{{ run.market }} {{ run.symbol }}</td>
              <td>MA{{ run.parameters.short_window }}/{{ run.parameters.long_window }}</td>
              <td>{{ run.start_date }} ~ {{ run.end_date }}</td>
              <td :class="pnlClass(run.total_return)">{{ run.total_return }}%</td>
              <td class="negative">{{ run.max_drawdown }}%</td>
              <td>{{ run.sharpe_ratio }}</td>
              <td>{{ run.trade_count }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty-card inline">还没有研究记录，去交易台运行一次回测。</p>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import * as echarts from 'echarts'
import { paperTradingApi, researchApi } from '@/api/stock'

interface PaperAccount { id: number; name: string; market: 'A' | 'US' | 'CRYPTO' }

const accounts = ref<PaperAccount[]>([])
const accountId = ref<number>()
const currency = ref('CNY')
const summary = ref<any>({})
const positions = ref<any[]>([])
const realizedCurve = ref<any[]>([])
const runs = ref<any[]>([])
const loading = ref(false)
const error = ref('')

const pnlChartElement = ref<HTMLElement>()
const holdingChartElement = ref<HTMLElement>()
let pnlChart: echarts.ECharts | undefined
let holdingChart: echarts.ECharts | undefined

const accountMetrics = computed(() => {
  const value = summary.value
  const unit = (amount: number) => `${(amount ?? 0).toFixed(2)} ${currency.value}`
  return [
    { label: '总资产', value: unit(value.total_assets), tone: '' },
    { label: '总收益率', value: `${(value.total_return ?? 0).toFixed(2)}%`, tone: toneOf(value.total_return) },
    { label: '已实现盈亏', value: unit(value.realized_pnl), tone: toneOf(value.realized_pnl) },
    { label: '浮动盈亏', value: unit(value.unrealized_pnl), tone: toneOf(value.unrealized_pnl) },
    { label: '持仓市值', value: unit(value.market_value), tone: '' },
    { label: '交易费用', value: unit(value.total_fees), tone: '' },
    { label: '成交笔数', value: `${value.trade_count ?? 0}`, tone: '' },
    { label: '平仓笔数', value: `${value.closed_count ?? 0}`, tone: '' },
    { label: '胜率', value: `${(value.win_rate ?? 0).toFixed(2)}%`, tone: '' },
    { label: '盈亏比', value: (value.profit_loss_ratio ?? 0).toFixed(2), tone: '' },
    { label: '平均盈利', value: unit(value.average_win), tone: toneOf(value.average_win) },
    { label: '平均亏损', value: unit(value.average_loss), tone: toneOf(value.average_loss) },
    { label: '最佳单笔', value: unit(value.best_trade), tone: toneOf(value.best_trade) },
    { label: '最差单笔', value: unit(value.worst_trade), tone: toneOf(value.worst_trade) },
  ]
})

function toneOf(value: number) {
  if (!value) return ''
  return value > 0 ? 'positive' : 'negative'
}
function pnlClass(value: number) {
  return toneOf(value)
}
function formatTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

function drawCharts() {
  if (realizedCurve.value.length && pnlChartElement.value) {
    pnlChart ||= echarts.init(pnlChartElement.value)
    pnlChart.setOption({
      grid: { left: 62, right: 24, top: 26, bottom: 40 },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: realizedCurve.value.map((item) => item.date), axisLabel: { color: '#718096' } },
      yAxis: { type: 'value', scale: true, axisLabel: { color: '#718096' }, splitLine: { lineStyle: { color: '#e8edf2' } } },
      series: [{
        type: 'line', smooth: true, showSymbol: true,
        data: realizedCurve.value.map((item) => item.cumulative_pnl),
        lineStyle: { color: '#006d5b', width: 2 },
        areaStyle: { color: 'rgba(0,109,91,.09)' },
      }],
    })
  }
  if (positions.value.length && holdingChartElement.value) {
    holdingChart ||= echarts.init(holdingChartElement.value)
    holdingChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{
        type: 'pie', radius: ['46%', '72%'], center: ['50%', '52%'],
        label: { formatter: '{b}\n{d}%', color: '#4a5a56' },
        data: positions.value.map((item) => ({ name: item.symbol, value: Number(item.market_value.toFixed(2)) })),
      }],
    })
  }
}

async function loadAll() {
  if (!accountId.value) return
  loading.value = true
  error.value = ''
  try {
    const [analytics, runList] = await Promise.all([
      paperTradingApi.getAnalytics(accountId.value),
      researchApi.getRuns(),
    ])
    const data = analytics.data.data
    currency.value = data.account.currency
    summary.value = data.summary
    positions.value = data.positions
    realizedCurve.value = data.realized_curve
    runs.value = runList.data.data
    await nextTick()
    drawCharts()
  } catch (value: any) {
    error.value = value?.response?.data?.error || '分析数据加载失败'
  } finally {
    loading.value = false
  }
}

function resizeCharts() {
  pnlChart?.resize()
  holdingChart?.resize()
}

onMounted(async () => {
  window.addEventListener('resize', resizeCharts)
  try {
    accounts.value = (await paperTradingApi.getAccounts()).data.data
    accountId.value = accounts.value[0]?.id
    await loadAll()
  } catch (value: any) {
    error.value = value?.response?.data?.error || '账户加载失败'
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  pnlChart?.dispose()
  holdingChart?.dispose()
})
</script>

<style scoped>
.earnings-overview {
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

.header-actions select {
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

.metrics-panel,
.chart-panel {
  margin-top: 20px;
  padding: 20px;
  background: #fff;
  border: 1px solid #e2e7e6;
}

.metrics-panel h2,
.panel-heading h2 { margin: 0; font-size: 17px; font-weight: 600; }

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 14px;
}

.hint { font-size: 12px; color: #8a9793; }

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 14px;
  margin-top: 16px;
}

.metric-item {
  padding: 12px;
  background: #f8faf9;
  border: 1px solid #eef1f0;
}

.metric-label { display: block; font-size: 12px; color: #71807c; }
.metric-value { display: block; margin-top: 6px; font-size: 17px; font-weight: 600; }

.chart { height: 300px; }
.holding-chart { flex: 0 0 330px; height: 260px; }
.holdings-layout { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.holding-table, .research-table { flex: 1; min-width: 320px; border-collapse: collapse; width: 100%; }

th, td {
  padding: 10px;
  text-align: right;
  border-bottom: 1px solid #eef1f0;
  font-size: 13px;
  white-space: nowrap;
}

th { color: #71807c; font-weight: 500; }
th:first-child, td:first-child { text-align: left; }

.positive { color: #b42318; }
.negative { color: #087a65; }

.empty-card {
  padding: 26px;
  background: #fff;
  border: 1px solid #e2e7e6;
  color: #8a9793;
  text-align: center;
}

.empty-card.inline { border: 0; padding: 18px; }

@media (max-width: 1280px) {
  .metrics-grid { grid-template-columns: repeat(4, 1fr); }
}

@media (max-width: 760px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
