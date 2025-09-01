<template>
  <div class="ma-param-table">
    <table>
      <thead>
        <tr>
          <th>参数</th>
          <th>说明</th>
          <th>默认值</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(param, idx) in params" :key="idx">
          <td class="param-name">{{ param.name }}</td>
          <td>{{ param.description }}</td>
          <td class="param-default">{{ param.default }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
const props = defineProps({
  params: {
    type: Array,
    required: true
  }
});
</script>

<style scoped>
.ma-param-table {
  margin: 16px 0;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  overflow: hidden;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  padding: 12px 16px;
  text-align: left;
}
th {
  background: #f8fafd;
  color: #666;
  font-weight: 500;
}
tr:not(:last-child) td {
  border-bottom: 1px solid #f0f2f5;
}
.param-name {
  color: #13ae6a;
  font-weight: bold;
}
.param-default {
  color: #13ae6a;
  font-weight: bold;
}
</style> 