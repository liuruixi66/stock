<template>
  <div class="table-container">
    <div class="table-header">
      <h2>{{ title }}</h2>
      <div class="controls">
        <div class="search-box">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索..." 
            class="search-input"
            @input="handleSearch"
          >
          <i class="fa fa-search search-icon"></i>
        </div>
        <button @click="fetchData" class="refresh-btn">
          <i class="fa fa-refresh" :class="{ 'fa-spin': loading }"></i>
          刷新数据
        </button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div class="table-wrapper">
      <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th v-for="(value, key) in headers" 
                :key="key" 
                  :data-column="key"
                @click="sortBy(key)"
                :class="{ sortable: true, active: sortKey === key }">
              {{ value }}
              <i class="fa" :class="getSortIcon(key)"></i>
            </th>
          </tr>
        </thead>
        <tbody>
            <template v-if="paginatedData.length">
              <tr v-for="(row, index) in paginatedData" :key="index">
                <td v-for="(value, key) in headers" 
                    :key="key"
                    :data-column="key"
                    :data-type="getColumnType(key)"
                    :data-value="row[key]">
                  {{ formatValue(row[key], key) }}
              </td>
            </tr>
          </template>
          <tr v-else-if="loading">
            <td :colspan="Object.keys(headers).length" class="loading-cell">
              <div class="loading-spinner"></div>
              加载中...
            </td>
          </tr>
          <tr v-else>
            <td :colspan="Object.keys(headers).length" class="empty-cell">
              暂无数据
            </td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>

    <div class="table-footer">
      <div class="pagination">
        <button 
          @click="prevPage" 
          :disabled="currentPage === 1"
          class="page-btn"
        >
          <i class="fa fa-angle-left"></i>
        </button>
        <span class="page-info">第 {{ currentPage }} 页，共 {{ totalPages }} 页</span>
        <button 
          @click="nextPage" 
          :disabled="currentPage === totalPages"
          class="page-btn"
        >
          <i class="fa fa-angle-right"></i>
        </button>
      </div>
      <div class="page-size">
        每页显示：
        <select v-model="pageSize" @change="handlePageSizeChange">
          <option v-for="size in pageSizes" :key="size" :value="size">
            {{ size }}
          </option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const props = defineProps<{ title: string }>()

// 数据状态
const stockData = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const searchQuery = ref('')
const sortKey = ref('')
const sortOrder = ref('asc')
const currentPage = ref(1)
const pageSize = ref(10)
const pageSizes = [10, 20, 50, 100]

// 根据截图显示的字段定义表头
const headers = {
  'date': '日期',
  'code': '代码',
  'name': '名称',
  'new_price': '最新价',
  'change_rate': '涨跌幅',
  'ups_downs': '涨跌额',
  'volume': '成交量',
  'deal_amount': '成交额',
  'amplitude': '振幅',
  'turnoverrate': '换手率',
  'volume_ratio': '量比',
  'open_price': '今开',
  'high_price': '最高',
  'low_price': '最低',
  'pre_close_price': '昨收',
  'speed_increase': '涨速',
  'speed_increase_5': '5分钟涨跌',
  'speed_increase_60': '60日涨跌幅',
  'speed_increase_all': '年初至今涨跌幅'
}

// 列宽配置
const columnWidths = {
  'date': 80,
  'code': 50,
  'name': 50,
  'new_price': 60,
  'change_rate': 70,
  'ups_downs': 70,
  'volume': 90,
  'deal_amount': 100,
  'amplitude': 70,
  'turnoverrate': 70,
  'volume_ratio': 70,
  'open_price': 70,
  'high_price': 70,
  'low_price': 70,
  'pre_close_price': 70,
  'speed_increase': 70,
  'speed_increase_5': 70,
  'speed_increase_60': 70,
  'speed_increase_all': 70
}

// 示例数据
const mockData = [{
  date: '2025-07-21',
  code: '603893',
  name: '瑞芯微',
  new_price: 161.95,
  change_rate: 5.31,
  ups_downs: 8.15,
  volume: 123.46,
  deal_amount: 12345.67,
  amplitude: 3.21,
  turnoverrate: 2.34,
  volume_ratio: 1.23,
  open_price: 160.00,
  high_price: 162.50,
  low_price: 159.80,
  pre_close_price: 153.80,
  speed_increase: 0.50,
  speed_increase_5: 1.20,
  speed_increase_60: 15.30,
  speed_increase_all: 25.60
}]

// 计算属性
const filteredData = computed(() => {
  console.log('filteredData计算开始，原始数据:', stockData.value)
  let data = [...stockData.value]
  
  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    data = data.filter(item => 
      Object.values(item).some(val => 
        String(val).toLowerCase().includes(query)
      )
    )
  }
  
  // 排序
  if (sortKey.value) {
    data.sort((a, b) => {
      const aVal = a[sortKey.value]
      const bVal = b[sortKey.value]
      const modifier = sortOrder.value === 'asc' ? 1 : -1
      
      // 数字类型的比较
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return (aVal - bVal) * modifier
      }
      
      // 字符串类型的比较
      return String(aVal).localeCompare(String(bVal)) * modifier
    })
  }
  
  console.log('filteredData计算结果:', data)
  return data
})

const paginatedData = computed(() => {
  console.log('paginatedData计算开始，过滤后数据长度:', filteredData.value.length)
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  const result = filteredData.value.slice(start, end)
  console.log('paginatedData计算结果:', result)
  return result
})

const totalPages = computed(() => 
  Math.ceil(filteredData.value.length / pageSize.value)
)

// 方法
const fetchData = async () => {
  console.log('开始获取数据...')
  loading.value = true
  error.value = ''
  try {
    // 使用模拟数据
    stockData.value = mockData
    console.log('数据处理完成，stockData:', stockData.value)
  } catch (e: any) {
    console.error('请求出错:', e)
    error.value = `数据加载错误: ${e.message}`
  } finally {
    loading.value = false
    console.log('数据获取流程结束')
  }
}

const handleSearch = () => {
  currentPage.value = 1
}

const sortBy = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

const getSortIcon = (key: string) => {
  if (sortKey.value !== key) return 'fa-sort'
  return sortOrder.value === 'asc' ? 'fa-sort-up' : 'fa-sort-down'
}

// 格式化数据
const formatValue = (value: any, key: string) => {
  if (value === undefined || value === null) return '-'
  
  if (typeof value === 'number') {
    // 处理百分比类型
    if (['change_rate', 'amplitude', 'turnoverrate', 'speed_increase', 
         'speed_increase_5', 'speed_increase_60', 'speed_increase_all'].includes(key)) {
      return (value > 0 ? '+' : '') + value.toFixed(2) + '%'
    }
    // 处理成交量（万手）
    if (key === 'volume') {
      return value.toFixed(2) + '万手'
    }
    // 处理成交额（万元）
    if (key === 'deal_amount') {
      return value.toFixed(2) + '万'
    }
    // 处理价格
    if (['new_price', 'open_price', 'high_price', 'low_price', 'pre_close_price', 'ups_downs'].includes(key)) {
      return value.toFixed(2)
    }
    // 处理量比
    if (key === 'volume_ratio') {
      return value.toFixed(2)
    }
    return value.toLocaleString()
  }
  return value
}

const prevPage = () => {
  if (currentPage.value > 1) currentPage.value--
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) currentPage.value++
}

const handlePageSizeChange = () => {
  currentPage.value = 1
}

// 自动刷新
let refreshInterval: number | null = null

const startAutoRefresh = () => {
  if (!refreshInterval) {
    refreshInterval = window.setInterval(fetchData, 30000) // 每30秒刷新一次
  }
}

const stopAutoRefresh = () => {
  if (refreshInterval) {
    window.clearInterval(refreshInterval)
    refreshInterval = null
  }
}

// 生命周期
onMounted(() => {
  console.log('Component mounted')
  fetchData()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})

// 获取列类型
const getColumnType = (key: string) => {
  if (key === 'date') return 'date'
  if (['code', 'name'].includes(key)) return 'text'
  if (['change_rate', 'amplitude', 'turnoverrate', 'speed_increase',
       'speed_increase_5', 'speed_increase_60', 'speed_increase_all'].includes(key)) return 'rate'
  if (['volume', 'deal_amount'].includes(key)) return 'amount'
  if (['new_price', 'open_price', 'high_price', 'low_price', 'pre_close_price', 'ups_downs'].includes(key)) return 'price'
  if (key === 'volume_ratio') return 'ratio'
  return 'text'
}
</script>

<style scoped>
.table-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 15px;  /* 减小容器内边距 */
  margin: 15px;  /* 减小容器外边距 */
  height: calc(100vh - 40px); /* 设置容器高度 */
  display: flex;
  flex-direction: column;
}

.error-message {
  color: #f56c6c;
  padding: 10px;
  margin: 10px 0;
  background-color: #fef0f0;
  border-radius: 4px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.5em;
}

.controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.search-box {
  position: relative;
}

.search-input {
  padding: 6px 28px 6px 10px;  /* 减小搜索框内边距 */
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  width: 180px;  /* 减小搜索框宽度 */
  transition: all 0.3s;
  font-size: 13px;  /* 稍微减小字体大小 */
}

.search-input:focus {
  border-color: #409eff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.search-icon {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #909399;
}

.refresh-btn {
  padding: 6px 12px;  /* 减小按钮内边距 */
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
}

.refresh-btn:hover {
  background: #66b1ff;
}

.refresh-btn:active {
  background: #3a8ee6;
}

/* 表格滚动容器 */
.table-wrapper {
  position: relative;
  flex: 1;
  overflow: hidden;
}

.table-scroll {
  width: 100%;
  height: 100%;
  overflow: auto;
}

/* 表格基础样式 */
table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

/* 单元格基础样式 */
th, td {
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
  white-space: nowrap;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 调整表头样式 */
th {
  background: #f5f7fa;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
  padding: 8px 10px;  /* 与td保持一致 */
  font-size: 13px;  /* 与td保持一致 */
}

th.sortable {
  cursor: pointer;
  user-select: none;
}

th.sortable:hover {
  background: #ebeef5;
}

th.active {
  color: #409eff;
}

.loading-cell, .empty-cell {
  text-align: center;
  padding: 40px;
  color: #909399;
}

.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-btn {
  padding: 4px 8px;  /* 减小翻页按钮内边距 */
  border: 1px solid #dcdfe6;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.page-btn:not(:disabled):hover {
  color: #409eff;
  border-color: #409eff;
}

.page-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.page-info {
  color: #606266;
}

.page-size {
  display: flex;
  align-items: center;
  gap: 8px;
}

select {
  padding: 4px;  /* 减小选择框内边距 */
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  outline: none;
  cursor: pointer;
}

select:focus {
  border-color: #409eff;
}

tr:hover {
  background-color: #f5f7fa;
}

/* 设置列宽 */
[data-column="date"] { width: 80px; }
[data-column="code"] { width: 60px; }
[data-column="name"] { width: 70px; }
[data-column="new_price"] { width: 70px; }
[data-column="change_rate"] { width: 70px; }
[data-column="ups_downs"] { width: 70px; }
[data-column="volume"] { width: 90px; }
[data-column="deal_amount"] { width: 100px; }
[data-column="amplitude"] { width: 70px; }
[data-column="turnoverrate"] { width: 70px; }
[data-column="volume_ratio"] { width: 70px; }
[data-column="open_price"] { width: 70px; }
[data-column="high_price"] { width: 70px; }
[data-column="low_price"] { width: 70px; }
[data-column="pre_close_price"] { width: 70px; }
[data-column="speed_increase"] { width: 70px; }
[data-column="speed_increase_5"] { width: 70px; }
[data-column="speed_increase_60"] { width: 70px; }
[data-column="speed_increase_all"] { width: 70px; }

/* 添加正负值的颜色显示 */
td[data-type="rate"],
td[data-type="amount"],
td[data-type="price"],
td[data-type="ratio"] {
  color: #333;
  text-align: right; /* 数字列右对齐 */
}

td[data-type="text"] {
  text-align: left;
}

td[data-type="date"] {
  text-align: center;
}

td[data-type="rate"]:not(:empty),
td[data-type="amount"]:not(:empty),
td[data-type="price"]:not(:empty),
td[data-type="ratio"]:not(:empty) {
  color: #333;
}

td[data-type="rate"][data-value^="-"],
td[data-type="amount"][data-value^="-"],
td[data-type="price"][data-value^="-"],
td[data-type="ratio"][data-value^="-"] {
  color: green;
}

td[data-type="rate"]:not([data-value^="-"]),
td[data-type="amount"]:not([data-value^="-"]),
td[data-type="price"]:not([data-value^="-"]),
td[data-type="ratio"]:not([data-value^="-"]) {
  color: red;
}

.fa-spin {
  animation: fa-spin 2s infinite linear;
}

@keyframes fa-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
