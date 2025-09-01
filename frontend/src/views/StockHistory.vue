<template>
  <div class="stock-history">
    <div class="control-panel">
      <div class="search-box">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="输入股票代码或名称搜索"
          @input="handleSearch"
        >
      </div>
      <div class="date-picker">
        <input 
          type="date" 
          v-model="selectedDate"
          @change="loadData"
        >
      </div>
      <button @click="loadData" class="refresh-btn">
        <i class="fa fa-refresh"></i> 刷新
      </button>
    </div>

    <div class="data-panel">
      <div class="stock-list" v-if="!selectedStock">
        <table>
          <thead>
            <tr>
              <th>代码</th>
              <th>名称</th>
              <th>最新价</th>
              <th>涨跌幅</th>
              <th>成交量</th>
              <th>成交额</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stock in filteredStocks" :key="stock.code">
              <td>{{ stock.code }}</td>
              <td>{{ stock.name }}</td>
              <td>{{ stock.history[stock.history.length - 1]?.close }}</td>
              <td :class="getChangeClass(stock.history[stock.history.length - 1]?.change_rate)">
                {{ formatNumber(stock.history[stock.history.length - 1]?.change_rate, 2) }}%
              </td>
              <td>{{ formatVolume(stock.history[stock.history.length - 1]?.volume) }}</td>
              <td>{{ formatAmount(stock.history[stock.history.length - 1]?.amount) }}</td>
              <td>
                <button @click="viewStockDetail(stock)" class="detail-btn">
                  查看详情
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="stock-detail" v-else>
        <div class="detail-header">
          <button @click="selectedStock = null" class="back-btn">
            <i class="fa fa-arrow-left"></i> 返回
          </button>
          <h2>{{ selectedStock.name }}({{ selectedStock.code }}) 历史数据</h2>
        </div>
        
        <div class="chart-container">
          <!-- 这里可以添加图表组件 -->
        </div>

        <div class="history-table">
          <table>
            <thead>
              <tr>
                <th>日期</th>
                <th>开盘价</th>
                <th>最高价</th>
                <th>最低价</th>
                <th>收盘价</th>
                <th>涨跌幅</th>
                <th>成交量</th>
                <th>成交额</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(record, index) in selectedStock.history" :key="index">
                <td>{{ formatDate(record.date) }}</td>
                <td>{{ formatNumber(record.open) }}</td>
                <td>{{ formatNumber(record.high) }}</td>
                <td>{{ formatNumber(record.low) }}</td>
                <td>{{ formatNumber(record.close) }}</td>
                <td :class="getChangeClass(record.change_rate)">
                  {{ formatNumber(record.change_rate, 2) }}%
                </td>
                <td>{{ formatVolume(record.volume) }}</td>
                <td>{{ formatAmount(record.amount) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import axios from 'axios'

const searchQuery = ref('')
const selectedDate = ref(new Date().toISOString().split('T')[0])
const stocks = ref([])
const selectedStock = ref(null)
const loading = ref(false)

const filteredStocks = computed(() => {
  if (!searchQuery.value) return stocks.value
  const query = searchQuery.value.toLowerCase()
  return stocks.value.filter(stock => 
    stock.code.toLowerCase().includes(query) || 
    stock.name.toLowerCase().includes(query)
  )
})

const loadData = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/stock/history', {
      params: {
        date: selectedDate.value
      }
    })
    if (response.data.code === 200) {
      stocks.value = response.data.data
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

const viewStockDetail = async (stock) => {
  try {
    loading.value = true
    const response = await axios.get(`/api/stock/history/${stock.code}`, {
      params: {
        date: selectedDate.value
      }
    })
    if (response.data.code === 200) {
      selectedStock.value = response.data.data
    }
  } catch (error) {
    console.error('加载股票详情失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // 实现搜索逻辑
}

const formatNumber = (num: number, decimals = 2) => {
  if (num === undefined || num === null) return '-'
  return num.toFixed(decimals)
}

const formatVolume = (volume: number) => {
  if (volume === undefined || volume === null) return '-'
  return (volume / 10000).toFixed(2) + '万'
}

const formatAmount = (amount: number) => {
  if (amount === undefined || amount === null) return '-'
  return (amount / 100000000).toFixed(2) + '亿'
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString()
}

const getChangeClass = (change: number) => {
  if (!change) return ''
  return change > 0 ? 'positive' : change < 0 ? 'negative' : ''
}

// 初始加载数据
loadData()
</script>

<style scoped>
.stock-history {
  padding: 20px;
}

.control-panel {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.search-box input,
.date-picker input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.refresh-btn,
.detail-btn,
.back-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: #409eff;
  color: white;
  cursor: pointer;
  transition: all 0.3s;
}

.refresh-btn:hover,
.detail-btn:hover,
.back-btn:hover {
  background: #66b1ff;
}

.data-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background: #f5f7fa;
  font-weight: 500;
}

.positive {
  color: #f56c6c;
}

.negative {
  color: #67c23a;
}

.detail-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  gap: 20px;
}

.chart-container {
  height: 400px;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.history-table {
  padding: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .control-panel {
    flex-direction: column;
  }
  
  .search-box,
  .date-picker {
    width: 100%;
  }
  
  table {
    display: block;
    overflow-x: auto;
  }
}
</style> 