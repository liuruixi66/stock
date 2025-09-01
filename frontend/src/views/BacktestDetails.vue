<template>
  <div class="backtest-details">
    <!-- 回到顶部按钮 -->
    <div class="page-header">
      <button class="scroll-to-top" @click="scrollToTop" title="回到顶部">
        <i class="fa fa-arrow-up"></i>
      </button>
    </div>

    <!-- 导航卡片 -->
    <NavigationCards />

    <!-- 回测信息面板 -->
    <div class="backtest-panel scroll-reveal">
      <div class="panel-header">
        <h2>回测基本信息</h2>
      </div>
      
      <div class="backtest-info">
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">策略名称</span>
            <span class="info-value">{{ backtestData.strategyName || '请先运行回测' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">回测时间</span>
            <span class="info-value">{{ 
              backtestData.startDate && backtestData.endDate 
                ? `${backtestData.startDate} 至 ${backtestData.endDate}` 
                : '请先设置回测时间' 
            }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">初始资金</span>
            <span class="info-value">{{ 
              backtestData.initialCapital > 0 
                ? `¥${backtestData.initialCapital.toLocaleString()}` 
                : '请先设置初始资金' 
            }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">回测频率</span>
            <span class="info-value">{{ backtestData.frequency || '每日' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">回测状态</span>
            <span class="info-value" :class="{
              'status-success': backtestData.status === '已完成',
              'status-running': backtestData.status === '运行中',
              'status-pending': backtestData.status === '准备运行' || backtestData.status === '未开始',
              'status-error': backtestData.status === '失败'
            }">
              <i class="fa" :class="{
                'fa-check-circle': backtestData.status === '已完成',
                'fa-spinner fa-spin': backtestData.status === '运行中',
                'fa-clock-o': backtestData.status === '准备运行',
                'fa-times-circle': backtestData.status === '失败'
              }"></i>
              {{ backtestData.status }}
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">执行时间</span>
            <span class="info-value">{{ backtestData.executionTime }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 回测结果统计 -->
    <div class="backtest-stats scroll-reveal">
      <div class="stats-header">
        <h2>回测结果统计</h2>
      </div>
      
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fa fa-chart-line"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ backtestResults.performance.total_return || '--' }}</div>
            <div class="stat-label">总收益率</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fa fa-calendar"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ backtestResults.performance.days_traded || '--' }}</div>
            <div class="stat-label">回测天数</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fa fa-exchange-alt"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ backtestResults.performance.total_trades || backtestResults.trades?.length || 0 }}</div>
            <div class="stat-label">交易次数</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fa fa-percentage"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ backtestResults.performance.win_rate || '--' }}</div>
            <div class="stat-label">胜率</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fa fa-arrow-down"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ backtestResults.performance.max_drawdown || '--' }}</div>
            <div class="stat-label">最大回撤</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fa fa-chart-bar"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ backtestResults.performance.sharpe_ratio || '--' }}</div>
            <div class="stat-label">夏普比率</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 回测参数设置 -->
    <div class="backtest-params scroll-reveal">
      <div class="params-header">
        <h2>回测参数设置</h2>
      </div>
      
      <div class="params-content">
        <div class="param-section">
          <h3>策略参数</h3>
          <div class="param-grid">
            <div class="param-item">
              <span class="param-label">策略名称</span>
              <span class="param-value">{{ backtestResults.strategyInfo.strategy_name || '等权重买入持有' }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">初始资金</span>
              <span class="param-value">{{ backtestData.initialCapital || 100000 }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">筛选股票数</span>
              <span class="param-value">{{ backtestResults.stockCount || 0 }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">回测频率</span>
              <span class="param-value">{{ backtestData.frequency || '每日' }}</span>
            </div>
          </div>
        </div>
        
        <div class="param-section">
          <h3>筛选股票</h3>
          <div class="filtered-stocks">
            <div v-if="backtestResults.filteredStocks.length > 0" class="stock-list">
              <div v-for="(stock, index) in backtestResults.filteredStocks" :key="index" class="stock-item">
                <span class="stock-symbol">{{ (stock as any).code || (stock as any).symbol || '未知代码' }}</span>
                <span class="stock-name">{{ (stock as any).name || '未知' }}</span>
              </div>
            </div>
            <div v-else class="no-stocks">
              暂无筛选股票数据
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import NavigationCards from '@/components/NavigationCards.vue'

const route = useRoute()

// 回到顶部功能
const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

// 获取频率显示文本
const getFrequencyLabel = (frequency: string, interval?: string) => {
  switch (frequency) {
    case 'daily':
      return '每日'
    case 'minute':
      return `${interval || '5'}分钟`
    case 'tick':
      return 'Tick'
    default:
      return '每日'
  }
}

// 回测数据
const backtestData = ref({
  strategyName: '',
  startDate: '',
  endDate: '',
  initialCapital: 0,
  frequency: '',
  status: '未开始',
  executionTime: '未运行'
})

// 回测结果数据
const backtestResults = ref<any>({
  filteredStocks: [],
  stockCount: 0,
  accountSummary: {},
  performance: {},
  trades: [],
  positions: [],
  strategyInfo: {}
})

// 加载回测结果
const loadBacktestResults = () => {
  try {
    // 首先从路由参数中获取设置
    const routeParams = {
      startDate: route.query.stockSelectionStartDate as string || '',
      endDate: route.query.stockSelectionEndDate as string || '',
      initialCapital: Number(route.query.initialCapital) * 10000 || 0, // 转换为元
      dataFrequency: route.query.dataFrequency as string || 'daily',
      minuteInterval: route.query.minuteInterval as string || '5',
      selectedConditions: []
    }

    // 解析selectedConditions
    if (route.query.selectedConditions) {
      try {
        if (typeof route.query.selectedConditions === 'string') {
          routeParams.selectedConditions = JSON.parse(decodeURIComponent(route.query.selectedConditions))
        }
      } catch (error) {
        console.error('解析选股条件失败:', error)
      }
    }

    console.log('路由参数:', routeParams)
    console.log('dataFrequency:', routeParams.dataFrequency)
    console.log('minuteInterval:', routeParams.minuteInterval)
    
    const frequencyLabel = getFrequencyLabel(routeParams.dataFrequency, routeParams.minuteInterval)
    console.log('计算出的频率标签:', frequencyLabel)

    // 更新基本信息 - 先用默认值，后面会被API数据覆盖
    backtestData.value = {
      strategyName: `智能选股策略-${new Date().getTime().toString().slice(-4)}`,
      startDate: routeParams.startDate || '加载中...',
      endDate: routeParams.endDate || '加载中...',
      initialCapital: routeParams.initialCapital,
      frequency: frequencyLabel,
      status: '准备运行',
      executionTime: '等待开始...'
    }

    // 总是调用新的API获取最新的回测结果
    console.log('准备调用新的API获取回测结果')
    startNewBacktest(routeParams)
    
    // 注释掉localStorage逻辑，确保总是获取最新数据
    /*
    // 尝试从localStorage获取保存的结果
    const savedResults = localStorage.getItem('backtestResults')
    if (savedResults) {
      const parsedResults = JSON.parse(savedResults)
      console.log('加载保存的回测结果:', parsedResults)
      
      // 更新回测结果但保持新的参数设置
      backtestResults.value = {
        filteredStocks: parsedResults.filteredStocks || [],
        stockCount: parsedResults.stockCount || 0,
        accountSummary: parsedResults.accountSummary || {},
        performance: parsedResults.performance || {},
        trades: parsedResults.trades || [],
        positions: parsedResults.positions || [],
        strategyInfo: parsedResults.strategyInfo || {}
      }
      
      // 如果有保存的结果，更新状态
      if (parsedResults.filteredStocks && parsedResults.filteredStocks.length > 0) {
        backtestData.value.status = '已完成'
        backtestData.value.executionTime = parsedResults.executionTime || '已完成'
      }
    } else {
      console.log('未找到保存的回测结果，准备运行新的回测')
      // 这里可以调用API开始新的回测
      startNewBacktest(routeParams)
    }
    */
  } catch (error) {
    console.error('加载回测结果时出错:', error)
  }
}

// 开始新的回测
const startNewBacktest = async (params: any) => {
  try {
    console.log('🚀 开始新的回测，参数:', params)
    backtestData.value.status = '运行中'
    backtestData.value.executionTime = '加载中...'
    
    // 调用新的回测结果API
    const apiParams = new URLSearchParams({
      start_date: params.startDate.replace(/-/g, ''),
      end_date: params.endDate.replace(/-/g, ''),
      initial_capital: params.initialCapital.toString(),
      data_frequency: params.dataFrequency,
      minute_interval: params.minuteInterval
    })
    
    console.log('📡 调用缓存回测详情API')
    
    // 使用缓存API，不需要参数
    const response = await fetch(`http://localhost:8002/api/cache/backtest-details/`)
    const result = await response.json()
    
    console.log('📊 缓存回测详情API响应:', result)
    
    if (result.status === 'success') {
      // 更新状态和执行时间
      backtestData.value.status = '已完成'
      backtestData.value.executionTime = result.execution_time
      
      // 从API响应中获取真实的日期范围
      const timeInfo = result.data.time_period || result.data.strategy_info || {}
      const strategyInfo = result.data.strategy_info || {}
      
      // 更新基本信息为真实的缓存数据
      const startDateRaw = timeInfo.start_date || strategyInfo.start_date || backtestData.value.startDate
      const endDateRaw = timeInfo.end_date || strategyInfo.end_date || backtestData.value.endDate
      
      // 将YYYYMMDD格式转换为YYYY-MM-DD
      backtestData.value.startDate = typeof startDateRaw === 'string' && startDateRaw.length === 8 
        ? `${startDateRaw.slice(0,4)}-${startDateRaw.slice(4,6)}-${startDateRaw.slice(6,8)}`
        : startDateRaw
      backtestData.value.endDate = typeof endDateRaw === 'string' && endDateRaw.length === 8
        ? `${endDateRaw.slice(0,4)}-${endDateRaw.slice(4,6)}-${endDateRaw.slice(6,8)}`
        : endDateRaw
      backtestData.value.strategyName = strategyInfo.name || backtestData.value.strategyName
      backtestData.value.initialCapital = strategyInfo.initial_capital || strategyInfo.initial_cash || backtestData.value.initialCapital
      
      console.log('📅 更新后的日期信息:', {
        startDate: backtestData.value.startDate,
        endDate: backtestData.value.endDate,
        executionTime: backtestData.value.executionTime
      })
      
      // 计算回测天数
      const calculateBacktestDays = (startDate: string, endDate: string) => {
        if (!startDate || !endDate) return 0
        const start = new Date(startDate.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3'))
        const end = new Date(endDate.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3'))
        const diffTime = Math.abs(end.getTime() - start.getTime())
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      }
      
      const backtest_days = calculateBacktestDays(
        result.data.time_period?.start_date || '', 
        result.data.time_period?.end_date || ''
      )
      
      // 格式化数据显示 - 与EarningsOverview保持一致
      const formatPercentage = (value: any) => {
        if (typeof value === 'string' && value.includes('%')) return value
        if (typeof value === 'number') {
          // 如果数值在 -1 到 1 之间，认为是小数需要转换为百分比
          if (Math.abs(value) <= 1) {
            return `${value > 0 ? '+' : ''}${(value * 100).toFixed(2)}%`
          }
          // 否则认为已经是百分比数值
          return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
        }
        return value || '--'
      }
      
      const formatNumber = (value: any, decimals = 2) => {
        if (value == null || isNaN(value)) return '--'
        if (typeof value === 'number') return value.toFixed(decimals)
        return value || '--'
      }
      
      // 更新回测结果 - 将性能数据同时放在 accountSummary 和 performance 中以确保兼容性
      const performanceData = result.data.performance_metrics || {}
      
      backtestResults.value = {
        filteredStocks: result.data.trades?.map((trade: any) => ({
          symbol: trade.stock_code,
          name: trade.stock_code,
          action: trade.action,
          price: trade.price,
          amount: trade.amount,
          date: trade.date
        })) || [],
        stockCount: result.data.trades?.length || 0,
        accountSummary: {
          total_return: performanceData.strategy_return || 0,
          annual_return: performanceData.strategy_annual_return || 0,
          max_drawdown: performanceData.max_drawdown || 0,
          sharpe_ratio: performanceData.sharpe_ratio || 0,
          win_rate: performanceData.win_rate || 0,
          days_traded: backtest_days
        },
        // 添加 performance 对象以兼容模板中的引用 - 确保数据一致性
        performance: {
          total_return: formatPercentage(performanceData.strategy_return),
          annual_return: formatPercentage(performanceData.strategy_annual_return),
          max_drawdown: formatPercentage(performanceData.max_drawdown),
          sharpe_ratio: formatNumber(performanceData.sharpe_ratio),
          win_rate: formatPercentage(performanceData.win_rate), // 注意：win_rate已经是小数，不需要*100
          days_traded: backtest_days,
          total_trades: performanceData.total_trades || result.data.trades?.length || 0
        },
        trades: result.data.trades || [],
        positions: result.data.positions || [],
        strategyInfo: {
          ...result.data.strategy_info,
          frequency_note: result.data.frequency_note
        }
      }
      
      console.log('📊 更新后的回测结果:', backtestResults.value.performance)
      
      // 保存到localStorage
      localStorage.setItem('backtestResults', JSON.stringify(backtestResults.value))
      
      console.log('✅ 回测结果加载成功')
      
    } else {
      throw new Error(result.message || '获取回测结果失败')
    }
    
  } catch (error) {
    console.error('❌ 获取回测结果失败:', error)
    backtestData.value.status = '失败'
    backtestData.value.executionTime = '执行失败'
    
    // 显示错误信息但不阻止页面显示
    console.warn('使用默认数据继续显示页面')
    
    // 使用默认的模拟数据
    backtestResults.value = {
      filteredStocks: [
        { symbol: '000001', name: '平安银行', action: 'buy', price: 10.5, amount: 10500, date: '2024-01-01' },
        { symbol: '000002', name: '万科A', action: 'buy', price: 15.2, amount: 15200, date: '2024-01-02' }
      ],
      stockCount: 2,
      accountSummary: {
        total_return: 15.5,
        annual_return: 15.5,
        max_drawdown: 5.2,
        sharpe_ratio: 1.2,
        win_rate: 0.6
      },
      performance: {},
      trades: [],
      positions: [],
      strategyInfo: {
        name: '模拟策略',
        frequency_note: '数据加载失败，显示模拟结果'
      }
    }
  }
}

// 滚动监听
const handleScroll = () => {
  const elements = document.querySelectorAll('.scroll-reveal')
  elements.forEach((element) => {
    const rect = element.getBoundingClientRect()
    const windowHeight = window.innerHeight
    
    if (rect.top < windowHeight * 0.8) {
      element.classList.add('revealed')
    }
  })
}

// 在组件挂载时加载回测结果
onMounted(() => {
  loadBacktestResults();
})

onUnmounted(() => {
  // 移除滚动监听
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.backtest-details {
  padding: 15px 20px 20px 20px;
  background-color: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 10px;
  position: relative;
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

/* 滚动动画 */
@keyframes slideInFromTop {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInFromLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInFromRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInFromBottom {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
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

.scroll-reveal {
  opacity: 0;
  transform: translateY(30px);
  transition: all 0.6s ease-out;
}

.scroll-reveal.revealed {
  opacity: 1;
  transform: translateY(0);
}





/* 回测信息面板 */
.backtest-panel {
  background: white;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: slideInFromLeft 0.8s ease-out 0.2s both;
  transform: translateX(-20px);
  opacity: 0;
  transition: all 0.3s ease;
}

.backtest-panel:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.backtest-info {
  padding: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f5f5f5;
  transition: all 0.3s ease;
}

.info-item:hover {
  background: rgba(24, 144, 255, 0.05);
  padding-left: 10px;
  padding-right: 10px;
  border-radius: 6px;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: #333;
  font-weight: 600;
}

.status-success {
  color: #52c41a;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-success i {
  font-size: 16px;
}

.status-running {
  color: #1890ff;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-running i {
  font-size: 16px;
}

.status-pending {
  color: #faad14;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-pending i {
  font-size: 16px;
}

.status-error {
  color: #ff4d4f;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-error i {
  font-size: 16px;
}

.status-running {
  color: #1890ff;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-running i {
  font-size: 16px;
}

.status-pending {
  color: #faad14;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-pending i {
  font-size: 16px;
}

.status-error {
  color: #ff4d4f;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-error i {
  font-size: 16px;
}

.status-running {
  color: #1890ff;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-running i {
  font-size: 16px;
}

.status-pending {
  color: #faad14;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-pending i {
  font-size: 16px;
}

.status-error {
  color: #ff4d4f;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-error i {
  font-size: 16px;
}

/* 回测结果统计 */
.backtest-stats {
  background: white;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: slideInFromRight 0.8s ease-out 0.4s both;
  transform: translateX(20px);
  opacity: 0;
  transition: all 0.3s ease;
}

.backtest-stats:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.stats-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.transaction-details-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #1890ff;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.transaction-details-btn:hover {
  background: #40a9ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.transaction-details-btn i {
  font-size: 14px;
}

.stats-grid {
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.stat-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: #1890ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

/* 回测参数设置 */
.backtest-params {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: slideInFromBottom 0.8s ease-out 0.6s both;
  transform: translateY(20px);
  opacity: 0;
  transition: all 0.3s ease;
}

.backtest-params:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.params-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.params-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.params-content {
  padding: 20px;
}

.param-section {
  margin-bottom: 24px;
}

.param-section:last-child {
  margin-bottom: 0;
}

.param-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
}

.param-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.param-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.param-item:hover {
  background: #e6f7ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.param-label {
  font-size: 13px;
  color: #666;
}

.param-value {
  font-size: 13px;
  color: #333;
  font-weight: 600;
}

/* 股票列表样式 */
.filtered-stocks {
  margin-top: 12px;
}

.stock-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}

.stock-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f0f8ff;
  border-radius: 6px;
  border-left: 3px solid #1890ff;
  transition: all 0.3s ease;
}

.stock-item:hover {
  background: #e6f7ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
}

.stock-symbol {
  font-size: 13px;
  color: #1890ff;
  font-weight: 600;
}

.stock-name {
  font-size: 12px;
  color: #666;
}

.no-stocks {
  text-align: center;
  color: #999;
  font-style: italic;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 6px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .param-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .backtest-details {
    padding: 10px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-card {
    padding: 15px;
  }
  
  .stat-icon {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }
  
  .stat-value {
    font-size: 20px;
  }
}
</style> 