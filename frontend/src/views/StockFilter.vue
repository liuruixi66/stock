<template>
  <div class="page-container">
    <!-- 右侧已选条件 -->
    <div class="selected-conditions">
      <div class="conditions-header">
        <h6 class="mb-0">选股条件</h6>
        <button class="btn btn-link p-0 text-decoration-none">排名条件</button>
      </div>
      
      <div v-for="(condition, index) in selectedConditions" 
           :key="index" 
           class="condition-item">
        <span class="indicator">{{ condition.indicator }}</span>
        <select v-if="condition.type === 'price' || condition.type === 'financial'"
                v-model="condition.operator" 
                class="operator-select">
          <option value="大于">大于</option>
          <option value="大于等于">大于等于</option>
          <option value="等于">等于</option>
          <option value="小于等于">小于等于</option>
          <option value="小于">小于</option>
        </select>
        <span v-else class="operator">{{ condition.operator }}</span>
        <input v-if="condition.type === 'price' || condition.type === 'financial'"
               type="number" 
               v-model="condition.value"
               class="value-input"
               :placeholder="'请输入' + condition.indicator + '值'">
        <span v-else class="value">{{ condition.value }}</span>
        <i class="fas fa-times remove" @click="removeCondition(index)"></i>
        <i class="fas fa-check check" 
           :class="{ 'text-muted': !condition.enabled }"
           @click="toggleCondition(index)"></i>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'

interface Condition {
  indicator: string
  operator: string
  value: string | number
  enabled: boolean
  type: 'price' | 'filter' | 'financial' | 'macd'
}

export default defineComponent({
  name: 'StockFilter',
  setup() {
    const selectedConditions = ref<Condition[]>([])

    const removeCondition = (index: number) => {
      selectedConditions.value.splice(index, 1)
    }

    const toggleCondition = (index: number) => {
      selectedConditions.value[index].enabled = !selectedConditions.value[index].enabled
    }

    const resetAll = () => {
      selectedConditions.value = []
    }

    const applyAll = () => {
      console.log('应用所有条件', selectedConditions.value)
    }

    return {
      selectedConditions,
      removeCondition,
      toggleCondition,
      resetAll,
      applyAll
    }
  }
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}

.selected-conditions {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.conditions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.condition-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.operator-select {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  color: #666;
  background-color: white;
}

.value-input {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 120px;
  font-size: 14px;
  color: #333;
}

.remove,
.check {
  cursor: pointer;
  color: #999;
}

.remove:hover {
  color: #666;
}

.check {
  color: #4CAF50;
}

.check.text-muted {
  color: #999;
}
</style> 