<template>
  <div class="earnings-overview">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>收益概述</h1>
      <button class="scroll-to-top" @click="scrollToTop" title="回到顶部">
        <i class="fa fa-arrow-up"></i>
      </button>
    </div>

    <!-- 性能指标网格 -->
    <div class="metrics-grid scroll-reveal">
      <div class="metrics-row">
        <div class="metric-item">
          <span class="metric-label">策略收益</span>
          <span class="metric-value" :class="{ 'negative': performanceMetrics.strategy_return < 0, 'positive': performanceMetrics.strategy_return > 0 }">
            {{ formatPercentage(performanceMetrics.strategy_return) }}
          </span>
        </div>
        <div class="metric-item">
          <span class="metric-label">策略年化收益</span>
          <span class="metric-value" :class="{ 'negative': performanceMetrics.strategy_annual_return < 0, 'positive': performanceMetrics.strategy_annual_return > 0 }">
            {{ formatPercentage(performanceMetrics.strategy_annual_return) }}
          </span>
        </div>
        <div class="metric-item">
          <span class="metric-label">超额收益</span>
          <span class="metric-value" :class="{ 'negative': performanceMetrics.excess_return < 0, 'positive': performanceMetrics.excess_return > 0 }">
            {{ formatPercentage(performanceMetrics.excess_return) }}
          </span>
        </div>
        <div class="metric-item">
          <span class="metric-label">基准收益</span>
          <span class="metric-value" :class="{ 'negative': performanceMetrics.benchmark_return < 0, 'positive': performanceMetrics.benchmark_return > 0 }">
            {{ formatPercentage(performanceMetrics.benchmark_return) }}
          </span>
        </div>
        <div class="metric-item">
          <span class="metric-label">阿尔法</span>
          <span class="metric-value" :class="{ 'negative': performanceMetrics.alpha < 0, 'positive': performanceMetrics.alpha > 0 }">
            {{ formatNumber(performanceMetrics.alpha) }}
          </span>
        </div>
        <div class="metric-item">
          <span class="metric-label">贝塔</span>
          <span class="metric-value">{{ formatNumber(performanceMetrics.beta) }}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">夏普比率</span>
          <span class="metric-value" :class="{ 'negative': performanceMetrics.sharpe_ratio < 0, 'positive': performanceMetrics.sharpe_ratio > 0 }">
            {{ formatNumber(performanceMetrics.sharpe_ratio) }}
          </span>
        </div>
        <div class="metric-item">
          <span class="metric-label">胜率</span>
          <span class="metric-value">{{ formatPercentage(performanceMetrics.win_rate * 100) }}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">盈亏比</span>
          <span class="metric-value">{{ formatNumber(performanceMetrics.profit_loss_ratio) }}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">最大回撤</span>
          <span class="metric-value negative">{{ formatPercentage(performanceMetrics.max_drawdown) }}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">索提诺比率</span>
          <span class="metric-value" :class="{ 'negative': performanceMetrics.sortino_ratio < 0, 'positive': performanceMetrics.sortino_ratio > 0 }">
            {{ formatNumber(performanceMetrics.sortino_ratio) }}
          </span>
        </div>
      </div>

      <div class="metrics-row">
        <div class="metric-item">
          <span class="metric-label">日均超额收益</span>
          <span class="metric-value negative">-0.04%</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">超额收益最大回撤</span>
          <span class="metric-value">13.01%</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">超额收益震荡比率</span>
          <span class="metric-value negative">-0.910</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">日胜率</span>
          <span class="metric-value">0.471</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">盈利次数</span>
          <span class="metric-value">1</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">亏损次数</span>
          <span class="metric-value">8</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">信息比率</span>
          <span class="metric-value negative">-0.672</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">策略波动率</span>
          <span class="metric-value">0.084</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">基准波动率</span>
          <span class="metric-value">0.165</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">最大回撤区间</span>
          <span class="metric-value">{{ performanceMetrics.max_drawdown_period }}</span>
        </div>
      </div>
    </div>

    <!-- 图表控制区域 -->
    <div class="chart-controls scroll-reveal">
      <div class="control-group">
        <span class="control-label">缩放:</span>
        <div class="zoom-buttons">
          <button 
            class="zoom-btn active" 
            @click="setZoom('1month', $event)"
          >
            1个月
          </button>
          <button 
            class="zoom-btn" 
            @click="setZoom('1year', $event)"
          >
            1年
          </button>
          <button 
            class="zoom-btn" 
            @click="setZoom('all', $event)"
          >
            全部
          </button>
        </div>
      </div>

      <div class="control-group">
        <div class="chart-legend">
          <div class="legend-item">
            <div class="legend-color strategy"></div>
            <span>策略收益</span>
          </div>
          <div class="legend-item">
            <div class="legend-color excess"></div>
            <span>超额收益</span>
          </div>
          <div class="legend-item">
            <div class="legend-color benchmark"></div>
            <span>沪深300</span>
          </div>
        </div>
      </div>

      <div class="control-group">
        <div class="axis-controls">
          <label class="radio-label">
            <input type="radio" v-model="axisType" value="normal" />
            <span>普通轴</span>
          </label>
          <label class="radio-label">
            <input type="radio" v-model="axisType" value="log" />
            <span>对数轴</span>
          </label>
        </div>
      </div>

      <div class="control-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="showExcessReturn" />
          <span>超额收益</span>
        </label>
      </div>

      <div class="control-group">
        <span class="control-label">时间:</span>
        <div class="date-range">
          <input 
            type="date" 
            v-model="startDate" 
            class="date-input"
          />
          <span class="date-separator">至</span>
          <input 
            type="date" 
            v-model="endDate" 
            class="date-input"
          />
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-container scroll-reveal">
      <!-- 收益趋势图 -->
      <div class="chart-wrapper">
        <div class="chart-title">收益趋势</div>
        <div class="chart" ref="performanceChart"></div>
      </div>

      <!-- 每日盈亏图 -->
      <div class="chart-wrapper">
        <div class="chart-title">每日盈亏</div>
        <div class="chart" ref="pnlChart"></div>
      </div>

      <!-- 每日成交图 -->
      <div class="chart-wrapper">
        <div class="chart-title">每日成交</div>
        <div class="chart" ref="turnoverChart"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

// 响应式数据
const zoom = ref('1month')
const axisType = ref('normal')
const showExcessReturn = ref(true)
const startDate = ref('2024-12-02')
const endDate = ref('2025-05-30')

// 性能指标响应式数据
const performanceMetrics = ref({
  strategy_return: 0,
  strategy_annual_return: 0,
  excess_return: 0,
  benchmark_return: 0,
  alpha: 0,
  beta: 0,
  sharpe_ratio: 0,
  win_rate: 0,
  profit_loss_ratio: 0,
  max_drawdown: 0,
  sortino_ratio: 0,
  information_ratio: 0,
  max_drawdown_period: "未知"
})

// 加载状态
const loading = ref(true)

// 图表引用
const performanceChart = ref<HTMLElement>()
const pnlChart = ref<HTMLElement>()
const turnoverChart = ref<HTMLElement>()

// 图表实例
let performanceChartInstance: echarts.ECharts | null = null
let pnlChartInstance: echarts.ECharts | null = null
let turnoverChartInstance: echarts.ECharts | null = null

// 从缓存获取性能数据
const loadPerformanceData = async () => {
  try {
    loading.value = true
    console.log('📊 收益概述页面：从缓存加载数据')
    
    const response = await fetch('http://localhost:8002/api/cache/earnings-overview/')
    if (response.ok) {
      const data = await response.json()
      
      if (data.status === 'success' && data.data) {
        const metrics = data.data.performance_metrics || {}
        const timeRange = data.data.time_period || {}
        
        console.log('📊 缓存性能指标:', metrics)
        
        // 更新性能指标 - 直接使用原始数值，不需要转换为百分比
        performanceMetrics.value = {
          strategy_return: metrics.strategy_return || 0,
          strategy_annual_return: metrics.strategy_annual_return || 0,
          excess_return: metrics.excess_return || 0,
          benchmark_return: metrics.benchmark_return || 10.0,
          alpha: metrics.alpha || 0,
          beta: metrics.beta || 1.0,
          sharpe_ratio: metrics.sharpe_ratio || 0,
          win_rate: metrics.win_rate || 0,
          profit_loss_ratio: metrics.profit_loss_ratio || 0,
          max_drawdown: metrics.max_drawdown || 0,
          sortino_ratio: metrics.sortino_ratio || 0,
          information_ratio: metrics.information_ratio || 0,
          max_drawdown_period: metrics.max_drawdown_period || "未知"
        }
        
        // 更新时间范围
        if (timeRange.start_date && timeRange.end_date) {
          const formatDate = (dateStr: string) => {
            if (dateStr.length === 8) {
              return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`
            }
            return dateStr
          }
          startDate.value = formatDate(timeRange.start_date)
          endDate.value = formatDate(timeRange.end_date)
        }
        
        console.log('✅ 收益概述数据加载成功:', performanceMetrics.value)
      }
    } else {
      console.warn('⚠️ 缓存API不可用，使用默认数据')
    }
  } catch (error) {
    console.error('❌ 获取收益概述数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 格式化百分比显示 - 处理已经是百分比的数值
const formatPercentage = (value: number): string => {
  // 如果数值在 -1 到 1 之间，认为是小数需要转换为百分比
  if (Math.abs(value) <= 1) {
    return `${value > 0 ? '+' : ''}${(value * 100).toFixed(2)}%`
  }
  // 否则认为已经是百分比数值
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
}

// 格式化数值显示
const formatNumber = (value: number, decimals = 3): string => {
  if (value == null || isNaN(value)) return '--'
  return value.toFixed(decimals)
}

// 模拟数据
const generatePerformanceData = () => {
  const dates = []
  const strategyData = []
  const benchmarkData = []
  const excessData = []
  
  let currentDate = new Date('2024-12-02')
  let strategyValue = 100
  let benchmarkValue = 100
  
  for (let i = 0; i < 180; i++) {
    const dateStr = currentDate.toISOString().split('T')[0]
    dates.push(dateStr)
    
    // 模拟策略收益（波动较大）
    const strategyChange = (Math.random() - 0.52) * 0.02 // 偏向下跌
    strategyValue *= (1 + strategyChange)
    strategyData.push(strategyValue)
    
    // 模拟基准收益（波动较小）
    const benchmarkChange = (Math.random() - 0.51) * 0.01 // 轻微下跌
    benchmarkValue *= (1 + benchmarkChange)
    benchmarkData.push(benchmarkValue)
    
    // 超额收益
    excessData.push(strategyValue - benchmarkValue)
    
    currentDate.setDate(currentDate.getDate() + 1)
  }
  
  return { dates, strategyData, benchmarkData, excessData }
}

const generatePnLData = () => {
  const data = []
  for (let i = 0; i < 180; i++) {
    // 大部分为亏损
    const value = Math.random() > 0.8 ? 
      (Math.random() * 2000) : 
      -(Math.random() * 5000)
    data.push(value)
  }
  return data
}

const generateTurnoverData = () => {
  const data = []
  for (let i = 0; i < 180; i++) {
    // 正负交替
    const value = Math.random() > 0.5 ? 
      (Math.random() * 100000) : 
      -(Math.random() * 200000)
    data.push(value)
  }
  return data
}

// 初始化收益趋势图
const initPerformanceChart = () => {
  if (!performanceChart.value) return
  
  performanceChartInstance = echarts.init(performanceChart.value)
  
  const { dates, strategyData, benchmarkData, excessData } = generatePerformanceData()
  
  const option = {
    title: {
      text: '收益趋势',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        let result = params[0].axisValue + '<br/>'
        params.forEach((param: any) => {
          const value = param.seriesName === '策略收益' || param.seriesName === '沪深300' 
            ? (param.value - 100).toFixed(2) + '%'
            : param.value.toFixed(2)
          result += param.marker + param.seriesName + ': ' + value + '<br/>'
        })
        return result
      }
    },
    legend: {
      data: ['策略收益', '沪深300', '超额收益'],
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        formatter: function(value: string) {
          return value.substring(5) // 只显示月-日
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '策略收益',
        type: 'line',
        data: strategyData.map((value, index) => [dates[index], value]),
        lineStyle: { color: '#1890ff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0.1)' }
          ])
        },
        smooth: true
      },
      {
        name: '沪深300',
        type: 'line',
        data: benchmarkData.map((value, index) => [dates[index], value]),
        lineStyle: { color: '#f5222d' },
        smooth: true
      },
      {
        name: '超额收益',
        type: 'line',
        data: excessData.map((value, index) => [dates[index], value]),
        lineStyle: { color: '#fa8c16' },
        smooth: true,
        show: showExcessReturn.value
      }
    ]
  }
  
  performanceChartInstance.setOption(option)
}

// 初始化每日盈亏图
const initPnLChart = () => {
  if (!pnlChart.value) return
  
  pnlChartInstance = echarts.init(pnlChart.value)
  
  const { dates } = generatePerformanceData()
  const pnlData = generatePnLData()
  
  const option = {
    title: {
      text: '每日盈亏',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        const value = params[0].value
        return params[0].axisValue + '<br/>' + 
               params[0].marker + '盈亏: ' + value.toFixed(0) + '元'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        formatter: function(value: string) {
          return value.substring(5)
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}元'
      }
    },
    series: [
      {
        type: 'bar',
        data: pnlData.map((value, index) => ({
          value: value,
          itemStyle: {
            color: value >= 0 ? '#52c41a' : '#722ed1'
          }
        })),
        barWidth: '60%'
      }
    ]
  }
  
  pnlChartInstance.setOption(option)
}

// 初始化每日成交图
const initTurnoverChart = () => {
  if (!turnoverChart.value) return
  
  turnoverChartInstance = echarts.init(turnoverChart.value)
  
  const { dates } = generatePerformanceData()
  const turnoverData = generateTurnoverData()
  
  const option = {
    title: {
      text: '每日成交',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        const value = params[0].value
        return params[0].axisValue + '<br/>' + 
               params[0].marker + '成交: ' + (value / 1000).toFixed(0) + 'k'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        formatter: function(value: string) {
          return value.substring(5)
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: function(value: number) {
          return (value / 1000).toFixed(0) + 'k'
        }
      }
    },
    series: [
      {
        type: 'bar',
        data: turnoverData.map((value, index) => ({
          value: value,
          itemStyle: {
            color: value >= 0 ? '#1890ff' : '#fa8c16'
          }
        })),
        barWidth: '60%'
      }
    ]
  }
  
  turnoverChartInstance.setOption(option)
}

// 设置缩放
const setZoom = (newZoom: string, event?: Event) => {
  zoom.value = newZoom
  
  // 更新按钮状态
  document.querySelectorAll('.zoom-btn').forEach(btn => {
    btn.classList.remove('active')
  })
  if (event?.target instanceof HTMLElement) {
    event.target.classList.add('active')
  }
  
  // 这里可以添加图表缩放逻辑
  updateCharts()
}

// 更新图表
const updateCharts = () => {
  if (performanceChartInstance) {
    const option = performanceChartInstance.getOption()
    if (option.series && Array.isArray(option.series) && option.series[2]) {
      (option.series[2] as any).show = showExcessReturn.value
      performanceChartInstance.setOption(option)
    }
  }
}

// 监听数据变化
watch(showExcessReturn, updateCharts)
watch(axisType, updateCharts)

// 滚动监听函数
const handleScroll = () => {
  const elements = document.querySelectorAll('.scroll-reveal')
  elements.forEach(element => {
    const rect = element.getBoundingClientRect()
    const isVisible = rect.top < window.innerHeight * 0.8
    if (isVisible) {
      element.classList.add('visible')
    }
  })
}

// 滚动到顶部
const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

// 组件挂载
onMounted(() => {
  console.log('收益概述页面已加载')
  
  // 首先加载性能数据
  loadPerformanceData()
  
  // 初始化图表
  setTimeout(() => {
    initPerformanceChart()
    initPnLChart()
    initTurnoverChart()
  }, 100)
  
  // 监听窗口大小变化
  const handleResize = () => {
    performanceChartInstance?.resize()
    pnlChartInstance?.resize()
    turnoverChartInstance?.resize()
  }
  
  window.addEventListener('resize', handleResize)
  
  // 监听滚动事件
  window.addEventListener('scroll', handleScroll)
  
  // 初始触发一次滚动监听
  handleScroll()
  
  // 使用 ResizeObserver 监听容器大小变化
  const chartsContainer = document.querySelector('.charts-container')
  if (chartsContainer) {
    const resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(chartsContainer)
  }
})
</script>

<style scoped>
.earnings-overview {
  padding: 20px;
  background-color: #f5f5f5;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 20px;
  scroll-behavior: smooth;
  overflow-y: auto;
}

.page-header {
  margin-bottom: 20px;
  animation: slideInFromTop 0.6s ease-out;
}

.page-header {
  position: relative;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.scroll-to-top {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #1890ff;
  color: white;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
  transition: all 0.3s ease;
  z-index: 1000;
  opacity: 0;
  transform: translateY(20px);
  animation: fadeInUp 0.6s ease-out 1s forwards;
}

.scroll-to-top:hover {
  background: #40a9ff;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.4);
}

.scroll-to-top i {
  font-size: 18px;
}

/* 性能指标网格 */
.metrics-grid {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
  animation: slideInFromLeft 0.8s ease-out 0.2s both;
  transform: translateX(-20px);
  opacity: 0;
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.metrics-row:last-child {
  margin-bottom: 0;
}

.metric-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  padding: 8px;
  border-radius: 6px;
}

.metric-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  background: rgba(24, 144, 255, 0.05);
}

.metric-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.metric-value.negative {
  color: #52c41a;
}

/* 图表控制区域 */
.chart-controls {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
  flex-shrink: 0;
  animation: slideInFromRight 0.8s ease-out 0.4s both;
  transform: translateX(20px);
  opacity: 0;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.control-label {
  font-size: 14px;
  color: #666;
  white-space: nowrap;
}

.zoom-buttons {
  display: flex;
  gap: 4px;
}

.zoom-btn {
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s ease;
  transform: scale(1);
}

.zoom-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.zoom-btn:hover {
  border-color: #1890ff;
}

.zoom-btn.active {
  background: #1890ff;
  color: white;
  border-color: #1890ff;
}

.chart-legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-color.strategy {
  background: #1890ff;
}

.legend-color.excess {
  background: #fa8c16;
}

.legend-color.benchmark {
  background: #f5222d;
}

.axis-controls {
  display: flex;
  gap: 12px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  cursor: pointer;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  cursor: pointer;
}

.date-range {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.date-input {
  padding: 4px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
}

.date-separator {
  font-size: 12px;
  color: #666;
}

/* 图表区域 */
.charts-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
  min-height: 0;
  animation: slideInFromBottom 1s ease-out 0.6s both;
  transform: translateY(30px);
  opacity: 0;
}

.chart-wrapper {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.chart-wrapper:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.chart {
  flex: 1;
  min-height: 200px;
  position: relative;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
}

/* 滑动动画 */
@keyframes slideInFromTop {
  from {
    transform: translateY(-30px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes slideInFromLeft {
  from {
    transform: translateX(-20px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideInFromRight {
  from {
    transform: translateX(20px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideInFromBottom {
  from {
    transform: translateY(30px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 滚动显示动画 */
.scroll-reveal {
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.6s ease;
}

.scroll-reveal.visible {
  opacity: 1;
  transform: translateY(0);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .earnings-overview {
    padding: 10px;
    gap: 15px;
  }
  
  .chart-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .metrics-row {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .metrics-grid {
    padding: 15px;
  }
  
  .chart-wrapper {
    padding: 15px;
  }
  
  .chart {
    min-height: 150px;
  }
}

@media (max-width: 480px) {
  .earnings-overview {
    padding: 8px;
    gap: 12px;
  }
  
  .metrics-grid {
    padding: 12px;
  }
  
  .chart-controls {
    padding: 12px;
    gap: 12px;
  }
  
  .chart-wrapper {
    padding: 12px;
  }
  
  .chart {
    min-height: 120px;
  }
  
  .metric-value {
    font-size: 14px;
  }
  
  .metric-label {
    font-size: 11px;
  }
  
  .page-header h1 {
    font-size: 20px;
  }
  
  .zoom-btn {
    padding: 4px 8px;
    font-size: 11px;
  }
  
  .date-input {
    font-size: 11px;
    padding: 3px 6px;
  }
  
  .legend-item {
    font-size: 11px;
  }
  
  .radio-label, .checkbox-label {
    font-size: 11px;
  }
}
</style> 