<template>
  <div class="menu-item" :class="{ active: activeMenu === 'timing' }" @click="$emit('toggle-menu', 'timing')">
    <div class="menu-item-header">
      <i class="fas fa-dollar-sign"></i>
      <span>个股择时指标</span>
      <span class="count">13</span>
      <i class="fas fa-chevron-right arrow" :class="{ expanded: activeMenu === 'timing' }"></i>
    </div>
    
    <!-- 二级菜单 -->
    <div class="submenu" v-if="activeMenu === 'timing'">
      <!-- MA指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'timing-ma' }"
           @click.stop="$emit('open-submenu', 'timing-ma')">
        <div class="submenu-content">
          <i class="fas fa-chart-line text-primary"></i>
          <span>MA指标设置</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>
      
      <!-- MA指标设置内容 -->
      <div class="ma-settings" v-if="activeSubMenu === 'timing-ma'">
        <IndicatorSettings
          title="个股MA指标参数设置"
          description="MA：移动平均线，短线：短期均线，长线：长期均线"
          :parameters="maParameters"
          :param-inputs="maParamInputs"
          :input-values="timingMaSettings"
          :selected-index="selectedTimingIndex"
          :selected-period="selectedTimingPeriod"
          :golden-cross-checked="timingMaGoldenCrossChecked"
          :death-cross-checked="timingMaDeathCrossChecked"
          help-title="个股MA指标说明"
          help-text="个股MA指标通过计算移动平均线来判断趋势。当短期均线上穿长期均线时产生金叉信号，下穿时产生死叉信号，用于判断个股买入卖出时机。"
          :show-index-selection="false"
          @update:selected-period="$emit('update:selectedTimingPeriod', $event)"
          @update:input-values="$emit('update:timingMaSettings', $event)"
          @update:golden-cross-checked="$emit('update:timingMaGoldenCrossChecked', $event)"
          @update:death-cross-checked="$emit('update:timingMaDeathCrossChecked', $event)"
          @reset="$emit('resetTimingMaSettings')"
          @apply="$emit('applyTimingMaSettings')"
        />
      </div>

      <!-- MACD指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'timing-macd' }"
           @click.stop="$emit('open-submenu', 'timing-macd')">
        <div class="submenu-content">
          <i class="fas fa-chart-bar text-warning"></i>
          <span>MACD指标</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>
      
      <!-- MACD指标设置内容 -->
      <div class="ma-settings" v-if="activeSubMenu === 'timing-macd'">
        <IndicatorSettings
          title="个股MACD指标参数设置"
          description="DIF：快线EMA，DEA：慢线EMA，MACD：信号线周期"
          :parameters="macdParameters"
          :param-inputs="macdParamInputs"
          :input-values="timingMacdSettings"
          :selected-index="selectedTimingIndex"
          :selected-period="selectedTimingPeriod"
          :golden-cross-checked="timingMacdGoldenCrossChecked"
          :death-cross-checked="timingMacdDeathCrossChecked"
          help-title="个股MACD指标说明"
          help-text="个股MACD = DIF - DEA，其中DIF为快线EMA，DEA为慢线EMA的平滑值。当DIF上穿DEA时产生金叉信号，下穿时产生死叉信号，用于判断个股买入卖出时机。"
          :show-index-selection="false"
          @update:selected-period="$emit('update:selectedTimingPeriod', $event)"
          @update:input-values="$emit('update:timingMacdSettings', $event)"
          @update:golden-cross-checked="$emit('update:timingMacdGoldenCrossChecked', $event)"
          @update:death-cross-checked="$emit('update:timingMacdDeathCrossChecked', $event)"
          @reset="$emit('resetTimingMacdSettings')"
          @apply="$emit('applyTimingMacdSettings')"
        />
      </div>

      <!-- KDJ指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'timing-kdj' }"
           @click.stop="$emit('open-submenu', 'timing-kdj')">
        <div class="submenu-content">
          <i class="fas fa-chart-area text-success"></i>
          <span>KDJ指标</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>
      
      <!-- KDJ指标设置内容 -->
      <div class="ma-settings" v-if="activeSubMenu === 'timing-kdj'">
        <IndicatorSettings
          title="个股KDJ指标参数设置"
          description="KDJ：随机指标，K：快速线，D：慢速线，J：信号线"
          :parameters="kdjParameters"
          :param-inputs="kdjParamInputs"
          :input-values="timingKdjSettings"
          :selected-index="selectedTimingIndex"
          :selected-period="selectedTimingPeriod"
          :golden-cross-checked="timingKdjGoldenCrossChecked"
          :death-cross-checked="timingKdjDeathCrossChecked"
          help-title="个股KDJ指标说明"
          help-text="个股KDJ指标是一种随机指标，通过K、D、J三条线来判断个股超买超卖。当K线上穿D线时产生金叉信号，下穿时产生死叉信号，用于判断个股买入卖出时机。"
          :show-index-selection="false"
          @update:selected-period="$emit('update:selectedTimingPeriod', $event)"
          @update:input-values="$emit('update:timingKdjSettings', $event)"
          @update:golden-cross-checked="$emit('update:timingKdjGoldenCrossChecked', $event)"
          @update:death-cross-checked="$emit('update:timingKdjDeathCrossChecked', $event)"
          @reset="$emit('resetTimingKdjSettings')"
          @apply="$emit('applyTimingKdjSettings')"
        />
      </div>

      <!-- RSI指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'timing-rsi' }"
           @click.stop="$emit('open-submenu', 'timing-rsi')">
        <div class="submenu-content">
          <i class="fas fa-chart-line text-info"></i>
          <span>RSI指标</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>

      <!-- BOLL指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'timing-boll' }"
           @click.stop="$emit('open-submenu', 'timing-boll')">
        <div class="submenu-content">
          <i class="fas fa-chart-line text-secondary"></i>
          <span>BOLL指标</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>

      <!-- CCI指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'timing-cci' }"
           @click.stop="$emit('open-submenu', 'timing-cci')">
        <div class="submenu-content">
          <i class="fas fa-chart-line text-warning"></i>
          <span>CCI指标</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>

      <!-- WR指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'timing-wr' }"
           @click.stop="$emit('open-submenu', 'timing-wr')">
        <div class="submenu-content">
          <i class="fas fa-chart-line text-danger"></i>
          <span>WR指标</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>

      <!-- DMI指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'timing-dmi' }"
           @click.stop="$emit('open-submenu', 'timing-dmi')">
        <div class="submenu-content">
          <i class="fas fa-chart-line text-primary"></i>
          <span>DMI指标</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>

      <!-- OBV指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'timing-obv' }"
           @click.stop="$emit('open-submenu', 'timing-obv')">
        <div class="submenu-content">
          <i class="fas fa-chart-line text-success"></i>
          <span>OBV指标</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>

      <!-- VR指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'timing-vr' }"
           @click.stop="$emit('open-submenu', 'timing-vr')">
        <div class="submenu-content">
          <i class="fas fa-chart-line text-info"></i>
          <span>VR指标</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>

      <!-- CR指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'timing-cr' }"
           @click.stop="$emit('open-submenu', 'timing-cr')">
        <div class="submenu-content">
          <i class="fas fa-chart-line text-warning"></i>
          <span>CR指标</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>

      <!-- AR指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'timing-ar' }"
           @click.stop="$emit('open-submenu', 'timing-ar')">
        <div class="submenu-content">
          <i class="fas fa-chart-line text-danger"></i>
          <span>AR指标</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>

      <!-- BR指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'timing-br' }"
           @click.stop="$emit('open-submenu', 'timing-br')">
        <div class="submenu-content">
          <i class="fas fa-chart-line text-secondary"></i>
          <span>BR指标</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>

      <!-- PSY指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'timing-psy' }"
           @click.stop="$emit('open-submenu', 'timing-psy')">
        <div class="submenu-content">
          <i class="fas fa-chart-line text-primary"></i>
          <span>PSY指标</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>
    </div>
  </div>
</template>

<script>
import IndicatorSettings from './IndicatorSettings.vue'

export default {
  name: 'StockTimingMenu',
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
    // 个股MA相关
    selectedTimingIndex: {
      type: String,
      default: 'sh'
    },
    selectedTimingPeriod: {
      type: String,
      default: 'daily'
    },
    timingMaSettings: {
      type: Object,
      default: () => ({ short: 5, long: 20 })
    },
    timingMaGoldenCrossChecked: {
      type: Boolean,
      default: false
    },
    timingMaDeathCrossChecked: {
      type: Boolean,
      default: false
    },
    // 个股MACD相关
    timingMacdSettings: {
      type: Object,
      default: () => ({ dif: 26, dea: 12, macd: 9 })
    },
    timingMacdGoldenCrossChecked: {
      type: Boolean,
      default: false
    },
    timingMacdDeathCrossChecked: {
      type: Boolean,
      default: false
    },
    // 个股KDJ相关
    timingKdjSettings: {
      type: Object,
      default: () => ({ k: 9, d: 3, j: 3 })
    },
    timingKdjGoldenCrossChecked: {
      type: Boolean,
      default: false
    },
    timingKdjDeathCrossChecked: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      maParameters: [
        { name: 'MA短线', description: '短期移动平均线周期', defaultValue: '5' },
        { name: 'MA长线', description: '长期移动平均线周期', defaultValue: '20' }
      ],
      maParamInputs: [
        { key: 'short', label: 'MA短线（日均线）', placeholder: '5', unit: '日' },
        { key: 'long', label: 'MA长线（日均线）', placeholder: '20', unit: '日' }
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
    'update:selectedTimingIndex',
    'update:selectedTimingPeriod',
    'update:timingMaSettings',
    'update:timingMaGoldenCrossChecked',
    'update:timingMaDeathCrossChecked',
    'update:timingMacdSettings',
    'update:timingMacdGoldenCrossChecked',
    'update:timingMacdDeathCrossChecked',
    'update:timingKdjSettings',
    'update:timingKdjGoldenCrossChecked',
    'update:timingKdjDeathCrossChecked',
    'resetTimingMaSettings',
    'applyTimingMaSettings',
    'resetTimingMacdSettings',
    'applyTimingMacdSettings',
    'resetTimingKdjSettings',
    'applyTimingKdjSettings'
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

.text-info {
  color: #17a2b8;
}

.text-secondary {
  color: #6c757d;
}

.text-danger {
  color: #dc3545;
}
</style> 