<template>
  <div class="technical-indicator-display">
    <div class="header">
      <h1>技术指标筛选结果</h1>
      <button @click="goBack" class="btn-back">
        <i class="fas fa-arrow-left"></i>
        返回
      </button>
    </div>
    
    <div class="filter-info">
      <h3>筛选条件</h3>
      <div class="filter-details">
        <p><strong>开始日期:</strong> {{ filterParams.stockSelectionStartDate || '未设置' }}</p>
        <p><strong>结束日期:</strong> {{ filterParams.stockSelectionEndDate || '未设置' }}</p>
        <p><strong>初始资金:</strong> {{ filterParams.initialCapital || '100' }}万元</p>
        <p><strong>数据频率:</strong> {{ getFrequencyLabel(filterParams.dataFrequency) }}</p>
        <p v-if="filterParams.dataFrequency === 'minute'"><strong>分钟周期:</strong> {{ filterParams.minuteInterval }}分钟</p>
        <p><strong>指标类型:</strong> {{ getIndicatorTitle(filterParams.selectedConditions) }}</p>
        <p><strong>筛选条件数量:</strong> {{ filterParams.selectedConditions ? filterParams.selectedConditions.length : 0 }}</p>
      </div>
    </div>
    
    <div class="results-section">
      <h3>{{ getTableTitle() }}</h3>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>正在加载股票数据...</p>
      </div>
      
      <!-- 错误信息 -->
      <div v-else-if="error" class="error-container">
        <p class="error-message">{{ error }}</p>
        <button @click="fetchStockData" class="btn-retry">重试</button>
      </div>
      
      <!-- 数据表格 -->
      <div v-else class="table-container">
        <table class="excel-table">
          <thead>
            <tr>
              <th>序号</th>
              <th>股票代码</th>
              <th>股票名称</th>
              <th>当前价格</th>
              <th>涨跌幅(%)</th>
              <th>MA5</th>
              <th>MA10</th>
              <th>MA20</th>
              <th>MA60</th>
              <th>成交量(万手)</th>
              <th>成交额(万元)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(stock, index) in filteredStockList" :key="stock.code">
              <td>{{ index + 1 }}</td>
              <td class="stock-code">{{ stock.code }}</td>
              <td class="stock-name">{{ stock.name }}</td>
              <td class="price" :class="{ 'up': stock.changeRate > 0, 'down': stock.changeRate < 0 }">
                {{ stock.price }}
              </td>
              <td class="change-rate" :class="{ 'up': stock.changeRate > 0, 'down': stock.changeRate < 0 }">
                {{ stock.changeRate > 0 ? '+' : '' }}{{ stock.changeRate.toFixed(2) }}
              </td>
              <td>{{ stock.ma5.toFixed(2) }}</td>
              <td>{{ stock.ma10.toFixed(2) }}</td>
              <td>{{ stock.ma20.toFixed(2) }}</td>
              <td>{{ stock.ma60.toFixed(2) }}</td>
              <td>{{ (stock.volume / 10000).toFixed(2) }}</td>
              <td>{{ (stock.turnover / 10000).toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div class="table-summary">
        <div class="summary-item">
          <span class="label">总数量:</span>
          <span class="value">{{ filteredStockList.length }}</span>
        </div>
        <div class="summary-item">
          <span class="label">金叉数量:</span>
          <span class="value golden">{{ goldenCrossCount }}</span>
        </div>
        <div class="summary-item">
          <span class="label">死叉数量:</span>
          <span class="value death">{{ deathCrossCount }}</span>
        </div>
        <div class="summary-item">
          <span class="label">平均涨跌幅:</span>
          <span class="value" :class="{ 'up': avgChangeRate > 0, 'down': avgChangeRate < 0 }">
            {{ avgChangeRate > 0 ? '+' : '' }}{{ avgChangeRate.toFixed(2) }}%
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

interface FilterParams {
  stockSelectionStartDate: string;
  stockSelectionEndDate: string;
  initialCapital: number;
  dataFrequency: string;
  minuteInterval: string;
  selectedConditions: any[];
  activeSubMenu: string;
  timestamp: string;
}

interface StockData {
  code: string;
  name: string;
  price: number;
  changeRate: number;
  ma5: number;
  ma10: number;
  ma20: number;
  ma60: number;
  volume: number;
  turnover: number;
}

// 筛选参数
const filterParams = ref<FilterParams>({
  stockSelectionStartDate: '',
  stockSelectionEndDate: '',
  initialCapital: 100,
  dataFrequency: 'daily',
  minuteInterval: '5',
  selectedConditions: [],
  activeSubMenu: '',
  timestamp: ''
})

// 股票数据
const stockList = ref<StockData[]>([])
const loading = ref(false)
const error = ref('')

// API基础URL
const API_BASE_URL = '/api'

// 获取股票数据
const fetchStockData = async () => {
  loading.value = true
  error.value = ''
  
  try {
    console.log('开始获取股票数据...')
    console.log('筛选参数:', filterParams.value)
    
    // 构建API请求参数
    const apiParams: any = {}
    
    // 添加日期参数
    if (filterParams.value.stockSelectionStartDate) {
      apiParams.start_date = filterParams.value.stockSelectionStartDate
      console.log('使用开始日期:', filterParams.value.stockSelectionStartDate)
    }
    if (filterParams.value.stockSelectionEndDate) {
      apiParams.end_date = filterParams.value.stockSelectionEndDate
      console.log('使用结束日期:', filterParams.value.stockSelectionEndDate)
    }
    
    // 添加回测参数
    if (filterParams.value.initialCapital) {
      apiParams.initial_capital = filterParams.value.initialCapital * 10000 // 转换为元
      console.log('使用初始资金:', filterParams.value.initialCapital, '万元')
    }
    if (filterParams.value.dataFrequency) {
      apiParams.data_frequency = filterParams.value.dataFrequency
      console.log('使用数据频率:', filterParams.value.dataFrequency)
    }
    if (filterParams.value.minuteInterval && filterParams.value.dataFrequency === 'minute') {
      apiParams.minute_interval = filterParams.value.minuteInterval
      console.log('使用分钟周期:', filterParams.value.minuteInterval)
    }
    
    // 获取股票数据
    const response = await axios.get(`${API_BASE_URL}/stock-spot/`, { params: apiParams })
    console.log('API响应:', response.data)
    
    if (response.data.status === 'success') {
      const rawData = response.data.data
      console.log('原始数据长度:', rawData.length)
      console.log('原始数据示例:', rawData[0])
      
      // 处理数据，计算MA指标
      const processedData = await processStockDataWithMA(rawData)
      console.log('处理后的数据长度:', processedData.length)
      console.log('处理后数据示例:', processedData[0])
      
      stockList.value = processedData
    } else {
      error.value = response.data.message || '获取数据失败'
      console.error('API返回错误:', response.data)
    }
  } catch (err) {
    console.error('获取股票数据失败:', err)
    error.value = '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 处理股票数据并计算MA指标
const processStockDataWithMA = async (rawData: any[]) => {
  const processedData: StockData[] = []
  
  // 获取MA设置参数
  const maConfig = getMASettingsFromConditions()
  console.log('MA配置参数:', maConfig)
  
  // 按股票代码分组数据
  const stockGroups: { [key: string]: any[] } = {}
  
  rawData.forEach(item => {
    // 确保数据字段存在
    if (!item.code || !item.new_price) {
      console.warn('跳过无效数据项:', item)
      return
    }
    
    if (!stockGroups[item.code]) {
      stockGroups[item.code] = []
    }
    
    // 转换数据类型，处理可能的null值
    const price = parseFloat(item.new_price) || 0
    const volume = parseFloat(item.volume) || 0
    const turnover = parseFloat(item.deal_amount) || 0
    
    if (price > 0) { // 只添加有效价格数据
      stockGroups[item.code].push({
        date: item.date,
        price: price,
        volume: volume,
        turnover: turnover
      })
    }
  })
  
  console.log('股票分组数量:', Object.keys(stockGroups).length)
  
  // 为每只股票计算MA指标
  for (const [code, data] of Object.entries(stockGroups)) {
    const stockData = data as any[]
    
    // 数据不足时，使用可用数据计算MA，而不是跳过
    const maxPeriod = Math.max(maConfig.shortPeriod || 5, maConfig.longPeriod || 60)
    if (stockData.length < 1) {
      console.log(`股票 ${code} 无数据，跳过`)
      continue
    }
    
    if (stockData.length < Math.min(maxPeriod, 20)) {
      console.log(`股票 ${code} 数据不足，使用可用数据 (${stockData.length} 天)`)
    }
    
    // 按日期排序
    stockData.sort((a, b) => {
      const dateA = new Date(a.date).getTime()
      const dateB = new Date(b.date).getTime()
      return dateA - dateB
    })
    
    // 获取最新数据
    const latest = stockData[stockData.length - 1]
    
    // 使用配置的MA参数计算指标，数据不足时使用可用数据
    const ma5 = calculateMA(stockData, Math.min(maConfig.shortPeriod || 5, stockData.length))
    const ma10 = calculateMA(stockData, Math.min(10, stockData.length))
    const ma20 = calculateMA(stockData, Math.min(maConfig.longPeriod || 20, stockData.length))
    const ma60 = calculateMA(stockData, Math.min(60, stockData.length))
    
    // 计算涨跌幅（相对于前一天）
    const prevDay = stockData[stockData.length - 2]
    const changeRate = prevDay ? ((latest.price - prevDay.price) / prevDay.price) * 100 : 0
    
    // 查找股票名称
    const stockInfo = rawData.find(item => item.code === code)
    
    processedData.push({
      code: code,
      name: stockInfo?.name || code,
      price: latest.price,
      changeRate: changeRate,
      ma5: ma5,
      ma10: ma10,
      ma20: ma20,
      ma60: ma60,
      volume: latest.volume,
      turnover: latest.turnover
    })
  }
  
  console.log('最终处理的数据数量:', processedData.length)
  return processedData
}

// 计算移动平均线
const calculateMA = (data: any[], period: number) => {
  if (data.length < period) {
    console.warn(`数据长度 ${data.length} 小于周期 ${period}，使用可用数据`)
    // 数据不足时，使用所有可用数据计算平均值
    const availablePeriod = Math.min(data.length, period)
    const prices = data.slice(-availablePeriod).map(item => item.price)
    const sum = prices.reduce((acc, price) => acc + price, 0)
    const result = sum / availablePeriod
    
    console.log(`MA${period} 计算(数据不足): 最近${availablePeriod}天价格 [${prices.join(', ')}], 平均值: ${result.toFixed(2)}`)
    return result
  }
  
  const prices = data.slice(-period).map(item => item.price)
  const sum = prices.reduce((acc, price) => acc + price, 0)
  const result = sum / period
  
  console.log(`MA${period} 计算: 最近${period}天价格 [${prices.join(', ')}], 平均值: ${result.toFixed(2)}`)
  
  return result
}

// 根据筛选条件过滤股票
const filterStocksByConditions = (stocks: StockData[], conditions: any[]) => {
  console.log('开始筛选股票，总数:', stocks.length)
  console.log('筛选条件:', conditions)
  
  if (!conditions || conditions.length === 0) {
    console.log('没有筛选条件，返回所有股票')
    return stocks
  }
  
  const filtered = stocks.filter(stock => {
    return conditions.every(condition => {
      console.log('检查条件:', condition)
      if (condition.type === 'market_ma') {
        const result = checkMASignal(stock, condition.config)
        console.log(`股票 ${stock.code} MA信号检查结果:`, result)
        return result
      }
      // 可以添加其他指标类型的判断
      console.log(`未知条件类型: ${condition.type}`)
      return true
    })
  })
  
  console.log('筛选后股票数量:', filtered.length)
  return filtered
}

// 检查MA信号
const checkMASignal = (stock: StockData, config: any) => {
  console.log('检查MA信号，股票:', stock.code, '配置:', config)
  
  if (!config) {
    console.log('没有配置，返回true')
    return true
  }
  
  const { ma, goldenCross, deathCross } = config
  
  // 使用配置的MA参数
  const shortMA = ma?.short === 5 ? stock.ma5 : 
                 ma?.short === 10 ? stock.ma10 : 
                 ma?.short === 20 ? stock.ma20 : stock.ma5
  
  const longMA = ma?.long === 10 ? stock.ma10 : 
                ma?.long === 20 ? stock.ma20 : 
                ma?.long === 60 ? stock.ma60 : stock.ma20
  
  // 金叉死叉只能二选一
  if (goldenCross && !deathCross) {
    // 只检查金叉：短周期MA上穿长周期MA
    const result = shortMA > longMA
    console.log(`金叉检查: MA${ma?.short || 5}(${shortMA}) > MA${ma?.long || 20}(${longMA}) = ${result}`)
    return result
  }
  
  if (deathCross && !goldenCross) {
    // 只检查死叉：短周期MA下穿长周期MA
    const result = shortMA < longMA
    console.log(`死叉检查: MA${ma?.short || 5}(${shortMA}) < MA${ma?.long || 20}(${longMA}) = ${result}`)
    return result
  }
  
  // 如果都没有选择或都选择了，返回true（显示所有股票）
  console.log('没有选择金叉或死叉，或者同时选择了，返回true')
  return true
}

// 计算属性
const filteredStockList = computed(() => {
  console.log('计算筛选后的股票列表')
  console.log('原始股票列表长度:', stockList.value.length)
  console.log('筛选条件:', filterParams.value.selectedConditions)
  
  const filtered = filterStocksByConditions(stockList.value, filterParams.value.selectedConditions)
  console.log('筛选后股票列表长度:', filtered.length)
  
  // 如果没有筛选条件或筛选后没有数据，显示所有股票（用于测试）
  if (filtered.length === 0 && stockList.value.length > 0) {
    console.log('筛选后没有数据，显示所有股票用于测试')
    return stockList.value.slice(0, 20) // 只显示前20只股票
  }
  
  return filtered
})

const goldenCrossCount = computed(() => {
  const maConfig = getMASettingsFromConditions()
  
  // 只有选择了金叉信号才计算金叉数量
  if (!maConfig.goldenCross || maConfig.deathCross) {
    return 0
  }
  
  const count = filteredStockList.value.filter(stock => {
    const shortMA = maConfig.shortPeriod === 5 ? stock.ma5 : 
                   maConfig.shortPeriod === 10 ? stock.ma10 : 
                   maConfig.shortPeriod === 20 ? stock.ma20 : stock.ma5
    
    const longMA = maConfig.longPeriod === 10 ? stock.ma10 : 
                  maConfig.longPeriod === 20 ? stock.ma20 : 
                  maConfig.longPeriod === 60 ? stock.ma60 : stock.ma20
    
    return shortMA > longMA
  }).length
  console.log('金叉数量:', count)
  return count
})

const deathCrossCount = computed(() => {
  const maConfig = getMASettingsFromConditions()
  
  // 只有选择了死叉信号才计算死叉数量
  if (!maConfig.deathCross || maConfig.goldenCross) {
    return 0
  }
  
  const count = filteredStockList.value.filter(stock => {
    const shortMA = maConfig.shortPeriod === 5 ? stock.ma5 : 
                   maConfig.shortPeriod === 10 ? stock.ma10 : 
                   maConfig.shortPeriod === 20 ? stock.ma20 : stock.ma5
    
    const longMA = maConfig.longPeriod === 10 ? stock.ma10 : 
                  maConfig.longPeriod === 20 ? stock.ma20 : 
                  maConfig.longPeriod === 60 ? stock.ma60 : stock.ma20
    
    return shortMA < longMA
  }).length
  console.log('死叉数量:', count)
  return count
})

const avgChangeRate = computed(() => {
  if (filteredStockList.value.length === 0) return 0
  const total = filteredStockList.value.reduce((sum, stock) => sum + stock.changeRate, 0)
  const avg = total / filteredStockList.value.length
  console.log('平均涨跌幅:', avg)
  return avg
})

// 获取指标类型显示名称
const getIndicatorName = (type: string) => {
  console.log('getIndicatorName接收到的type:', type)
  
  // 从 type 中提取指标类型
  if (type.includes('market_ma')) return '大盘择时-MA指标'
  if (type.includes('market_macd')) return '大盘择时-MACD指标'
  if (type.includes('market_kdj')) return '大盘择时-KDJ指标'
  
  // 板块择时指标
  if (type.includes('sector_ma')) return '板块择时-MA指标'
  if (type.includes('sector_macd')) return '板块择时-MACD指标'
  if (type.includes('sector_kdj')) return '板块择时-KDJ指标'
  
  // 个股择时指标
  if (type.includes('timing_ma')) return '个股择时-MA指标'
  if (type.includes('timing_macd')) return '个股择时-MACD指标'
  if (type.includes('timing_kdj')) return '个股择时-KDJ指标'
  if (type.includes('timing_rsi')) return '个股择时-RSI指标'
  if (type.includes('timing_boll')) return '个股择时-BOLL指标'
  if (type.includes('timing_cr')) return '个股择时-CR指标'
  if (type.includes('timing_atr')) return '个股择时-ATR指标'
  if (type.includes('timing_trix')) return '个股择时-TRIX指标'
  if (type.includes('timing_cci')) return '个股择时-CCI指标'
  if (type.includes('timing_bbic')) return '个股择时-BBIC指标'
  if (type.includes('timing_multi_bull')) return '个股择时-多头指标'
  if (type.includes('timing_ema')) return '个股择时-EMA指标'
  
  // 基本面指标
  if (type === 'open-price') return '开盘价'
  if (type === 'close-price') return '收盘价'
  if (type === 'high-price') return '最高价'
  if (type === 'low-price') return '最低价'
  if (type === 'prev-close-price') return '昨收价'
  if (type === 'avg-price') return '均价'
  if (type === 'change-rate') return '涨跌幅'
  if (type === 'volume-ratio') return '量比'
  if (type === 'turnover') return '成交额'
  if (type === 'turnover-rate') return '换手率'
  if (type === 'market-value') return '市值'
  if (type === 'volume') return '成交量'
  if (type === 'net-inflow') return '净流入'
  
  // 股东指标
  if (type === 'shareholder-reduction') return '股东减持'
  if (type === 'shareholder-increase') return '股东增持'
  if (type === 'shareholder-dividend') return '股东分红'
  
  // 其他指标
  if (type === 'violation-inquiry') return '违规查询'
  if (type === 'performance-forecast') return '业绩预告'
  if (type === 'performance-announcement') return '业绩公告'
  
  // 过滤器
  if (type === 'filter-new-listing') return '新股过滤'
  if (type === 'filter-beijing') return '北交所过滤'
  if (type === 'filter-main-board') return '主板过滤'
  if (type === 'filter-st') return 'ST过滤'
  if (type === 'filter-star-st') return '科创板ST过滤'
  if (type === 'filter-suspension') return '停牌过滤'
  if (type === 'filter-star-market') return '科创板过滤'
  if (type === 'filter-growth-board') return '创业板过滤'
  if (type === 'filter-delisting') return '退市过滤'
  
  // 财务指标
  if (type === 'roa') return '总资产收益率(ROA)'
  if (type === 'roe') return '净资产收益率(ROE)'
  if (type === 'gross-margin') return '毛利率'
  if (type === 'net-margin') return '净利率'
  if (type === 'revenue-growth') return '营收增长率'
  if (type === 'profit-growth') return '利润增长率'
  if (type === 'dynamic-pe') return '动态市盈率'
  if (type === 'pb-ratio') return '市净率'
  if (type === 'ps-ratio') return '市销率'
  if (type === 'static-pe') return '静态市盈率'
  
  // 打印未匹配的类型
  if (type) {
    console.log('未匹配的指标类型:', type)
  }
  
  return '未选择'
}

// 从选中的条件中获取指标类型
const getIndicatorTypeFromConditions = (conditions: any[]) => {
  console.log('getIndicatorTypeFromConditions 接收到的条件:', conditions)
  
  if (!conditions || conditions.length === 0) {
    console.log('没有条件或条件为空')
    return ''
  }
  
  // 获取第一个条件的类型
  const firstCondition = conditions[0]
  console.log('第一个条件:', firstCondition)
  
  if (firstCondition && typeof firstCondition === 'object' && 'type' in firstCondition) {
    console.log('找到条件类型:', firstCondition.type)
    return firstCondition.type
  }
  
  console.log('未找到有效的条件类型')
  return ''
}

// 获取指标类型显示名称
const getIndicatorTitle = (conditions: any[]) => {
  // 如果没有条件，返回未选择
  if (!conditions || conditions.length === 0) return '未选择'
  
  // 直接获取第一个条件的标题
  const firstCondition = conditions[0]
  return firstCondition?.title || '未选择'
}

// 获取数据频率显示标签
const getFrequencyLabel = (frequency: string) => {
  const labels: { [key: string]: string } = {
    'daily': '每日',
    'minute': '分钟',
    'tick': 'tick'
  }
  return labels[frequency] || frequency
}

// 从筛选条件中获取MA设置
const getMASettingsFromConditions = () => {
  const maCondition = filterParams.value.selectedConditions.find(condition => condition.type === 'market_ma')
  
  if (maCondition && maCondition.config) {
    return {
      shortPeriod: maCondition.config.ma?.short || 5,
      longPeriod: maCondition.config.ma?.long || 60,
      goldenCross: maCondition.config.goldenCross || false,
      deathCross: maCondition.config.deathCross || false,
      period: maCondition.config.period || 'day',
      index: maCondition.config.index || 'sh'
    }
  }
  
  // 默认设置
  return {
    shortPeriod: 5,
    longPeriod: 60,
    goldenCross: false,
    deathCross: false,
    period: 'day',
    index: 'sh'
  }
}

// 获取表格标题
const getTableTitle = () => {
  const maConfig = getMASettingsFromConditions()
  const shortMA = maConfig.shortPeriod === 5 ? 'MA5' : 
                 maConfig.shortPeriod === 10 ? 'MA10' : 
                 maConfig.shortPeriod === 20 ? 'MA20' : 'MA5'
  const longMA = maConfig.longPeriod === 10 ? 'MA10' : 
                maConfig.longPeriod === 20 ? 'MA20' : 
                maConfig.longPeriod === 60 ? 'MA60' : 'MA20'
  
  let signalType = ''
  if (maConfig.goldenCross && !maConfig.deathCross) {
    signalType = '金叉'
  } else if (maConfig.deathCross && !maConfig.goldenCross) {
    signalType = '死叉'
  } else {
    signalType = '全部'
  }
  
  return `MA指标筛选结果 (${shortMA} vs ${longMA} - ${signalType}信号)`
}

// 返回上一页
const goBack = () => {
  router.go(-1)
}

// 组件挂载时获取路由参数并加载数据
onMounted(async () => {
  console.log('路由参数:', route.query)
  console.log('路由参数类型:', typeof route.query.selectedConditions)
  
  // 从路由query中获取筛选参数
  filterParams.value = {
    stockSelectionStartDate: route.query.stockSelectionStartDate as string || '',
    stockSelectionEndDate: route.query.stockSelectionEndDate as string || '',
    initialCapital: Number(route.query.initialCapital) || 100,
    dataFrequency: route.query.dataFrequency as string || 'daily',
    minuteInterval: route.query.minuteInterval as string || '5',
    selectedConditions: [],
    activeSubMenu: route.query.activeSubMenu as string || '',
    timestamp: route.query.timestamp as string || ''
  }
  
  // 处理selectedConditions参数
  if (route.query.selectedConditions) {
    try {
      // 如果是字符串，尝试解析JSON
      if (typeof route.query.selectedConditions === 'string') {
        filterParams.value.selectedConditions = JSON.parse(decodeURIComponent(route.query.selectedConditions))
      } else if (Array.isArray(route.query.selectedConditions)) {
        // 如果是数组，直接使用
        filterParams.value.selectedConditions = route.query.selectedConditions
      }
    } catch (error) {
      console.error('解析selectedConditions失败:', error)
      filterParams.value.selectedConditions = []
    }
  }
  
  console.log('解析后的筛选参数:', filterParams.value)
  
  // 如果没有条件，创建一个默认的MA条件用于测试
  if (filterParams.value.selectedConditions.length === 0) {
    console.log('没有筛选条件，创建默认MA条件用于测试')
    filterParams.value.selectedConditions = [{
      id: Date.now(),
      type: 'market_ma',
      title: '大盘择时 - MA指标',
      details: '上证指数 日周期 MA(5,60) 金叉信号',
      enabled: true,
      config: {
        index: 'sh',
        period: 'day',
        ma: { short: 5, long: 60 },
        goldenCross: true,
        deathCross: false
      }
    }]
  }
  
  // 加载股票数据
  await fetchStockData()
})
</script>

<style scoped>
.technical-indicator-display {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.header h1 {
  margin: 0;
  color: #333;
  font-size: 24px;
}

.btn-back {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.btn-back:hover {
  background: #5a6268;
}

.filter-info {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.filter-info h3 {
  margin-top: 0;
  color: #495057;
  font-size: 18px;
}

.filter-details p {
  margin: 8px 0;
  color: #666;
}

.results-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.results-section h3 {
  margin-top: 0;
  color: #495057;
  font-size: 18px;
  margin-bottom: 20px;
}

.table-container {
  overflow-x: auto;
  margin-bottom: 20px;
}

.excel-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.excel-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  padding: 12px 8px;
  text-align: center;
  border: 1px solid #dee2e6;
  position: sticky;
  top: 0;
  z-index: 10;
}

.excel-table td {
  padding: 10px 8px;
  text-align: center;
  border: 1px solid #dee2e6;
  vertical-align: middle;
}

.excel-table tbody tr:hover {
  background-color: #f8f9fa;
}

.highlight-row {
  background-color: #fff3cd !important;
}

.highlight-row:hover {
  background-color: #ffeaa7 !important;
}

.stock-code {
  font-weight: 600;
  color: #007bff;
}

.stock-name {
  font-weight: 500;
  color: #333;
}

.price {
  font-weight: 600;
}

.change-rate {
  font-weight: 600;
}

.up {
  color: #dc3545;
}

.down {
  color: #28a745;
}

.signal-type {
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
}

.golden-cross {
  background-color: #d4edda;
  color: #155724;
}

.death-cross {
  background-color: #f8d7da;
  color: #721c24;
}

.signal-strength {
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 3px;
}

.signal-strength.strong {
  background-color: #d1ecf1;
  color: #0c5460;
}

.signal-strength.medium {
  background-color: #fff3cd;
  color: #856404;
}

.signal-strength.weak {
  background-color: #f8d7da;
  color: #721c24;
}

.table-summary {
  display: flex;
  gap: 30px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.summary-item .label {
  font-weight: 600;
  color: #495057;
}

.summary-item .value {
  font-weight: 600;
  font-size: 16px;
}

.summary-item .value.golden {
  color: #155724;
}

.summary-item .value.death {
  color: #721c24;
}

/* 加载状态样式 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 错误状态样式 */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #721c24;
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  margin: 20px 0;
}

.error-message {
  margin-bottom: 20px;
  font-size: 16px;
  text-align: center;
}

.btn-retry {
  background: #dc3545;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
}

.btn-retry:hover {
  background: #c82333;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .excel-table {
    font-size: 12px;
  }
  
  .excel-table th,
  .excel-table td {
    padding: 8px 4px;
  }
}

@media (max-width: 768px) {
  .table-summary {
    flex-direction: column;
    gap: 15px;
  }
  
  .summary-item {
    justify-content: space-between;
  }
}
</style> 