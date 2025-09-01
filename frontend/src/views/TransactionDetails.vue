<template>
  <div class="transaction-details">
    <!-- 策略头部区域 -->
    <div class="strategy-header">
      <div class="strategy-title">
        <h1>{{ strategyInfo.name }}</h1>
        <i class="fa fa-edit edit-icon"></i>
      </div>
      <div class="strategy-settings">
        <span class="setting-item">
          设置: {{ formatDate(strategyInfo.start_date) }} 到 {{ formatDate(strategyInfo.end_date) }}, 
          ¥{{ formatAmount(strategyInfo.initial_cash || 100000) }}, 每天
        </span>
      </div>
      <div class="strategy-status">
        <span class="status-item">
          <i class="fa fa-check-circle status-icon"></i>
          状态: {{ strategyInfo.status }}, 实际耗时{{ strategyInfo.runtime }} {{ strategyInfo.platform }}
        </span>
      </div>
    </div>

    <!-- 子导航/操作栏 -->
    <div class="sub-navigation">
      <div class="nav-tabs">
        <button class="nav-tab">编辑策略</button>
        <button class="nav-tab active">回测详情</button>
        <button class="nav-tab">编译运行列表</button>
        <button class="nav-tab">回测列表</button>
      </div>
      <div class="action-buttons">
        <button class="action-btn">模拟交易</button>
        <button class="action-btn">归因分析</button>
        <button class="action-btn">分享到社区</button>
        <button class="action-btn">导出</button>
      </div>
    </div>

    <!-- 交易详情面板 -->
    <div class="transaction-panel">
      <div class="panel-header">
        <h2>交易详情</h2>
        <button class="group-btn">Group by day</button>
      </div>

      <!-- 列显示控制 -->
      <div class="column-controls">
        <div class="control-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="visibleColumns.date" />
            <span>日期</span>
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="visibleColumns.orderTime" />
            <span>委托时间</span>
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="visibleColumns.target" />
            <span>标的</span>
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="visibleColumns.transactionType" />
            <span>交易类型</span>
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="visibleColumns.orderType" />
            <span>下单类型</span>
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="visibleColumns.quantity" />
            <span>成交数量</span>
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="visibleColumns.price" />
            <span>成交价</span>
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="visibleColumns.amount" />
            <span>成交额</span>
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="visibleColumns.pl" />
            <span>平仓盈亏</span>
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="visibleColumns.fee" />
            <span>手续费</span>
          </label>
        </div>
      </div>

      <!-- 交易表格 -->
      <div class="table-container">
        <table class="transaction-table">
          <thead>
            <tr>
              <th v-if="visibleColumns.date" class="sortable">
                日期
                <i class="fa fa-sort sort-icon"></i>
              </th>
              <th v-if="visibleColumns.orderTime">委托时间</th>
              <th v-if="visibleColumns.target">标的</th>
              <th v-if="visibleColumns.transactionType">交易类型</th>
              <th v-if="visibleColumns.orderType">下单类型</th>
              <th v-if="visibleColumns.quantity">成交数量</th>
              <th v-if="visibleColumns.price">成交价</th>
              <th v-if="visibleColumns.amount">成交额</th>
              <th v-if="visibleColumns.pl">平仓盈亏</th>
              <th v-if="visibleColumns.fee">手续费</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="transaction in filteredTransactions" :key="transaction.id">
              <td v-if="visibleColumns.date">{{ transaction.date }}</td>
              <td v-if="visibleColumns.orderTime">{{ transaction.orderTime }}</td>
              <td v-if="visibleColumns.target">{{ transaction.target }}</td>
              <td v-if="visibleColumns.transactionType">
                <span :class="['transaction-type', transaction.type]">
                  {{ transaction.transactionType }}
                </span>
              </td>
              <td v-if="visibleColumns.orderType">{{ transaction.orderType }}</td>
              <td v-if="visibleColumns.quantity">
                <span :class="{ 'negative': transaction.quantity < 0 }">
                  {{ transaction.quantity > 0 ? '+' : '' }}{{ transaction.quantity }}股
                </span>
              </td>
              <td v-if="visibleColumns.price">¥{{ formatAmount(transaction.price) }}</td>
              <td v-if="visibleColumns.amount">
                <span :class="{ 'negative': transaction.amount < 0 }">
                  {{ transaction.amount > 0 ? '+' : '' }}¥{{ formatAmount(Math.abs(transaction.amount)) }}
                </span>
              </td>
              <td v-if="visibleColumns.pl">
                <span :class="{ 'positive': transaction.pl > 0, 'negative': transaction.pl < 0 }">
                  {{ transaction.pl > 0 ? '+' : '' }}¥{{ formatAmount(Math.abs(transaction.pl)) }}
                </span>
              </td>
              <td v-if="visibleColumns.fee">¥{{ formatAmount(transaction.fee) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 聊天图标 -->
    <div class="chat-icon">
      <i class="fa fa-comments"></i>
      <span class="notification-badge">1</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface Transaction {
  id: number
  date: string
  orderTime: string
  target: string
  transactionType: string
  type: string
  orderType: string
  quantity: number
  price: number
  amount: number
  pl: number
  fee: number
}

interface StrategyInfo {
  name: string
  start_date: string
  end_date: string
  initial_cash: number
  status: string
  runtime: string
  platform: string
}

// 列显示控制
const visibleColumns = ref({
  date: true,
  orderTime: true,
  target: true,
  transactionType: true,
  orderType: true,
  quantity: true,
  price: true,
  amount: true,
  pl: true,
  fee: true
})

// 交易数据和策略信息
const transactions = ref<Transaction[]>([])
const strategyInfo = ref<StrategyInfo>({
  name: '加载中...',
  start_date: '',
  end_date: '',
  initial_cash: 0,
  status: '加载中',
  runtime: '',
  platform: ''
})
const loading = ref(true)
const error = ref('')

// 从缓存数据或localStorage获取交易详情数据
const fetchTransactionDetails = async () => {
  try {
    loading.value = true
    
    // 首先尝试从缓存API获取最新的回测结果
    try {
      console.log('📡 从缓存API获取交易详情数据')
      const response = await fetch('http://localhost:8002/api/cache/transaction-details/')
      
      if (response.ok) {
        const data = await response.json()
        
        if (data.status === 'success' && data.backtest_result && data.backtest_result.trades) {
          console.log('📊 使用缓存API数据')
          const backtestData = data.backtest_result
          
          // 将后端交易数据格式转换为前端显示格式
          const transformedTrades = backtestData.trades.map((trade: any, index: number) => ({
            id: index + 1,
            date: trade.date || trade.trade_time?.split('T')[0]?.replace(/-/g, '') || '20240101',
            orderTime: trade.trade_time?.split('T')[1]?.slice(0, 8) || '09:30:00',
            target: trade.stock_code || trade.symbol || '未知',
            transactionType: trade.action === 'buy' ? '买入' : '卖出',
            type: trade.action, // 添加类型用于样式
            orderType: '市价单',
            quantity: trade.shares || 0,
            price: Number(trade.price || 0),
            amount: Number(trade.amount || (trade.shares * trade.price)),
            pl: 0, // 盈亏需要计算
            fee: Number((trade.amount || (trade.shares * trade.price)) * 0.001) // 简化手续费计算
          }))
          
          transactions.value = transformedTrades
          
          // 设置策略信息 - 使用缓存数据中的实际执行时间和日期
          const timeRange = data.backtest_result?.time_period || data.data?.time_period || {}
          const strategyData = data.backtest_result?.strategy_info || backtestData
          
          console.log('🔍 调试数据结构:')
          console.log('  - data.backtest_result:', data.backtest_result ? '存在' : '不存在')
          console.log('  - data.data:', data.data ? '存在' : '不存在')
          console.log('  - timeRange:', timeRange)
          console.log('  - strategyData:', strategyData)
          
          strategyInfo.value = {
            name: strategyData.strategy_name || strategyData.name || '实时回测策略',
            start_date: timeRange.start_date || strategyData.start_date || '20230101',
            end_date: timeRange.end_date || strategyData.end_date || '20231231',
            initial_cash: strategyData.initial_cash || strategyData.total_cash || strategyData.initial_capital || 100000,
            status: '回测完成',
            runtime: data.execution_time || strategyData.execution_time || strategyData.runtime || '00分03秒',
            platform: 'Python3'
          }
          
          console.log('✅ 从缓存API加载交易数据成功:', transformedTrades.length, '条记录')
          console.log('⏱️ 实际执行时间:', data.execution_time)
          console.log('📅 日期范围:', strategyInfo.value.start_date, '到', strategyInfo.value.end_date)
          console.log('📊 完整策略信息:', strategyInfo.value)
          return
        }
      }
    } catch (apiError) {
      console.log('📦 缓存API未可用，尝试localStorage')
    }
    
    // 回退到localStorage数据
    const savedResults = localStorage.getItem('backtestResults')
    if (savedResults) {
      console.log('� 从localStorage加载回测交易数据')
      const backtestData = JSON.parse(savedResults)
      
      // 如果有交易数据，使用localStorage中的数据
      if (backtestData.trades && backtestData.trades.length > 0) {
        // 将后端交易数据格式转换为前端显示格式
        const transformedTrades = backtestData.trades.map((trade: any, index: number) => ({
          id: index + 1,
          date: trade.date || trade.trade_time?.split('T')[0]?.replace(/-/g, '') || '20240101',
          orderTime: trade.trade_time?.split('T')[1]?.slice(0, 8) || '09:30:00',
          target: trade.stock_code || trade.symbol || '未知',
          transactionType: trade.action === 'buy' ? '买入' : '卖出',
          type: trade.action, // 添加类型用于样式
          orderType: '市价单',
          quantity: trade.shares || 0,
          price: Number(trade.price || 0),
          amount: Number(trade.amount || (trade.shares * trade.price)),
          pl: 0, // 盈亏需要计算
          fee: Number((trade.amount || (trade.shares * trade.price)) * 0.001) // 简化手续费计算
        }))
        
        transactions.value = transformedTrades
        
        // 设置策略信息
        strategyInfo.value = {
          name: backtestData.strategyInfo?.strategy_name || '实时回测策略',
          start_date: backtestData.strategyInfo?.start_date || backtestData.startDate || '',
          end_date: backtestData.strategyInfo?.end_date || backtestData.endDate || '',
          initial_cash: backtestData.strategyInfo?.total_cash || backtestData.initialCapital || 100000,
          status: '回测完成',
          runtime: backtestData.executionTime || '00分03秒',
          platform: 'Python3'
        }
        
        console.log('✅ 从localStorage加载交易数据成功:', transformedTrades.length, '条记录')
        return
      }
    }
    
    // 如果都没有数据，显示空状态
    console.log('⚠️ 没有找到交易数据')
    transactions.value = []
    strategyInfo.value = {
      name: '实时回测策略',
      start_date: '',
      end_date: '',
      initial_cash: 100000,
      status: '无数据',
      runtime: '00分00秒',
      platform: 'Python3'
    }
    
  } catch (err: any) {
    console.error('❌ 获取交易详情失败:', err)
    error.value = `获取交易详情失败: ${err?.message || '未知错误'}`
    // 使用默认数据作为后备
    transactions.value = []
  } finally {
    loading.value = false
  }
}

// 过滤显示的交易数据
const filteredTransactions = computed(() => {
  return transactions.value
})

// 格式化日期显示
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  // 将 YYYYMMDD 格式转换为 YYYY-MM-DD
  if (dateStr.length === 8) {
    return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`
  }
  return dateStr
}

// 格式化金额，保留2位小数并添加千分符
const formatAmount = (amount: number) => {
  return Number(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 组件挂载时获取数据
onMounted(() => {
  fetchTransactionDetails()
})
</script>

<style scoped>
.transaction-details {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 策略头部区域 */
.strategy-header {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.strategy-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.strategy-title h1 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.edit-icon {
  color: #666;
  cursor: pointer;
  font-size: 16px;
  transition: color 0.2s;
}

.edit-icon:hover {
  color: #1890ff;
}

.strategy-settings {
  margin-bottom: 8px;
}

.setting-item {
  color: #666;
  font-size: 14px;
}

.strategy-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-item {
  color: #52c41a;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-icon {
  color: #52c41a;
  font-size: 16px;
}

/* 子导航/操作栏 */
.sub-navigation {
  background: white;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-tabs {
  display: flex;
  gap: 4px;
}

.nav-tab {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.nav-tab:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.nav-tab.active {
  background: #1890ff;
  color: white;
  border-color: #1890ff;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.action-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

/* 交易详情面板 */
.transaction-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.group-btn {
  padding: 4px 12px;
  border: 1px solid #d9d9d9;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.group-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

/* 列显示控制 */
.column-controls {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.control-group {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  margin: 0;
}

/* 表格容器 */
.table-container {
  overflow-x: auto;
  max-height: 600px;
  overflow-y: auto;
}

.transaction-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.transaction-table th {
  background: #fafafa;
  padding: 12px 8px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #f0f0f0;
  position: sticky;
  top: 0;
  z-index: 10;
}

.transaction-table td {
  padding: 12px 8px;
  border-bottom: 1px solid #f0f0f0;
  color: #333;
}

.transaction-table tbody tr:hover {
  background: #f5f5f5;
}

.sortable {
  cursor: pointer;
  user-select: none;
}

.sort-icon {
  margin-left: 4px;
  color: #999;
  font-size: 12px;
}

.transaction-type {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
}

.transaction-type.buy {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.transaction-type.sell {
  background: #fff2e8;
  color: #fa541c;
  border: 1px solid #ffbb96;
}

.positive {
  color: #52c41a;
}

.negative {
  color: #ff4d4f;
}

/* 聊天图标 */
.chat-icon {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 50px;
  height: 50px;
  background: #1890ff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
  transition: all 0.3s ease;
  z-index: 1000;
}

.chat-icon:hover {
  background: #40a9ff;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.4);
}

.chat-icon i {
  font-size: 20px;
}

.notification-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background: #ff4d4f;
  color: white;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .transaction-details {
    padding: 10px;
  }
  
  .sub-navigation {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .nav-tabs {
    flex-wrap: wrap;
  }
  
  .action-buttons {
    flex-wrap: wrap;
  }
  
  .control-group {
    gap: 12px;
  }
  
  .transaction-table {
    font-size: 12px;
  }
  
  .transaction-table th,
  .transaction-table td {
    padding: 8px 6px;
  }
}
</style> 