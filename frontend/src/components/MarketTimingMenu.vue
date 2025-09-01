<template>
  <div class="menu-item" :class="{ active: activeMenu === 'market' }" @click="$emit('toggle-menu', 'market')">
    <div class="menu-item-header">
      <i class="fas fa-chart-line"></i>
      <span>大盘择时</span>
      <span class="count">3</span>
      <i class="fas fa-chevron-right arrow" :class="{ expanded: activeMenu === 'market' }"></i>
    </div>
    
    <!-- 二级菜单 -->
    <div class="submenu" v-if="activeMenu === 'market'">
      <!-- MA指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'ma' }"
           @click.stop="$emit('open-submenu', 'ma')">
        <div class="submenu-content">
          <i class="fas fa-chart-line text-primary"></i>
          <span>MA指标设置</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>
      
      <!-- MA指标设置内容 -->
      <div class="ma-settings" v-if="activeSubMenu === 'ma'">
        <IndicatorSettings
          title="MA指标参数设置"
          description="MA：移动平均线，短线：短期均线，长线：长期均线"
          :parameters="maParameters"
          :param-inputs="maParamInputs"
          :input-values="maSettings"
          :selected-index="selectedIndex"
          :selected-period="selectedPeriod"
          :golden-cross-checked="maGoldenCrossChecked"
          :death-cross-checked="maDeathCrossChecked"
          help-title="MA指标说明"
          help-text="MA指标通过计算移动平均线来判断趋势。当短期均线上穿长期均线时产生金叉信号，下穿时产生死叉信号，用于判断买入卖出时机。"
          @update:selected-index="$emit('update:selectedIndex', $event)"
          @update:selected-period="$emit('update:selectedPeriod', $event)"
          @update:input-values="$emit('update:maSettings', $event)"
          @update:golden-cross-checked="$emit('update:maGoldenCrossChecked', $event)"
          @update:death-cross-checked="$emit('update:maDeathCrossChecked', $event)"
          @reset="$emit('resetMaSettings')"
          @apply="$emit('applyMaSettings')"
        />
      </div>

      <!-- MACD指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'macd' }"
           @click.stop="$emit('open-submenu', 'macd')">
        <div class="submenu-content">
          <i class="fas fa-chart-bar text-warning"></i>
          <span>MACD指标</span>
        </div>
        <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'macd' }"></i>
      </div>
      
      <!-- MACD指标设置内容 -->
      <div class="ma-settings" v-if="activeSubMenu === 'macd'">
        <IndicatorSettings
          title="MACD指标参数设置"
          description="DIF：快线EMA，DEA：慢线EMA，MACD：信号线周期"
          :parameters="macdParameters"
          :param-inputs="macdParamInputs"
          :input-values="macdSettings"
          :selected-index="selectedMacdIndex"
          :selected-period="selectedMacdPeriod"
          :golden-cross-checked="macdGoldenCrossChecked"
          :death-cross-checked="macdDeathCrossChecked"
          help-title="MACD指标说明"
          help-text="MACD = DIF - DEA，其中DIF为快线EMA，DEA为慢线EMA的平滑值。当DIF上穿DEA时产生金叉信号，下穿时产生死叉信号。"
          @update:selected-index="$emit('update:selectedMacdIndex', $event)"
          @update:selected-period="$emit('update:selectedMacdPeriod', $event)"
          @update:input-values="$emit('update:macdSettings', $event)"
          @update:golden-cross-checked="$emit('update:macdGoldenCrossChecked', $event)"
          @update:death-cross-checked="$emit('update:macdDeathCrossChecked', $event)"
          @reset="$emit('resetMacdSettings')"
          @apply="$emit('applyMacdSettings')"
        />
      </div>

      <!-- KDJ指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'kdj' }"
           @click.stop="$emit('open-submenu', 'kdj')">
        <div class="submenu-content">
          <i class="fas fa-chart-area text-success"></i>
          <span>KDJ指标</span>
        </div>
        <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'kdj' }"></i>
      </div>
      
      <!-- KDJ指标设置内容 -->
      <div class="ma-settings" v-if="activeSubMenu === 'kdj'">
        <IndicatorSettings
          title="KDJ指标参数设置"
          description="KDJ：随机指标，K：快速线，D：慢速线，J：信号线"
          :parameters="kdjParameters"
          :param-inputs="kdjParamInputs"
          :input-values="kdjSettings"
          :selected-index="selectedKdjIndex"
          :selected-period="selectedKdjPeriod"
          :golden-cross-checked="kdjGoldenCrossChecked"
          :death-cross-checked="kdjDeathCrossChecked"
          help-title="KDJ指标说明"
          help-text="KDJ指标是一种随机指标，通过K、D、J三条线来判断超买超卖。当K线上穿D线时产生金叉信号，下穿时产生死叉信号。"
          @update:selected-index="$emit('update:selectedKdjIndex', $event)"
          @update:selected-period="$emit('update:selectedKdjPeriod', $event)"
          @update:input-values="$emit('update:kdjSettings', $event)"
          @update:golden-cross-checked="$emit('update:kdjGoldenCrossChecked', $event)"
          @update:death-cross-checked="$emit('update:kdjDeathCrossChecked', $event)"
          @reset="$emit('resetKdjSettings')"
          @apply="$emit('applyKdjSettings')"
        />
      </div>
    </div>
  </div>
</template>

<script>
import IndicatorSettings from './IndicatorSettings.vue'

export default {
  name: 'MarketTimingMenu',
  components: {
    IndicatorSettings
  },
  props: {
    activeMenu: {
      type: String,
      default: ''
    },
    activeSubMenu: {
      type: String,
      default: ''
    },
    // MA相关
    selectedIndex: {
      type: String,
      default: 'sh'
    },
    selectedPeriod: {
      type: String,
      default: 'daily'
    },
    maSettings: {
      type: Object,
      default: () => ({ short: 5, long: 60 })
    },
    maGoldenCrossChecked: {
      type: Boolean,
      default: false
    },
    maDeathCrossChecked: {
      type: Boolean,
      default: false
    },
    // MACD相关
    selectedMacdIndex: {
      type: String,
      default: 'sh'
    },
    selectedMacdPeriod: {
      type: String,
      default: 'daily'
    },
    macdSettings: {
      type: Object,
      default: () => ({ dif: 26, dea: 12, macd: 9 })
    },
    macdGoldenCrossChecked: {
      type: Boolean,
      default: false
    },
    macdDeathCrossChecked: {
      type: Boolean,
      default: false
    },
    // KDJ相关
    selectedKdjIndex: {
      type: String,
      default: 'sh'
    },
    selectedKdjPeriod: {
      type: String,
      default: 'daily'
    },
    kdjSettings: {
      type: Object,
      default: () => ({ k: 9, d: 3, j: 3 })
    },
    kdjGoldenCrossChecked: {
      type: Boolean,
      default: false
    },
    kdjDeathCrossChecked: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      maParameters: [
        { name: 'MA短线', description: '短期移动平均线周期', defaultValue: '5' },
        { name: 'MA长线', description: '长期移动平均线周期', defaultValue: '60' }
      ],
      maParamInputs: [
        { key: 'short', label: 'MA短线（日均线）', placeholder: '5', unit: '日' },
        { key: 'long', label: 'MA长线（日均线）', placeholder: '60', unit: '日' }
      ],
      macdParameters: [
        { name: 'DIF', description: '快线指数移动平均线周期', defaultValue: '26' },
        { name: 'DEA', description: '慢线指数移动平均线周期', defaultValue: '12' },
        { name: 'MACD', description: '信号线平滑周期', defaultValue: '9' }
      ],
      macdParamInputs: [
        { key: 'dif', label: 'DIF（快线周期）', placeholder: '26', unit: '日' },
        { key: 'dea', label: 'DEA（慢线周期）', placeholder: '12', unit: '日' },
        { key: 'macd', label: 'MACD（信号线）', placeholder: '9', unit: '日' }
      ],
      kdjParameters: [
        { name: 'K', description: '快速随机指标周期', defaultValue: '9' },
        { name: 'D', description: '慢速随机指标周期', defaultValue: '3' },
        { name: 'J', description: '信号线平滑周期', defaultValue: '3' }
      ],
      kdjParamInputs: [
        { key: 'k', label: 'K（随机指标）', placeholder: '9', unit: '日' },
        { key: 'd', label: 'D（随机指标）', placeholder: '3', unit: '日' },
        { key: 'j', label: 'J（随机指标）', placeholder: '3', unit: '日' }
      ]
    }
  },
  emits: [
    'toggle-menu',
    'open-submenu',
    'update:selectedIndex',
    'update:selectedPeriod',
    'update:maSettings',
    'update:maGoldenCrossChecked',
    'update:maDeathCrossChecked',
    'update:selectedMacdIndex',
    'update:selectedMacdPeriod',
    'update:macdSettings',
    'update:macdGoldenCrossChecked',
    'update:macdDeathCrossChecked',
    'update:selectedKdjIndex',
    'update:selectedKdjPeriod',
    'update:kdjSettings',
    'update:kdjGoldenCrossChecked',
    'update:kdjDeathCrossChecked',
    'resetMaSettings',
    'applyMaSettings',
    'resetMacdSettings',
    'applyMacdSettings',
    'resetKdjSettings',
    'applyKdjSettings'
  ]
}
</script>

<style scoped>
.menu-item {
  border-bottom: 1px solid #e9ecef;
  cursor: pointer;
  transition: all 0.3s ease;
}

.menu-item:hover {
  background-color: #f8f9fa;
}

.menu-item.active {
  background-color: #e3f2fd;
}

.menu-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 20px;
  font-weight: 500;
  color: #333;
}

.menu-item-header i {
  margin-right: 10px;
  color: #667eea;
}

.count {
  background: #667eea;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.arrow {
  transition: transform 0.3s ease;
}

.arrow.expanded {
  transform: rotate(90deg);
}

.submenu {
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.submenu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid #e9ecef;
  cursor: pointer;
  transition: all 0.3s ease;
}

.submenu-item:hover {
  background-color: #e9ecef;
}

.submenu-item.active {
  background-color: #667eea;
  color: white;
}

.submenu-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.submenu-content i {
  font-size: 14px;
}

.ma-settings {
  background: white;
  border-top: 1px solid #e9ecef;
  padding: 0;
}

.text-primary {
  color: #667eea;
}

.text-warning {
  color: #ffc107;
}

.text-success {
  color: #28a745;
}
</style> 