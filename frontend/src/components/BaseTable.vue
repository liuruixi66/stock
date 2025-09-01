<template>
  <div class="table-container">


    <!-- 表格主体 -->
    <div class="table-wrapper">
      <!-- 可滚动区域 -->
      <div class="table-scroll">
        <table>
          <colgroup>
            <col v-for="(_, key) in headers" :key="key" :class="getColumnClass(key)">
          </colgroup>
          <thead>
            <tr>
              <th
                v-for="(label, key) in headers"
                :key="key"
                :class="[
                  ...getColumnClass(key),
                  { sortable: isSortable(key) }
                ]"
                @click="handleSort(key)"
              >
                {{ label }}
                <span v-if="isSortable(key)" class="sort-icon">
                  {{ getSortIcon(key) }}
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in displayData" :key="index">
              <td
                v-for="(_, key) in headers"
                :key="key"
                :class="[
                  ...getColumnClass(key),
                  getValueClass(row[key], key)
                ]"
              >
                {{ formatValue(row[key], key) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 表格底部分页 -->
    <div class="table-footer">
      <div class="pagination-info">
        显示 {{ startIndex + 1 }}-{{ endIndex }} 条，共 {{ totalItems }} 条
      </div>
      <div class="pagination">
        <button
          class="page-btn first"
          :disabled="currentPage === 1"
          @click="changePage(1)"
        >
          首页
        </button>
        <button
          class="page-btn prev"
          :disabled="currentPage === 1"
          @click="changePage(currentPage - 1)"
        >
          上一页
        </button>
        <div class="page-number-group">
        <span class="page-number">{{ currentPage }} / {{ totalPages }}</span>
        </div>
        <button
          class="page-btn next"
          :disabled="currentPage === totalPages"
          @click="changePage(currentPage + 1)"
        >
          下一页
        </button>
        <button
          class="page-btn last"
          :disabled="currentPage === totalPages"
          @click="changePage(totalPages)"
        >
          末页
        </button>
        <div class="page-size">
          <select v-model="pageSize" @change="handlePageSizeChange">
            <option v-for="size in pageSizeOptions" :key="size" :value="size">
              {{ size }}条/页
            </option>
          </select>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

interface TableRow {
  [key: string]: string | number | null | undefined;
}

interface TableHeaders {
  [key: string]: string;
}

interface TableColumnTypes {
  [key: string]: string;
}

interface TableFormatters {
  [key: string]: (value: any) => string;
}

const props = defineProps<{
  headers: TableHeaders;
  apiUrl: string;
  columnTypes?: TableColumnTypes;
  formatters?: TableFormatters;
  queryParams?: Record<string, string>;  // 修改类型为 string
}>()

// 数据状态
const rawData = ref<TableRow[]>([])
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(50)
const pageSizeOptions = [20, 50, 100, 200, 500, 1000]
const sortKey = ref('')
const sortOrder = ref<'asc' | 'desc' | ''>('')

// 计算可滚动列的表头
const scrollableHeaders = computed(() => {
  const { date, code, name, ...rest } = props.headers
  return rest
})

// 获取数据
const fetchData = async () => {
  try {
    console.log('正在获取数据:', props.apiUrl)
    console.log('查询参数:', props.queryParams)
    
    // 构建查询参数
    const params = new URLSearchParams()
    
    // 添加查询参数
    if (props.queryParams && Object.keys(props.queryParams).length > 0) {
      Object.entries(props.queryParams).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, String(value))
        }
      })
    }
    
    // 添加搜索参数
    if (searchQuery.value) {
      params.append('search', searchQuery.value)
    }
    
    // 添加分页参数
    params.append('page', String(currentPage.value))
    params.append('page_size', String(pageSize.value))
    
    // 添加排序参数
    if (sortKey.value && sortOrder.value) {
      params.append('sort_by', sortKey.value)
      params.append('sort_order', sortOrder.value)
    }
    
    // 构建完整URL
    const url = `${props.apiUrl}${params.toString() ? '?' + params.toString() : ''}`
    console.log('完整请求URL:', url)
    
    const response = await axios.get(url)
    console.log('API响应:', response.data)
    
    if (response.data.status === 'success') {
      rawData.value = response.data.data
      console.log('数据加载成功，共', rawData.value.length, '条记录')
    } else {
      console.error('API返回错误状态:', response.data)
    }
  } catch (error: any) {
    console.error('获取数据失败:', error)
    console.error('API URL:', props.apiUrl)
    console.error('错误详情:', error.response?.data || error.message)
  }
}

// 刷新方法
const refresh = async () => {
  console.log('调用刷新方法')
  await fetchData()
}

// 搜索方法
const search = async (keyword: string) => {
  console.log('调用搜索方法，关键词:', keyword)
  searchQuery.value = keyword
  currentPage.value = 1
  await fetchData()
}

// 计算属性
const filteredData = computed(() => {
  let data = [...rawData.value]
  
  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    data = data.filter(item => 
      Object.entries(item).some(([key, value]) => 
        String(value).toLowerCase().includes(query)
      )
    )
  }
  
  // 排序
  if (sortKey.value && sortOrder.value) {
    data.sort((a, b) => {
      const aVal = a[sortKey.value]
      const bVal = b[sortKey.value]
      const modifier = sortOrder.value === 'asc' ? 1 : -1
      
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return (aVal - bVal) * modifier
      }
      return String(aVal).localeCompare(String(bVal)) * modifier
    })
  }
  
  return data
})

const totalItems = computed(() => filteredData.value.length)
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize.value))
const startIndex = computed(() => (currentPage.value - 1) * pageSize.value)
const endIndex = computed(() => Math.min(startIndex.value + pageSize.value, totalItems.value))

const displayData = computed(() => 
  filteredData.value.slice(startIndex.value, endIndex.value)
)

// 方法
const handleSearch = () => {
  currentPage.value = 1
}

const handleSort = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 
                      sortOrder.value === 'desc' ? '' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

// 格式化显示值
const formatValue = (value: any, key: string): string => {
  // 处理空值
  if (value === null || value === undefined) {
    return '-'
  }

  // 使用自定义格式化函数
  if (props.formatters && props.formatters[key]) {
    try {
      return props.formatters[key](value)
    } catch (e) {
      console.warn(`格式化失败 (${key}):`, e)
      return '-'
    }
  }
  
  // 根据列类型格式化
  const type = props.columnTypes?.[key]
  try {
    if (type === 'rate') {
      const num = typeof value === 'string' ? parseFloat(value) : Number(value)
      return num > 0 ? `+${num.toFixed(2)}%` : `${num.toFixed(2)}%`
    }
    if (type === 'price') {
      const num = typeof value === 'string' ? parseFloat(value) : Number(value)
      return num.toFixed(2)
    }
    if (type === 'amount') {
      const num = typeof value === 'string' ? parseFloat(value) : Number(value)
      return (num / 10000).toFixed(2) + '万'
    }
    if (type === 'date') {
      return String(value)
    }
  } catch (e) {
    console.warn(`格式化失败 (${key}):`, e)
    return '-'
  }
  
  return String(value)
}

const isSortable = (key: string) => {
  const type = props.columnTypes?.[key]
  return type === 'number' || type === 'rate' || type === 'price' || type === 'date'
}

const getSortIcon = (key: string) => {
  if (sortKey.value !== key) return '↕'
  return sortOrder.value === 'asc' ? '↑' : sortOrder.value === 'desc' ? '↓' : '↕'
}

const changePage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

const handlePageSizeChange = () => {
  currentPage.value = 1
}

// 导出到Excel
const exportToExcel = () => {
  // 准备数据
  const data = filteredData.value.map(row => {
    const exportRow: Record<string, any> = {}
    for (const [key, label] of Object.entries(props.headers)) {
      exportRow[label] = formatValue(row[key], key)
    }
    return exportRow
  })

  // 转换为CSV格式
  const headers = Object.values(props.headers)
  const csvContent = [
    headers.join(','), // 表头
    ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(',')) // 数据行
  ].join('\n')

  // 创建Blob对象
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  
  // 创建下载链接
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  
  // 设置文件名（使用当前日期时间）
  const now = new Date()
  const fileName = `数据导出_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}.csv`
  
  // 触发下载
  link.href = url
  link.setAttribute('download', fileName)
  document.body.appendChild(link)
  link.click()
  
  // 清理
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

// 监听查询参数变化
watch(() => props.queryParams, (newVal, oldVal) => {
  console.log('查询参数变化:', newVal, oldVal)
  if (JSON.stringify(newVal) !== JSON.stringify(oldVal)) {
    fetchData()
  }
}, { deep: true })

// 生命周期
onMounted(() => {
  console.log('组件挂载，初始化数据')
  fetchData()
})

// 监听
watch([searchQuery, pageSize], () => {
  currentPage.value = 1
})

// 获取列的类名
const getColumnClass = (key: string): string[] => {
  const type = props.columnTypes?.[key] || 'text'
  const classes: string[] = []
  
  // 基础列宽
  if (type === 'price' || type === 'rate') {
    classes.push('col-price')
  } else if (type === 'amount') {
    classes.push('col-amount')
  } else if (type === 'volume') {
    classes.push('col-volume')
  } else {
    classes.push('col-other')
  }
  
  // 对齐方式
  if (type === 'text') {
    classes.push('text-left')
  } else if (type === 'date') {
    classes.push('text-center')
  } else {
    classes.push('text-right')
  }
  
  return classes
}

// 获取值的类名
const getValueClass = (value: any, key: string): string => {
  if (value === null || value === undefined) return ''
  
  const type = props.columnTypes?.[key]
  if (type === 'rate' || type === 'price') {
    const num = typeof value === 'string' ? parseFloat(value) : Number(value)
    return !isNaN(num) ? (num >= 0 ? 'positive' : 'negative') : ''
  }
  return ''
}

// 导出方法
defineExpose({
  refresh,
  search,
  fetchData
})
</script>

<style scoped>
.table-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: calc(100vh - 120px);
  background: transparent;
}

.table-toolbar {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.left-tools, .right-tools {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-box {
  position: relative;
}

.search-input {
  width: 240px;
  height: 32px;
  padding: 0 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  transition: all 0.3s;
  font-size: 14px;
}

.search-input:focus {
  border-color: #409eff;
  outline: none;
}

.export-btn {
  height: 32px;
  padding: 0 16px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-right: 8px;
}

.export-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.refresh-btn {
  height: 32px;
  padding: 0 16px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.refresh-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

/* 表格容器 */
.table-wrapper {
  flex: 1;
  overflow: hidden;
  position: relative;
  height: calc(100vh - 200px);
}

.table-scroll {
  width: 100%;
  height: 100%;
  overflow: auto;
  max-height: calc(100vh - 120px);
}

/* 表格基础样式 */
table {
  width: 100%;
  border-collapse: collapse;
  border-spacing: 0;
  table-layout: fixed;
  color: #000000;
  background: #ffffff;
  border: 1px solid #dcdfe6;
}

/* 单元格边框 */
td, th {
  border-right: 1px solid #dcdfe6;
  border-bottom: 1px solid #dcdfe6;
}

/* 固定表头 */
thead {
  position: sticky;
  top: 0;
  z-index: 999;
  background: #ffffff;
}

thead th {
  position: sticky;
  top: 0;
  z-index: 999;
  background: #ffffff;
  font-weight: 500;
  color: #000000;
  padding: 12px 8px;
  border: 1px solid #dcdfe6;
  white-space: nowrap;
  text-align: center;
}

/* 确保表头边框显示 */
thead th:after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  border-right: 1px solid #dcdfe6;
  border-bottom: 2px solid #dcdfe6;
  pointer-events: none;
}

/* 单元格基础样式 */
th, td {
  padding: 8px;
  font-size: 13px;
  border-bottom: 1px solid #ebeef5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #000000;
  background: #ffffff;
}

/* 确保最后一行的固定列也有背景色 */
tr:last-child .td-date,
tr:last-child .td-code,
tr:last-child .td-name {
  border-bottom: 1px solid #ebeef5;
}

/* 添加固定列的右边框 */
.td-date, .th-date {
  border-right: 1px solid #ebeef5;
}

.td-code, .th-code {
  border-right: 1px solid #ebeef5;
}

.td-name, .th-name {
  border-right: 1px solid #ebeef5;
}

/* 数据列的对齐方式 */
.td-price, 
.td-rate, 
.td-amount,
.td-volume {
  text-align: right;
  padding-right: 15px;
}

/* 表格底部 */
.table-footer {
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff;
  border-top: 1px solid #ebeef5;
  flex-shrink: 0;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 分页器样式 */
.page-btn {
  min-width: 32px;
  height: 28px;
  padding: 0 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #ffffff;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 12px;
  color: #000000;
}

.page-btn:not(:disabled):hover {
  border-color: #409eff;
  color: #409eff;
  background: #ffffff;
}

.page-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
  background: #ffffff;
}

.page-number-group {
  display: flex;
  align-items: center;
  min-width: 80px;
  justify-content: center;
}

.page-number {
  font-size: 13px;
  color: #000000;
}

.page-size {
  margin-left: 8px;
}

.page-size select {
  height: 28px;
  padding: 0 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  outline: none;
  transition: all 0.3s;
  font-size: 13px;
  color: #000000;
  background: #ffffff;
  cursor: pointer;
}

.page-size select:hover {
  border-color: #c0c4cc;
}

.page-size select:focus {
  border-color: #409eff;
}

.pagination-info {
  color: #000000;
  font-size: 13px;
}

/* 确保分页始终显示在底部 */
.table-container {
  display: flex;
  flex-direction: column;
  min-height: 400px;  /* 设置最小高度 */
}

.table-wrapper {
  flex: 1;
  min-height: 0;  /* 允许表格区域收缩 */
}

.table-footer {
  flex-shrink: 0;  /* 防止分页栏被压缩 */
}

/* 设置表格行高 */
tr {
  height: 32px;  /* 减小行高 */
}

/* 设置滚动条样式 */
.table-scroll::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.table-scroll::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.table-scroll::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.table-scroll::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 列类型样式 */
.td-rate, .td-price, .td-amount {
  text-align: center;
}

.td-text {
  text-align: center;
}

.td-date {
  text-align: center;
}

/* 正负值颜色 */
td[data-type="rate"][data-value^="-"],
td[data-type="amount"][data-value^="-"] {
  color: #67c23a;
}

td[data-type="rate"]:not([data-value^="-"]),
td[data-type="amount"]:not([data-value^="-"]) {
  color: #f56c6c;
}

/* 添加CSS变量用于列宽计算 */
:root {
  --date-width: 90px;
  --code-width: 70px;
  --name-width: 90px;
}

/* 列宽定义 */
.col-date { width: 90px; }
.col-code { width: 80px; }
.col-name { width: 100px; }
.col-price { width: 80px; }
.col-change { width: 80px; }
.col-volume { width: 100px; }
.col-amount { width: 120px; }
.col-other { width: 90px; }

/* 对齐方式 */
.text-left { text-align: left; }
.text-center { text-align: center; }
.text-right { text-align: right; }

/* 表头样式 */
thead th {
  background: #ffffff;
  font-weight: 500;
  color: #000000;
  position: sticky;
  top: 0;
  z-index: 1;
}

.fixed-columns thead th {
  z-index: 3;
}

/* 数据格式化 */
.positive { color: #f56c6c; }
.negative { color: #67c23a; }

/* 响应式布局 */
@media screen and (max-width: 1400px) {
  .col-other { width: 80px; }
  .col-amount { width: 100px; }
}

@media screen and (max-width: 1200px) {
  .col-volume { width: 90px; }
  .col-price { width: 70px; }
  .col-change { width: 70px; }
}

@media screen and (max-width: 992px) {
  .col-date { width: 80px; }
  .col-code { width: 70px; }
  .col-name { width: 90px; }
}
</style> 