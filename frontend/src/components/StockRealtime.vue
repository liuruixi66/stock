<template>
  <div class="table-responsive left-align">
    <h2 class="table-title left-align">股票实时数据</h2>
    <div class="table-wrapper left-align">
      <table>
      <thead>
        <tr>
          <th>日期</th>
          <th>时间</th>
          <th>代码</th>
          <th>名称</th>
          <th>开盘价</th>
          <th>昨收</th>
          <th>最新价</th>
          <th>最高价</th>
          <th>最低价</th>
          <th>买一价</th>
          <th>买二价</th>
          <th>买三价</th>
          <th>买四价</th>
          <th>买五价</th>
          <th>卖一价</th>
          <th>卖二价</th>
          <th>卖三价</th>
          <th>卖四价</th>
          <th>卖五价</th>
          <th>成交量</th>
          <th>成交额</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in quotes" :key="item.code">
          <td>{{ item.date }}</td>
          <td>{{ item.time }}</td>
          <td>{{ item.code }}</td>
          <td>{{ item.name }}</td>
          <td>{{ item.open }}</td>
          <td>{{ item.pre_close }}</td>
          <td>{{ item.price }}</td>
          <td>{{ item.high }}</td>
          <td>{{ item.low }}</td>
          <td>{{ item.b1_p }}</td>
          <td>{{ item.b2_p }}</td>
          <td>{{ item.b3_p }}</td>
          <td>{{ item.b4_p }}</td>
          <td>{{ item.b5_p }}</td>
          <td>{{ item.a1_p }}</td>
          <td>{{ item.a2_p }}</td>
          <td>{{ item.a3_p }}</td>
          <td>{{ item.a4_p }}</td>
          <td>{{ item.a5_p }}</td>
          <td>{{ item.volume }}</td>
          <td>{{ item.amount }}</td>
        </tr>
      </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const quotes = ref([])

function fetchData() {
  axios.get('/api/stock-realtime/').then(res => {
    quotes.value = res.data.data
  })
}

onMounted(() => {
  fetchData()
  setInterval(fetchData, 3000)
})
</script>

<style scoped>
/* 响应式表格容器 */
body, html {
  margin: 0;
  padding: 0;
  height: 100%;
}
/* 靠左显示 */
.left-align {
  align-items: flex-start !important;
  text-align: left !important;
  margin-left: 0 !important;
}
.table-responsive {
  width: 60vw;
  min-height: 40vh;
  background: #f7f8fa;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
  box-sizing: border-box;
  padding: 0;
}
/* 标题紧贴左侧 */
.table-title {
  text-align: left;
  font-size: 3rem;
  font-weight: bold;
  margin: 32px 0 32px 0;
  color: #222;
}

/* 表格横向滚动，保证所有列都能显示 */
.table-wrapper {
  width: 100%;
  min-width: 0;
  max-width: none;
  overflow-x: auto;
  margin-left: 0;
  background: #fff;
  border-radius: 0;
  box-shadow: none;
  padding: 0;
}
table {
  min-width: 1200px;
  width: 100%;
  border-collapse: collapse;
  font-size: 1.2rem;
  margin-left: 0;
}
th, td {
  border: 1px solid #e5e7eb;
  padding: 10px 12px;
  text-align: left;
  white-space: nowrap;
}
th {
  background: #f3f4f6;
  font-size: 1.1rem;
  text-align: left;
}
/* 修复缺少结束标签 */
</style>


