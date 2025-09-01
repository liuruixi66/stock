<template>
  <div class="indicator-selection">
    <!-- 左侧指标选择区域 -->
    <div class="left-panel">
      <!-- 顶部搜索和筛选区域 -->
      <div class="top-controls">
        <div class="search-box">
          <input type="text" v-model="searchQuery" placeholder="搜索指标名称..." class="search-input" />
          <span class="search-icon">🔍</span>
        </div>
        
        <div class="action-buttons">
          <button @click="enableAll" class="action-btn enable-btn">全部启用</button>
          <button @click="disableAll" class="action-btn disable-btn">全部禁用</button>
        </div>
      </div>

      <!-- 顶部导航栏 -->
      <div class="nav-container">
        <div class="nav-scroll" ref="navScroll">
          <div v-for="category in categories" :key="category.id" class="nav-item"
            :class="{ active: activeCategory === category.id }" @click="setActiveCategory(category.id)">
            {{ category.name }}
          </div>
        </div>
        <button class="nav-scroll-btn left" @click="scrollNav('left')">‹</button>
        <button class="nav-scroll-btn right" @click="scrollNav('right')">›</button>
      </div>

      <!-- 指标卡片网格 -->
      <div class="indicators-grid">
        <div v-for="indicator in filteredIndicators" :key="indicator.id" class="indicator-card"
          :class="getCardColorClass(indicator.id)">
          <div class="card-header">
            <div class="card-title">{{ indicator.name }}</div>
            <div class="card-type">{{ indicator.type }}</div>
          </div>
          
          <div class="card-description">{{ indicator.description }}</div>
          
          <div class="card-footer">
            <div class="switch-container">
              <label class="switch">
                <input type="checkbox" v-model="indicator.enabled" @change="handleIndicatorChange(indicator)" />
                <span class="slider"></span>
              </label>
              <span>{{ indicator.enabled ? '已启用' : '已禁用' }}</span>
            </div>
            
            <button class="detail-btn" @click="openDetailModal(indicator)">
              查看详情
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧已选择指标区域 -->
    <div class="right-panel">
      <div class="selected-header">
        <h2>已选择指标</h2>
        <div class="date-range">
          <div class="date-input">
            <label>开始日期</label>
            <input type="date" v-model="startDate" />
          </div>
          <div class="date-input">
            <label>结束日期</label>
            <input type="date" v-model="endDate" />
          </div>
        </div>
        
        <!-- 资金数据框 -->
        <div class="capital-data-box">
          <div class="capital-input">
            <label>初始资金</label>
            <div class="input-with-currency">
              <span class="currency-symbol">¥</span>
              <input type="number" v-model="initialCapital" placeholder="100000" />
            </div>
          </div>
        </div>
        
        <!-- 时间周期框 -->
        <div class="time-period-box">
          <div class="period-input">
            <label>数据频率</label>
            <select v-model="dataFrequency" class="period-select">
              <option value="daily">每天</option>
              <option value="minute">分钟</option>
              <option value="tick">tick</option>
            </select>
          </div>
        </div>
      </div>

      <div class="selected-indicators">
        <div v-if="selectedIndicators.length === 0" class="empty-state">
          <p>暂无已选择的指标</p>
          <p>请在左侧选择指标</p>
        </div>
        
        <div v-for="indicator in selectedIndicators" :key="indicator.id" class="selected-card">
          <div class="selected-card-header">
            <div class="selected-title">{{ indicator.name }}</div>
            <div class="selected-params">
              {{ formatParameters(indicator.parameters) }}
            </div>
          </div>
          
          <div class="selected-card-footer">
            <button class="detail-btn" @click="openDetailModal(indicator)">
              查看详情
            </button>
            <button class="remove-btn" @click="removeIndicator(indicator)">
              移除
            </button>
          </div>
        </div>
      </div>

      <div class="backtest-section">
        <button class="backtest-btn" @click="runBacktest" :disabled="isBacktesting">
          运行回测
        </button>
      </div>
    </div>

    <!-- 指标详情模态框 -->
    <IndicatorParamDialog v-if="showModal" :show="showModal" :indicator="currentIndicator"
      :marketIndex="currentIndicator.category === 'trend' ? selectedMarketIndex : ''" 
      :period="currentIndicator.category === 'trend' ? selectedPeriod : ''" 
      :maShort="currentIndicator.category === 'trend' ? maShort : 0" 
      :maLong="currentIndicator.category === 'trend' ? maLong : 0"
      @update:marketIndex="val => (selectedMarketIndex = val)" @update:period="val => (selectedPeriod = val)"
      @update:maShort="val => (maShort = val)" @update:maLong="val => (maLong = val)"
      @update:indicator="updateIndicatorData"
      @save="saveParameters(currentIndicator)" @reset="resetParameters(currentIndicator)" @close="closeModal" />

    <!-- 通知提示 -->
    <div v-if="notification.show" :class="['notification', notification.type]">
      {{ notification.message }}
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import IndicatorParamDialog from '../components/IndicatorParamDialog.vue';

export default {
  components: { IndicatorParamDialog },
  setup() {
    // 模拟数据
    const categories = ref([
      { id: 'all', name: '全部' },
      { id: 'trend', name: '大盘择时' },
      { id: 'block', name: '板块择时' },
      { id: 'stock', name: '个股择时指标' },
      { id: 'price', name: '股票价格' },
      { id: 'filter', name: '过滤项' },
      { id: 'finance', name: '财务指标' },
      { id: 'tech_signal', name: '技术指标信号' },
      { id: 'announcement', name: '公告类' },
      { id: 'other', name: '其他' }
    ]);

    // 从 IndicatorParamDialog 组件获取指标数据
    const indicators = ref([
      // 大盘择时
      {
        id: 1,
        name: 'MA指标设置',
        category: 'trend',
        enabled: true,
        parameters: [
          { name: '周期', value: '20', description: '计算移动平均的周期数', default: '20' },
          { name: '类型', value: 'SMA', description: '简单移动平均(SMA)或指数移动平均(EMA)', default: 'SMA' },
          { name: '价格类型', value: 'Close', description: '使用的价格类型(开盘、收盘、最高、最低等)', default: 'Close' }
        ]
      },
      {
        id: 2,
        name: 'MACD指标',
        category: 'trend',
        enabled: true,
        parameters: [
          { name: '快线周期', value: '26', description: 'DIF快线周期', default: '26' },
          { name: '慢线周期', value: '12', description: 'DEA慢线周期', default: '12' },
          { name: '信号线周期', value: '9', description: 'MACD信号线周期', default: '9' },
          { name: '金叉信号', value: 'true', description: '启用金叉信号', default: 'true' },
          { name: '死叉信号', value: 'true', description: '启用死叉信号', default: 'true' }
        ]
      },
      {
        id: 3,
        name: 'KDJ指标',
        category: 'trend',
        enabled: true,
        parameters: [
          { name: 'K周期', value: '9', description: 'K线周期', default: '9' },
          { name: 'D周期', value: '3', description: 'D线周期', default: '3' },
          { name: 'J周期', value: '3', description: 'J线周期', default: '3' }
        ]
      },
      // 板块择时
      {
        id: 4,
        name: 'MA指标设置',
        type: '趋势指标',
        description: '板块MA指标',
        category: 'block',
        enabled: false,
        parameters: [
          { name: '周期', value: '20', description: '计算移动平均的周期数', default: '20' }
        ]
      },
      {
        id: 5,
        name: 'MACD指标',
        type: '趋势指标',
        description: '板块MACD指标',
        category: 'block',
        enabled: false,
        parameters: [
          { name: '快线周期', value: '26', description: 'DIF快线周期', default: '26' },
          { name: '慢线周期', value: '12', description: 'DEA慢线周期', default: '12' },
          { name: '信号线周期', value: '9', description: 'MACD信号线周期', default: '9' },
          { name: '金叉信号', value: 'true', description: '启用金叉信号', default: 'true' }
        ]
      },
      {
        id: 6,
        name: 'KDJ指标',
        type: '趋势指标',
        description: '板块KDJ指标',
        category: 'block',
        enabled: false,
        parameters: [
          { name: 'K周期', value: '9', description: 'K线周期', default: '9' },
          { name: 'D周期', value: '3', description: 'D线周期', default: '3' },
          { name: 'J周期', value: '3', description: 'J线周期', default: '3' }
        ]
      },
      // 个股买卖信号
      {
        id: 1001,
        name: '开盘价',
        type: '价格',
        description: '当日开盘价',
        category: 'tech_signal',
        enabled: false,
        parameters: []
      },
      {
        id: 1002,
        name: '收盘价',
        type: '价格',
        description: '当日收盘价',
        category: 'tech_signal',
        enabled: false,
        parameters: []
      },
      {
        id: 1003,
        name: '最高价',
        type: '价格',
        description: '当日最高价',
        category: 'tech_signal',
        enabled: false,
        parameters: []
      },
      {
        id: 1004,
        name: '最低价',
        type: '价格',
        description: '当日最低价',
        category: 'tech_signal',
        enabled: false,
        parameters: []
      },
      {
        id: 1005,
        name: '涨幅',
        type: '价格',
        description: '当日涨跌幅',
        category: 'tech_signal',
        enabled: false,
        parameters: []
      },
      // 个股买卖信号 - 量能信号
      {
        id: 1011,
        name: '成交额',
        type: '成交额',
        description: '成交金额',
        category: 'tech_signal',
        enabled: false,
        parameters: []
      },
      {
        id: 1012,
        name: '成交量',
        type: '成交量',
        description: '成交量',
        category: 'tech_signal',
        enabled: false,
        parameters: []
      },
      {
        id: 1013,
        name: '量比',
        type: '成交量',
        description: '量比',
        category: 'tech_signal',
        enabled: false,
        parameters: []
      },
      {
        id: 1014,
        name: '换手率',
        type: '换手率',
        description: '换手率',
        category: 'tech_signal',
        enabled: false,
        parameters: []
      },
      // 个股买卖信号 - 技术指标信号（复用个股择时指标，id 1201 起）
      {
        id: 1201,
        name: 'MA指标设置',
        type: '趋势指标',
        description: '个股MA指标',
        category: 'stock',
        enabled: false,
        parameters: [
          { name: '周期', value: '20', description: '计算移动平均的周期数', default: '20' },
          { name: '类型', value: 'SMA', description: '简单移动平均(SMA)或指数移动平均(EMA)', default: 'SMA' },
          { name: '价格类型', value: 'Close', description: '使用的价格类型(开盘、收盘、最高、最低等)', default: 'Close' },
          { name: 'MA短线', value: 5, description: '短期移动平均线周期', default: '5' },
          { name: 'MA长线', value: 20, description: '长期移动平均线周期', default: '20' }
        ]
      },
      {
        id: 1202,
        name: 'MACD指标',
        type: '趋势指标',
        description: '个股MACD指标',
        category: 'stock',
        enabled: false,
        parameters: [
          { name: '快线周期', value: '12', description: '快线EMA周期', default: '12' },
          { name: '慢线周期', value: '26', description: '慢线EMA周期', default: '26' },
          { name: '信号线周期', value: '9', description: '信号线EMA周期', default: '9' }
        ]
      },
      {
        id: 1203,
        name: 'KDJ指标',
        type: '趋势指标',
        description: '个股KDJ指标',
        category: 'stock',
        enabled: false,
        parameters: [
          { name: 'K周期', value: '9', description: 'K线周期', default: '9' },
          { name: 'D周期', value: '3', description: 'D线周期', default: '3' },
          { name: 'J周期', value: '3', description: 'J线周期', default: '3' }
        ]
      },
      {
        id: 1204,
        name: 'RSI指标',
        type: '动量指标',
        description: '个股RSI指标',
        category: 'stock',
        enabled: false,
        parameters: [
          { name: '周期', value: '14', description: '计算RSI的周期数', default: '14' }
        ]
      },
      {
        id: 1205,
        name: 'BOLL指标',
        type: '波动率指标',
        description: '个股BOLL指标',
        category: 'stock',
        enabled: false,
        parameters: [
          { name: '周期', value: '20', description: '计算BOLL的周期数', default: '20' },
          { name: '标准差倍数', value: '2', description: '标准差倍数', default: '2' }
        ]
      },
      {
        id: 1206,
        name: 'CR指标',
        type: '动量指标',
        description: '个股CR指标',
        category: 'stock',
        enabled: false,
        parameters: [
          { name: '周期', value: '26', description: '计算CR的周期数', default: '26' }
        ]
      },
      {
        id: 1207,
        name: 'ATR指标',
        type: '波动率指标',
        description: '个股ATR指标',
        category: 'stock',
        enabled: false,
        parameters: [
          { name: '周期', value: '14', description: '计算ATR的周期数', default: '14' }
        ]
      },
      {
        id: 1208,
        name: 'TRIX指标',
        type: '动量指标',
        description: '个股TRIX指标',
        category: 'stock',
        enabled: false,
        parameters: [
          { name: '周期', value: '12', description: '计算TRIX的周期数', default: '12' }
        ]
      },
      {
        id: 1209,
        name: 'CCI指标',
        type: '动量指标',
        description: '个股CCI指标',
        category: 'stock',
        enabled: false,
        parameters: [
          { name: '周期', value: '14', description: '计算CCI的周期数', default: '14' }
        ]
      },
      {
        id: 1210,
        name: 'BBIC指标',
        type: '动量指标',
        description: '个股BBIC指标',
        category: 'stock',
        enabled: false,
        parameters: [
          { name: '周期', value: '20', description: '计算BBIC的周期数', default: '20' }
        ]
      },
      {
        id: 1211,
        name: '四周期多头排列',
        type: '趋势指标',
        description: '个股四周期多头排列',
        category: 'stock',
        enabled: false,
        parameters: [
          { name: '周期1', value: '5', description: '第一个周期', default: '5' },
          { name: '周期2', value: '10', description: '第二个周期', default: '10' },
          { name: '周期3', value: '20', description: '第三个周期', default: '20' },
          { name: '周期4', value: '60', description: '第四个周期', default: '60' }
        ]
      },
      {
        id: 1212,
        name: 'EMA指标',
        type: '趋势指标',
        description: '个股EMA指标',
        category: 'stock',
        enabled: false,
        parameters: [
          { name: '周期', value: '20', description: '计算EMA的周期数', default: '20' }
        ]
      },
      // 股票价格
      {
        id: 19,
        name: '开盘价',
        type: '价格',
        description: '当日开盘价',
        category: 'price',
        enabled: false,
        parameters: [
          { name: '比较符', value: '大于', description: '比较方式', default: '大于' },
          { name: '比较指标', value: '收盘价', description: '比较的指标', default: '收盘价' }
        ]
      },
      {
        id: 20,
        name: '收盘价',
        type: '价格',
        description: '当日收盘价',
        category: 'price',
        enabled: false,
        parameters: [
          { name: '比较符', value: '大于', description: '比较方式', default: '大于' },
          { name: '比较指标', value: '开盘价', description: '比较的指标', default: '开盘价' }
        ]
      },
      {
        id: 21,
        name: '最高价',
        type: '价格',
        description: '当日最高价',
        category: 'price',
        enabled: false,
        parameters: [
          { name: '比较符', value: '大于', description: '比较方式', default: '大于' },
          { name: '比较指标', value: '收盘价', description: '比较的指标', default: '收盘价' }
        ]
      },
      {
        id: 22,
        name: '最低价',
        type: '价格',
        description: '当日最低价',
        category: 'price',
        enabled: false,
        parameters: [
          { name: '比较符', value: '大于', description: '比较方式', default: '大于' },
          { name: '比较指标', value: '收盘价', description: '比较的指标', default: '收盘价' }
        ]
      },
      {
        id: 23,
        name: '昨日收盘价',
        type: '价格',
        description: '昨日收盘价',
        category: 'price',
        enabled: false,
        parameters: [
          { name: '比较符', value: '大于', description: '比较方式', default: '大于' },
          { name: '比较指标', value: '收盘价', description: '比较的指标', default: '收盘价' }
        ]
      },
      {
        id: 24,
        name: '日成交均价',
        type: '价格',
        description: '当日成交均价',
        category: 'price',
        enabled: false,
        parameters: [
          { name: '比较符', value: '大于', description: '比较方式', default: '大于' },
          { name: '比较指标', value: '收盘价', description: '比较的指标', default: '收盘价' }
        ]
      },
      {
        id: 25,
        name: '涨幅',
        type: '价格',
        description: '当日涨跌幅',
        category: 'price',
        enabled: false,
        parameters: [
          { name: '信号类型', value: 'single', description: '涨幅信号类型', default: 'single' },
          { name: '比较符', value: '大于', description: '比较方式', default: '大于' },
          { name: '百分比值', value: '0', description: '涨幅百分比', default: '0' },
          { name: '区间天数', value: '5', description: '区间涨幅天数', default: '5' }
        ]
      },
      {
        id: 26,
        name: '量比',
        type: '成交量',
        description: '量比',
        category: 'price',
        enabled: false,
        parameters: [
          { name: '比较符', value: '大于', description: '比较方式', default: '大于' },
          { name: '量比值', value: '1.0', description: '量比值', default: '1.0' }
        ]
      },
      {
        id: 27,
        name: '成交额',
        type: '成交额',
        description: '成交金额',
        category: 'price',
        enabled: false,
        parameters: [
          { name: '比较符', value: '大于', description: '比较方式', default: '大于' },
          { name: '成交额', value: '0', description: '成交额(万元)', default: '0' }
        ]
      },
      {
        id: 28,
        name: '换手率',
        type: '换手率',
        description: '换手率',
        category: 'price',
        enabled: false,
        parameters: [
          { name: '比较符', value: '大于', description: '比较方式', default: '大于' },
          { name: '换手率', value: '0', description: '换手率(%)', default: '0' }
        ]
      },
      {
        id: 29,
        name: '市值',
        type: '市值',
        description: '总市值',
        category: 'price',
        enabled: false,
        parameters: [
          { name: '比较符', value: '大于', description: '比较方式', default: '大于' },
          { name: '市值', value: '0', description: '市值(亿元)', default: '0' }
        ]
      },
      {
        id: 30,
        name: '成交量',
        type: '成交量',
        description: '成交量',
        category: 'price',
        enabled: false,
        parameters: [
          { name: '比较符', value: '大于', description: '比较方式', default: '大于' },
          { name: '成交量', value: '0', description: '成交量(万股)', default: '0' }
        ]
      },
      {
        id: 31,
        name: '资金净流入',
        type: '资金流',
        description: '主力资金净流入',
        category: 'price',
        enabled: false,
        parameters: [
          { name: '比较符', value: '大于', description: '比较方式', default: '大于' },
          { name: '资金净流入', value: '0', description: '资金净流入(万元)', default: '0' }
        ]
      },
      // 公告类
      {
        id: 32,
        name: '股东减持',
        type: '公告',
        description: '公司股东减持公告',
        category: 'announcement',
        enabled: false,
        parameters: []
      },
      {
        id: 33,
        name: '股东增持',
        type: '公告',
        description: '公司股东增持公告',
        category: 'announcement',
        enabled: false,
        parameters: []
      },
      {
        id: 34,
        name: '股东分红',
        type: '公告',
        description: '公司分红公告',
        category: 'announcement',
        enabled: false,
        parameters: []
      },
      {
        id: 35,
        name: '违规问询函',
        type: '公告',
        description: '公司收到违规问询函',
        category: 'announcement',
        enabled: false,
        parameters: []
      },
      {
        id: 36,
        name: '业绩预告',
        type: '公告',
        description: '公司业绩预告',
        category: 'announcement',
        enabled: false,
        parameters: []
      },
      {
        id: 37,
        name: '业绩公告',
        type: '公告',
        description: '公司业绩公告',
        category: 'announcement',
        enabled: false,
        parameters: []
      },
      // 过滤项
      {
        id: 38,
        name: '过滤新上市',
        type: '过滤',
        description: '过滤新上市股票',
        category: 'filter',
        enabled: false,
        parameters: [
          { name: '启用', value: 'false', description: '是否启用过滤', default: 'false' },
          { name: '上市天数限制', value: '30', description: '新上市股票的上市天数限制', default: '30' },
          { name: '比较符', value: '>=', description: '比较符', default: '>=' },
          { name: '比较指标', value: '成交量', description: '比较的指标', default: '成交量' }
        ]
      },
      {
        id: 39,
        name: '过滤北交所',
        type: '过滤',
        description: '过滤北交所股票',
        category: 'filter',
        enabled: false,
        parameters: [
          { name: '过滤北交所', value: 'false', description: '是否启用北交所过滤', default: 'false' }
        ]
      },
      {
        id: 40,
        name: '过滤沪深主板',
        type: '过滤',
        description: '过滤沪深主板股票',
        category: 'filter',
        enabled: false,
        parameters: [
          { name: '过滤沪深主板', value: 'false', description: '是否启用沪深主板过滤', default: 'false' }
        ]
      },
      {
        id: 41,
        name: '过滤ST',
        type: '过滤',
        description: '过滤ST股票',
        category: 'filter',
        enabled: false,
        parameters: [
          { name: '过滤ST', value: 'false', description: '是否启用ST过滤', default: 'false' }
        ]
      },
      {
        id: 42,
        name: '过滤*ST',
        type: '过滤',
        description: '过滤*ST股票',
        category: 'filter',
        enabled: false,
        parameters: [
          { name: '过滤*ST', value: 'false', description: '是否启用*ST过滤', default: 'false' }
        ]
      },
      {
        id: 43,
        name: '过滤停牌',
        type: '过滤',
        description: '过滤停牌股票',
        category: 'filter',
        enabled: false,
        parameters: [
          { name: '过滤停牌', value: 'false', description: '是否启用停牌过滤', default: 'false' }
        ]
      },
      {
        id: 44,
        name: '过滤科创板',
        type: '过滤',
        description: '过滤科创板股票',
        category: 'filter',
        enabled: false,
        parameters: [
          { name: '过滤科创板', value: 'false', description: '是否启用科创板过滤', default: 'false' }
        ]
      },
      {
        id: 45,
        name: '过滤创业板',
        type: '过滤',
        description: '过滤创业板股票',
        category: 'filter',
        enabled: false,
        parameters: [
          { name: '过滤创业板', value: 'false', description: '是否启用创业板过滤', default: 'false' }
        ]
      },
      {
        id: 46,
        name: '过滤退市',
        type: '过滤',
        description: '过滤退市股票',
        category: 'filter',
        enabled: false,
        parameters: [
          { name: '过滤退市', value: 'false', description: '是否启用退市过滤', default: 'false' }
        ]
      },
      // 财务指标
      {
        id: 47,
        name: 'ROA',
        type: '财务指标',
        description: '资产收益率',
        category: 'finance',
        enabled: false,
        parameters: []
      },
      {
        id: 48,
        name: 'ROE',
        type: '财务指标',
        description: '净资产收益率',
        category: 'finance',
        enabled: false,
        parameters: []
      },
      {
        id: 49,
        name: '毛利率',
        type: '财务指标',
        description: '毛利率',
        category: 'finance',
        enabled: false,
        parameters: []
      },
      {
        id: 50,
        name: '净利率',
        type: '财务指标',
        description: '净利率',
        category: 'finance',
        enabled: false,
        parameters: []
      },
      {
        id: 51,
        name: '营收增长率',
        type: '财务指标',
        description: '营业收入增长率',
        category: 'finance',
        enabled: false,
        parameters: []
      },
      {
        id: 52,
        name: '净利润增长率',
        type: '财务指标',
        description: '净利润增长率',
        category: 'finance',
        enabled: false,
        parameters: []
      },
      {
        id: 53,
        name: '动态市盈率',
        type: '财务指标',
        description: '动态市盈率',
        category: 'finance',
        enabled: false,
        parameters: []
      }
    ]);

    // 状态变量
    const activeCategory = ref('all');
    const searchQuery = ref('');
    const showModal = ref(false);
    const currentIndicator = ref({});
    const startDate = ref('2023-01-01');
    const endDate = ref('2023-12-31');
    const notification = ref({
      show: false,
      message: '',
      type: 'info'
    });

    // 选股策略控制区
    const selectedMarketIndex = ref('上证指数');
    const selectedPeriod = ref('D'); // 'D' for 日, 'W' for 周, 'M' for 月
    const maShort = ref(5);
    const maLong = ref(20);
    
    // 回测参数
    const initialCapital = ref(100000);
    const dataFrequency = ref('daily');
    const executionEnvironment = ref('python2');

    // 计算属性
    const filteredIndicators = computed(() => {
      return indicators.value.filter(indicator => {
        const matchesCategory = activeCategory.value === 'all' || indicator.category === activeCategory.value;
        const matchesSearch = indicator.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
                              indicator.description.toLowerCase().includes(searchQuery.value.toLowerCase());
        return matchesCategory && matchesSearch;
      });
    });

    const selectedIndicators = computed(() => {
      return indicators.value.filter(indicator => indicator.enabled);
    });

    const indicatorNameMap = {
      'MA指标设置': 'ma',
      'MACD指标': 'macd',
      'KDJ指标': 'kdj',
      'RSI指标': 'rsi',
      'BOLL指标': 'boll',
      'CR指标': 'cr',
      'ATR指标': 'atr',
      'TRIX指标': 'trix',
      'CCI指标': 'cci',
      'BBIC指标': 'bbic',
      '四周期多头排列': 'four_ma_long',
      'EMA指标': 'ema'
      // 如有其它指标可继续补充
    };

    const isBacktesting = ref(false);
    const router = useRouter();

    // 方法
    const setActiveCategory = (categoryId) => {
      activeCategory.value = categoryId;
    };

    const handleIndicatorChange = (indicator) => {
      // 如果是过滤项，更新对应的参数
      if (indicator.category === 'filter') {
        const filterParam = indicator.parameters.find(p => p.name.includes('过滤'));
        if (filterParam) {
          filterParam.value = indicator.enabled ? 'true' : 'false';
        }
      }
      
      if (indicator.enabled) {
        showNotification(`已启用指标: ${indicator.name}`, 'success');
      } else {
        showNotification(`已禁用指标: ${indicator.name}`, 'warning');
      }
    };

    const enableAll = () => {
      indicators.value.forEach(indicator => {
        indicator.enabled = true;
      });
      showNotification('已启用所有指标', 'success');
    };

    const disableAll = () => {
      indicators.value.forEach(indicator => {
        indicator.enabled = false;
      });
      showNotification('已禁用所有指标', 'warning');
    };

    const openDetailModal = (indicator) => {
      currentIndicator.value = JSON.parse(JSON.stringify(indicator)); // 深拷贝
      showModal.value = true;
    };

    const closeModal = () => {
      showModal.value = false;
    };

    const saveParameters = (updatedIndicator) => {
      // 更新原始指标数据
      const originalIndicator = indicators.value.find(i => i.id === updatedIndicator.id);
      if (originalIndicator) {
        originalIndicator.parameters = [...updatedIndicator.parameters];
        // 针对MA的参数，只有大盘择时（trend）的MA指标才添加市场指数和周期选择
        if (originalIndicator.name.includes('MA') && originalIndicator.category === 'trend') {
          originalIndicator.parameters.push({ name: 'MA短线', value: maShort.value, description: '短期移动平均线周期', default: '5' });
          originalIndicator.parameters.push({ name: 'MA长线', value: maLong.value, description: '长期移动平均线周期', default: '20' });
        }
      }
      
      showNotification('参数已保存', 'success');
      closeModal();
    };

    const resetParameters = (updatedIndicator) => {
      currentIndicator.value.parameters.forEach(param => {
        param.value = param.default;
      });
      // 针对MA的参数，只有大盘择时（trend）的MA指标才重置市场指数和周期选择
      if (currentIndicator.value.name.includes('MA') && currentIndicator.value.category === 'trend') {
        maShort.value = 5;
        maLong.value = 20;
      }
      showNotification('参数已重置为默认值', 'info');
    };

    const updateIndicatorData = (updatedIndicator) => {
      console.log('🔄 updateIndicatorData 被调用', updatedIndicator);
      // 更新主界面中的指标数据
      const originalIndicator = indicators.value.find(i => i.id === updatedIndicator.id);
      if (originalIndicator) {
        console.log('📝 找到原始指标，正在更新参数', originalIndicator.name);
        // 更新参数
        originalIndicator.parameters = [...updatedIndicator.parameters];
        // 更新其他属性
        Object.assign(originalIndicator, updatedIndicator);
        console.log('✅ 参数更新完成', originalIndicator.parameters);
      } else {
        console.log('❌ 未找到对应的原始指标', updatedIndicator.id);
      }
    };

    const removeIndicator = (indicator) => {
      indicator.enabled = false;
      showNotification(`已移除指标: ${indicator.name}`, 'warning');
    };

    const runBacktest = async () => {
      if (selectedIndicators.value.length === 0) {
        showNotification('请至少选择一个指标', 'warning');
        return;
      }
      isBacktesting.value = true;
      showNotification('回测运行中...', 'info');

      // 收集所有选中指标的详细信息
      const selectedIndicatorDetails = selectedIndicators.value.map(indicator => ({
        name: indicator.name,
        type: indicator.type,
        category: indicator.category,
        enabled: indicator.enabled,
        // 添加指标的具体参数配置
        params: indicator.params || {},
        // 添加指标的中文名称用于显示
        displayName: indicator.displayName || indicator.name
      }));

      // 构造请求参数
      const indicators = selectedIndicators.value.map(i => indicatorNameMap[i.name] || i.name.toLowerCase());
      const payload = {
        indicators,
        // 添加详细的指标配置
        indicator_details: selectedIndicatorDetails,
        conditions: {}, // 可根据实际需求补充
        start_date: startDate.value.replace(/-/g, ''),
        end_date: endDate.value.replace(/-/g, ''),
        total_cash: initialCapital.value,
        // 添加策略类型，基于指标动态生成交易信号
        strategy_type: 'indicator_driven',
        // 添加交易频率配置
        trade_frequency: 'daily' // 可选: daily, weekly, monthly
      };

      console.log('🚀 发送回测请求，选中指标:', selectedIndicatorDetails);
      console.log('📊 完整请求参数:', payload);

      try {
        const response = await fetch('http://localhost:8002/api/backtest/run/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (result.status === 'success') {
          showNotification('回测成功', 'success');
          console.log('回测结果', result);

          // 保存回测结果到 localStorage 用于结果页面显示
          const backtestData = {
            strategyName: '指标筛选策略',
            startDate: startDate.value,
            endDate: endDate.value,
            initialCapital: payload.total_cash,
            frequency: '每日',
            status: '已完成',
            executionTime: '刚刚',
            filteredStocks: result.filtered_stocks || [],
            stockCount: result.filtered_stock_codes?.length || 0,
            accountSummary: result.backtest?.backtest_results?.data?.account_summary || {},
            performance: result.backtest?.backtest_results?.data?.performance || {},
            trades: result.backtest?.backtest_results?.data?.trades || [],
            positions: result.backtest?.backtest_results?.data?.positions || [],
            strategyInfo: result.backtest?.strategy_info || {}
          };

          // 保存到 localStorage
          localStorage.setItem('backtestResults', JSON.stringify(backtestData));

          // 添加详细的调试信息
          console.log('🔍 前端收到的完整回测数据:', result);
          console.log('🔍 处理后的回测数据:', backtestData);
          console.log('🔍 Performance数据:', backtestData.performance);
          console.log('🔍 Account数据:', backtestData.accountSummary);

          // 跳转到回测详情页面，传递参数
          router.push({ 
            name: 'BacktestDetails',
            query: {
              startDate: startDate.value,
              endDate: endDate.value,
              initialCapital: payload.total_cash,
              dataFrequency: 'daily',
              minuteInterval: '5',
              selectedConditions: JSON.stringify(selectedIndicatorDetails)
            }
          });
          showNotification('回测数据已保存，已跳转到回测详情页面', 'success');
        } else {
          showNotification('回测失败: ' + (result.error || '未知错误'), 'warning');
        }
      } catch (e) {
        showNotification('请求失败: ' + e.message, 'warning');
      } finally {
        isBacktesting.value = false;
      }
    };

    const showNotification = (message, type = 'info') => {
      notification.value = {
        show: true,
        message,
        type
      };
      
      setTimeout(() => {
        notification.value.show = false;
      }, 3000);
    };

    const formatParameters = (parameters) => {
      if (!parameters || parameters.length === 0) return '无参数';
      
      // 特殊处理过滤项
      const filterParams = parameters.filter(param => 
        param.name.includes('过滤') || 
        param.name === '上市天数限制'
      );
      
      if (filterParams.length > 0) {
        // 对于过滤项，显示启用状态和具体参数
        const enabledParam = filterParams.find(p => p.name.includes('过滤'));
        const daysParam = filterParams.find(p => p.name === '上市天数限制');
        
        const status = enabledParam && enabledParam.value === 'true' ? '已启用' : '已禁用';
        
        if (daysParam) {
          return `${status}, 上市天数限制: ${daysParam.value}天`;
        } else {
          return status;
        }
      }
      
      // 处理价格指标（开盘价、收盘价、最高价、最低价等）
      const compareParam = parameters.find(p => p.name === '比较符');
      const indicatorParam = parameters.find(p => p.name === '比较指标');
      
      if (compareParam && indicatorParam) {
        return `${compareParam.value}, ${indicatorParam.value}`;
      }
      
      // 处理MACD指标
      const fastParam = parameters.find(p => p.name === '快线周期');
      const slowParam = parameters.find(p => p.name === '慢线周期');
      const signalParam = parameters.find(p => p.name === '信号线周期');
      const goldenCrossParam = parameters.find(p => p.name === '金叉信号');
      const deathCrossParam = parameters.find(p => p.name === '死叉信号');
      
      if (fastParam && slowParam && signalParam) {
        let result = `DIF:${fastParam.value}, DEA:${slowParam.value}, MACD:${signalParam.value}`;
        if (goldenCrossParam && goldenCrossParam.value === 'true') {
          result += ', 金叉信号';
        }
        if (deathCrossParam && deathCrossParam.value === 'true') {
          result += ', 死叉信号';
        }
        return result;
      }
      
      // 处理涨幅指标
      const typeParam = parameters.find(p => p.name === '信号类型');
      const valueParam = parameters.find(p => p.name === '百分比值');
      const daysParam = parameters.find(p => p.name === '区间天数');
      
      if (typeParam && valueParam) {
        if (typeParam.value === 'range' && daysParam) {
          return `${typeParam.value}, ${valueParam.value}%, ${daysParam.value}天`;
        } else {
          return `${typeParam.value}, ${valueParam.value}%`;
        }
      }
      
      // 对于其他指标，正常显示参数
      return parameters.map(param => {
        const value = param.value !== undefined ? param.value : param.default;
        return `${param.name}: ${value}`;
      }).join(', ');
    };

    const getCardColorClass = (id) => {
      const colors = ['color-1', 'color-2', 'color-3', 'color-4', 'color-5'];
      return colors[(id - 1) % colors.length];
    };

    const scrollNav = (direction) => {
      const navScroll = document.querySelector('.nav-scroll');
      const scrollAmount = 200;
      
      if (direction === 'left') {
        navScroll.scrollLeft -= scrollAmount;
      } else {
        navScroll.scrollLeft += scrollAmount;
      }
    };

    return {
      categories,
      indicators,
      activeCategory,
      searchQuery,
      showModal,
      currentIndicator,
      startDate,
      endDate,
      notification,
      filteredIndicators,
      selectedIndicators,
      setActiveCategory,
      handleIndicatorChange,
      enableAll,
      disableAll,
      openDetailModal,
      closeModal,
      saveParameters,
      resetParameters,
      removeIndicator,
      runBacktest,
      formatParameters,
      getCardColorClass,
      scrollNav,
      isBacktesting,
      selectedMarketIndex,
      selectedPeriod,
      maShort,
      maLong,
      initialCapital,
      dataFrequency,
      executionEnvironment
    };
  }
};
</script>

<style scoped>
/* 整体布局 */
.indicator-selection {
  display: flex;
  height: 90vh;
  font-family: 'Arial', sans-serif;
  background-color: #f5f7fa;
}

/* 左侧面板 */
.left-panel {
  flex: 7;
  padding: 20px;
  overflow-y: auto;
  border-right: 1px solid #e0e6ed;
}

/* 右侧面板 */
.right-panel {
  flex: 3;
  padding: 20px;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
}

/* 顶部控制区域 */
.top-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.search-box {
  position: relative;
  width: 300px;
}

.search-input {
  width: 100%;
  padding: 10px 40px 10px 15px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #409eff;
}

.search-icon {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  color: #909399;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.action-btn {
  padding: 8px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.enable-btn {
  background-color: #67c23a;
  color: white;
}

.enable-btn:hover {
  background-color: #85ce61;
}

.disable-btn {
  background-color: #f56c6c;
  color: white;
}

.disable-btn:hover {
  background-color: #f78989;
}

/* 导航栏 */
.nav-container {
  position: relative;
  margin-bottom: 20px;
}

.nav-scroll {
  display: flex;
  overflow-x: auto;
  padding: 10px 0;
  scrollbar-width: none;
  /* Firefox */
  -ms-overflow-style: none;
  /* IE 10+ */
}

.nav-scroll::-webkit-scrollbar {
  display: none;
  /* Chrome Safari */
}

.nav-item {
  padding: 8px 20px;
  margin-right: 10px;
  white-space: nowrap;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  background-color: #f0f2f5;
}

.nav-item:hover {
  background-color: #e6e8eb;
}

.nav-item.active {
  background-color: #409eff;
  color: white;
}

.nav-scroll-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: #409eff;
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  z-index: 1;
}

.nav-scroll-btn.left {
  left: 0;
}

.nav-scroll-btn.right {
  right: 0;
}

/* 指标卡片网格 */
.indicators-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

/* 指标卡片 */
.indicator-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 15px;
  transition: all 0.3s;
  border-top: 4px solid;
}

.indicator-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

/* 卡片颜色 */
.color-1 {
  border-top-color: #409eff;
}

.color-2 {
  border-top-color: #67c23a;
}

.color-3 {
  border-top-color: #e6a23c;
}

.color-4 {
  border-top-color: #f56c6c;
}

.color-5 {
  border-top-color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.card-title {
  font-size: 18px;
  font-weight: bold;
}

.card-type {
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 4px;
  background-color: #f0f2f5;
  color: #606266;
}

.card-description {
  font-size: 14px;
  color: #606266;
  margin-bottom: 15px;
  height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.switch-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 开关样式 */
.switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 20px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 20px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked+.slider {
  background-color: #409eff;
}

input:checked+.slider:before {
  transform: translateX(20px);
}

.detail-btn {
  padding: 5px 10px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.3s;
}

.detail-btn:hover {
  background-color: #66b1ff;
}

/* 右侧面板样式 */
.selected-header {
  margin-bottom: 20px;
}

.selected-header h2 {
  margin: 0 0 15px 0;
  color: #303133;
}

.date-range {
  display: flex;
  gap: 15px;
}

.date-input {
  flex: 1;
}

.date-input label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  color: #606266;
}

.date-input input {
  width: 100%;
  padding: 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

/* 资金数据框 */
.capital-data-box {
  margin-top: 15px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.capital-input {
  display: flex;
  flex-direction: column;
}

.capital-input label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.input-with-currency {
  display: flex;
  align-items: center;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: white;
}

.currency-symbol {
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-right: 1px solid #dcdfe6;
  color: #606266;
  font-weight: 500;
  font-size: 14px;
}

.input-with-currency input {
  flex: 1;
  padding: 8px 12px;
  border: none;
  outline: none;
  font-size: 14px;
}

.input-with-currency input:focus {
  background-color: #fafbfc;
}

/* 时间周期框 */
.time-period-box {
  margin-top: 15px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.period-input {
  margin-bottom: 10px;
}

.period-input:last-child {
  margin-bottom: 0;
}

.period-input label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.period-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: white;
  font-size: 14px;
  color: #606266;
  cursor: pointer;
  outline: none;
}

.period-select:focus {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.selected-indicators {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 20px;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}

.selected-card {
  background-color: #f5f7fa;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  border-left: 4px solid #409eff;
}

.selected-card-header {
  margin-bottom: 10px;
}

.selected-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 5px;
}

.selected-params {
  font-size: 14px;
  color: #606266;
}

.selected-card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.remove-btn {
  padding: 5px 10px;
  background-color: #f56c6c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.3s;
}

.remove-btn:hover {
  background-color: #f78989;
}

.backtest-section {
  text-align: center;
}

.backtest-btn {
  padding: 12px 30px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
  transition: background-color 0.3s;
}

.backtest-btn:hover {
  background-color: #66b1ff;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  border-radius: 8px;
  width: 600px;
  max-width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #ebeef5;
}

.modal-header h3 {
  margin: 0;
  color: #303133;
}

.modal-type {
  font-size: 14px;
  padding: 3px 8px;
  border-radius: 4px;
  background-color: #f0f2f5;
  color: #606266;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #909399;
}

.close-btn:hover {
  color: #606266;
}

.modal-description {
  padding: 15px 20px;
  color: #606266;
  border-bottom: 1px solid #ebeef5;
}

.strategy-controls {
  padding: 15px 20px;
  border-bottom: 1px solid #ebeef5;
}

.form-row {
  margin-bottom: 10px;
}

.form-label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  color: #606266;
}

.form-select {
  width: 100%;
  padding: 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
}

.period-tabs {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.tab {
  padding: 8px 15px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #f5f7fa;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
  transition: all 0.3s;
}

.tab:hover {
  background-color: #e6e8eb;
}

.tab.active {
  background-color: #409eff;
  color: white;
  border-color: #409eff;
}

.modal-params {
  padding: 15px 20px;
}

.modal-params h4 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #303133;
}

.params-table {
  width: 100%;
  border-collapse: collapse;
}

.params-table th,
.params-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
}

.params-table th {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: normal;
}

.param-input {
  width: 100%;
  padding: 5px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.ma-inputs {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.param-table {
  width: 100%;
  border-collapse: collapse;
}

.param-table th,
.param-table td {
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
}

.param-table th {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: normal;
}

.modal-actions {
  padding: 15px 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  border-top: 1px solid #ebeef5;
}

.save-btn {
  padding: 8px 15px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.save-btn:hover {
  background-color: #66b1ff;
}

.reset-btn {
  padding: 8px 15px;
  background-color: #e6a23c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.reset-btn:hover {
  background-color: #ebb563;
}

/* 通知提示 */
.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 4px;
  color: white;
  font-size: 14px;
  z-index: 2000;
  animation: slideIn 0.3s ease-out;
}

.notification.success {
  background-color: #67c23a;
}

.notification.warning {
  background-color: #e6a23c;
}

.notification.info {
  background-color: #409eff;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }

  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .indicators-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 900px) {
  .indicators-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .indicator-selection {
    flex-direction: column;
  }
  
  .left-panel {
    border-right: none;
    border-bottom: 1px solid #e0e6ed;
  }
  
  .indicators-grid {
    grid-template-columns: 1fr;
  }
}
</style>
