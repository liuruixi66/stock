<template>
  <div class="indicator-settings">
    <!-- 市场指数选择 -->
    <div class="setting-group" v-if="showIndexSelection">
      <div class="setting-label">{{ indexLabel }}</div>
      <div class="form-select-wrapper">
        <select
          :value="selectedIndex"
          class="form-select"
          @input="$emit('update:selectedIndex', $event.target.value)"
          @click.stop
          @focus.stop
        >
          <option v-for="option in indexOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
    </div>

    <!-- 周期选择 -->
    <div class="setting-group" v-if="showPeriodSelection">
      <div class="setting-label">周期选择</div>
      <div class="button-group">
        <button 
          v-for="period in periods" 
          :key="period.value"
          :class="['period-btn', { active: selectedPeriod === period.value }]"
          @click.stop="$emit('update:selectedPeriod', period.value)"
        >
          {{ period.label }}
        </button>
      </div>
    </div>

    <!-- 指标参数设置 -->
    <div class="setting-group" @click.stop>
      <div class="indicator-header">
        <div class="indicator-title">{{ title }}</div>
        <div class="indicator-description">{{ description }}</div>
      </div>
      
      <!-- 参数说明表格 -->
      <ParameterTable :parameters="parameters" />
      
      <!-- 参数输入 -->
      <div class="param-inputs">
        <div 
          v-for="input in paramInputs" 
          :key="input.key"
          class="ma-input-row" 
          @click.stop
        >
          <label>{{ input.label }}</label>
          <div class="input-with-unit" @click.stop>
            <input 
              type="number" 
              v-model="inputValues[input.key]" 
              class="ma-input" 
              :placeholder="input.placeholder"
              @click.stop
              @focus.stop
              @input="$emit('update:inputValues', inputValues)"
            >
            <span class="unit">{{ input.unit }}</span>
          </div>
        </div>
      </div>

      <!-- 信号选择 -->
      <div class="signal-selection" v-if="showSignalSelection">
        <div class="ma-input-row" @click.stop>
          <label>金叉</label>
          <div class="checkbox-wrapper" @click.stop>
            <input 
              type="checkbox"
              :checked="goldenCrossChecked"
              @change="$emit('update:goldenCrossChecked', $event.target.checked)"
              @click.stop
              @focus.stop
            >
            <span class="checkbox-label">启用金叉信号</span>
          </div>
        </div>
        <div class="ma-input-row" @click.stop>
          <label>死叉</label>
          <div class="checkbox-wrapper" @click.stop>
            <input 
              type="checkbox"
              :checked="deathCrossChecked"
              @change="$emit('update:deathCrossChecked', $event.target.checked)"
              @click.stop
              @focus.stop
            >
            <span class="checkbox-label">启用死叉信号</span>
          </div>
        </div>
      </div>
      
      <!-- 帮助提示 -->
      <div class="help-section">
        <div class="help-icon">
          <i class="fas fa-info-circle"></i>
        </div>
        <div class="help-content">
          <div class="help-title">{{ helpTitle }}</div>
          <div class="help-text">{{ helpText }}</div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <ActionButtons 
      @reset="$emit('reset')"
      @apply="$emit('apply')"
    />
  </div>
</template>

<script>
import ParameterTable from './ParameterTable.vue'
import ActionButtons from './ActionButtons.vue'

export default {
  name: 'IndicatorSettings',
  components: {
    ParameterTable,
    ActionButtons
  },
  props: {
    title: {
      type: String,
      required: true
    },
    description: {
      type: String,
      required: true
    },
    parameters: {
      type: Array,
      required: true
    },
    paramInputs: {
      type: Array,
      required: true
    },
    inputValues: {
      type: Object,
      required: true
    },
    selectedIndex: {
      type: String,
      default: ''
    },
    selectedPeriod: {
      type: String,
      default: ''
    },
    goldenCrossChecked: {
      type: Boolean,
      default: false
    },
    deathCrossChecked: {
      type: Boolean,
      default: false
    },
    helpTitle: {
      type: String,
      required: true
    },
    helpText: {
      type: String,
      required: true
    },
    showIndexSelection: {
      type: Boolean,
      default: true
    },
    showPeriodSelection: {
      type: Boolean,
      default: true
    },
    showSignalSelection: {
      type: Boolean,
      default: true
    },
    indexLabel: {
      type: String,
      default: '市场指数'
    },
    indexOptions: {
      type: Array,
      default: () => [
        { value: 'sh', label: '上证指数' },
        { value: 'sz', label: '深证指数' },
        { value: 'hs300', label: '沪深300指数' }
      ]
    },
    periods: {
      type: Array,
      default: () => [
        { value: 'daily', label: '日线' },
        { value: 'weekly', label: '周线' },
        { value: 'monthly', label: '月线' }
      ]
    }
  },
  emits: [
    'update:selectedIndex',
    'update:selectedPeriod', 
    'update:inputValues',
    'update:goldenCrossChecked',
    'update:deathCrossChecked',
    'reset',
    'apply'
  ]
}
</script>

<style scoped>
.indicator-settings {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.setting-group {
  margin-bottom: 20px;
}

.setting-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #495057;
}

.form-select-wrapper {
  position: relative;
}

.form-select {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
  background: white;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-select:focus {
  border-color: #4a90e2;
  outline: 0;
  box-shadow: 0 0 0 0.2rem rgba(74, 144, 226, 0.25);
}

.button-group {
  display: flex;
  gap: 15px;
}

.period-btn {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
  text-align: center;
}

.period-btn:hover {
  border-color: #4a90e2;
  color: #4a90e2;
}

.period-btn.active {
  background: #4a90e2;
  color: white;
  border-color: #4a90e2;
}

.indicator-header {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
}

.indicator-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
  text-align: center;
}

.indicator-description {
  font-size: 11px;
  opacity: 0.9;
  text-align: center;
  line-height: 1.4;
}

.param-inputs {
  margin-bottom: 20px;
}

.ma-input-row {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.ma-input-row label {
  flex: 0 0 150px;
  font-size: 14px;
  color: #666;
}

.input-with-unit {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 300px;
}

.ma-input {
  flex: 1;
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  max-width: 100px;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.ma-input:focus {
  border-color: #4a90e2;
  outline: 0;
  box-shadow: 0 0 0 0.2rem rgba(74, 144, 226, 0.25);
}

.unit {
  color: #999;
  font-size: 14px;
}

.signal-selection {
  margin-bottom: 20px;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.checkbox-wrapper input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.checkbox-label {
  font-size: 14px;
  color: #666;
}

.help-section {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 12px;
  margin-top: 16px;
}

.help-section .help-icon {
  color: #4a90e2;
  margin-right: 8px;
}

.help-section .help-title {
  font-weight: 600;
  color: #495057;
  margin-bottom: 8px;
}

.help-section .help-text {
  font-size: 13px;
  color: #6c757d;
  line-height: 1.5;
}

/* 参数表格样式 */
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

/* 按钮样式 */
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