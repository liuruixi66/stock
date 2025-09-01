<template>
  <div class="page-container">
    <div class="table-container">
      <div class="table-header">
        <div class="header-left">
          <h3>分红送股数据</h3>
          <div class="date-picker">
            <input type="date" v-model="selectedDate" @change="handleDateChange" />
          </div>
        </div>
        <div class="table-tools">
          <div class="search-box">
            <input type="text" v-model="searchKeyword" placeholder="请输入股票代码或名称" @input="handleSearch" />
            <i class="fa fa-search"></i>
          </div>
          <button class="export-btn" @click="handleExport">
            <i class="fa fa-download"></i>
            导出
          </button>
          <button class="refresh-btn" @click="refreshData">
            <i class="fa fa-sync"></i>
            刷新
          </button>
        </div>
      </div>
      
      <base-table
        :headers="headers"
        :api-url="'/api/stock-bonus/'"
        :column-types="columnTypes"
        :formatters="formatters"
        :fixed-columns="[]"
        :query-params="queryParams"
        ref="baseTableRef"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import BaseTable from '@/components/BaseTable.vue'

const baseTableRef = ref()
const searchKeyword = ref('')
const selectedDate = ref(new Date().toISOString().split('T')[0])

// 计算查询参数
const queryParams = computed(() => {
  const params: Record<string, string> = {}
  
  if (selectedDate.value) {
    params.date = selectedDate.value
  }
  
  if (searchKeyword.value) {
    params.keyword = searchKeyword.value
  }
  
  console.log('当前查询参数:', params)
  return params
})

// 根据TABLE_CN_STOCK_BONUS结构定义表头
const headers = {
  'date': '日期',
  'code': '代码',
  'name': '名称',
  'convertible_total_rate': '送转股份-送转总比例',
  'convertible_rate': '送转股份-送转比例',
  'convertible_transfer_rate': '送转股份-转股比例',
  'bonusaward_rate': '现金分红-现金分红比例',
  'bonusaward_yield': '现金分红-股息率',
  'basic_eps': '每股收益',
  'bvps': '每股净资产',
  'per_capital_reserve': '每股公积金',
  'per_unassign_profit': '每股未分配利润',
  'netprofit_yoy_ratio': '净利润同比增长',
  'total_shares': '总股本',
  'plan_date': '预案公告日',
  'record_date': '股权登记日',
  'ex_dividend_date': '除权除息日',
  'progress': '方案进度',
  'report_date': '最新公告日期'
}

// 定义列类型
const columnTypes = {
  'date': 'date',
  'code': 'text',
  'name': 'text',
  'convertible_total_rate': 'rate',
  'convertible_rate': 'rate',
  'convertible_transfer_rate': 'rate',
  'bonusaward_rate': 'rate',
  'bonusaward_yield': 'rate',
  'basic_eps': 'price',
  'bvps': 'price',
  'per_capital_reserve': 'price',
  'per_unassign_profit': 'price',
  'netprofit_yoy_ratio': 'rate',
  'total_shares': 'amount',
  'plan_date': 'date',
  'record_date': 'date',
  'ex_dividend_date': 'date',
  'progress': 'text',
  'report_date': 'date'
}

// 定义格式化函数
const formatters = {
  'total_shares': (value: number) => {
    if (value === null || value === undefined) return '-'
    return (value / 10000).toFixed(2) + '万股'
  },
  'bonusaward_rate': (value: number) => {
    if (value === null || value === undefined) return '-'
    return value.toFixed(4) + '元/10股'
  },
  'bonusaward_yield': (value: number) => {
    if (value === null || value === undefined) return '-'
    return value.toFixed(2) + '%'
  },
  'convertible_total_rate': (value: number) => {
    if (value === null || value === undefined) return '-'
    return value.toFixed(2) + '股/10股'
  },
  'convertible_rate': (value: number) => {
    if (value === null || value === undefined) return '-'
    return value.toFixed(2) + '股/10股'
  },
  'convertible_transfer_rate': (value: number) => {
    if (value === null || value === undefined) return '-'
    return value.toFixed(2) + '股/10股'
  }
}

// 处理搜索
const handleSearch = () => {
  console.log('触发搜索:', searchKeyword.value)
  if (baseTableRef.value) {
    baseTableRef.value.refresh()
  }
}

// 处理日期变化
const handleDateChange = () => {
  console.log('日期变化:', selectedDate.value)
  if (baseTableRef.value) {
    baseTableRef.value.refresh()
  }
}

// 刷新数据
const refreshData = () => {
  console.log('触发刷新')
  if (baseTableRef.value) {
    baseTableRef.value.refresh()
  }
}

// 处理导出
const handleExport = () => {
  console.log('触发导出')
  const params = new URLSearchParams()
  
  if (selectedDate.value) {
    params.append('date', selectedDate.value)
  }
  
  if (searchKeyword.value) {
    params.append('keyword', searchKeyword.value)
  }
  
  params.append('export', 'true')
  
  const url = `/api/stock-bonus/?${params.toString()}`
  console.log('导出URL:', url)
  
  // 使用 window.open 打开新窗口下载
  window.open(url, '_blank')
}
</script>

<style scoped>
.page-container {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 200px;
  padding: 0;
  display: flex;
  flex-direction: column;
  background: transparent;
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.sidebar-collapsed) .page-container {
  left: 60px;
}

.table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: transparent;
}

.table-header {
  padding: 16px 24px;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  background: #ffffff;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: nowrap;
  min-width: 300px;
}

h3 {
  margin: 0;
  color: #000000 !important;
  font-size: 18px;
  font-weight: 600;
  white-space: nowrap;
}

.date-picker input {
  padding: 6px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  transition: all 0.3s;
  min-width: 120px;
  max-width: 200px;
  background: #ffffff;
  color: #000000 !important;
}

.date-picker input:hover {
  border-color: #40a9ff;
}

.date-picker input:focus {
  border-color: #40a9ff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.table-tools {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: nowrap;
  min-width: 320px;
}

.search-box {
  position: relative;
  min-width: 200px;
  max-width: 300px;
  flex: 1;
}

.search-box input {
  width: 100%;
  padding: 6px 32px 6px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  transition: all 0.3s;
  background: #ffffff;
  color: #000000 !important;
}

.search-box input::placeholder {
  color: #000000 !important;
  opacity: 0.65;
}

.search-box input:hover {
  border-color: #40a9ff;
}

.search-box input:focus {
  border-color: #40a9ff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.search-box i {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #000000 !important;
  opacity: 0.65;
}

.export-btn,
.refresh-btn {
  padding: 6px 16px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #ffffff;
  color: #000000 !important;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
  white-space: nowrap;
  min-height: 32px;
}

.export-btn:hover,
.refresh-btn:hover {
  border-color: #000000;
  background: #ffffff;
}

.export-btn i,
.refresh-btn i {
  font-size: 14px;
  color: #000000 !important;
}

:deep(.el-table) {
  flex: 1;
  background: transparent;
}

:deep(.el-table th),
:deep(.el-table td),
:deep(.el-table .cell) {
  background: transparent;
}

:deep(.el-table--border) {
  border: none;
}

:deep(.el-table--border::after),
:deep(.el-table--border::before) {
  display: none;
}

:deep(.el-table__inner-wrapper::before) {
  display: none;
}

:deep(.el-table th) {
  font-weight: 500;
  border-bottom: 1px solid #dcdfe6;
  white-space: nowrap;
  color: #000000 !important;
}

:deep(.rate-up) {
  color: #cf1322;
  font-weight: 500;
}

:deep(.rate-down) {
  color: #389e0d;
  font-weight: 500;
}

:deep(.el-pagination) {
  padding: 16px 24px;
  background: #ffffff;
  border-top: 1px solid #dcdfe6;
  display: flex;
  justify-content: center;
  align-items: center;
}

:deep(.el-pagination button),
:deep(.el-pagination .el-pager li) {
  background: #ffffff;
  color: #000000;
  border: 1px solid #dcdfe6;
}

:deep(.el-pagination .el-pager li.active) {
  color: #000000;
  font-weight: bold;
  border-color: #000000;
}

@media screen and (max-width: 1440px) {
  .table-container {
    margin: 16px;
  }
}

@media screen and (max-width: 1200px) {
  .table-container {
    margin: 12px;
  }
  
  .table-header {
    padding: 12px 16px;
  }
  
  .header-left {
    gap: 16px;
  }
}

@media screen and (max-width: 768px) {
  .page-container {
    margin-left: 0;
    width: 100%;
  }
  
  :deep(.sidebar-collapsed) .page-container {
    margin-left: 0;
    width: 100%;
  }
  
  .table-container {
    margin: 8px;
    border-radius: 4px;
  }
  
  .table-header {
    padding: 12px;
    flex-direction: row;
    align-items: center;
    flex-wrap: wrap;
  }
  
  .header-left {
    flex-direction: row;
    align-items: center;
    gap: 12px;
    min-width: auto;
  }
  
  .table-tools {
    flex-direction: row;
    align-items: center;
    gap: 12px;
    min-width: auto;
  }
  
  .search-box {
    min-width: 150px;
    max-width: none;
  }
  
  .export-btn,
  .refresh-btn {
    min-width: auto;
    padding: 6px 12px;
  }
  
  :deep(.el-pagination) {
    padding: 12px;
    flex-wrap: wrap;
    gap: 8px;
  }
}

@media (prefers-color-scheme: dark) {
  .table-container {
    background: #ffffff;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
  }
  
  .table-header {
    border-bottom-color: #2f2f2f;
  }
  
  h3 {
    color: #e0e0e0;
  }
  
  .search-box input,
  .date-picker input,
  .export-btn,
  .refresh-btn {
    background: #ffffff;
    border-color: #3f3f3f;
    color: #e0e0e0;
  }
  
  :deep(.el-table) {
    background-color: #1f1f1f;
    color: #e0e0e0;
  }
  
  :deep(.el-table th) {
    background-color: #2f2f2f;
    color: #e0e0e0;
    border-bottom-color: #3f3f3f;
  }
  
  :deep(.el-table td) {
    border-bottom-color: #2f2f2f;
  }
  
  :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
    background-color: #2a2a2a;
  }
  
  :deep(.el-table__body tr:hover > td) {
    background-color: #2f2f2f !important;
  }
  
  :deep(.el-pagination) {
    background-color: #1f1f1f;
    border-top-color: #2f2f2f;
  }
}
</style> 