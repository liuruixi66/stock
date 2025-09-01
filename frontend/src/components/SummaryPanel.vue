<template>
  <div class="summary-card">
    <div class="summary-title">选股条件</div>
    <div class="date-row">
      <div>
        <label>开始日期</label>
        <input type="date" v-model="dateRange.start" />
      </div>
      <div>
        <label>结束日期</label>
        <input type="date" v-model="dateRange.end" />
      </div>
    </div>
    <div class="condition-list">
      <div v-if="conditions.length === 0" class="empty">
        <i class="icon-info"></i>
        暂无选股条件，请在左侧添加条件
      </div>
      <ul v-else>
        <li v-for="(c, i) in conditions" :key="i">{{ c.title }}</li>
      </ul>
    </div>
    <button class="run-btn" @click="$emit('run')">运行回测</button>
  </div>
</template>
<script>
export default {
  props: {
    conditions: Array,
    dateRange: Object
  }
}
</script>
<style scoped>
.summary-card {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  padding: 28px 32px 24px 32px;
  min-width: 340px;
  max-width: 400px;
}
.summary-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 18px;
}
.date-row {
  display: flex;
  gap: 18px;
  margin-bottom: 18px;
}
.date-row label {
  font-size: 13px;
  color: #888;
  margin-bottom: 4px;
  display: block;
}
.date-row input[type="date"] {
  padding: 6px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  width: 150px;
}
.condition-list {
  margin-bottom: 24px;
}
.empty {
  color: #bbb;
  text-align: center;
  padding: 32px 0;
  font-size: 15px;
}
.icon-info {
  display: block;
  font-size: 32px;
  margin-bottom: 8px;
  color: #e6a23c;
}
ul {
  padding: 0;
  margin: 0;
  list-style: none;
}
li {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 15px;
  color: #333;
}
li:last-child {
  border-bottom: none;
}
.run-btn {
  width: 100%;
  background: #409eff;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 12px 0;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.run-btn:hover {
  background: #66b1ff;
}
</style> 