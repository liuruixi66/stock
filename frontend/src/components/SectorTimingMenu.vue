<template>
  <div class="menu-item" :class="{ active: activeMenu === 'sector' }" @click="$emit('toggle-menu', 'sector')">
    <div class="menu-item-header">
      <i class="fas fa-layer-group"></i>
      <span>板块择时</span>
      <span class="count">3</span>
      <i class="fas fa-chevron-right arrow" :class="{ expanded: activeMenu === 'sector' }"></i>
    </div>
    
    <!-- 二级菜单 -->
    <div class="submenu" v-if="activeMenu === 'sector'">
      <!-- MA指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'sector-ma' }"
           @click.stop="$emit('open-submenu', 'sector-ma')">
        <div class="submenu-content">
          <i class="fas fa-chart-line text-primary"></i>
          <span>MA指标设置</span>
        </div>
        <i class="fas fa-chevron-right"></i>
      </div>
      
      <!-- MA指标设置内容 -->
      <div class="ma-settings" v-if="activeSubMenu === 'sector-ma'">
        <IndicatorSettings
          title="板块MA指标参数设置"
          description="MA：移动平均线，短线：短期均线，长线：长期均线"
          :parameters="maParameters"
          :param-inputs="maParamInputs"
          :input-values="sectorSettings"
          :selected-index="selectedSectorIndex"
          :selected-period="selectedSectorPeriod"
          :golden-cross-checked="sectorMaGoldenCrossChecked"
          :death-cross-checked="sectorMaDeathCrossChecked"
          help-title="板块MA指标说明"
          help-text="板块MA指标通过计算板块指数的移动平均线来判断趋势。当短期均线上穿长期均线时产生金叉信号，下穿时产生死叉信号，用于判断板块买入卖出时机。"
          index-label="板块指数"
          :index-options="sectorIndexOptions"
          @update:selected-index="$emit('update:selectedSectorIndex', $event)"
          @update:selected-period="$emit('update:selectedSectorPeriod', $event)"
          @update:input-values="$emit('update:sectorSettings', $event)"
          @update:golden-cross-checked="$emit('update:sectorMaGoldenCrossChecked', $event)"
          @update:death-cross-checked="$emit('update:sectorMaDeathCrossChecked', $event)"
          @reset="$emit('resetSectorSettings')"
          @apply="$emit('applySectorSettings')"
        />
      </div>

      <!-- MACD指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'sector-macd' }"
           @click.stop="$emit('open-submenu', 'sector-macd')">
        <div class="submenu-content">
          <i class="fas fa-chart-bar text-warning"></i>
          <span>MACD指标</span>
        </div>
        <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'sector-macd' }"></i>
      </div>
      
      <!-- MACD指标设置内容 -->
      <div class="ma-settings" v-if="activeSubMenu === 'sector-macd'">
        <IndicatorSettings
          title="板块MACD指标参数设置"
          description="DIF：快线EMA，DEA：慢线EMA，MACD：信号线周期"
          :parameters="macdParameters"
          :param-inputs="macdParamInputs"
          :input-values="sectorMacdSettings"
          :selected-index="selectedSectorMacdIndex"
          :selected-period="selectedSectorMacdPeriod"
          :golden-cross-checked="sectorMacdGoldenCrossChecked"
          :death-cross-checked="sectorMacdDeathCrossChecked"
          help-title="板块MACD指标说明"
          help-text="板块MACD = DIF - DEA，其中DIF为快线EMA，DEA为慢线EMA的平滑值。当DIF上穿DEA时产生金叉信号，下穿时产生死叉信号，用于判断板块买入卖出时机。"
          index-label="板块指数"
          :index-options="sectorIndexOptions"
          @update:selected-index="$emit('update:selectedSectorMacdIndex', $event)"
          @update:selected-period="$emit('update:selectedSectorMacdPeriod', $event)"
          @update:input-values="$emit('update:sectorMacdSettings', $event)"
          @update:golden-cross-checked="$emit('update:sectorMacdGoldenCrossChecked', $event)"
          @update:death-cross-checked="$emit('update:sectorMacdDeathCrossChecked', $event)"
          @reset="$emit('resetSectorMacdSettings')"
          @apply="$emit('applySectorMacdSettings')"
        />
      </div>

      <!-- KDJ指标设置 -->
      <div class="submenu-item" 
           :class="{ active: activeSubMenu === 'sector-kdj' }"
           @click.stop="$emit('open-submenu', 'sector-kdj')">
        <div class="submenu-content">
          <i class="fas fa-chart-area text-success"></i>
          <span>KDJ指标</span>
        </div>
        <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'sector-kdj' }"></i>
      </div>
      
      <!-- KDJ指标设置内容 -->
      <div class="ma-settings" v-if="activeSubMenu === 'sector-kdj'">
        <IndicatorSettings
          title="板块KDJ指标参数设置"
          description="KDJ：随机指标，K：快速线，D：慢速线，J：信号线"
          :parameters="kdjParameters"
          :param-inputs="kdjParamInputs"
          :input-values="sectorKdjSettings"
          :selected-index="selectedSectorKdjIndex"
          :selected-period="selectedSectorKdjPeriod"
          :golden-cross-checked="sectorKdjGoldenCrossChecked"
          :death-cross-checked="sectorKdjDeathCrossChecked"
          help-title="板块KDJ指标说明"
          help-text="板块KDJ指标是一种随机指标，通过K、D、J三条线来判断板块超买超卖。当K线上穿D线时产生金叉信号，下穿时产生死叉信号，用于判断板块买入卖出时机。"
          index-label="板块指数"
          :index-options="sectorIndexOptions"
          @update:selected-index="$emit('update:selectedSectorKdjIndex', $event)"
          @update:selected-period="$emit('update:selectedSectorKdjPeriod', $event)"
          @update:input-values="$emit('update:sectorKdjSettings', $event)"
          @update:golden-cross-checked="$emit('update:sectorKdjGoldenCrossChecked', $event)"
          @update:death-cross-checked="$emit('update:sectorKdjDeathCrossChecked', $event)"
          @reset="$emit('resetSectorKdjSettings')"
          @apply="$emit('applySectorKdjSettings')"
        />
      </div>
    </div>
  </div>
</template>

<script>
import IndicatorSettings from './IndicatorSettings.vue'

export default {
  name: 'SectorTimingMenu',
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
    // 板块MA相关
    selectedSectorIndex: {
      type: String,
      default: 'transport'
    },
    selectedSectorPeriod: {
      type: String,
      default: 'daily'
    },
    sectorSettings: {
      type: Object,
      default: () => ({ short: 5, long: 60 })
    },
    sectorMaGoldenCrossChecked: {
      type: Boolean,
      default: false
    },
    sectorMaDeathCrossChecked: {
      type: Boolean,
      default: false
    },
    // 板块MACD相关
    selectedSectorMacdIndex: {
      type: String,
      default: 'transport'
    },
    selectedSectorMacdPeriod: {
      type: String,
      default: 'daily'
    },
    sectorMacdSettings: {
      type: Object,
      default: () => ({ dif: 26, dea: 12, macd: 9 })
    },
    sectorMacdGoldenCrossChecked: {
      type: Boolean,
      default: false
    },
    sectorMacdDeathCrossChecked: {
      type: Boolean,
      default: false
    },
    // 板块KDJ相关
    selectedSectorKdjIndex: {
      type: String,
      default: 'transport'
    },
    selectedSectorKdjPeriod: {
      type: String,
      default: 'daily'
    },
    sectorKdjSettings: {
      type: Object,
      default: () => ({ k: 9, d: 3, j: 3 })
    },
    sectorKdjGoldenCrossChecked: {
      type: Boolean,
      default: false
    },
    sectorKdjDeathCrossChecked: {
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
      ],
      sectorIndexOptions: [
        { value: 'transport', label: '交通运输' },
        { value: 'leisure', label: '休闲服务' },
        { value: 'media', label: '传媒' },
        { value: 'utilities', label: '公用事业' },
        { value: 'agriculture', label: '农林牧渔' },
        { value: 'chemicals', label: '化工' },
        { value: 'pharmaceuticals', label: '医药生物' },
        { value: 'commerce', label: '商业贸易' },
        { value: 'defense', label: '国防军工' },
        { value: 'appliances', label: '家用电器' },
        { value: 'building_materials', label: '建筑材料' },
        { value: 'decoration', label: '建筑装饰' },
        { value: 'real_estate', label: '房地产' },
        { value: 'nonferrous_metals', label: '有色金属' },
        { value: 'machinery', label: '机械设备' },
        { value: 'automotive', label: '汽车' },
        { value: 'electronics', label: '电子' },
        { value: 'electrical_equipment', label: '电气设备' },
        { value: 'textiles', label: '纺织服装' },
        { value: 'comprehensive', label: '综合' },
        { value: 'computer', label: '计算机' },
        { value: 'light_industry', label: '轻工制造' },
        { value: 'telecommunications', label: '通信' },
        { value: 'mining', label: '采掘' },
        { value: 'steel', label: '钢铁' },
        { value: 'banking', label: '银行' },
        { value: 'non_banking_finance', label: '非银金融' },
        { value: 'food_beverage', label: '食品饮料' }
      ]
    }
  },
  emits: [
    'toggle-menu',
    'open-submenu',
    'update:selectedSectorIndex',
    'update:selectedSectorPeriod',
    'update:sectorSettings',
    'update:sectorMaGoldenCrossChecked',
    'update:sectorMaDeathCrossChecked',
    'update:selectedSectorMacdIndex',
    'update:selectedSectorMacdPeriod',
    'update:sectorMacdSettings',
    'update:sectorMacdGoldenCrossChecked',
    'update:sectorMacdDeathCrossChecked',
    'update:selectedSectorKdjIndex',
    'update:selectedSectorKdjPeriod',
    'update:sectorKdjSettings',
    'update:sectorKdjGoldenCrossChecked',
    'update:sectorKdjDeathCrossChecked',
    'resetSectorSettings',
    'applySectorSettings',
    'resetSectorMacdSettings',
    'applySectorMacdSettings',
    'resetSectorKdjSettings',
    'applySectorKdjSettings'
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