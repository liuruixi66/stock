<template>
  <div class="page-container">
    <div class="macd-calculator">
      <h2>MACD指标计算器</h2>

      <!-- 参数输入表单 -->
      <div class="parameter-form">
        <div class="form-group">
          <label>股票代码:</label>
          <input type="text" v-model="stockCode" placeholder="请输入股票代码">
          <span v-if="isLoading" class="loading-text">加载中...</span>
        </div>

        <!-- 股票信息显示 -->
        <div v-if="stockInfo" class="stock-info">
          <h3>{{ stockInfo.name }} ({{ stockInfo.code }})</h3>
          <p>可用数据范围: {{ stockInfo.date_range.earliest }} 到 {{ stockInfo.date_range.latest }}</p>
          <p>共有 {{ stockInfo.total_days }} 天的数据</p>
        </div>

        <div class="form-group">
          <label>开始日期:</label>
          <input type="date" v-model="startDate" :min="stockInfo?.date_range?.earliest" :max="stockInfo?.date_range?.latest">
        </div>

        <div class="form-group">
          <label>结束日期:</label>
          <input type="date" v-model="endDate" :min="startDate" :max="stockInfo?.date_range?.latest">
        </div>

        <div class="form-group">
          <label>短期周期(默认12):</label>
          <input type="number" v-model.number="shortPeriod" min="1" max="50">
        </div>

        <div class="form-group">
          <label>长期周期(默认26):</label>
          <input type="number" v-model.number="longPeriod" min="1" max="100">
        </div>

        <div class="form-group">
          <label>信号周期(默认9):</label>
          <input type="number" v-model.number="signalPeriod" min="1" max="30">
        </div>

        <button @click="calculateMACD" :disabled="isCalculating || !stockInfo">
          {{ isCalculating ? '计算中...' : '计算MACD' }}
        </button>
      </div>

      <!-- 结果显示 -->
      <div class="results" v-if="results.length > 0">
        <h3>计算结果</h3>

        <!-- 图表展示 -->
        <div ref="chart" class="chart-container"></div>

        <!-- 数据表格 -->
        <table class="result-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>收盘价</th>
              <th>DIF</th>
              <th>DEA</th>
              <th>MACD</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in paginatedResults" :key="index">
              <td>{{ item.date }}</td>
              <td>{{ item.close }}</td>
              <td :class="{ positive: item.dif > 0, negative: item.dif < 0 }">
                {{ item.dif !== null ? item.dif.toFixed(4) : '--' }}
              </td>
              <td>{{ item.dea !== null ? item.dea.toFixed(4) : '--' }}</td>
              <td :class="{ positive: item.macd > 0, negative: item.macd < 0 }">
                {{ item.macd !== null ? item.macd.toFixed(4) : '--' }}
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 分页控制 -->
        <div class="pagination" v-if="results.length > itemsPerPage">
          <button @click="currentPage--" :disabled="currentPage === 1">上一页</button>
          <span>第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
          <button @click="currentPage++" :disabled="currentPage === totalPages">下一页</button>
        </div>
      </div>

      <!-- 错误提示 -->
      <div class="error-message" v-if="errorMessage">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script>
import { nextTick } from 'vue';
import axios from 'axios';
import * as echarts from 'echarts';

export default {
  data() {
    return {
      stockCode: '',
      startDate: '',
      endDate: '',
      shortPeriod: 12,
      longPeriod: 26,
      signalPeriod: 9,
      isCalculating: false,
      results: [],
      errorMessage: '',
      currentPage: 1,
      itemsPerPage: 10,
      stockInfo: null,
      isLoading: false,
      chart: null
    };
  },
  computed: {
    totalPages() {
      return Math.ceil(this.results.length / this.itemsPerPage);
    },
    paginatedResults() {
      const start = (this.currentPage - 1) * this.itemsPerPage;
      const end = start + this.itemsPerPage;
      return this.results.slice(start, end);
    }
  },
  methods: {
    validateDates() {
      const start = new Date(this.startDate);
      const end = new Date(this.endDate);
      const now = new Date();
      
      if (start > end) {
        this.errorMessage = '开始日期不能大于结束日期';
        return false;
      }
      
      if (start > now || end > now) {
        this.errorMessage = '不能选择未来的日期';
        return false;
      }
      
      // 清除错误信息
      this.errorMessage = '';
      return true;
    },
    
    // 添加新方法：查询股票数据范围
    async fetchStockDateRange() {
      if (!this.stockCode) return;
      
      this.isLoading = true;
      this.errorMessage = '';
      
      try {
        const response = await axios.post('/api/calculate-macd/', {
          stock_code: this.stockCode,
          start_date: '2000-01-01',  // 使用一个很早的日期
          end_date: '2030-12-31'     // 使用一个很晚的日期
        });
        
        if (response.data.status === 'success') {
          this.stockInfo = response.data.stock_info;
          // 设置日期范围
          this.startDate = this.stockInfo.date_range.earliest;
          this.endDate = this.stockInfo.date_range.latest;
        } else {
          this.errorMessage = response.data.message;
        }
      } catch (error) {
        this.errorMessage = '获取股票数据失败: ' + (error.response?.data?.message || error.message);
      } finally {
        this.isLoading = false;
      }
    },

    // 修改计算MACD方法
    async calculateMACD() {
      if (!this.validateDates()) return;
      
      if (!this.stockCode) {
        this.errorMessage = '请输入股票代码';
        return;
      }

      this.isCalculating = true;
      this.errorMessage = '';

      try {
        const response = await axios.post('/api/calculate-macd/', {
          stock_code: this.stockCode,
          start_date: this.startDate,
          end_date: this.endDate,
          short_period: this.shortPeriod,
          long_period: this.longPeriod,
          signal_period: this.signalPeriod
        });

        if (response.data.status === 'success') {
          this.results = response.data.data;
          this.stockInfo = response.data.stock_info;
          this.currentPage = 1;
          await this.renderChart();
        } else {
          this.errorMessage = response.data.message || '计算失败';
        }
      } catch (error) {
        console.error('API Error:', error);
        this.errorMessage = '请求失败: ' + (error.response?.data?.message || error.message);
      } finally {
        this.isCalculating = false;
      }
    },

    async renderChart() {
      if (!this.results.length) return;

      try {
        // 等待 DOM 更新
        await nextTick();
        
        // 如果已有图表实例，先销毁
        if (this.chart) {
          this.chart.dispose();
        }

        // 确保容器元素存在
        const chartContainer = this.$refs.chart;
        if (!chartContainer) {
          console.error('Chart container not found');
          return;
        }

        // 创建新的图表实例
        this.chart = echarts.init(chartContainer);
        
        const dates = this.results.map(item => item.date);
        const closes = this.results.map(item => item.close);
        const dif = this.results.map(item => item.dif);
        const dea = this.results.map(item => item.dea);
        const macd = this.results.map(item => item.macd);

        const option = {
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'cross'
            }
          },
          legend: {
            data: ['收盘价', 'DIF', 'DEA', 'MACD']
          },
          grid: [{
            left: '3%',
            right: '4%',
            height: '60%'
          }, {
            left: '3%',
            right: '4%',
            top: '75%',
            height: '20%'
          }],
          xAxis: [{
            type: 'category',
            data: dates,
            scale: true,
            boundaryGap: false,
            axisLine: { onZero: false },
            splitLine: { show: false },
            min: 'dataMin',
            max: 'dataMax'
          }, {
            type: 'category',
            gridIndex: 1,
            data: dates,
            scale: true,
            boundaryGap: false,
            axisLine: { onZero: false },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false },
            min: 'dataMin',
            max: 'dataMax'
          }],
          yAxis: [{
            scale: true,
            splitArea: {
              show: true
            }
          }, {
            scale: true,
            gridIndex: 1,
            splitNumber: 2,
            axisLabel: { show: false },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: false }
          }],
          dataZoom: [{
            type: 'inside',
            xAxisIndex: [0, 1],
            start: 0,
            end: 100
          }, {
            show: true,
            xAxisIndex: [0, 1],
            type: 'slider',
            bottom: '0%',
            start: 0,
            end: 100
          }],
          series: [
            {
              name: '收盘价',
              type: 'line',
              data: closes,
              smooth: true,
              lineStyle: {
                width: 1
              }
            },
            {
              name: 'DIF',
              type: 'line',
              data: dif,
              smooth: true,
              lineStyle: {
                width: 1,
                color: '#FF9800'
              }
            },
            {
              name: 'DEA',
              type: 'line',
              data: dea,
              smooth: true,
              lineStyle: {
                width: 1,
                color: '#2196F3'
              }
            },
            {
              name: 'MACD',
              type: 'bar',
              xAxisIndex: 1,
              yAxisIndex: 1,
              data: macd,
              itemStyle: {
                color: function(params) {
                  return params.value >= 0 ? '#00C853' : '#FF5252';
                }
              }
            }
          ]
        };

        this.chart.setOption(option);
        
        // 添加窗口大小变化的监听
        window.addEventListener('resize', this.handleResize);
      } catch (error) {
        console.error('Chart initialization failed:', error);
        this.errorMessage = '图表初始化失败: ' + error.message;
      }
    },
    
    handleResize() {
      if (this.chart) {
        this.chart.resize();
      }
    }
  },
  mounted() {
    // 设置默认日期范围（最近一年）
    const end = new Date();
    const start = new Date();
    start.setFullYear(start.getFullYear() - 1);
    
    this.endDate = end.toISOString().split('T')[0];
    this.startDate = start.toISOString().split('T')[0];

    // 获取当前日期作为最大值
    const maxDate = new Date().toISOString().split('T')[0];
    
    // 设置日期输入框的最大值
    const startDateInput = document.querySelector('input[type="date"]:first-of-type');
    const endDateInput = document.querySelector('input[type="date"]:last-of-type');
    if (startDateInput) {
      startDateInput.max = maxDate;
      // 设置最小日期为2年前
      const minDate = new Date();
      minDate.setFullYear(minDate.getFullYear() - 2);
      startDateInput.min = minDate.toISOString().split('T')[0];
    }
    if (endDateInput) {
      endDateInput.max = maxDate;
      endDateInput.min = this.startDate;
    }
  },
  watch: {
    // 监听开始日期变化
    startDate(newVal) {
      const endDateInput = document.querySelector('input[type="date"]:last-of-type');
      if (endDateInput) {
        endDateInput.min = newVal;
      }
      this.validateDates();
    },
    // 监听结束日期变化
    endDate(newVal) {
      const startDateInput = document.querySelector('input[type="date"]:first-of-type');
      if (startDateInput) {
        startDateInput.max = newVal;
      }
      this.validateDates();
    },
    // 监听股票代码变化
    stockCode(newVal) {
      if (newVal && newVal.length >= 6) {
        this.fetchStockDateRange();
      } else {
        this.stockInfo = null;
      }
    }
  },
  beforeUnmount() {
    // 组件销毁前清理
    window.removeEventListener('resize', this.handleResize);
    if (this.chart) {
      this.chart.dispose();
      this.chart = null;
    }
  }
};
</script>

<style scoped>
.page-container {
  height: calc(100vh - 90px);  /* 减去头部和边距 */
  overflow-y: auto;
  padding: 20px;
  background: #fff;
}

.macd-calculator {
  width: 100%;
}

/* 参数表单部分 */
.parameter-form {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

/* 图表容器 */
.chart-container {
  width: 100%;
  height: 400px;
  margin: 20px 0;
}

/* 表格样式 */
.result-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  margin-bottom: 20px;
}

.result-table th, .result-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center;
}

.result-table th {
  background-color: #f2f2f2;
}

/* 其他样式保持不变 */
.form-group {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
}

.form-group label {
  width: 150px;
  margin-right: 10px;
}

.form-group input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 200px;
}

.loading-text {
  margin-left: 10px;
  color: #666;
}

.stock-info {
  background: #fff;
  padding: 15px;
  border-radius: 4px;
  margin: 15px 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stock-info h3 {
  margin: 0 0 10px 0;
  color: #2c3e50;
}

.stock-info p {
  margin: 5px 0;
  color: #666;
}

button {
  background: #1976D2;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.positive {
  color: #00C853;
}

.negative {
  color: #FF5252;
}

.pagination {
  margin: 20px 0;
  text-align: center;
  padding: 10px 0;
}

.pagination button {
  margin: 0 10px;
}

.error-message {
  color: #FF5252;
  margin: 20px 0;
  text-align: center;
}

h2 {
  margin: 0 0 20px 0;
  color: #2c3e50;
}

h3 {
  margin: 20px 0;
  color: #2c3e50;
  font-size: 1.5em;
}
</style>