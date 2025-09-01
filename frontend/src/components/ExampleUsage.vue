<template>
  <div class="example-usage">
    <h2>组件使用示例</h2>
    
    <!-- 示例1: 单独使用MenuHeader -->
    <div class="example-section">
      <h3>1. MenuHeader 组件</h3>
      <MenuHeader />
    </div>
    
    <!-- 示例2: 单独使用ParameterTable -->
    <div class="example-section">
      <h3>2. ParameterTable 组件</h3>
      <ParameterTable :parameters="exampleParameters" />
    </div>
    
    <!-- 示例3: 单独使用ActionButtons -->
    <div class="example-section">
      <h3>3. ActionButtons 组件</h3>
      <ActionButtons 
        reset-text="重置设置"
        apply-text="保存设置"
        @reset="handleReset"
        @apply="handleApply"
      />
    </div>
    
    <!-- 示例4: 单独使用IndicatorSettings -->
    <div class="example-section">
      <h3>4. IndicatorSettings 组件</h3>
      <IndicatorSettings
        title="示例指标设置"
        description="这是一个示例指标，用于演示组件功能"
        :parameters="exampleParameters"
        :param-inputs="exampleParamInputs"
        :input-values="exampleInputValues"
        :selected-index="selectedIndex"
        :selected-period="selectedPeriod"
        :golden-cross-checked="goldenCrossChecked"
        :death-cross-checked="deathCrossChecked"
        help-title="示例帮助"
        help-text="这是一个示例帮助文本，说明如何使用该指标。"
        @update:selected-index="selectedIndex = $event"
        @update:selected-period="selectedPeriod = $event"
        @update:input-values="exampleInputValues = $event"
        @update:golden-cross-checked="goldenCrossChecked = $event"
        @update:death-cross-checked="deathCrossChecked = $event"
        @reset="handleReset"
        @apply="handleApply"
      />
    </div>
    
    <!-- 示例5: 使用MarketTimingMenu -->
    <div class="example-section">
      <h3>5. MarketTimingMenu 组件</h3>
      <MarketTimingMenu
        :active-menu="activeMenu"
        :active-submenu="activeSubMenu"
        :selected-index="selectedIndex"
        :selected-period="selectedPeriod"
        :ma-settings="maSettings"
        :ma-golden-cross-checked="maGoldenCrossChecked"
        :ma-death-cross-checked="maDeathCrossChecked"
        @toggle-menu="toggleMenu"
        @open-submenu="openSubMenu"
        @update:selected-index="selectedIndex = $event"
        @update:selected-period="selectedPeriod = $event"
        @update:ma-settings="maSettings = $event"
        @update:ma-golden-cross-checked="maGoldenCrossChecked = $event"
        @update:ma-death-cross-checked="maDeathCrossChecked = $event"
        @reset-ma-settings="resetMaSettings"
        @apply-ma-settings="applyMaSettings"
      />
    </div>
  </div>
</template>

<script>
import MenuHeader from './MenuHeader.vue'
import ParameterTable from './ParameterTable.vue'
import ActionButtons from './ActionButtons.vue'
import IndicatorSettings from './IndicatorSettings.vue'
import MarketTimingMenu from './MarketTimingMenu.vue'

export default {
  name: 'ExampleUsage',
  components: {
    MenuHeader,
    ParameterTable,
    ActionButtons,
    IndicatorSettings,
    MarketTimingMenu
  },
  data() {
    return {
      // 示例参数
      exampleParameters: [
        { name: '参数A', description: '这是参数A的描述', defaultValue: '10' },
        { name: '参数B', description: '这是参数B的描述', defaultValue: '20' },
        { name: '参数C', description: '这是参数C的描述', defaultValue: '30' }
      ],
      
      // 示例输入配置
      exampleParamInputs: [
        { key: 'paramA', label: '参数A', placeholder: '10', unit: '个' },
        { key: 'paramB', label: '参数B', placeholder: '20', unit: '个' },
        { key: 'paramC', label: '参数C', placeholder: '30', unit: '个' }
      ],
      
      // 示例输入值
      exampleInputValues: {
        paramA: 10,
        paramB: 20,
        paramC: 30
      },
      
      // 菜单状态
      activeMenu: '',
      activeSubMenu: '',
      selectedIndex: 'sh',
      selectedPeriod: 'daily',
      
      // MA设置
      maSettings: { short: 5, long: 60 },
      maGoldenCrossChecked: false,
      maDeathCrossChecked: false,
      
      // 示例状态
      goldenCrossChecked: false,
      deathCrossChecked: false
    }
  },
  methods: {
    handleReset() {
      console.log('重置设置')
      this.exampleInputValues = {
        paramA: 10,
        paramB: 20,
        paramC: 30
      }
      this.goldenCrossChecked = false
      this.deathCrossChecked = false
    },
    
    handleApply() {
      console.log('应用设置:', {
        inputValues: this.exampleInputValues,
        goldenCross: this.goldenCrossChecked,
        deathCross: this.deathCrossChecked
      })
    },
    
    toggleMenu(menu) {
      if (this.activeMenu === menu) {
        this.activeMenu = ''
        this.activeSubMenu = ''
      } else {
        this.activeMenu = menu
        this.activeSubMenu = ''
      }
    },
    
    openSubMenu(submenu) {
      this.activeSubMenu = submenu
    },
    
    resetMaSettings() {
      this.maSettings = { short: 5, long: 60 }
      this.maGoldenCrossChecked = false
      this.maDeathCrossChecked = false
      console.log('MA设置已重置')
    },
    
    applyMaSettings() {
      console.log('应用MA设置:', {
        settings: this.maSettings,
        goldenCross: this.maGoldenCrossChecked,
        deathCross: this.maDeathCrossChecked
      })
    }
  }
}
</script>

<style scoped>
.example-usage {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.example-usage h2 {
  color: #333;
  margin-bottom: 30px;
  text-align: center;
}

.example-section {
  margin-bottom: 40px;
  padding: 20px;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  background: white;
}

.example-section h3 {
  color: #667eea;
  margin-bottom: 20px;
  font-size: 18px;
}
</style> 