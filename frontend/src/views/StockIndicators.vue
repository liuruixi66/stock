<template>
  <div class="indicators-container">
    <div class="indicators-header">
      <div class="stock-info">
        <h2>{{ stockName }} ({{ stockCode }})</h2>
        <div class="stock-price" v-if="currentPrice">
          <span class="price" :class="{ 'up': priceChange > 0, 'down': priceChange < 0 }">
            {{ currentPrice }}
          </span>
          <span class="change" :class="{ 'up': priceChange > 0, 'down': priceChange < 0 }">
            {{ priceChange > 0 ? '+' : '' }}{{ priceChange }}%
          </span>
        </div>
      </div>
      
      <div class="controls">
        <div class="date-picker-wrapper">
          <i class="fa fa-calendar"></i>
          <input 
            type="text" 
            v-model="currentDate" 
            class="date-picker" 
            placeholder="选择日期"
          />
        </div>
        
        <div class="indicators-select">
          <select v-model="selectedIndicators" multiple>
            <option v-for="(name, key) in availableIndicators" 
                    :key="key" 
                    :value="key">
              {{ name }}
            </option>
          </select>
        </div>

        <button class="refresh-btn" @click="refreshData">
          <i class="fa fa-refresh" :class="{ 'fa-spin': loading }"></i>
          刷新数据
        </button>
      </div>
    </div>

    <div class="charts-container" :class="{ loading: loading }">
      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>
      <div ref="chartContainer" class="chart"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { getIndicatorsData } from '@/api/stock'
import dayjs from 'dayjs'
import type { ECharts } from 'echarts'
import * as echarts from 'echarts/core'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import { LineChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'

// 注册必需的组件
echarts.use([
  GridComponent,
  TooltipComponent,
  LegendComponent,
  LineChart,
  CanvasRenderer
])

// 声明 jQuery datepicker 类型
declare global {
  interface JQuery {
    datepicker(options?: any): JQuery
  }
}

const route = useRoute()
const chartContainer = ref<HTMLElement | null>(null)
const stockCode = ref(route.query.code as string || '')
const stockName = ref(route.query.name as string || '')
const currentDate = ref(route.query.date as string || dayjs().format('YYYY-MM-DD'))
const loading = ref(false)
const chart = ref<ECharts | null>(null)
const currentPrice = ref<number | null>(null)
const priceChange = ref<number>(0)

// 可用指标
const availableIndicators = {
  macd: 'MACD',
  kdj: 'KDJ',
  rsi: 'RSI',
  boll: 'BOLL',
  ma: '均线',
  volume: '成交量'
}

const selectedIndicators = ref(['macd', 'volume'])

onMounted(() => {
  initChart()
  initDatePicker()
  loadData()
})

const initChart = () => {
  if (chartContainer.value) {
    chart.value = echarts.init(chartContainer.value)
    window.addEventListener('resize', () => chart.value?.resize())
  }
}

const initDatePicker = () => {
  $(document).ready(() => {
    $('.date-picker').datepicker({
      language: 'zh-CN',
      format: 'yyyy-mm-dd',
      autoclose: true,
      todayHighlight: true
    }).on('changeDate', () => {
      loadData()
    })
  })
}

const loadData = async () => {
  if (!stockCode.value) return
  
  loading.value = true
  try {
    const response = await getIndicatorsData(
      stockCode.value, 
      currentDate.value,
      stockName.value // 修改这里，只传递一个字符串参数
    )
    
    if (response.data) {
      updateChart(response.data)
      currentPrice.value = response.data.current_price
      priceChange.value = response.data.price_change
    }
  } catch (error) {
    console.error('Failed to load indicators data:', error)
  } finally {
    loading.value = false
  }
}

const updateChart = (data: any) => {
  if (!chart.value) return
  
  // 这里根据实际数据结构更新图表配置
  const option = {
    // ... echarts配置
  }
  
  chart.value.setOption(option)
}

const refreshData = () => {
  loadData()
}

watch(selectedIndicators, () => {
  loadData()
})

onUnmounted(() => {
  chart.value?.dispose()
  window.removeEventListener('resize', () => chart.value?.resize())
})
</script>

<style scoped>
.indicators-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 20px;
  height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
}

.indicators-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 20px;
}

.stock-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stock-info h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.8em;
}

.stock-price {
  display: flex;
  align-items: center;
  gap: 10px;
}

.price {
  font-size: 1.4em;
  font-weight: bold;
}

.change {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.9em;
}

.up {
  color: #f56c6c;
}

.down {
  color: #67c23a;
}

.controls {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.date-picker-wrapper {
  position: relative;
}

.date-picker-wrapper i {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #606266;
}

.date-picker {
  padding: 8px 8px 8px 32px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  width: 140px;
  transition: all 0.3s;
}

.date-picker:focus {
  border-color: #409eff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.indicators-select select {
  padding: 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  min-width: 200px;
  outline: none;
}

.indicators-select select:focus {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.refresh-btn {
  padding: 8px 16px;
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

.charts-container {
  flex: 1;
  position: relative;
  min-height: 400px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.chart {
  width: 100%;
  height: 100%;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .indicators-container {
    padding: 15px;
    height: calc(100vh - 100px);
  }

  .indicators-header {
    flex-direction: column;
    align-items: stretch;
  }

  .stock-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .controls {
    flex-direction: column;
    align-items: stretch;
  }

  .date-picker,
  .indicators-select select {
    width: 100%;
  }
}
</style> 