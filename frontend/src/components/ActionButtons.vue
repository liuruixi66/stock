<template>
  <div class="action-buttons">
    <button class="btn-reset" @click="$emit('reset')">
      {{ resetText }}
    </button>
    <button class="btn-apply" @click="$emit('apply')">
      {{ applyText }}
    </button>
  </div>
</template>

<script>
export default {
  name: 'ActionButtons',
  props: {
    resetText: {
      type: String,
      default: '重置'
    },
    applyText: {
      type: String,
      default: '应用设置'
    }
  },
  emits: ['reset', 'apply']
}
</script>

<style scoped>
.action-buttons {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn-reset {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
}

.btn-reset:hover {
  border-color: #4a90e2;
  color: #4a90e2;
}

.btn-apply {
  padding: 8px 16px;
  border: 1px solid #4a90e2;
  border-radius: 4px;
  background: #4a90e2;
  color: white;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
}

.btn-apply:hover {
  background: #357abd;
  border-color: #357abd;
}
</style> 