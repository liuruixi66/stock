<template>
  <div class="param-table-wrapper">
    <table class="param-table">
      <thead>
        <tr>
          <th>参数</th>
          <th>说明</th>
          <th>默认值</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="param in parameters" :key="param.name">
          <td>{{ param.name }}</td>
          <td>{{ param.description }}</td>
          <td>{{ param.defaultValue }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: 'ParameterTable',
  props: {
    parameters: {
      type: Array,
      required: true,
      default: () => []
    }
  }
}
</script>

<style scoped>
.param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
}

.param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.param-table tr:last-child td {
  border-bottom: none;
}

.param-table td:first-child {
  font-weight: 600;
  color: #28a745;
}

.param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.param-table td:last-child {
  font-weight: 600;
  color: #28a745;
}
</style> 