<template>
    <div class="menu-layout">
      <div class="content-wrapper">
        <!-- 左侧菜单 -->
        <div class="menu-container">
          <div class="menu-header">
            <i class="fas fa-list"></i>
            菜单功能
          </div>
          
          <!-- 一级菜单列表 -->
          <div class="menu-list">
            <!-- 大盘择时 -->
            <div class="menu-item" :class="{ active: activeMenu === 'market' }" @click="toggleMenu('market')">
              <div class="menu-item-header">
                <i class="fas fa-chart-line"></i>
                <span>大盘择时</span>
                <span class="count">3</span>
                <i class="fas fa-chevron-right arrow" :class="{ expanded: activeMenu === 'market' }"></i>
              </div>
              <!-- 二级菜单 -->
              <div class="submenu" v-if="activeMenu === 'market'">
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'ma' }"
                     @click.stop="openSubMenu('ma')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-line text-primary"></i>
                    <span>MA指标设置</span>
                  </div>
                  <i class="fas fa-chevron-right"></i>
                </div>
                <!-- MA指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'ma'">
                  <!-- 市场指数选择 -->
                  <div class="setting-group">
                    <div class="setting-label">市场指数</div>
                    <div class="form-select-wrapper">
                      <select v-model="selectedIndex" class="form-select" @click.stop @focus.stop>
                        <option value="sh">上证指数</option>
                        <option value="sz">深证指数</option>
                        <option value="hs300">沪深300指数</option>
                      </select>
                    </div>
                  </div>
  
                  <!-- 周期选择 -->
                  <div class="setting-group">
                    <div class="setting-label">周期选择</div>
                    <div class="button-group">
                      <button 
                        v-for="period in periods" 
                        :key="period.value"
                        :class="['period-btn', { active: selectedPeriod === period.value }]"
                        @click.stop="selectedPeriod = period.value"
                      >
                        {{ period.label }}
                      </button>
                    </div>
                  </div>
  
                  <!-- MA设置 -->
                  <div class="setting-group" @click.stop>
                    <!-- MA参数说明表头 -->
                    <div class="ma-header">
                      <div class="ma-title">MA指标参数设置</div>
                      <div class="ma-description">
                        MA：移动平均线，短线：短期均线，长线：长期均线
                      </div>
                    </div>
                    
                    <!-- MA参数说明表格 -->
                    <div class="ma-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>MA短线</td>
                            <td>短期移动平均线周期</td>
                            <td>5</td>
                          </tr>
                          <tr>
                            <td>MA长线</td>
                            <td>长期移动平均线周期</td>
                            <td>60</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>MA短线（日均线）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="maSettings.short" 
                          class="ma-input" 
                          placeholder="5"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>MA长线（日均线）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="maSettings.long" 
                          class="ma-input" 
                          placeholder="60"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>金叉</label>
                      <div class="checkbox-wrapper" @click.stop>
                        <input type="checkbox" v-model="maGoldenCrossChecked" @click.stop @focus.stop>
                        <span class="checkbox-label">启用金叉信号</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>死叉</label>
                      <div class="checkbox-wrapper" @click.stop>
                        <input type="checkbox" v-model="maDeathCrossChecked" @click.stop @focus.stop>
                        <span class="checkbox-label">启用死叉信号</span>
                      </div>
                    </div>
                    
                    <!-- MA帮助提示 -->
                    <div class="ma-help">
                      <div class="help-icon">
                        <i class="fas fa-info-circle"></i>
                      </div>
                      <div class="help-content">
                        <div class="help-title">MA指标说明</div>
                        <div class="help-text">
                          MA指标通过计算移动平均线来判断趋势。当短期均线上穿长期均线时产生金叉信号，
                          下穿时产生死叉信号，用于判断买入卖出时机。
                        </div>
                      </div>
                    </div>
                  </div>
  
                  <!-- 按钮组 -->
                  <div class="action-buttons">
                    <button class="btn-reset" @click.stop="resetMaSettings">重置</button>
                    <button class="btn-apply" @click.stop="applyMaSettings">应用设置</button>
                  </div>
                </div>
  
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'macd' }"
                     @click.stop="openSubMenu('macd')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-bar text-warning"></i>
                    <span>MACD指标</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'macd' }"></i>
                </div>
                <!-- MACD指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'macd'">
                  <!-- 市场指数选择 -->
                  <div class="setting-group">
                    <div class="setting-label">市场指数</div>
                    <div class="form-select-wrapper">
                      <select v-model="selectedMacdIndex" class="form-select" @click.stop @focus.stop>
                        <option value="sh">上证指数</option>
                        <option value="sz">深证指数</option>
                        <option value="hs300">沪深300指数</option>
                      </select>
                    </div>
                  </div>
  
                  <!-- 周期选择 -->
                  <div class="setting-group">
                    <div class="setting-label">周期选择</div>
                    <div class="button-group">
                      <button 
                        v-for="period in periods" 
                        :key="period.value"
                        :class="['period-btn', { active: selectedMacdPeriod === period.value }]"
                        @click.stop="selectedMacdPeriod = period.value"
                      >
                        {{ period.label }}
                      </button>
                    </div>
                  </div>
  
                  <!-- MACD设置 -->
                  <div class="setting-group" @click.stop>
                    <!-- MACD参数说明表头 -->
                    <div class="macd-header">
                      <div class="macd-title">MACD指标参数设置</div>
                      <div class="macd-description">
                        DIF：快线EMA，DEA：慢线EMA，MACD：信号线周期
                      </div>
                    </div>
                    
                    <!-- MACD参数说明表格 -->
                    <div class="macd-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>DIF</td>
                            <td>快线指数移动平均线周期</td>
                            <td>26</td>
                          </tr>
                          <tr>
                            <td>DEA</td>
                            <td>慢线指数移动平均线周期</td>
                            <td>12</td>
                          </tr>
                          <tr>
                            <td>MACD</td>
                            <td>信号线平滑周期</td>
                            <td>9</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>DIF（快线周期）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="macdSettings.dif" 
                          class="ma-input" 
                          placeholder="26"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>DEA（慢线周期）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="macdSettings.dea" 
                          class="ma-input" 
                          placeholder="12"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>MACD（信号线）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="macdSettings.macd" 
                          class="ma-input" 
                          placeholder="9"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>金叉</label>
                      <div class="checkbox-wrapper" @click.stop>
                        <input type="checkbox" v-model="macdGoldenCrossChecked" @click.stop @focus.stop>
                        <span class="checkbox-label">启用金叉信号</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>死叉</label>
                      <div class="checkbox-wrapper" @click.stop>
                        <input type="checkbox" v-model="macdDeathCrossChecked" @click.stop @focus.stop>
                        <span class="checkbox-label">启用死叉信号</span>
                      </div>
                    </div>
                    
                    <!-- MACD帮助提示 -->
                    <div class="macd-help">
                      <div class="help-icon">
                        <i class="fas fa-info-circle"></i>
                      </div>
                      <div class="help-content">
                        <div class="help-title">MACD指标说明</div>
                        <div class="help-text">
                          MACD = DIF - DEA，其中DIF为快线EMA，DEA为慢线EMA的平滑值。
                          当DIF上穿DEA时产生金叉信号，下穿时产生死叉信号。
                        </div>
                      </div>
                    </div>
                  </div>
  
                  <!-- 按钮组 -->
                  <div class="action-buttons">
                    <button class="btn-reset" @click.stop="resetMacdSettings">重置</button>
                    <button class="btn-apply" @click.stop="applyMacdSettings">应用设置</button>
                  </div>
                </div>
  
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'kdj' }"
                     @click.stop="openSubMenu('kdj')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-area text-success"></i>
                    <span>KDJ指标</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'kdj' }"></i>
                </div>
                <!-- KDJ指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'kdj'">
                  <!-- 市场指数选择 -->
                  <div class="setting-group">
                    <div class="setting-label">市场指数</div>
                    <div class="form-select-wrapper">
                      <select v-model="selectedKdjIndex" class="form-select" @click.stop @focus.stop>
                        <option value="sh">上证指数</option>
                        <option value="sz">深证指数</option>
                        <option value="hs300">沪深300指数</option>
                      </select>
                    </div>
                  </div>
  
                  <!-- 周期选择 -->
                  <div class="setting-group">
                    <div class="setting-label">周期选择</div>
                    <div class="button-group">
                      <button 
                        v-for="period in periods" 
                        :key="period.value"
                        :class="['period-btn', { active: selectedKdjPeriod === period.value }]"
                        @click.stop="selectedKdjPeriod = period.value"
                      >
                        {{ period.label }}
                      </button>
                    </div>
                  </div>
  
                  <!-- KDJ设置 -->
                  <div class="setting-group" @click.stop>
                    <!-- KDJ参数说明表头 -->
                    <div class="kdj-header">
                      <div class="kdj-title">KDJ指标参数设置</div>
                      <div class="kdj-description">
                        KDJ：随机指标，K：快速线，D：慢速线，J：信号线
                      </div>
                    </div>
                    
                    <!-- KDJ参数说明表格 -->
                    <div class="kdj-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>K</td>
                            <td>快速随机指标周期</td>
                            <td>9</td>
                          </tr>
                          <tr>
                            <td>D</td>
                            <td>慢速随机指标周期</td>
                            <td>3</td>
                          </tr>
                          <tr>
                            <td>J</td>
                            <td>信号线平滑周期</td>
                            <td>3</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>K（随机指标）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="kdjSettings.k" 
                          class="ma-input" 
                          placeholder="9"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>D（随机指标）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="kdjSettings.d" 
                          class="ma-input" 
                          placeholder="3"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>J（随机指标）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="kdjSettings.j" 
                          class="ma-input" 
                          placeholder="3"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>金叉</label>
                      <div class="checkbox-wrapper" @click.stop>
                        <input type="checkbox" v-model="kdjGoldenCrossChecked" @click.stop @focus.stop>
                        <span class="checkbox-label">启用金叉信号</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>死叉</label>
                      <div class="checkbox-wrapper" @click.stop>
                        <input type="checkbox" v-model="kdjDeathCrossChecked" @click.stop @focus.stop>
                        <span class="checkbox-label">启用死叉信号</span>
                      </div>
                    </div>
                    
                    <!-- KDJ帮助提示 -->
                    <div class="kdj-help">
                      <div class="help-icon">
                        <i class="fas fa-info-circle"></i>
                      </div>
                      <div class="help-content">
                        <div class="help-title">KDJ指标说明</div>
                        <div class="help-text">
                          KDJ指标是一种随机指标，通过K、D、J三条线来判断超买超卖。
                          当K线上穿D线时产生金叉信号，下穿时产生死叉信号。
                        </div>
                      </div>
                    </div>
                  </div>
  
                  <!-- 按钮组 -->
                  <div class="action-buttons">
                    <button class="btn-reset" @click.stop="resetKdjSettings">重置</button>
                    <button class="btn-apply" @click.stop="applyKdjSettings">应用设置</button>
                  </div>
                </div>
              </div>
            </div>
  
            <!-- 板块择时 -->
            <div class="menu-item" :class="{ active: activeMenu === 'sector' }" @click="toggleMenu('sector')">
              <div class="menu-item-header">
                <i class="fas fa-layer-group"></i>
                <span>板块择时</span>
                <span class="count">3</span>
                <i class="fas fa-chevron-right arrow" :class="{ expanded: activeMenu === 'sector' }"></i>
              </div>
              <!-- 二级菜单 -->
              <div class="submenu" v-if="activeMenu === 'sector'">
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'sector-ma' }"
                     @click.stop="openSubMenu('sector-ma')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-line text-primary"></i>
                    <span>MA指标设置</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'sector-ma' }"></i>
                </div>
                <!-- MA指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'sector-ma'">
                  <!-- 板块指数选择 -->
                  <div class="setting-group">
                    <div class="setting-label">板块指数</div>
                    <!-- 下拉选择 -->
                    <div class="form-select-wrapper">
                      <select v-model="selectedSectorIndex" class="form-select" @click.stop @focus.stop>
                        <option value="transport">交通运输</option>
                        <option value="leisure">休闲服务</option>
                        <option value="media">传媒</option>
                        <option value="utilities">公用事业</option>
                        <option value="agriculture">农林牧渔</option>
                        <option value="chemicals">化工</option>
                        <option value="pharmaceuticals">医药生物</option>
                        <option value="commerce">商业贸易</option>
                        <option value="defense">国防军工</option>
                        <option value="appliances">家用电器</option>
                        <option value="building_materials">建筑材料</option>
                        <option value="decoration">建筑装饰</option>
                        <option value="real_estate">房地产</option>
                        <option value="nonferrous_metals">有色金属</option>
                        <option value="machinery">机械设备</option>
                        <option value="automotive">汽车</option>
                        <option value="electronics">电子</option>
                        <option value="electrical_equipment">电气设备</option>
                        <option value="textiles">纺织服装</option>
                        <option value="comprehensive">综合</option>
                        <option value="computer">计算机</option>
                        <option value="light_industry">轻工制造</option>
                        <option value="telecommunications">通信</option>
                        <option value="mining">采掘</option>
                        <option value="steel">钢铁</option>
                        <option value="banking">银行</option>
                        <option value="non_banking_finance">非银金融</option>
                        <option value="food_beverage">食品饮料</option>
                      </select>
                    </div>
  
                                        <div class="sector-dropdown-wrapper" style="margin-bottom: 8px;">
                      <div class="sector-dropdown-list" v-show="showSectorDropdown">
                        <div
                          class="sector-dropdown-item"
                          v-for="option in sectorIndices"
                          :key="option.value"
                          :class="{ active: selectedSectorIndex === option.value }"
                          @click="selectSectorDropdownOption(option)"
                        >
                          {{ option.label }}
                        </div>
                      </div>
                    </div>
  
                    <!-- 搜索标题 -->
                    <div class="search-title" style="margin-bottom: 8px; font-weight: 500; color: #333;">
                      请输入板块名称
                    </div>
  
                    <div class="search-select">
                      <div class="select-input" @click="toggleDropdown('sector')">
                        <input 
                          type="text" 
                          v-model="sectorSearchText" 
                          placeholder="请输入搜索关键词"
                          @input="filterSectorOptions"
                          @click.stop
                        >
                        <i class="fas fa-chevron-down" :class="{ 'expanded': showDropdown === 'sector' }"></i>
                      </div>
                      <div class="select-dropdown" v-show="showDropdown === 'sector'">
                        <div class="dropdown-item" 
                             v-for="option in filteredSectorOptions" 
                             :key="option.value"
                             :class="{ 
                               active: (activeSubMenu === 'sector-ma' && selectedSectorIndex === option.value) ||
                                       (activeSubMenu === 'sector-macd' && selectedSectorMacdIndex === option.value) ||
                                       (activeSubMenu === 'sector-kdj' && selectedSectorKdjIndex === option.value)
                             }"
                             @click="selectSectorOption(option)">
                          {{ option.label }}
                        </div>
                      </div>
                    </div>
                  </div>
  
                  <!-- 周期选择 -->
                  <div class="setting-group">
                    <div class="setting-label">周期选择</div>
                    <div class="button-group">
                      <button 
                        v-for="period in periods" 
                        :key="period.value"
                        :class="['period-btn', { active: selectedSectorPeriod === period.value }]"
                        @click.stop="selectedSectorPeriod = period.value"
                      >
                        {{ period.label }}
                      </button>
                    </div>
                  </div>
  
                  <!-- MA设置 -->
                  <div class="setting-group" @click.stop>
                    <!-- MA参数说明表头 -->
                    <div class="ma-header">
                      <div class="ma-title">板块MA指标参数设置</div>
                      <div class="ma-description">
                        MA：移动平均线，短线：短期均线，长线：长期均线
                      </div>
                    </div>
                    
                    <!-- MA参数说明表格 -->
                    <div class="ma-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>MA短线</td>
                            <td>短期移动平均线周期</td>
                            <td>5</td>
                          </tr>
                          <tr>
                            <td>MA长线</td>
                            <td>长期移动平均线周期</td>
                            <td>60</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>MA短线（日均线）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="sectorSettings.short" 
                          class="ma-input" 
                          placeholder="5"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>MA长线（日均线）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="sectorSettings.long" 
                          class="ma-input" 
                          placeholder="60"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>金叉</label>
                      <div class="checkbox-wrapper" @click.stop>
                        <input type="checkbox" v-model="sectorMaGoldenCrossChecked" @click.stop @focus.stop>
                        <span class="checkbox-label">启用金叉信号</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>死叉</label>
                      <div class="checkbox-wrapper" @click.stop>
                        <input type="checkbox" v-model="sectorMaDeathCrossChecked" @click.stop @focus.stop>
                        <span class="checkbox-label">启用死叉信号</span>
                      </div>
                    </div>
                    
                    <!-- MA帮助提示 -->
                    <div class="ma-help">
                      <div class="help-icon">
                        <i class="fas fa-info-circle"></i>
                      </div>
                      <div class="help-content">
                        <div class="help-title">板块MA指标说明</div>
                        <div class="help-text">
                          板块MA指标通过计算板块指数的移动平均线来判断趋势。当短期均线上穿长期均线时产生金叉信号，
                          下穿时产生死叉信号，用于判断板块买入卖出时机。
                        </div>
                      </div>
                    </div>
                  </div>
  
                  <!-- 按钮组 -->
                  <div class="action-buttons">
                    <button class="btn-reset" @click.stop="resetSectorSettings">重置</button>
                    <button class="btn-apply" @click.stop="applySectorSettings">应用设置</button>
                  </div>
                </div>
  
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'sector-macd' }"
                     @click.stop="openSubMenu('sector-macd')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-bar text-warning"></i>
                    <span>MACD指标</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'sector-macd' }"></i>
                </div>
                <!-- MACD指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'sector-macd'">
                  <!-- 板块指数选择 -->
                  <div class="setting-group">
                    <div class="setting-label">板块指数</div>
                    <div class="form-select-wrapper">
                      <select v-model="selectedSectorMacdIndex" class="form-select" @click.stop @focus.stop>
                          <option value="transport">交通运输</option>
                          <option value="leisure">休闲服务</option>
                          <option value="media">传媒</option>
                          <option value="utilities">公用事业</option>
                          <option value="agriculture">农林牧渔</option>
                          <option value="chemicals">化工</option>
                          <option value="pharmaceuticals">医药生物</option>
                          <option value="commerce">商业贸易</option>
                          <option value="defense">国防军工</option>
                          <option value="appliances">家用电器</option>
                          <option value="building_materials">建筑材料</option>
                          <option value="decoration">建筑装饰</option>
                          <option value="real_estate">房地产</option>
                          <option value="nonferrous_metals">有色金属</option>
                          <option value="machinery">机械设备</option>
                          <option value="automotive">汽车</option>
                          <option value="electronics">电子</option>
                          <option value="electrical_equipment">电气设备</option>
                          <option value="textiles">纺织服装</option>
                          <option value="comprehensive">综合</option>
                          <option value="computer">计算机</option>
                          <option value="light_industry">轻工制造</option>
                          <option value="telecommunications">通信</option>
                          <option value="mining">采掘</option>
                          <option value="steel">钢铁</option>
                          <option value="banking">银行</option>
                          <option value="non_banking_finance">非银金融</option>
                          <option value="food_beverage">食品饮料</option>
                                                </select>
                      </div> 
  
                    <!-- 搜索标题 -->
                    <div class="search-title" style="margin-bottom: 8px; font-weight: 500; color: #333;">
                      请输入板块名称
                    </div>
  
                    <div class="search-select">
                      <div class="select-input" @click="toggleDropdown('sector')">
                        <input 
                          type="text" 
                          v-model="sectorSearchText" 
                          placeholder="请输入搜索关键词"
                          @input="filterSectorOptions"
                          @click.stop
                        >
                        <i class="fas fa-chevron-down" :class="{ 'expanded': showDropdown === 'sector' }"></i>
                      </div>
                      <div class="select-dropdown" v-show="showDropdown === 'sector'">
                        <div class="dropdown-item" 
                             v-for="option in filteredSectorOptions" 
                             :key="option.value"
                             :class="{ 
                               active: (activeSubMenu === 'sector-ma' && selectedSectorIndex === option.value) ||
                                       (activeSubMenu === 'sector-macd' && selectedSectorMacdIndex === option.value) ||
                                       (activeSubMenu === 'sector-kdj' && selectedSectorKdjIndex === option.value)
                             }"
                             @click="selectSectorOption(option)">
                          {{ option.label }}
                        </div>
                      </div>
                    </div>
                  </div>
  
                  <!-- 周期选择 -->
                  <div class="setting-group">
                    <div class="setting-label">周期选择</div>
                    <div class="button-group">
                      <button 
                        v-for="period in periods" 
                        :key="period.value"
                        :class="['period-btn', { active: selectedSectorMacdPeriod === period.value }]"
                        @click.stop="selectedSectorMacdPeriod = period.value"
                      >
                        {{ period.label }}
                      </button>
                    </div>
                  </div>
  
                  <!-- MACD设置 -->
                  <div class="setting-group" @click.stop>
                    <!-- MACD参数说明表头 -->
                    <div class="macd-header">
                      <div class="macd-title">板块MACD指标参数设置</div>
                      <div class="macd-description">
                        DIF：快线EMA，DEA：慢线EMA，MACD：信号线周期
                      </div>
                    </div>
                    
                    <!-- MACD参数说明表格 -->
                    <div class="macd-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>DIF</td>
                            <td>快线指数移动平均线周期</td>
                            <td>26</td>
                          </tr>
                          <tr>
                            <td>DEA</td>
                            <td>慢线指数移动平均线周期</td>
                            <td>12</td>
                          </tr>
                          <tr>
                            <td>MACD</td>
                            <td>信号线平滑周期</td>
                            <td>9</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>DIF（快线周期）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="sectorMacdSettings.dif" 
                          class="ma-input" 
                          placeholder="26"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>DEA（慢线周期）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="sectorMacdSettings.dea" 
                          class="ma-input" 
                          placeholder="12"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>MACD（信号线）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="sectorMacdSettings.macd" 
                          class="ma-input" 
                          placeholder="9"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>金叉</label>
                      <div class="checkbox-wrapper" @click.stop>
                        <input type="checkbox" v-model="sectorMacdGoldenCrossChecked" @click.stop @focus.stop>
                        <span class="checkbox-label">启用金叉信号</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>死叉</label>
                      <div class="checkbox-wrapper" @click.stop>
                        <input type="checkbox" v-model="sectorMacdDeathCrossChecked" @click.stop @focus.stop>
                        <span class="checkbox-label">启用死叉信号</span>
                      </div>
                    </div>
                    
                    <!-- MACD帮助提示 -->
                    <div class="macd-help">
                      <div class="help-icon">
                        <i class="fas fa-info-circle"></i>
                      </div>
                      <div class="help-content">
                        <div class="help-title">板块MACD指标说明</div>
                        <div class="help-text">
                          板块MACD = DIF - DEA，其中DIF为快线EMA，DEA为慢线EMA的平滑值。
                          当DIF上穿DEA时产生金叉信号，下穿时产生死叉信号，用于判断板块买入卖出时机。
                        </div>
                      </div>
                    </div>
                  </div>
  
                  <!-- 按钮组 -->
                  <div class="action-buttons">
                    <button class="btn-reset" @click.stop="resetSectorMacdSettings">重置</button>
                    <button class="btn-apply" @click.stop="applySectorMacdSettings">应用设置</button>
                  </div>
                </div>
  
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'sector-kdj' }"
                     @click.stop="openSubMenu('sector-kdj')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-area text-success"></i>
                    <span>KDJ指标</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'sector-kdj' }"></i>
                </div>
                <!-- KDJ指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'sector-kdj'">
                  <!-- 板块指数选择 -->
                  <div class="setting-group">
                    <div class="setting-label">板块指数</div>
                    <div class="form-select-wrapper">
                        <select v-model="selectedSectorKdjIndex" class="form-select" @click.stop @focus.stop>
                          <option value="transport">交通运输</option>
                          <option value="leisure">休闲服务</option>
                          <option value="media">传媒</option>
                          <option value="utilities">公用事业</option>
                          <option value="agriculture">农林牧渔</option>
                          <option value="chemicals">化工</option>
                          <option value="pharmaceuticals">医药生物</option>
                          <option value="commerce">商业贸易</option>
                          <option value="defense">国防军工</option>
                          <option value="appliances">家用电器</option>
                          <option value="building_materials">建筑材料</option>
                          <option value="decoration">建筑装饰</option>
                          <option value="real_estate">房地产</option>
                          <option value="nonferrous_metals">有色金属</option>
                          <option value="machinery">机械设备</option>
                          <option value="automotive">汽车</option>
                          <option value="electronics">电子</option>
                          <option value="electrical_equipment">电气设备</option>
                          <option value="textiles">纺织服装</option>
                          <option value="comprehensive">综合</option>
                          <option value="computer">计算机</option>
                          <option value="light_industry">轻工制造</option>
                          <option value="telecommunications">通信</option>
                          <option value="mining">采掘</option>
                          <option value="steel">钢铁</option>
                          <option value="banking">银行</option>
                          <option value="non_banking_finance">非银金融</option>
                          <option value="food_beverage">食品饮料</option>
                        </select>
                      </div>
  
                    <!-- 搜索标题 -->
                    <div class="search-title" style="margin-bottom: 8px; font-weight: 500; color: #333;">
                      请输入板块名称
                    </div>
  
                    <div class="search-select">
                      <div class="select-input" @click="toggleDropdown('sector')">
                        <input 
                          type="text" 
                          v-model="sectorSearchText" 
                          placeholder="请输入搜索关键词"
                          @input="filterSectorOptions"
                          @click.stop
                        >
                        <i class="fas fa-chevron-down" :class="{ 'expanded': showDropdown === 'sector' }"></i>
                      </div>
                      <div class="select-dropdown" v-show="showDropdown === 'sector'">
                        <div class="dropdown-item" 
                             v-for="option in filteredSectorOptions" 
                             :key="option.value"
                             :class="{ 
                               active: (activeSubMenu === 'sector-ma' && selectedSectorIndex === option.value) ||
                                       (activeSubMenu === 'sector-macd' && selectedSectorMacdIndex === option.value) ||
                                       (activeSubMenu === 'sector-kdj' && selectedSectorKdjIndex === option.value)
                             }"
                             @click="selectSectorOption(option)">
                          {{ option.label }}
                        </div>
                      </div>
                    </div>
                  </div>
                  <!-- 周期选择 -->
                  <div class="setting-group">
                    <div class="setting-label">周期选择</div>
                    <div class="button-group">
                      <button 
                        v-for="period in periods" 
                        :key="period.value"
                        :class="['period-btn', { active: selectedSectorKdjPeriod === period.value }]"
                        @click.stop="selectedSectorKdjPeriod = period.value"
                      >
                        {{ period.label }}
                      </button>
                    </div>
                  </div>
  
                  <!-- KDJ设置 -->
                  <div class="setting-group" @click.stop>
                    <!-- KDJ参数说明表头 -->
                    <div class="kdj-header">
                      <div class="kdj-title">板块KDJ指标参数设置</div>
                      <div class="kdj-description">
                        KDJ：随机指标，K：快速线，D：慢速线，J：信号线
                      </div>
                    </div>
                    
                    <!-- KDJ参数说明表格 -->
                    <div class="kdj-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>K</td>
                            <td>快速随机指标周期</td>
                            <td>9</td>
                          </tr>
                          <tr>
                            <td>D</td>
                            <td>慢速随机指标周期</td>
                            <td>3</td>
                          </tr>
                          <tr>
                            <td>J</td>
                            <td>信号线平滑周期</td>
                            <td>3</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>K（随机指标）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="sectorKdjSettings.k" 
                          class="ma-input" 
                          placeholder="5"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>D（随机指标）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="sectorKdjSettings.d" 
                          class="ma-input" 
                          placeholder="3"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>J（随机指标）</label>
                      <div class="input-with-unit" @click.stop>
                        <input 
                          type="number" 
                          v-model="sectorKdjSettings.j" 
                          class="ma-input" 
                          placeholder="3"
                          @click.stop
                          @focus.stop
                        >
                        <span class="unit">日</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>金叉</label>
                      <div class="checkbox-wrapper" @click.stop>
                        <input type="checkbox" v-model="sectorKdjGoldenCrossChecked" @click.stop @focus.stop>
                        <span class="checkbox-label">启用金叉信号</span>
                      </div>
                    </div>
                    <div class="ma-input-row" @click.stop>
                      <label>死叉</label>
                      <div class="checkbox-wrapper" @click.stop>
                        <input type="checkbox" v-model="sectorKdjDeathCrossChecked" @click.stop @focus.stop>
                        <span class="checkbox-label">启用死叉信号</span>
                      </div>
                    </div>
                    
                    <!-- KDJ帮助提示 -->
                    <div class="kdj-help">
                      <div class="help-icon">
                        <i class="fas fa-info-circle"></i>
                      </div>
                      <div class="help-content">
                        <div class="help-title">板块KDJ指标说明</div>
                        <div class="help-text">
                          板块KDJ指标是一种随机指标，通过K、D、J三条线来判断板块超买超卖。
                          当K线上穿D线时产生金叉信号，下穿时产生死叉信号，用于判断板块买入卖出时机。
                        </div>
                      </div>
                    </div>
                  </div>
  
                  <!-- 按钮组 -->
                  <div class="action-buttons">
                    <button class="btn-reset" @click.stop="resetSectorKdjSettings">重置</button>
                    <button class="btn-apply" @click.stop="applySectorKdjSettings">应用设置</button>
                  </div>
                </div>
              </div>
            </div>
  
              <!-- 个股择时指标 -->
            <div class="menu-item" :class="{ active: activeMenu === 'timing' }" @click="toggleMenu('timing')">
              <div class="menu-item-header">
                <i class="fas fa-dollar-sign"></i>
                <span>个股择时指标</span>
                <span class="count">13</span>
                <i class="fas fa-chevron-right arrow" :class="{ expanded: activeMenu === 'timing' }"></i>
              </div>
              <!-- 二级菜单 -->
              <div class="submenu" v-if="activeMenu === 'timing'">
                <div class="submenu-item" 
                    :class="{ active: activeSubMenu === 'timing-ma' }"
                    @click.stop="openSubMenu('timing-ma')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-line text-primary"></i>
                    <span>MA指标设置</span>
                  </div>
                  <i class="fas fa-chevron-right"></i>
                </div>
                
                <!-- MA指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'timing-ma'">
                  <!-- MA参数说明表头 -->
                  <div class="ma-header">
                    <div class="ma-title">个股MA指标参数设置</div>
                    <div class="ma-description">
                      MA：移动平均线，短线：短期均线，长线：长期均线
                    </div>
                  </div>
                  
                  <!-- MA参数说明表格 -->
                  <div class="ma-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>默认值</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>MA短线</td>
                          <td>短期移动平均线周期</td>
                          <td>5</td>
                        </tr>
                        <tr>
                          <td>MA长线</td>
                          <td>长期移动平均线周期</td>
                          <td>20</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  
                  <!-- MA信号选择 -->
                  <div class="setting-group">
                    <div class="indicator-section">
                      <div class="section-title">基础指标</div>
                      <div class="button-group">
                                              <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'ma' }]"
                        @click.stop="selectTimingSignal('ma')"
                      >
                        MA
                      </button>
                      </div>
                    </div>
                  </div>
                  
                  <!-- MA参数设置表格 -->
                  <div v-if="timingSelectedSignal === 'ma'" class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">MA短线</div>
                        <div class="table-cell">MA长线</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <input type="number" v-model="maShortPeriod" class="form-control" placeholder="5" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="maLongPeriod" class="form-control" placeholder="20" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell">
                          <select v-model="maCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="maCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- 交叉信号 -->
                  <div class="indicator-section">
                    <div class="section-title">交叉信号</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'ma_golden_cross' }]"
                        @click.stop="selectTimingSignal('ma_golden_cross')"
                      >
                        MA金叉
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'ma_death_cross' }]"
                        @click.stop="selectTimingSignal('ma_death_cross')"
                      >
                        MA死叉
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'ma_golden_cross' || timingSelectedSignal === 'ma_death_cross'" class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">MA短线</div>
                        <div class="table-cell">MA长线</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <input type="number" v-model="maShortPeriod" class="form-control" placeholder="5" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="maLongPeriod" class="form-control" placeholder="20" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell">
                          <select v-model="maCrossCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="maCrossCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- 趋势信号 -->
                  <div class="indicator-section">
                    <div class="section-title">趋势信号</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'ma_bull' }]"
                        @click.stop="selectTimingSignal('ma_bull')"
                      >
                        MA多头
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'ma_bear' }]"
                        @click.stop="selectTimingSignal('ma_bear')"
                      >
                        MA空头
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'ma_bull' || timingSelectedSignal === 'ma_bear'" class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">MA短线</div>
                        <div class="table-cell">MA长线</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <input type="number" v-model="maShortPeriod" class="form-control" placeholder="5" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="maLongPeriod" class="form-control" placeholder="20" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell">
                          <select v-model="maTrendCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="maTrendCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- 背离信号 -->
                  <div class="indicator-section">
                    <div class="section-title">背离信号</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'ma_bottom_divergence' }]"
                        @click.stop="selectTimingSignal('ma_bottom_divergence')"
                      >
                        MA底背离
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'ma_top_divergence' }]"
                        @click.stop="selectTimingSignal('ma_top_divergence')"
                      >
                        MA顶背离
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'ma_bottom_divergence' || timingSelectedSignal === 'ma_top_divergence'" class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">MA短线</div>
                        <div class="table-cell">MA长线</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <input type="number" v-model="maShortPeriod" class="form-control" placeholder="5" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="maLongPeriod" class="form-control" placeholder="20" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell">
                          <select v-model="maDivergenceCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="maDivergenceCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- MA帮助提示 -->
                  <div class="ma-help">
                    <div class="help-icon">
                      <i class="fas fa-info-circle"></i>
                    </div>
                    <div class="help-content">
                      <div class="help-title">个股MA指标说明</div>
                      <div class="help-text">
                        个股MA指标通过计算移动平均线来判断趋势。当短期均线上穿长期均线时产生金叉信号，
                        下穿时产生死叉信号，用于判断个股买入卖出时机。
                      </div>
                    </div>
                  </div>
                </div>
  
                  <div class="submenu-item"
                      :class="{ active: activeSubMenu === 'timing-macd' }"
                      @click.stop="openSubMenu('timing-macd')">
                    <div class="submenu-content">
                      <i class="fas fa-chart-bar text-warning"></i>
                      <span>MACD指标</span>
                    </div>
                    <i class="fas fa-chevron-right"></i>
                  </div>
                
                  <!-- MACD指标设置内容 -->
                  <div class="ma-settings" v-if="activeSubMenu === 'timing-macd'">
                    <!-- MACD参数说明表头 -->
                    <div class="macd-header">
                      <div class="macd-title">个股MACD指标参数设置</div>
                      <div class="macd-description">
                        DIF：快线EMA，DEA：慢线EMA，MACD：信号线周期
                      </div>
                    </div>
                    
                    <!-- MACD参数说明表格 -->
                    <div class="macd-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>DIF</td>
                            <td>快线指数移动平均线周期</td>
                            <td>26</td>
                          </tr>
                          <tr>
                            <td>DEA</td>
                            <td>慢线指数移动平均线周期</td>
                            <td>12</td>
                          </tr>
                          <tr>
                            <td>MACD</td>
                            <td>信号线平滑周期</td>
                            <td>9</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    
                    <!-- MACD信号选择 -->
                    <div class="setting-group">
                      <!-- 基础指标 -->
                      <div class="indicator-section">
                        <div class="section-title">基础指标</div>
                                              <div class="button-group">
                        <button 
                          :class="['signal-btn', { active: timingSelectedSignal === 'dif' }]"
                          @click.stop="selectTimingSignal('dif')"
                        >
                          DIF
                        </button>
                        <button 
                          :class="['signal-btn', { active: timingSelectedSignal === 'dea' }]"
                          @click.stop="selectTimingSignal('dea')"
                        >
                          DEA
                        </button>
                        <button 
                          :class="['signal-btn', { active: timingSelectedSignal === 'macd' }]"
                          @click.stop="selectTimingSignal('macd')"
                        >
                          MACD
                        </button>
                      </div>

                      </div>
                    </div>
                  
                    <!-- DIF参数设置表格 -->
                    <div v-if="timingSelectedSignal === 'dif'" class="param-content" @click.stop>
                      <!-- MACD参数输入框 -->
                      <div class="macd-param-inputs">
                        <div class="ma-input-row" @click.stop>
                          <label>DIF（快线周期）</label>
                          <div class="input-with-unit" @click.stop>
                            <input 
                              type="number" 
                              v-model="timingMacdSettings.dif" 
                              class="ma-input" 
                              placeholder="26"
                              @click.stop
                              @focus.stop
                            >
                            <span class="unit">日</span>
                          </div>
                        </div>
                        <div class="ma-input-row" @click.stop>
                          <label>DEA（慢线周期）</label>
                          <div class="input-with-unit" @click.stop>
                            <input 
                              type="number" 
                              v-model="timingMacdSettings.dea" 
                              class="ma-input" 
                              placeholder="12"
                              @click.stop
                              @focus.stop
                            >
                            <span class="unit">日</span>
                          </div>
                        </div>
                        <div class="ma-input-row" @click.stop>
                          <label>MACD（信号线）</label>
                          <div class="input-with-unit" @click.stop>
                            <input 
                              type="number" 
                              v-model="timingMacdSettings.macd" 
                              class="ma-input" 
                              placeholder="9"
                              @click.stop
                              @focus.stop
                            >
                            <span class="unit">日</span>
                          </div>
                        </div>
                      </div>
                      
                      <!-- DIF比较设置 -->
                      <div class="param-table" @click.stop>
                        <div class="table-row table-header">
                          <div class="table-cell">DIF值</div>
                          <div class="table-cell">比较符</div>
                          <div class="table-cell">数值</div>
                        </div>
                        <div class="table-row" @click.stop>
                          <div class="table-cell" @click.stop>
                            <input type="number" v-model="difCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                          </div>
                          <div class="table-cell" @click.stop>
                            <select v-model="difCompare" class="form-select" @click.stop @focus.stop>
                              <option value="大于">大于</option>
                              <option value="小于">小于</option>
                              <option value="大于等于">大于等于</option>
                              <option value="小于等于">小于等于</option>
                              <option value="等于">等于</option>
                            </select>
                          </div>
                          <div class="table-cell" @click.stop>
                            <input type="number" v-model="difTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                          </div>
                        </div>
                      </div>
                      <div class="action-buttons">
                        <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                        <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                      </div>
                    </div>
                  
                  <!-- DEA参数设置表格 -->
                  <div v-if="timingSelectedSignal === 'dea'" class="param-content" @click.stop>
                    <!-- MACD参数输入框 -->
                    <div class="macd-param-inputs">
                      <div class="ma-input-row" @click.stop>
                        <label>DIF（快线周期）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingMacdSettings.dif" 
                            class="ma-input" 
                            placeholder="26"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                      <div class="ma-input-row" @click.stop>
                        <label>DEA（慢线周期）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingMacdSettings.dea" 
                            class="ma-input" 
                            placeholder="12"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                      <div class="ma-input-row" @click.stop>
                        <label>MACD（信号线）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingMacdSettings.macd" 
                            class="ma-input" 
                            placeholder="9"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- DEA比较设置 -->
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">DEA值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="deaCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="deaCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="deaTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- MACD参数设置表格 -->
                  <div v-if="timingSelectedSignal === 'macd'" class="param-content" @click.stop>
                    <!-- MACD参数输入框 -->
                    <div class="macd-param-inputs">
                      <div class="ma-input-row" @click.stop>
                        <label>DIF（快线周期）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingMacdSettings.dif" 
                            class="ma-input" 
                            placeholder="26"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                      <div class="ma-input-row" @click.stop>
                        <label>DEA（慢线周期）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingMacdSettings.dea" 
                            class="ma-input" 
                            placeholder="12"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                      <div class="ma-input-row" @click.stop>
                        <label>MACD（信号线）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingMacdSettings.macd" 
                            class="ma-input" 
                            placeholder="9"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- MACD比较设置 -->
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">MACD值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="macdCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="macdCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="macdTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- 交叉信号 -->
                  <div class="indicator-section">
                    <div class="section-title">交叉信号</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'golden_cross' }]"
                        @click.stop="selectTimingSignal('golden_cross')"
                      >
                        MACD金叉
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'death_cross' }]"
                        @click.stop="selectTimingSignal('death_cross')"
                      >
                        MACD死叉
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'golden_cross'" class="param-content" @click.stop>
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">DIF</div>
                        <div class="table-cell">DEA</div>
                        <div class="table-cell">MACD</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="goldenDifPeriod" class="form-control" placeholder="12" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="goldenDeaPeriod" class="form-control" placeholder="26" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="goldenMacdPeriod" class="form-control" placeholder="9" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'death_cross'" class="param-content" @click.stop>
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">DIF</div>
                        <div class="table-cell">DEA</div>
                        <div class="table-cell">MACD</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="deathDifPeriod" class="form-control" placeholder="12" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="deathDeaPeriod" class="form-control" placeholder="26" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="deathMacdPeriod" class="form-control" placeholder="9" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- 趋势信号 -->
                  <div class="indicator-section">
                    <div class="section-title">趋势信号</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'bull' }]"
                        @click.stop="selectTimingSignal('bull')"
                      >
                        MACD多头
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'bear' }]"
                        @click.stop="selectTimingSignal('bear')"
                      >
                        MACD空头
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'bull' || timingSelectedSignal === 'bear'" class="param-content" @click.stop>
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">DIF</div>
                        <div class="table-cell">DEA</div>
                        <div class="table-cell">MACD</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="macdShortPeriod" class="form-control" placeholder="12" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="macdLongPeriod" class="form-control" placeholder="26" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="macdTrendPeriod" class="form-control" placeholder="9" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="macdTrendCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="macdTrendCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- 背离信号 -->
                  <div class="indicator-section">
                    <div class="section-title">背离信号</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'bottom_divergence' }]"
                        @click.stop="selectTimingSignal('bottom_divergence')"
                      >
                        MACD底背离
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'top_divergence' }]"
                        @click.stop="selectTimingSignal('top_divergence')"
                      >
                        MACD顶背离
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'bottom_divergence' || timingSelectedSignal === 'top_divergence'" class="param-content" @click.stop>
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">DIF</div>
                        <div class="table-cell">DEA</div>
                        <div class="table-cell">MACD</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="macdShortPeriod" class="form-control" placeholder="12" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="macdLongPeriod" class="form-control" placeholder="26" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="macdDivergencePeriod" class="form-control" placeholder="9" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="macdDivergenceCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="macdDivergenceCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- MACD帮助提示 -->
                  <div class="macd-help">
                    <div class="help-icon">
                      <i class="fas fa-info-circle"></i>
                    </div>
                    <div class="help-content">
                      <div class="help-title">个股MACD指标说明</div>
                      <div class="help-text">
                        个股MACD = DIF - DEA，其中DIF为快线EMA，DEA为慢线EMA的平滑值。
                        当DIF上穿DEA时产生金叉信号，下穿时产生死叉信号，用于判断个股买入卖出时机。
                      </div>
                    </div>
                  </div>
                </div>
  
                <div class="submenu-item" 
                    :class="{ active: activeSubMenu === 'timing-kdj' }"
                    @click.stop="openSubMenu('timing-kdj')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-area text-success"></i>
                    <span>KDJ指标</span>
                  </div>
                  <i class="fas fa-chevron-right"></i>
                </div>
                
                <!-- KDJ指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'timing-kdj'">
                  <!-- KDJ参数说明表头 -->
                  <div class="kdj-header">
                    <div class="kdj-title">个股KDJ指标参数设置</div>
                    <div class="kdj-description">
                      KDJ：随机指标，K：快速线，D：慢速线，J：信号线
                    </div>
                  </div>
                  
                  <!-- KDJ参数说明表格 -->
                  <div class="kdj-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>默认值</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>K</td>
                          <td>快速随机指标周期</td>
                          <td>9</td>
                        </tr>
                        <tr>
                          <td>D</td>
                          <td>慢速随机指标周期</td>
                          <td>3</td>
                        </tr>
                        <tr>
                          <td>J</td>
                          <td>信号线平滑周期</td>
                          <td>3</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  
                  <!-- KDJ信号选择 -->
                  <div class="setting-group">
                    <!-- 基础指标 -->
                    <div class="indicator-section">
                      <div class="section-title">基础指标</div>
                      <div class="button-group">
                        <button 
                          :class="['signal-btn', { active: timingSelectedSignal === 'kdj_k' }]"
                          @click.stop="selectTimingSignal('kdj_k')"
                        >
                          KDJ_K
                        </button>
                        <button 
                          :class="['signal-btn', { active: timingSelectedSignal === 'kdj_d' }]"
                          @click.stop="selectTimingSignal('kdj_d')"
                        >
                          KDJ_D
                        </button>
                        <button 
                          :class="['signal-btn', { active: timingSelectedSignal === 'kdj_j' }]"
                          @click.stop="selectTimingSignal('kdj_j')"
                        >
                          KDJ_J
                        </button>
                      </div>

                    </div>
                  </div>
                  
                  <!-- KDJ_K参数设置表格 -->
                  <div v-if="timingSelectedSignal === 'kdj_k'" class="param-content" @click.stop>
                    <!-- KDJ参数说明表头 -->
                    <div class="kdj-header">
                      <div class="kdj-title">个股KDJ指标参数设置</div>
                      <div class="kdj-description">
                        K：快速随机线，D：慢速随机线，J：随机指标
                      </div>
                    </div>
                    <!-- KDJ参数说明表格 -->
                    <div class="kdj-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>K</td>
                            <td>快速随机线周期</td>
                            <td>9</td>
                          </tr>
                          <tr>
                            <td>D</td>
                            <td>慢速随机线周期</td>
                            <td>3</td>
                          </tr>
                          <tr>
                            <td>J</td>
                            <td>随机指标周期</td>
                            <td>3</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <!-- KDJ参数输入框 -->
                    <div class="kdj-param-inputs">
                      <div class="ma-input-row" @click.stop>
                        <label>K（随机指标）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingKdjSettings.k" 
                            class="ma-input" 
                            placeholder="9"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                      <div class="ma-input-row" @click.stop>
                        <label>D（随机指标）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingKdjSettings.d" 
                            class="ma-input" 
                            placeholder="3"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                      <div class="ma-input-row" @click.stop>
                        <label>J（随机指标）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingKdjSettings.j" 
                            class="ma-input" 
                            placeholder="3"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- KDJ_K比较设置 -->
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">KDJ_K值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjKCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="kdjKCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjKTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click="resetMASettings">重置</button>
                      <button class="btn-apply" @click="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- KDJ_D参数设置表格 -->
                  <div v-if="timingSelectedSignal === 'kdj_d'" class="param-content" @click.stop>
                    <!-- KDJ参数说明表头 -->
                    <div class="kdj-header">
                      <div class="kdj-title">个股KDJ指标参数设置</div>
                      <div class="kdj-description">
                        K：快速随机线，D：慢速随机线，J：随机指标
                      </div>
                    </div>
                    <!-- KDJ参数说明表格 -->
                    <div class="kdj-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>K</td>
                            <td>快速随机线周期</td>
                            <td>9</td>
                          </tr>
                          <tr>
                            <td>D</td>
                            <td>慢速随机线周期</td>
                            <td>3</td>
                          </tr>
                          <tr>
                            <td>J</td>
                            <td>随机指标周期</td>
                            <td>3</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <!-- KDJ参数输入框 -->
                    <div class="kdj-param-inputs">
                      <div class="ma-input-row" @click.stop>
                        <label>K（随机指标）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingKdjSettings.k" 
                            class="ma-input" 
                            placeholder="9"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                      <div class="ma-input-row" @click.stop>
                        <label>D（随机指标）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingKdjSettings.d" 
                            class="ma-input" 
                            placeholder="3"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                      <div class="ma-input-row" @click.stop>
                        <label>J（随机指标）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingKdjSettings.j" 
                            class="ma-input" 
                            placeholder="3"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- KDJ_D比较设置 -->
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">KDJ_D值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjDCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="kdjDCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjDTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click="resetMASettings">重置</button>
                      <button class="btn-apply" @click="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- KDJ_J参数设置表格 -->
                  <div v-if="timingSelectedSignal === 'kdj_j'" class="param-content" @click.stop>
                    <!-- KDJ参数说明表头 -->
                    <div class="kdj-header">
                      <div class="kdj-title">个股KDJ指标参数设置</div>
                      <div class="kdj-description">
                        K：快速随机线，D：慢速随机线，J：随机指标
                      </div>
                    </div>
                    <!-- KDJ参数说明表格 -->
                    <div class="kdj-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>K</td>
                            <td>快速随机线周期</td>
                            <td>9</td>
                          </tr>
                          <tr>
                            <td>D</td>
                            <td>慢速随机线周期</td>
                            <td>3</td>
                          </tr>
                          <tr>
                            <td>J</td>
                            <td>随机指标周期</td>
                            <td>3</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <!-- KDJ参数输入框 -->
                    <div class="kdj-param-inputs">
                      <div class="ma-input-row" @click.stop>
                        <label>K（随机指标）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingKdjSettings.k" 
                            class="ma-input" 
                            placeholder="9"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                      <div class="ma-input-row" @click.stop>
                        <label>D（随机指标）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingKdjSettings.d" 
                            class="ma-input" 
                            placeholder="3"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                      <div class="ma-input-row" @click.stop>
                        <label>J（随机指标）</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingKdjSettings.j" 
                            class="ma-input" 
                            placeholder="3"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- KDJ_J比较设置 -->
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">KDJ_J值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjJCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="kdjJCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjJTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click="resetMASettings">重置</button>
                      <button class="btn-apply" @click="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- 交叉信号 -->
                  <div class="indicator-section">
                    <div class="section-title">交叉信号</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'kdj_golden_cross' }]"
                        @click.stop="selectTimingSignal('kdj_golden_cross')"
                      >
                        KDJ金叉
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'kdj_death_cross' }]"
                        @click.stop="selectTimingSignal('kdj_death_cross')"
                      >
                        KDJ死叉
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'kdj_golden_cross'" class="param-content" @click.stop>
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">K周期</div>
                        <div class="table-cell">D周期</div>
                        <div class="table-cell">J周期</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjGoldenKPeriod" class="form-control" placeholder="9" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjGoldenDPeriod" class="form-control" placeholder="3" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjGoldenJPeriod" class="form-control" placeholder="3" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'kdj_death_cross'" class="param-content" @click.stop>
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">K周期</div>
                        <div class="table-cell">D周期</div>
                        <div class="table-cell">J周期</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjDeathKPeriod" class="form-control" placeholder="9" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjDeathDPeriod" class="form-control" placeholder="3" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjDeathJPeriod" class="form-control" placeholder="3" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- 趋势信号 -->
                  <div class="indicator-section">
                    <div class="section-title">趋势信号</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'kdj_bull' }]"
                        @click.stop="selectTimingSignal('kdj_bull')"
                      >
                        KDJ多头
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'kdj_bear' }]"
                        @click.stop="selectTimingSignal('kdj_bear')"
                      >
                        KDJ空头
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'kdj_bull' || timingSelectedSignal === 'kdj_bear'" class="param-content" @click.stop>
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">K周期</div>
                        <div class="table-cell">D周期</div>
                        <div class="table-cell">J周期</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjShortPeriod" class="form-control" placeholder="9" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjLongPeriod" class="form-control" placeholder="3" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjTrendJPeriod" class="form-control" placeholder="3" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="kdjTrendCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjTrendCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- 背离信号 -->
                  <div class="indicator-section">
                    <div class="section-title">背离信号</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'kdj_bottom_divergence' }]"
                        @click.stop="selectTimingSignal('kdj_bottom_divergence')"
                      >
                        KDJ底背离
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'kdj_top_divergence' }]"
                        @click.stop="selectTimingSignal('kdj_top_divergence')"
                      >
                        KDJ顶背离
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'kdj_bottom_divergence' || timingSelectedSignal === 'kdj_top_divergence'" class="param-content" @click.stop>
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">K周期</div>
                        <div class="table-cell">D周期</div>
                        <div class="table-cell">J周期</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjShortPeriod" class="form-control" placeholder="9" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjLongPeriod" class="form-control" placeholder="3" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjDivergenceJPeriod" class="form-control" placeholder="3" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="kdjDivergenceCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="kdjDivergenceCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click="resetMASettings">重置</button>
                      <button class="btn-apply" @click="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- KDJ帮助提示 -->
                  <div class="kdj-help">
                    <div class="help-icon">
                      <i class="fas fa-info-circle"></i>
                    </div>
                    <div class="help-content">
                      <div class="help-title">个股KDJ指标说明</div>
                      <div class="help-text">
                        个股KDJ指标是一种随机指标，通过K、D、J三条线来判断个股超买超卖。
                        当K线上穿D线时产生金叉信号，下穿时产生死叉信号，用于判断个股买入卖出时机。
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 在个股择时指标submenu下插入RSI菜单项 -->
                <div class="submenu-item"
                    :class="{ active: activeSubMenu === 'timing-rsi' }"
                    @click.stop="openSubMenu('timing-rsi')">
                  <div class="submenu-content">
                    <i class="fas fa-wave-square text-info"></i>
                    <span>RSI指标</span>
                  </div>
                  <i class="fas fa-chevron-right"></i>
                </div>
                
                                <!-- RSI指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'timing-rsi'">
                  <!-- RSI信号选择 -->
                  <div class="setting-group">
                    <!-- RSI参数说明表头 -->
                    <div class="rsi-header">
                      <div class="rsi-title">个股RSI指标参数设置</div>
                      <div class="rsi-description">
                        RSI：相对强弱指数，用于判断超买超卖状态
                      </div>
                    </div>
                    <!-- RSI参数说明表格 -->
                    <div class="rsi-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>RSI</td>
                            <td>相对强弱指数计算周期</td>
                            <td>14</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <!-- 基础指标 -->
                    <div class="indicator-section">
                      <div class="section-title">基础指标</div>
                      <div class="button-group">
                        <button 
                          :class="['signal-btn', { active: timingSelectedSignal === 'rsi' }]"
                          @click.stop="selectTimingSignal('rsi')"
                        >
                          RSI
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <!-- RSI参数设置表格 -->
                  <div v-if="timingSelectedSignal === 'rsi'" class="param-content" @click.stop>
                    <!-- RSI参数输入框 -->
                    <div class="rsi-param-inputs">
                      <div class="ma-input-row" @click.stop>
                        <label>RSI周期</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingRsiSettings.period" 
                            class="ma-input" 
                            placeholder="14"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- RSI比较设置 -->
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">RSI值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="rsiCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="rsiCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="rsiTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- 交叉信号 -->
                  <div class="indicator-section">
                    <div class="section-title">交叉信号</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'rsi_golden_cross' }]"
                        @click.stop="selectTimingSignal('rsi_golden_cross')"
                      >
                        RSI金叉
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'rsi_death_cross' }]"
                        @click.stop="selectTimingSignal('rsi_death_cross')"
                      >
                        RSI死叉
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'rsi_golden_cross' || timingSelectedSignal === 'rsi_death_cross'" class="param-content" @click.stop>
                    <!-- RSI参数输入框 -->
                    <div class="rsi-param-inputs">
                      <div class="ma-input-row" @click.stop>
                        <label>RSI周期</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingRsiSettings.period" 
                            class="ma-input" 
                            placeholder="14"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- RSI交叉比较设置 -->
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">RSI值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="rsiCrossCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="rsiCrossCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="rsiTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- 趋势信号 -->
                  <div class="indicator-section">
                    <div class="section-title">趋势信号</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'rsi_bull' }]"
                        @click.stop="selectTimingSignal('rsi_bull')"
                      >
                        RSI多头
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'rsi_bear' }]"
                        @click.stop="selectTimingSignal('rsi_bear')"
                      >
                        RSI空头
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'rsi_bull' || timingSelectedSignal === 'rsi_bear'" class="param-content" @click.stop>
                    <!-- RSI参数输入框 -->
                    <div class="rsi-param-inputs">
                      <div class="ma-input-row" @click.stop>
                        <label>RSI周期</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingRsiSettings.period" 
                            class="ma-input" 
                            placeholder="14"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- RSI趋势比较设置 -->
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">RSI值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="rsiTrendCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="rsiTrendCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="rsiTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- 背离信号 -->
                  <div class="indicator-section">
                    <div class="section-title">背离信号</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'rsi_bottom_divergence' }]"
                        @click.stop="selectTimingSignal('rsi_bottom_divergence')"
                      >
                        RSI底背离
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'rsi_top_divergence' }]"
                        @click.stop="selectTimingSignal('rsi_top_divergence')"
                      >
                        RSI顶背离
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'rsi_bottom_divergence' || timingSelectedSignal === 'rsi_top_divergence'" class="param-content" @click.stop>
                    <!-- RSI参数输入框 -->
                    <div class="rsi-param-inputs">
                      <div class="ma-input-row" @click.stop>
                        <label>RSI周期</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingRsiSettings.period" 
                            class="ma-input" 
                            placeholder="14"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- RSI背离比较设置 -->
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">RSI值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="rsiDivergenceCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="rsiDivergenceCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="rsiTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click="resetMASettings">重置</button>
                      <button class="btn-apply" @click="applyMASettings">应用设置</button>
                    </div>
                  </div>
                </div>
                <!-- 在个股择时指标submenu下插入BOLL、CR、ATR、TRIX菜单项 -->
                <div class="submenu-item"
                     :class="{ active: activeSubMenu === 'timing-boll' }"
                     @click.stop="openSubMenu('timing-boll')">
                  <div class="submenu-content">
                    <i class="fas fa-circle-notch text-info"></i>
                    <span>BOLL指标</span>
                  </div>
                  <i class="fas fa-chevron-right"></i>
                </div>
                
                <!-- BOLL指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'timing-boll'">
                  <!-- BOLL信号选择 -->
                  <div class="setting-group">
                    <!-- BOLL参数说明表头 -->
                    <div class="boll-header">
                      <div class="boll-title">个股BOLL指标参数设置</div>
                      <div class="boll-description">
                        布林带：移动平均线 + 标准差通道
                      </div>
                    </div>
                    <!-- BOLL参数说明表格 -->
                    <div class="boll-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>周期</td>
                            <td>移动平均线周期</td>
                            <td>20</td>
                          </tr>
                          <tr>
                            <td>倍数</td>
                            <td>标准差倍数</td>
                            <td>2</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <!-- 基础指标 -->
                    <div class="indicator-section">
                      <div class="section-title">基础指标</div>
                      <div class="button-group">
                        <button 
                          :class="['signal-btn', { active: timingSelectedSignal === 'boll' }]"
                          @click.stop="selectTimingSignal('boll')"
                        >
                          BOLL
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <!-- BOLL参数设置表格 -->
                  <div v-if="timingSelectedSignal === 'boll'" class="param-content" @click.stop>
                    <!-- BOLL参数输入框 -->
                    <div class="boll-param-inputs">
                      <div class="ma-input-row" @click.stop>
                        <label>周期</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingBollSettings.period" 
                            class="ma-input" 
                            placeholder="20"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                      <div class="ma-input-row" @click.stop>
                        <label>倍数</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingBollSettings.multiplier" 
                            class="ma-input" 
                            placeholder="2"
                            step="0.1"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">倍</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- BOLL比较设置 -->
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">BOLL值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="bollCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="bollCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="bollTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetBOLLSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyBOLLSettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- BOLL轨道信号 -->
                  <div class="indicator-section">
                    <div class="section-title">BOLL轨道</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'boll_upper' }]"
                        @click.stop="selectTimingSignal('boll_upper')"
                      >
                        BOLL上线
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'boll_middle' }]"
                        @click.stop="selectTimingSignal('boll_middle')"
                      >
                        BOLL中线
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'boll_lower' }]"
                        @click.stop="selectTimingSignal('boll_lower')"
                      >
                        BOLL下线
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'boll_upper' || timingSelectedSignal === 'boll_middle' || timingSelectedSignal === 'boll_lower'" class="param-content" @click.stop>
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">天数</div>
                        <div class="table-cell">波动率系数</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="bollShortPeriod" class="form-control" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="bollLongPeriod" class="form-control" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="bollCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="bollCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetBOLLSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyBOLLSettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- BOLL突破信号 -->
                  <div class="indicator-section">
                    <div class="section-title">BOLL突破</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'boll_break_upper' }]"
                        @click.stop="selectTimingSignal('boll_break_upper')"
                      >
                        BOLL突破上轨
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'boll_break_lower' }]"
                        @click.stop="selectTimingSignal('boll_break_lower')"
                      >
                        BOLL突破下轨
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'boll_break_upper' || timingSelectedSignal === 'boll_break_lower'" class="param-content" @click.stop>
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">天数</div>
                        <div class="table-cell">波动率系数</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="bollShortPeriod" class="form-control" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="bollLongPeriod" class="form-control" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="bollCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="bollCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetBOLLSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyBOLLSettings">应用设置</button>
                    </div>
                  </div>
  
                </div>
                
                <div class="submenu-item"
                     :class="{ active: activeSubMenu === 'timing-cr' }"
                     @click.stop="openSubMenu('timing-cr')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-pie text-warning"></i>
                    <span>CR指标</span>
                  </div>
                  <i class="fas fa-chevron-right"></i>
                </div>
  
  
                <!-- CR指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'timing-cr'">
                  <div class="setting-group">
                    <!-- CR参数说明表头 -->
                    <div class="cr-header">
                      <div class="cr-title">个股CR指标参数设置</div>
                      <div class="cr-description">
                        CR：能量指标，用于判断价格趋势的强弱
                      </div>
                    </div>
                    <!-- CR参数说明表格 -->
                    <div class="cr-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>CR</td>
                            <td>能量指标计算周期</td>
                            <td>26</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div class="indicator-section">
                      <div class="section-title">基础指标</div>
                      <div class="button-group">
                        <button :class="['signal-btn', { active: timingSelectedSignal === 'cr' }]" @click.stop="selectTimingSignal('cr')">CR</button>
                      </div>
                    </div>
                  </div>
                  <div v-if="timingSelectedSignal === 'cr'" class="param-content" @click.stop>
                    <!-- CR参数输入框 -->
                    <div class="cr-param-inputs">
                      <div class="ma-input-row" @click.stop>
                        <label>CR周期</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingCrSettings.period" 
                            class="ma-input" 
                            placeholder="26"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- CR比较设置 -->
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">CR值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="crCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="crCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="crTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetCRSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyCRSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <div class="submenu-item"
                     :class="{ active: activeSubMenu === 'timing-atr' }"
                     @click.stop="openSubMenu('timing-atr')">
                  <div class="submenu-content">
                    <i class="fas fa-wave-square text-danger"></i>
                    <span>ATR指标</span>
                  </div>
                  <i class="fas fa-chevron-right"></i>
                </div>
                
                <!-- ATR指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'timing-atr'">
                  <!-- ATR信号选择 -->
                  <div class="setting-group">
                    <!-- ATR参数说明表头 -->
                    <div class="atr-header">
                      <div class="atr-title">个股ATR指标参数设置</div>
                      <div class="atr-description">
                        ATR：平均真实波幅，用于衡量市场波动性
                      </div>
                    </div>
                    <!-- ATR参数说明表格 -->
                    <div class="atr-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>ATR</td>
                            <td>平均真实波幅计算周期</td>
                            <td>14</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <!-- 基础指标 -->
                    <div class="indicator-section">
                      <div class="section-title">基础指标</div>
                      <div class="button-group">
                        <button 
                          :class="['signal-btn', { active: timingSelectedSignal === 'atr' }]"
                          @click.stop="selectTimingSignal('atr')"
                        >
                          ATR
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <!-- ATR参数设置表格 -->
                  <div v-if="timingSelectedSignal === 'atr'" class="param-content" @click.stop>
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">ATR周期</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="atrShortPeriod" class="form-control" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="atrCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="atrCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click="resetMASettings">重置</button>
                      <button class="btn-apply" @click="applyMASettings">应用设置</button>
                    </div>
                  </div>
                </div>
                
                <div class="submenu-item"
                     :class="{ active: activeSubMenu === 'timing-trix' }"
                     @click.stop="openSubMenu('timing-trix')">
                  <div class="submenu-content">
                    <i class="fas fa-random text-success"></i>
                    <span>TRIX指标</span>
                  </div>
                  <i class="fas fa-chevron-right"></i>
                </div>
                
                <!-- TRIX指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'timing-trix'">
                  <!-- TRIX信号选择 -->
                  <div class="setting-group">
                    <!-- TRIX参数说明表头 -->
                    <div class="trix-header">
                      <div class="trix-title">个股TRIX指标参数设置</div>
                      <div class="trix-description">
                        TRIX：三重指数平滑移动平均线，用于判断趋势变化
                      </div>
                    </div>
                    <!-- TRIX参数说明表格 -->
                    <div class="trix-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>TRIX</td>
                            <td>三重指数平滑周期</td>
                            <td>12</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <!-- 基础指标 -->
                    <div class="indicator-section">
                      <div class="section-title">基础指标</div>
                      <div class="button-group">
                        <button 
                          :class="['signal-btn', { active: timingSelectedSignal === 'trix' }]"
                          @click.stop="selectTimingSignal('trix')"
                        >
                          TRIX
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <!-- TRIX参数设置表格 -->
                  <div v-if="timingSelectedSignal === 'trix'" class="param-content" @click.stop>
                    <!-- TRIX参数输入框 -->
                    <div class="trix-param-inputs">
                      <div class="ma-input-row" @click.stop>
                        <label>TRIX周期</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingTrixSettings.period" 
                            class="ma-input" 
                            placeholder="12"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- TRIX比较设置 -->
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">TRIX值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="trixCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="trixCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="trixTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click="resetMASettings">重置</button>
                      <button class="btn-apply" @click="applyMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- 交叉信号 -->
                  <div class="indicator-section">
                    <div class="section-title">交叉信号</div>
                    <div class="button-group">
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'trix_golden_cross' }]"
                        @click.stop="selectTimingSignal('trix_golden_cross')"
                      >
                        TRIX金叉
                      </button>
                      <button 
                        :class="['signal-btn', { active: timingSelectedSignal === 'trix_death_cross' }]"
                        @click.stop="selectTimingSignal('trix_death_cross')"
                      >
                        TRIX死叉
                      </button>
                    </div>
                  </div>
                  
                  <div v-if="timingSelectedSignal === 'trix_golden_cross' || timingSelectedSignal === 'trix_death_cross'" class="param-content" @click.stop>
                    <!-- TRIX参数说明表头 -->
                    <div class="trix-header">
                      <div class="trix-title">个股TRIX指标参数设置</div>
                      <div class="trix-description">
                        TRIX：三重指数平滑移动平均线，用于判断趋势变化
                      </div>
                    </div>
                    <!-- TRIX参数说明表格 -->
                    <div class="trix-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>TRIX</td>
                            <td>三重指数平滑周期</td>
                            <td>12</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <!-- TRIX参数输入框 -->
                    <div class="trix-param-inputs">
                      <div class="ma-input-row" @click.stop>
                        <label>TRIX周期</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="timingTrixSettings.period" 
                            class="ma-input" 
                            placeholder="12"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- TRIX交叉比较设置 -->
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">TRIX值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="trixCrossCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="trixCrossCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="trixTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click="resetMASettings">重置</button>
                      <button class="btn-apply" @click="applyMASettings">应用设置</button>
                    </div>
                  </div>
                </div>
                
                <!-- 在个股择时指标submenu下插入CCI、BBIC、EMA、多头排列菜单项 -->
                <div class="submenu-item"
                     :class="{ active: activeSubMenu === 'timing-cci' }"
                     @click.stop="openSubMenu('timing-cci')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-line text-warning"></i>
                    <span>CCI指标</span>
                  </div>
                  <i class="fas fa-chevron-right"></i>
                </div>
                
                <!-- CCI指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'timing-cci'">
                  <!-- CCI信号选择 -->
                  <div class="setting-group">
                    <!-- CCI参数说明表头 -->
                    <div class="cci-header">
                      <div class="cci-title">个股CCI指标参数设置</div>
                      <div class="cci-description">
                        CCI：商品通道指数，用于判断超买超卖状态
                      </div>
                    </div>
                    <!-- CCI参数说明表格 -->
                    <div class="cci-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>CCI</td>
                            <td>商品通道指数计算周期</td>
                            <td>14</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <!-- 基础指标 -->
                    <div class="indicator-section">
                      <div class="section-title">基础指标</div>
                      <div class="button-group">
                        <button 
                          :class="['signal-btn', { active: timingSelectedSignal === 'cci' }]"
                          @click.stop="selectTimingSignal('cci')"
                        >
                          CCI
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <!-- CCI参数设置表格 -->
                  <div v-if="timingSelectedSignal === 'cci'" class="param-content" @click.stop>
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">CCI周期</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="cciShortPeriod" class="form-control" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="cciCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="cciCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click="resetMASettings">重置</button>
                      <button class="btn-apply" @click="applyMASettings">应用设置</button>
                    </div>
                  </div>
                </div> 
  
                
                
                <div class="submenu-item"
                     :class="{ active: activeSubMenu === 'timing-bbic' }"
                     @click.stop="openSubMenu('timing-bbic')">
                  <div class="submenu-content">
                    <i class="fas fa-balance-scale text-info"></i>
                    <span>BBIC指标</span>
                  </div>
                  <i class="fas fa-chevron-right"></i>
                </div>              
                 
  
                
                <!-- BBIC指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'timing-bbic'">
                  <div class="setting-group">
                    <!-- BBIC参数说明表头 -->
                    <div class="bbic-header">
                      <div class="bbic-title">个股BBIC指标参数设置</div>
                      <div class="bbic-description">
                        BBIC：布林带指标组合，用于判断价格通道和趋势强度
                      </div>
                    </div>
                    <!-- BBIC参数说明表格 -->
                    <div class="bbic-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>BBIC1</td>
                            <td>短期布林带周期</td>
                            <td>5</td>
                          </tr>
                          <tr>
                            <td>BBIC2</td>
                            <td>中期布林带周期</td>
                            <td>10</td>
                          </tr>
                          <tr>
                            <td>BBIC3</td>
                            <td>长期布林带周期</td>
                            <td>20</td>
                          </tr>
                          <tr>
                            <td>BBIC4</td>
                            <td>超长期布林带周期</td>
                            <td>60</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div class="indicator-section">
                      <div class="section-title">基础指标</div>
                      <div class="button-group">
                        <button :class="['signal-btn', { active: timingSelectedSignal === 'bbic' }]" @click.stop="selectTimingSignal('bbic')">BBIC</button>
                      </div>
                    </div>
                  </div>
                  <div v-if="timingSelectedSignal === 'bbic'" class="param-content" @click.stop>
                    <!-- BBIC参数输入框 -->
                    <div class="bbic-param-inputs">
                      <div class="ma-input-row" @click.stop>
                        <label>BBIC1周期</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="bbicPeriod1" 
                            class="ma-input" 
                            placeholder="5"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                      <div class="ma-input-row" @click.stop>
                        <label>BBIC2周期</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="bbicPeriod2" 
                            class="ma-input" 
                            placeholder="10"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                      <div class="ma-input-row" @click.stop>
                        <label>BBIC3周期</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="bbicPeriod3" 
                            class="ma-input" 
                            placeholder="20"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                      <div class="ma-input-row" @click.stop>
                        <label>BBIC4周期</label>
                        <div class="input-with-unit" @click.stop>
                          <input 
                            type="number" 
                            v-model="bbicPeriod4" 
                            class="ma-input" 
                            placeholder="60"
                            @click.stop
                            @focus.stop
                          >
                          <span class="unit">日</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- BBIC比较设置 -->
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">BBIC值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="bbicCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="bbicCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="bbicTargetValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetBBICSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyBBICSettings">应用设置</button>
                    </div>
                  </div>
                </div>
                
                <div class="submenu-item"
                     :class="{ active: activeSubMenu === 'timing-multi-bull' }"
                     @click.stop="openSubMenu('timing-multi-bull')">
                  <div class="submenu-content">
                    <i class="fas fa-layer-group text-success"></i>
                    <span>四周期多头排列</span>
                  </div>
                  <i class="fas fa-chevron-right"></i>
                </div>
  
                <!-- 多头排列指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'timing-multi-bull'">
                  <div class="setting-group">
                    <!-- 四周期多头排列参数说明表头 -->
                    <div class="multi-bull-header">
                      <div class="multi-bull-title">个股四周期多头排列参数设置</div>
                      <div class="multi-bull-description">
                        四周期多头排列：多个移动平均线呈多头排列，判断强势趋势
                      </div>
                    </div>
                    <!-- 四周期多头排列参数说明表格 -->
                    <div class="multi-bull-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>周期1</td>
                            <td>短期移动平均线周期</td>
                            <td>5</td>
                          </tr>
                          <tr>
                            <td>周期2</td>
                            <td>中期移动平均线周期</td>
                            <td>10</td>
                          </tr>
                          <tr>
                            <td>周期3</td>
                            <td>长期移动平均线周期</td>
                            <td>20</td>
                          </tr>
                          <tr>
                            <td>周期4</td>
                            <td>超长期移动平均线周期</td>
                            <td>60</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <div class="indicator-section">
                      <div class="section-title">多头排列</div>
                      <div class="button-group">
                        <button :class="['signal-btn', { active: timingSelectedSignal === 'multi_bull' }]" @click.stop="selectTimingSignal('multi_bull')">四周期多头排列</button>
                      </div>
                    </div>
                  </div>
                  <div v-if="timingSelectedSignal === 'multi_bull'" class="param-content" @click.stop>
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">周期1</div>
                        <div class="table-cell">周期2</div>
                        <div class="table-cell">周期3</div>
                        <div class="table-cell">周期4</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell"><input type="number" v-model="multiBullPeriod1" class="form-control" placeholder="5" @click.stop @focus.stop></div>
                        <div class="table-cell"><input type="number" v-model="multiBullPeriod2" class="form-control" placeholder="10" @click.stop @focus.stop></div>
                        <div class="table-cell"><input type="number" v-model="multiBullPeriod3" class="form-control" placeholder="20" @click.stop @focus.stop></div>
                        <div class="table-cell"><input type="number" v-model="multiBullPeriod4" class="form-control" placeholder="60" @click.stop @focus.stop></div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMultiBullSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMultiBullSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <div class="submenu-item"
                     :class="{ active: activeSubMenu === 'timing-ema' }"
                     @click.stop="openSubMenu('timing-ema')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-area text-primary"></i>
                    <span>EMA指标</span>
                  </div>
                  <i class="fas fa-chevron-right"></i>
                </div>
                
                <!-- EMA指标三级菜单内容 -->
                <!-- EMA指标设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'timing-ema'">
                  <!-- EMA信号选择 -->
                  <div class="setting-group">
                    <!-- EMA参数说明表头 -->
                    <div class="ema-header">
                      <div class="ema-title">个股EMA指标参数设置</div>
                      <div class="ema-description">
                        EMA：指数移动平均线，对近期数据给予更高权重
                      </div>
                    </div>
                    <!-- EMA参数说明表格 -->
                    <div class="ema-param-table">
                      <table class="param-table">
                        <thead>
                          <tr>
                            <th>参数</th>
                            <th>说明</th>
                            <th>默认值</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>EMA短线</td>
                            <td>短期指数移动平均线周期</td>
                            <td>12</td>
                          </tr>
                          <tr>
                            <td>EMA长线</td>
                            <td>长期指数移动平均线周期</td>
                            <td>26</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <!-- 基础指标 -->
                    <div class="indicator-section">
                      <div class="section-title">基础指标</div>
                      <div class="button-group">
                        <button 
                          :class="['signal-btn', { active: timingSelectedSignal === 'ema' }]"
                          @click.stop="selectTimingSignal('ema')"
                        >
                          EMA
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <!-- EMA参数设置表格 -->
                  <div v-if="timingSelectedSignal === 'ema'" class="param-content" @click.stop>
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">EMA短线</div>
                        <div class="table-cell">EMA长线</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row" @click.stop>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="emaShortPeriod" class="form-control" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="emaLongPeriod" class="form-control" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell" @click.stop>
                          <select v-model="emaCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell" @click.stop>
                          <input type="number" v-model="emaCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetEMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyEMASettings">应用设置</button>
                    </div>
                  </div>
                  
                  <!-- 交叉信号 -->
                  <div class="indicator-section">
                    <div class="section-title">交叉信号</div>
                    <div class="button-group">
                      <button :class="['signal-btn', { active: timingSelectedSignal === 'ema_golden_cross' }]" @click.stop="selectTimingSignal('ema_golden_cross')">EMA金叉</button>
                      <button :class="['signal-btn', { active: timingSelectedSignal === 'ema_death_cross' }]" @click.stop="selectTimingSignal('ema_death_cross')">EMA死叉</button>
                    </div>
                  </div>
                  <div v-if="timingSelectedSignal === 'ema_golden_cross' || timingSelectedSignal === 'ema_death_cross'" class="param-content" @click.stop>
                    <div class="param-table" @click.stop>
                      <div class="table-row table-header">
                        <div class="table-cell">EMA短线</div>
                        <div class="table-cell">EMA长线</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell"><input type="number" v-model="emaShortPeriod" class="form-control" placeholder="6" @click.stop @focus.stop></div>
                        <div class="table-cell"><input type="number" v-model="emaLongPeriod" class="form-control" placeholder="12" @click.stop @focus.stop></div>
                        <div class="table-cell">
                          <select v-model="emaCrossCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell"><input type="number" v-model="emaCrossCustomValue" class="form-control" step="0.01" @click.stop @focus.stop></div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetEMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyEMASettings">应用设置</button>
                    </div>
                  </div>
                  <!-- 趋势信号 -->
                  <div class="indicator-section">
                    <div class="section-title">趋势信号</div>
                    <div class="button-group">
                      <button :class="['signal-btn', { active: timingSelectedSignal === 'ema_bull' }]" @click.stop="selectTimingSignal('ema_bull')">EMA多头</button>
                      <button :class="['signal-btn', { active: timingSelectedSignal === 'ema_bear' }]" @click.stop="selectTimingSignal('ema_bear')">EMA空头</button>
                    </div>
                  </div>
                  <div v-if="timingSelectedSignal === 'ema_bull' || timingSelectedSignal === 'ema_bear'" class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">EMA短线</div>
                        <div class="table-cell">EMA长线</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell"><input type="number" v-model="emaShortPeriod" class="form-control" placeholder="14" @click.stop @focus.stop></div>
                        <div class="table-cell"><input type="number" v-model="emaLongPeriod" class="form-control" placeholder="28" @click.stop @focus.stop></div>
                        <div class="table-cell">
                          <select v-model="emaTrendCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell"><input type="number" v-model="emaTrendCustomValue" class="form-control" step="0.01" @click.stop @focus.stop></div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetEMASettings">重置</button>
                      <button class="btn-apply" @click.stop="applyEMASettings">应用设置</button>
                    </div>
                                  </div>
                </div>
                </div>
            </div>
          </div>
  
            <div class="menu-item" :class="{ active: activeMenu === 'price' }" @click="toggleMenu('price')">
              <div class="menu-item-header">
                <i class="fas fa-yen-sign"></i>
                <span>股票价格</span>
                <span class="count">13</span>
                <i class="fas fa-chevron-right arrow" :class="{ expanded: activeMenu === 'price' }"></i>
              </div>
              <!-- 二级菜单 -->
              <div class="submenu" v-if="activeMenu === 'price'">
                <!-- 开盘价 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'open-price' }"
                     @click.stop="openSubMenu('open-price')">
                  <div class="submenu-content">
                    <i class="fas fa-sun text-warning"></i>
                    <span>开盘价</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'open-price' }"></i>
                </div>
                
                <!-- 开盘价设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'open-price'">
                  <!-- 开盘价参数说明表头 -->
                  <div class="open-price-header">
                    <div class="open-price-title">股票开盘价指标参数设置</div>
                    <div class="open-price-description">
                      开盘价：股票当日开盘时的价格，反映市场开盘情绪
                    </div>
                  </div>
                  <!-- 开盘价参数说明表格 -->
                  <div class="open-price-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>比较指标</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>开盘价</td>
                          <td>股票当日开盘价格</td>
                          <td>收盘价、最高价、最低价、昨日收盘价、日成交均价</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">开盘价</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">比较指标</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">开盘价</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="openPriceCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <select v-model="openPriceIndicator" class="form-select" @click.stop @focus.stop>
                            <option value="" disabled>请选择比较指标</option>
                            <option value="收盘价">收盘价</option>
                            <option value="最高价">最高价</option>
                            <option value="最低价">最低价</option>
                            <option value="昨日收盘价">昨日收盘价</option>
                            <option value="日成交均价">日成交均价</option>
                          </select>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetOpenPriceSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyOpenPriceSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  

  
                <!-- 最高价 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'high-price' }"
                     @click.stop="openSubMenu('high-price')">
                  <div class="submenu-content">
                    <i class="fas fa-arrow-up text-success"></i>
                    <span>最高价</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'high-price' }"></i>
                </div>
                
                <!-- 最高价设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'high-price'">
                  <!-- 最高价参数说明表头 -->
                  <div class="high-price-header">
                    <div class="high-price-title">股票最高价指标参数设置</div>
                    <div class="high-price-description">
                      最高价：股票当日交易中的最高价格，反映当日价格上限
                    </div>
                  </div>
                  <!-- 最高价参数说明表格 -->
                  <div class="high-price-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>比较指标</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>最高价</td>
                          <td>股票当日最高价格</td>
                          <td>开盘价、收盘价、最低价、昨日收盘价、日成交均价</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">最高价</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">比较指标</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">最高价</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="highPriceCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <select v-model="highPriceIndicator" class="form-select" @click.stop @focus.stop>
                            <option value="" disabled>请选择比较指标</option>
                            <option value="开盘价">开盘价</option>
                            <option value="收盘价">收盘价</option>
                            <option value="最低价">最低价</option>
                            <option value="昨日收盘价">昨日收盘价</option>
                            <option value="日成交均价">日成交均价</option>
                          </select>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetHighPriceSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyHighPriceSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 最低价 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'low-price' }"
                     @click.stop="openSubMenu('low-price')">
                  <div class="submenu-content">
                    <i class="fas fa-arrow-down text-danger"></i>
                    <span>最低价</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'low-price' }"></i>
                </div>
                
                <!-- 最低价设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'low-price'">
                  <!-- 最低价参数说明表头 -->
                  <div class="low-price-header">
                    <div class="low-price-title">股票最低价指标参数设置</div>
                    <div class="low-price-description">
                      最低价：股票当日交易中的最低价格，反映当日价格下限
                    </div>
                  </div>
                  <!-- 最低价参数说明表格 -->
                  <div class="low-price-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>比较指标</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>最低价</td>
                          <td>股票当日最低价格</td>
                          <td>开盘价、收盘价、最高价、昨日收盘价、日成交均价</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">最低价</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">比较指标</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">最低价</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="lowPriceCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <select v-model="lowPriceIndicator" class="form-select" @click.stop @focus.stop>
                            <option value="" disabled>请选择比较指标</option>
                            <option value="开盘价">开盘价</option>
                            <option value="收盘价">收盘价</option>
                            <option value="最高价">最高价</option>
                            <option value="昨日收盘价">昨日收盘价</option>
                            <option value="日成交均价">日成交均价</option>
                          </select>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetLowPriceSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyLowPriceSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 昨日收盘价 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'prev-close-price' }"
                     @click.stop="openSubMenu('prev-close-price')">
                  <div class="submenu-content">
                    <i class="fas fa-history text-secondary"></i>
                    <span>昨日收盘价</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'prev-close-price' }"></i>
                </div>
                
                <!-- 昨日收盘价设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'prev-close-price'">
                  <!-- 昨日收盘价参数说明表头 -->
                  <div class="prev-close-price-header">
                    <div class="prev-close-price-title">股票昨日收盘价指标参数设置</div>
                    <div class="prev-close-price-description">
                      昨日收盘价：股票前一交易日的收盘价格，用于计算涨跌幅
                    </div>
                  </div>
                  <!-- 昨日收盘价参数说明表格 -->
                  <div class="prev-close-price-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>比较指标</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>昨日收盘价</td>
                          <td>股票前一交易日收盘价格</td>
                          <td>开盘价、收盘价、最高价、最低价、日成交均价</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">昨日收盘价</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">比较指标</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">昨日收盘价</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="prevClosePriceCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <select v-model="prevClosePriceIndicator" class="form-select" @click.stop @focus.stop>
                            <option value="" disabled>请选择比较指标</option>
                            <option value="开盘价">开盘价</option>
                            <option value="收盘价">收盘价</option>
                            <option value="最高价">最高价</option>
                            <option value="最低价">最低价</option>
                            <option value="日成交均价">日成交均价</option>
                          </select>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetPrevClosePriceSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyPrevClosePriceSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 日成交均价 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'avg-price' }"
                     @click.stop="openSubMenu('avg-price')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-area text-primary"></i>
                    <span>日成交均价</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'avg-price' }"></i>
                </div>
                
                <!-- 日成交均价设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'avg-price'">
                  <!-- 日成交均价参数说明表头 -->
                  <div class="avg-price-header">
                    <div class="avg-price-title">股票日成交均价指标参数设置</div>
                    <div class="avg-price-description">
                      日成交均价：股票当日成交金额除以成交量的平均价格
                    </div>
                  </div>
                  <!-- 日成交均价参数说明表格 -->
                  <div class="avg-price-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>比较指标</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>日成交均价</td>
                          <td>股票当日成交平均价格</td>
                          <td>开盘价、收盘价、最高价、最低价、昨日收盘价</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">日成交均价</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">比较指标</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">日成交均价</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="avgPriceCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <select v-model="avgPriceIndicator" class="form-select" @click.stop @focus.stop>
                            <option value="" disabled>请选择比较指标</option>
                            <option value="开盘价">开盘价</option>
                            <option value="收盘价">收盘价</option>
                            <option value="最高价">最高价</option>
                            <option value="最低价">最低价</option>
                            <option value="昨日收盘价">昨日收盘价</option>
                          </select>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetAvgPriceSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyAvgPriceSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 涨幅 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'change-rate' }"
                     @click.stop="openSubMenu('change-rate')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-line text-success"></i>
                    <span>涨幅</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'change-rate' }"></i>
                </div>
                
                <!-- 涨幅设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'change-rate'">
                  <!-- 涨幅参数说明表头 -->
                  <div class="change-rate-header">
                    <div class="change-rate-title">股票涨幅指标参数设置</div>
                    <div class="change-rate-description">
                      涨幅：股票价格相对于基准价格的变动百分比，反映价格变动幅度
                    </div>
                  </div>
                  <!-- 涨幅参数说明表格 -->
                  <div class="change-rate-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>涨幅</td>
                          <td>股票价格变动百分比</td>
                          <td>%</td>
                        </tr>
                        <tr>
                          <td>区间涨幅</td>
                          <td>指定时间段内的价格变动百分比</td>
                          <td>%</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="setting-group">
                    <div class="indicator-section">
                      <div class="section-title">信号选择</div>
                      <div class="button-group">
                        <button :class="['signal-btn', { active: changeRateType === 'single' }]" @click.stop="changeRateType = 'single'">涨幅</button>
                        <button :class="['signal-btn', { active: changeRateType === 'range' }]" @click.stop="changeRateType = 'range'">区间涨幅</button>
                      </div>
                    </div>
                  </div>
                  <div class="param-content" v-if="changeRateType === 'single'">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">涨幅</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">自定义百分比</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">涨幅</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="changeRateCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="changeRateValue" class="form-control" placeholder="请输入百分比" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="param-content" v-if="changeRateType === 'range'">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">几日</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">数值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <input type="text" v-model="changeRateRangeDate" class="form-control" placeholder="请输入几日" @click.stop @focus.stop>
                        </div>
                        <div class="table-cell">
                          <select v-model="changeRateCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="changeRateRangeCustomValue" class="form-control" placeholder="请输入数值" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="action-buttons">
                    <button class="btn-reset" @click.stop="resetChangeRateSettings">重置</button>
                    <button class="btn-apply" @click.stop="applyChangeRateSettings">应用设置</button>
                  </div>
                </div>
  
                <!-- 量比 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'volume-ratio' }"
                     @click.stop="openSubMenu('volume-ratio')">
                  <div class="submenu-content">
                    <i class="fas fa-balance-scale text-primary"></i>
                    <span>量比</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'volume-ratio' }"></i>
                </div>
                
                <!-- 量比设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'volume-ratio'">
                  <!-- 量比参数说明表头 -->
                  <div class="volume-ratio-header">
                    <div class="volume-ratio-title">股票量比指标参数设置</div>
                    <div class="volume-ratio-description">
                      量比：当前成交量与过去5日平均成交量的比值，反映交易活跃度
                    </div>
                  </div>
                  <!-- 量比参数说明表格 -->
                  <div class="volume-ratio-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>参考值</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>量比</td>
                          <td>当前成交量与5日平均成交量比值</td>
                          <td>1.0为正常水平</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">量比</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">量比</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="volumeRatioCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="volumeRatioCustomValue" class="form-control" placeholder="0.00" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetVolumeRatioSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyVolumeRatioSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 成交额 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'turnover' }"
                     @click.stop="openSubMenu('turnover')">
                  <div class="submenu-content">
                    <i class="fas fa-money-bill-wave text-warning"></i>
                    <span>成交额</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'turnover' }"></i>
                </div>
                
                <!-- 成交额设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'turnover'">
                  <!-- 成交额参数说明表头 -->
                  <div class="turnover-header">
                    <div class="turnover-title">股票成交额指标参数设置</div>
                    <div class="turnover-description">
                      成交额：股票当日成交的总金额，反映市场交易规模
                    </div>
                  </div>
                  <!-- 成交额参数说明表格 -->
                  <div class="turnover-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>成交额</td>
                          <td>股票当日成交总金额</td>
                          <td>万元</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">成交额</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">成交额</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="turnoverCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="turnoverCustomValue" class="form-control" placeholder="0.00" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetTurnoverSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyTurnoverSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 换手率 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'turnover-rate' }"
                     @click.stop="openSubMenu('turnover-rate')">
                  <div class="submenu-content">
                    <i class="fas fa-sync-alt text-info"></i>
                    <span>换手率</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'turnover-rate' }"></i>
                </div>
                
                <!-- 换手率设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'turnover-rate'">
                  <!-- 换手率参数说明表头 -->
                  <div class="turnover-rate-header">
                    <div class="turnover-rate-title">股票换手率指标参数设置</div>
                    <div class="turnover-rate-description">
                      换手率：股票成交量与流通股本的比值，反映股票交易活跃度
                    </div>
                  </div>
                  <!-- 换手率参数说明表格 -->
                  <div class="turnover-rate-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>换手率</td>
                          <td>成交量与流通股本比值</td>
                          <td>%</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">换手率</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">换手率</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="turnoverRateCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="turnoverRateCustomValue" class="form-control" placeholder="0.00" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetTurnoverRateSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyTurnoverRateSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 市值 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'market-value' }"
                     @click.stop="openSubMenu('market-value')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-pie text-danger"></i>
                    <span>市值</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'market-value' }"></i>
                </div>
                
                <!-- 市值设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'market-value'">
                  <!-- 市值参数说明表头 -->
                  <div class="market-value-header">
                    <div class="market-value-title">股票市值指标参数设置</div>
                    <div class="market-value-description">
                      市值：股票总股本乘以当前股价，反映公司整体价值
                    </div>
                  </div>
                  <!-- 市值参数说明表格 -->
                  <div class="market-value-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>市值</td>
                          <td>总股本乘以当前股价</td>
                          <td>亿元</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">市值</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">市值</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="marketValueCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="marketValueCustomValue" class="form-control" placeholder="0.00" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetMarketValueSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyMarketValueSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 成交量 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'volume' }"
                     @click.stop="openSubMenu('volume')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-bar text-secondary"></i>
                    <span>成交量</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'volume' }"></i>
                </div>
                
                <!-- 成交量设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'volume'">
                  <!-- 成交量参数说明表头 -->
                  <div class="volume-header">
                    <div class="volume-title">股票成交量指标参数设置</div>
                    <div class="volume-description">
                      成交量：股票当日成交的股票数量，反映市场交易活跃度
                    </div>
                  </div>
                  <!-- 成交量参数说明表格 -->
                  <div class="volume-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>成交量</td>
                          <td>股票当日成交数量</td>
                          <td>万股</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">成交量</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">成交量</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="volumeCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="volumeCustomValue" class="form-control" placeholder="0.00" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetVolumeSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyVolumeSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 资金净流入 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'net-inflow' }"
                     @click.stop="openSubMenu('net-inflow')">
                  <div class="submenu-content">
                    <i class="fas fa-water text-success"></i>
                    <span>资金净流入</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'net-inflow' }"></i>
                </div>
                
                <!-- 资金净流入设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'net-inflow'">
                  <!-- 资金净流入参数说明表头 -->
                  <div class="net-inflow-header">
                    <div class="net-inflow-title">股票资金净流入指标参数设置</div>
                    <div class="net-inflow-description">
                      资金净流入：主力资金流入与流出的差额，反映资金流向趋势
                    </div>
                  </div>
                  <!-- 资金净流入参数说明表格 -->
                  <div class="net-inflow-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>资金净流入</td>
                          <td>主力资金流入与流出差额</td>
                          <td>万元</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">资金净流入</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">自定义金额</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">资金净流入</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="netInflowCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model.number="netInflowAmount" class="form-control" placeholder="0.00" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetNetInflowSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyNetInflowSettings">应用设置</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
  
            <!-- 公告类 -->
            <div class="menu-item" :class="{ active: activeMenu === 'announcement' }" @click="toggleMenu('announcement')">
              <div class="menu-item-header">
                <i class="fas fa-bullhorn"></i>
                <span>公告类</span>
                <span class="count">6</span>
                <i class="fas fa-chevron-right arrow" :class="{ expanded: activeMenu === 'announcement' }"></i>
              </div>
              <!-- 二级菜单 -->
              <div class="submenu" v-if="activeMenu === 'announcement'">
                <!-- 股东减持 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'shareholder-reduction' }"
                     @click.stop="openSubMenu('shareholder-reduction')">
                  <div class="submenu-content">
                    <i class="fas fa-arrow-down text-danger"></i>
                    <span>股东减持</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'shareholder-reduction' }"></i>
                </div>
                
                <!-- 股东减持设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'shareholder-reduction'">
                  <!-- 股东减持参数说明表头 -->
                  <div class="shareholder-reduction-header">
                    <div class="shareholder-reduction-title">股东减持指标参数设置</div>
                    <div class="shareholder-reduction-description">
                      股东减持：公司股东减少持股数量的行为，可能影响股价走势
                    </div>
                  </div>
                  <!-- 股东减持参数说明表格 -->
                  <div class="shareholder-reduction-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>类型</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>股东减持</td>
                          <td>股东减少持股数量</td>
                          <td>布尔值</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">股东减持</div>
                        <div class="table-cell">是否勾选</div>
                      </div>
                                            <div class="table-row">
                          <div class="table-cell">
                            <span class="price-label">股东减持</span>
                          </div>
                          <div class="table-cell">
                            <input type="checkbox" v-model="shareholderReductionChecked" @click.stop @focus.stop> 勾选
                          </div>
                        </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetShareholderReductionSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyShareholderReductionSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 股东增持 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'shareholder-increase' }"
                     @click.stop="openSubMenu('shareholder-increase')">
                  <div class="submenu-content">
                    <i class="fas fa-arrow-up text-success"></i>
                    <span>股东增持</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'shareholder-increase' }"></i>
                </div>
                
                <!-- 股东增持设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'shareholder-increase'">
                  <!-- 股东增持参数说明表头 -->
                  <div class="shareholder-increase-header">
                    <div class="shareholder-increase-title">股东增持指标参数设置</div>
                    <div class="shareholder-increase-description">
                      股东增持：公司股东增加持股数量的行为，通常被视为积极信号
                    </div>
                  </div>
                  <!-- 股东增持参数说明表格 -->
                  <div class="shareholder-increase-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>类型</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>股东增持</td>
                          <td>股东增加持股数量</td>
                          <td>布尔值</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">股东增持</div>
                        <div class="table-cell">是否勾选</div>
                      </div>
                                            <div class="table-row">
                          <div class="table-cell">
                            <span class="price-label">股东增持</span>
                          </div>
                          <div class="table-cell">
                            <input type="checkbox" v-model="shareholderIncreaseChecked" @click.stop @focus.stop> 勾选
                          </div>
                        </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetShareholderIncreaseSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyShareholderIncreaseSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 股东分红 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'shareholder-dividend' }"
                     @click.stop="openSubMenu('shareholder-dividend')">
                  <div class="submenu-content">
                    <i class="fas fa-gift text-warning"></i>
                    <span>股东分红</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'shareholder-dividend' }"></i>
                </div>
                
                <!-- 股东分红设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'shareholder-dividend'">
                  <!-- 股东分红参数说明表头 -->
                  <div class="shareholder-dividend-header">
                    <div class="shareholder-dividend-title">股东分红指标参数设置</div>
                    <div class="shareholder-dividend-description">
                      股东分红：公司向股东分配利润的行为，反映公司盈利能力和股东回报
                    </div>
                  </div>
                  <!-- 股东分红参数说明表格 -->
                  <div class="shareholder-dividend-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>类型</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>股东分红</td>
                          <td>公司向股东分配利润</td>
                          <td>布尔值</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">股东分红</div>
                        <div class="table-cell">是否勾选</div>
                      </div>
                                            <div class="table-row">
                          <div class="table-cell">
                            <span class="price-label">股东分红</span>
                          </div>
                          <div class="table-cell">
                            <input type="checkbox" v-model="shareholderDividendChecked" @click.stop @focus.stop> 勾选
                          </div>
                        </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetShareholderDividendSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyShareholderDividendSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 违规问询函 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'violation-inquiry' }"
                     @click.stop="openSubMenu('violation-inquiry')">
                  <div class="submenu-content">
                    <i class="fas fa-exclamation-triangle text-danger"></i>
                    <span>违规问询函</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'violation-inquiry' }"></i>
                </div>
                
                <!-- 违规问询函设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'violation-inquiry'">
                  <!-- 违规问询函参数说明表头 -->
                  <div class="violation-inquiry-header">
                    <div class="violation-inquiry-title">违规问询函指标参数设置</div>
                    <div class="violation-inquiry-description">
                      违规问询函：监管机构对公司违规行为的问询，可能影响公司声誉和股价
                    </div>
                  </div>
                  <!-- 违规问询函参数说明表格 -->
                  <div class="violation-inquiry-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>类型</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>违规问询函</td>
                          <td>监管机构违规问询</td>
                          <td>布尔值</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">违规问询函</div>
                        <div class="table-cell">是否勾选</div>
                      </div>
                                            <div class="table-row">
                          <div class="table-cell">
                            <span class="price-label">违规问询函</span>
                          </div>
                          <div class="table-cell">
                            <input type="checkbox" v-model="violationInquiryChecked" @click.stop @focus.stop> 勾选
                          </div>
                        </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetViolationInquirySettings">重置</button>
                      <button class="btn-apply" @click.stop="applyViolationInquirySettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 业绩预告 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'performance-forecast' }"
                     @click.stop="openSubMenu('performance-forecast')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-line text-info"></i>
                    <span>业绩预告</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'performance-forecast' }"></i>
                </div>
                
                <!-- 业绩预告设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'performance-forecast'">
                  <!-- 业绩预告参数说明表头 -->
                  <div class="performance-forecast-header">
                    <div class="performance-forecast-title">业绩预告指标参数设置</div>
                    <div class="performance-forecast-description">
                      业绩预告：公司对未来业绩的预测公告，影响投资者对公司前景的判断
                    </div>
                  </div>
                  <!-- 业绩预告参数说明表格 -->
                  <div class="performance-forecast-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>净利润同比去年涨幅</td>
                          <td>净利润与去年同期相比的增长率</td>
                          <td>%</td>
                        </tr>
                        <tr>
                          <td>净利润</td>
                          <td>公司当期净利润金额</td>
                          <td>万元</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="setting-group">
                    <div class="indicator-section">
                      <div class="section-title">基础指标</div>
                      <div class="button-group">
                        <button :class="['signal-btn', { active: selectedSignal === 'profit_yoy' }]" @click.stop="selectedSignal = 'profit_yoy'">净利润同比去年涨幅</button>
                        <button :class="['signal-btn', { active: selectedSignal === 'net_profit' }]" @click.stop="selectedSignal = 'net_profit'">净利润</button>
                      </div>
                    </div>
                    <div class="param-content">
                      <div class="param-table">
                        <div class="table-row table-header">
                          <div class="table-cell">{{ selectedSignal === 'profit_yoy' ? '净利润同比去年涨幅' : '净利润' }}</div>
                          <div class="table-cell">比较符</div>
                          <div class="table-cell">{{ selectedSignal === 'profit_yoy' ? '自定义涨幅' : '自定义金额' }}</div>
                        </div>
                        <div class="table-row">
                          <div class="table-cell">
                            <span class="price-label">{{ selectedSignal === 'profit_yoy' ? '净利润同比去年涨幅' : '净利润' }}</span>
                          </div>
                          <div class="table-cell">
                            <select v-model="performanceForecastCompare" class="form-select" @click.stop @focus.stop v-if="selectedSignal === 'profit_yoy'">
                              <option value="大于">大于</option>
                              <option value="小于">小于</option>
                              <option value="大于等于">大于等于</option>
                              <option value="小于等于">小于等于</option>
                              <option value="等于">等于</option>
                            </select>
                            <select v-model="netProfitCompare" class="form-select" @click.stop @focus.stop v-if="selectedSignal === 'net_profit'">
                              <option value="大于">大于</option>
                              <option value="小于">小于</option>
                              <option value="大于等于">大于等于</option>
                              <option value="小于等于">小于等于</option>
                              <option value="等于">等于</option>
                            </select>
                          </div>
                          <div class="table-cell">
                            <input type="number" v-model="performanceForecastAmount" class="form-control" placeholder="0.00" step="0.01" @click.stop @focus.stop v-if="selectedSignal === 'profit_yoy'">
                            <input type="number" v-model="netProfitAmount" class="form-control" placeholder="0.00" step="0.01" @click.stop @focus.stop v-if="selectedSignal === 'net_profit'">
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetPerformanceForecastSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyPerformanceForecastSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 业绩公告 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'performance-announcement' }"
                     @click.stop="openSubMenu('performance-announcement')">
                  <div class="submenu-content">
                    <i class="fas fa-file-alt text-primary"></i>
                    <span>业绩公告</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'performance-announcement' }"></i>
                </div>
                
                <!-- 业绩公告设置内容 -->
                <div class="ma-settings" v-if="activeSubMenu === 'performance-announcement'">
                  <!-- 业绩公告参数说明表头 -->
                  <div class="performance-announcement-header">
                    <div class="performance-announcement-title">业绩公告指标参数设置</div>
                    <div class="performance-announcement-description">
                      业绩公告：公司正式发布的业绩报告，反映公司实际经营状况
                    </div>
                  </div>
                  <!-- 业绩公告参数说明表格 -->
                  <div class="performance-announcement-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>净利润同比去年涨幅</td>
                          <td>净利润与去年同期相比的增长率</td>
                          <td>%</td>
                        </tr>
                        <tr>
                          <td>净利润</td>
                          <td>公司当期净利润金额</td>
                          <td>万元</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="setting-group">
                    <div class="indicator-section">
                      <div class="section-title">基础指标</div>
                      <div class="button-group">
                        <button :class="['signal-btn', { active: selectedSignalAnnouncement === 'announcement_profit_yoy' }]" @click.stop="selectedSignalAnnouncement = 'announcement_profit_yoy'">净利润同比去年涨幅</button>
                        <button :class="['signal-btn', { active: selectedSignalAnnouncement === 'announcement_net_profit' }]" @click.stop="selectedSignalAnnouncement = 'announcement_net_profit'">净利润</button>
                      </div>
                    </div>
                    <div class="param-content">
                      <div class="param-table">
                        <div class="table-row table-header">
                          <div class="table-cell">{{ selectedSignalAnnouncement === 'announcement_profit_yoy' ? '净利润同比去年涨幅' : '净利润' }}</div>
                          <div class="table-cell">比较符</div>
                          <div class="table-cell">{{ selectedSignalAnnouncement === 'announcement_profit_yoy' ? '自定义涨幅' : '自定义金额' }}</div>
                        </div>
                        <div class="table-row">
                          <div class="table-cell">
                            <span class="price-label">{{ selectedSignalAnnouncement === 'announcement_profit_yoy' ? '净利润同比去年涨幅' : '净利润' }}</span>
                          </div>
                          <div class="table-cell">
                            <select v-model="performanceAnnouncementCompare" class="form-select" @click.stop @focus.stop v-if="selectedSignalAnnouncement === 'announcement_profit_yoy'">
                              <option value="大于">大于</option>
                              <option value="小于">小于</option>
                              <option value="大于等于">大于等于</option>
                              <option value="小于等于">小于等于</option>
                              <option value="等于">等于</option>
                            </select>
                            <select v-model="netProfitAnnouncementCompare" class="form-select" @click.stop @focus.stop v-if="selectedSignalAnnouncement === 'announcement_net_profit'">
                              <option value="大于">大于</option>
                              <option value="小于">小于</option>
                              <option value="大于等于">大于等于</option>
                              <option value="小于等于">小于等于</option>
                              <option value="等于">等于</option>
                            </select>
                          </div>
                          <div class="table-cell">
                            <input type="number" v-model="performanceAnnouncementAmount" class="form-control" placeholder="0.00" step="0.01" @click.stop @focus.stop v-if="selectedSignalAnnouncement === 'announcement_profit_yoy'">
                            <input type="number" v-model="netProfitAnnouncementAmount" class="form-control" placeholder="0.00" step="0.01" @click.stop @focus.stop v-if="selectedSignalAnnouncement === 'announcement_net_profit'">
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetPerformanceAnnouncementSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyPerformanceAnnouncementSettings">应用设置</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
  
            <!-- 过滤项 -->
            <div class="menu-item" :class="{ active: activeMenu === 'filter' }" @click="toggleMenu('filter')">
              <div class="menu-item-header">
                <i class="fas fa-filter"></i>
                <span>过滤项</span>
                <span class="count">9</span>
                <i class="fas fa-chevron-right arrow" :class="{ expanded: activeMenu === 'filter' }"></i>
              </div>
              <!-- 二级菜单 -->
              <div class="submenu" v-if="activeMenu === 'filter'">
                <!-- 过滤新上市 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'filter-new-listing' }"
                     @click.stop="openSubMenu('filter-new-listing')">
                  <div class="submenu-content">
                    <i class="fas fa-star text-warning"></i>
                    <span>过滤新上市</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'filter-new-listing' }"></i>
                </div>
                
                <!-- 过滤新上市设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'filter-new-listing'">
                  <!-- 过滤新上市参数说明表头 -->
                  <div class="filter-new-listing-header">
                    <div class="filter-new-listing-title">过滤新上市指标参数设置</div>
                    <div class="filter-new-listing-description">
                      过滤新上市：排除新上市的股票，避免新股波动对选股结果的影响
                    </div>
                  </div>
                  <!-- 过滤新上市参数说明表格 -->
                  <div class="filter-new-listing-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>类型</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>过滤新上市</td>
                          <td>排除新上市股票</td>
                          <td>布尔值</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">过滤新上市</div>
                        <div class="table-cell">是否勾选</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">过滤新上市</span>
                        </div>
                        <div class="table-cell">
                          <input type="checkbox" v-model="filterNewListingChecked" @click.stop @focus.stop> 勾选
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetFilterNewListingSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyFilterNewListingSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 过滤北交所 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'filter-beijing' }"
                     @click.stop="openSubMenu('filter-beijing')">
                  <div class="submenu-content">
                    <i class="fas fa-building text-primary"></i>
                    <span>过滤北交所</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'filter-beijing' }"></i>
                </div>
                
                <!-- 过滤北交所设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'filter-beijing'">
                  <!-- 过滤北交所参数说明表头 -->
                  <div class="filter-beijing-header">
                    <div class="filter-beijing-title">过滤北交所指标参数设置</div>
                    <div class="filter-beijing-description">
                      过滤北交所：排除北京证券交易所的股票，专注于其他市场板块
                    </div>
                  </div>
                  <!-- 过滤北交所参数说明表格 -->
                  <div class="filter-beijing-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>类型</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>过滤北交所</td>
                          <td>排除北交所股票</td>
                          <td>布尔值</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">过滤北交所</div>
                        <div class="table-cell">是否勾选</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">过滤北交所</span>
                        </div>
                        <div class="table-cell">
                          <input type="checkbox" v-model="filterBeijingChecked" @click.stop @focus.stop> 勾选
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetFilterBeijingSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyFilterBeijingSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 过滤沪深主板 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'filter-main-board' }"
                     @click.stop="openSubMenu('filter-main-board')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-line text-success"></i>
                    <span>过滤沪深主板</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'filter-main-board' }"></i>
                </div>
                
                <!-- 过滤沪深主板设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'filter-main-board'">
                  <!-- 过滤沪深主板参数说明表头 -->
                  <div class="filter-main-board-header">
                    <div class="filter-main-board-title">过滤沪深主板指标参数设置</div>
                    <div class="filter-main-board-description">
                      过滤沪深主板：排除上海和深圳主板的股票，专注于其他市场板块
                    </div>
                  </div>
                  <!-- 过滤沪深主板参数说明表格 -->
                  <div class="filter-main-board-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>类型</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>过滤沪深主板</td>
                          <td>排除沪深主板股票</td>
                          <td>布尔值</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">过滤沪深主板</div>
                        <div class="table-cell">是否勾选</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">过滤沪深主板</span>
                        </div>
                        <div class="table-cell">
                          <input type="checkbox" v-model="filterMainBoardChecked" @click.stop @focus.stop> 勾选
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetFilterMainBoardSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyFilterMainBoardSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 过滤ST -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'filter-st' }"
                     @click.stop="openSubMenu('filter-st')">
                  <div class="submenu-content">
                    <i class="fas fa-exclamation-triangle text-danger"></i>
                    <span>过滤ST</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'filter-st' }"></i>
                </div>
                
                <!-- 过滤ST设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'filter-st'">
                  <!-- 过滤ST参数说明表头 -->
                  <div class="filter-st-header">
                    <div class="filter-st-title">过滤ST指标参数设置</div>
                    <div class="filter-st-description">
                      过滤ST：排除特别处理股票，避免投资风险较高的股票
                    </div>
                  </div>
                  <!-- 过滤ST参数说明表格 -->
                  <div class="filter-st-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>类型</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>过滤ST</td>
                          <td>排除特别处理股票</td>
                          <td>布尔值</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">过滤ST</div>
                        <div class="table-cell">是否勾选</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">过滤ST</span>
                        </div>
                        <div class="table-cell">
                          <input type="checkbox" v-model="filterStChecked" @click.stop @focus.stop> 勾选
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetFilterStSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyFilterStSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 过滤*ST -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'filter-star-st' }"
                     @click.stop="openSubMenu('filter-star-st')">
                  <div class="submenu-content">
                    <i class="fas fa-exclamation-circle text-danger"></i>
                    <span>过滤*ST</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'filter-star-st' }"></i>
                </div>
                
                <!-- 过滤*ST设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'filter-star-st'">
                  <!-- 过滤*ST参数说明表头 -->
                  <div class="filter-star-st-header">
                    <div class="filter-star-st-title">过滤*ST指标参数设置</div>
                    <div class="filter-star-st-description">
                      过滤*ST：排除特别处理且存在退市风险的股票，避免投资高风险股票
                    </div>
                  </div>
                  <!-- 过滤*ST参数说明表格 -->
                  <div class="filter-star-st-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>类型</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>过滤*ST</td>
                          <td>排除特别处理且存在退市风险的股票</td>
                          <td>布尔值</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">过滤*ST</div>
                        <div class="table-cell">是否勾选</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">过滤*ST</span>
                        </div>
                        <div class="table-cell">
                          <input type="checkbox" v-model="filterStarStChecked" @click.stop @focus.stop> 勾选
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetFilterStarStSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyFilterStarStSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 过滤停牌 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'filter-suspension' }"
                     @click.stop="openSubMenu('filter-suspension')">
                  <div class="submenu-content">
                    <i class="fas fa-pause text-warning"></i>
                    <span>过滤停牌</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'filter-suspension' }"></i>
                </div>
                
                <!-- 过滤停牌设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'filter-suspension'">
                  <!-- 过滤停牌参数说明表头 -->
                  <div class="filter-suspension-header">
                    <div class="filter-suspension-title">过滤停牌指标参数设置</div>
                    <div class="filter-suspension-description">
                      过滤停牌：排除暂停交易的股票，确保选股结果中的股票可以正常交易
                    </div>
                  </div>
                  <!-- 过滤停牌参数说明表格 -->
                  <div class="filter-suspension-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>类型</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>过滤停牌</td>
                          <td>排除暂停交易的股票</td>
                          <td>布尔值</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">过滤停牌</div>
                        <div class="table-cell">是否勾选</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">过滤停牌</span>
                        </div>
                        <div class="table-cell">
                          <input type="checkbox" v-model="filterSuspensionChecked" @click.stop @focus.stop> 勾选
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetFilterSuspensionSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyFilterSuspensionSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 过滤科创板 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'filter-star-market' }"
                     @click.stop="openSubMenu('filter-star-market')">
                  <div class="submenu-content">
                    <i class="fas fa-rocket text-info"></i>
                    <span>过滤科创板</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'filter-star-market' }"></i>
                </div>
                
                <!-- 过滤科创板设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'filter-star-market'">
                  <!-- 过滤科创板参数说明表头 -->
                  <div class="filter-star-market-header">
                    <div class="filter-star-market-title">过滤科创板指标参数设置</div>
                    <div class="filter-star-market-description">
                      过滤科创板：排除上海证券交易所科创板的股票，专注于其他市场板块
                    </div>
                  </div>
                  <!-- 过滤科创板参数说明表格 -->
                  <div class="filter-star-market-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>类型</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>过滤科创板</td>
                          <td>排除科创板股票</td>
                          <td>布尔值</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">过滤科创板</div>
                        <div class="table-cell">是否勾选</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">过滤科创板</span>
                        </div>
                        <div class="table-cell">
                          <input type="checkbox" v-model="filterStarMarketChecked" @click.stop @focus.stop> 勾选
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetFilterStarMarketSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyFilterStarMarketSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 过滤创业板 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'filter-growth-board' }"
                     @click.stop="openSubMenu('filter-growth-board')">
                  <div class="submenu-content">
                    <i class="fas fa-seedling text-success"></i>
                    <span>过滤创业板</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'filter-growth-board' }"></i>
                </div>
                
                <!-- 过滤创业板设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'filter-growth-board'">
                  <!-- 过滤创业板参数说明表头 -->
                  <div class="filter-growth-board-header">
                    <div class="filter-growth-board-title">过滤创业板指标参数设置</div>
                    <div class="filter-growth-board-description">
                      过滤创业板：排除深圳证券交易所创业板的股票，专注于其他市场板块
                    </div>
                  </div>
                  <!-- 过滤创业板参数说明表格 -->
                  <div class="filter-growth-board-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>类型</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>过滤创业板</td>
                          <td>排除创业板股票</td>
                          <td>布尔值</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">过滤创业板</div>
                        <div class="table-cell">是否勾选</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">过滤创业板</span>
                        </div>
                        <div class="table-cell">
                          <input type="checkbox" v-model="filterGrowthBoardChecked" @click.stop @focus.stop> 勾选
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetFilterGrowthBoardSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyFilterGrowthBoardSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 过滤退市 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'filter-delisting' }"
                     @click.stop="openSubMenu('filter-delisting')">
                  <div class="submenu-content">
                    <i class="fas fa-times-circle text-danger"></i>
                    <span>过滤退市</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'filter-delisting' }"></i>
                </div>
                
                <!-- 过滤退市设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'filter-delisting'">
                  <!-- 过滤退市参数说明表头 -->
                  <div class="filter-delisting-header">
                    <div class="filter-delisting-title">过滤退市指标参数设置</div>
                    <div class="filter-delisting-description">
                      过滤退市：排除已退市或存在退市风险的股票，避免投资无法交易的股票
                    </div>
                  </div>
                  <!-- 过滤退市参数说明表格 -->
                  <div class="filter-delisting-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>类型</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>过滤退市</td>
                          <td>排除已退市或存在退市风险的股票</td>
                          <td>布尔值</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">过滤退市</div>
                        <div class="table-cell">是否勾选</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">过滤退市</span>
                        </div>
                        <div class="table-cell">
                          <input type="checkbox" v-model="filterDelistingChecked" @click.stop @focus.stop> 勾选
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetFilterDelistingSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyFilterDelistingSettings">应用设置</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
  
            <!-- 财务指标 -->
            <div class="menu-item" :class="{ active: activeMenu === 'financial' }" @click="toggleMenu('financial')">
              <div class="menu-item-header">
                <i class="fas fa-file-invoice-dollar"></i>
                <span>财务指标</span>
                <span class="count">9</span>
                <i class="fas fa-chevron-right arrow" :class="{ expanded: activeMenu === 'financial' }"></i>
              </div>
              <!-- 二级菜单 -->
              <div class="submenu financial-submenu" v-if="activeMenu === 'financial'">
                <!-- ROA -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'roa' }"
                     @click.stop="openSubMenu('roa')">
                  <div class="submenu-content">
                    <i class="fas fa-percentage text-primary"></i>
                    <span>ROA</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'roa' }"></i>
                </div>
                
                <!-- ROA设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'roa'">
                  <!-- ROA参数说明表头 -->
                  <div class="roa-header">
                    <div class="roa-title">ROA财务指标参数设置</div>
                    <div class="roa-description">
                      ROA：总资产收益率，反映公司利用总资产创造利润的能力
                    </div>
                  </div>
                  <!-- ROA参数说明表格 -->
                  <div class="roa-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>ROA</td>
                          <td>总资产收益率</td>
                          <td>%</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">ROA</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">ROA</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="roaCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="roaCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetRoaSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyRoaSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- ROE -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'roe' }"
                     @click.stop="openSubMenu('roe')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-line text-success"></i>
                    <span>ROE</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'roe' }"></i>
                </div>
                
                <!-- ROE设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'roe'">
                  <!-- ROE参数说明表头 -->
                  <div class="roe-header">
                    <div class="roe-title">ROE财务指标参数设置</div>
                    <div class="roe-description">
                      ROE：净资产收益率，反映公司利用股东权益创造利润的能力
                    </div>
                  </div>
                  <!-- ROE参数说明表格 -->
                  <div class="roe-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>ROE</td>
                          <td>净资产收益率</td>
                          <td>%</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">ROE</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">ROE</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="roeCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="roeCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetRoeSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyRoeSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 毛利率 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'gross-margin' }"
                     @click.stop="openSubMenu('gross-margin')">
                  <div class="submenu-content">
                    <i class="fas fa-coins text-warning"></i>
                    <span>毛利率</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'gross-margin' }"></i>
                </div>
                
                <!-- 毛利率设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'gross-margin'">
                  <!-- 毛利率参数说明表头 -->
                  <div class="gross-margin-header">
                    <div class="gross-margin-title">毛利率财务指标参数设置</div>
                    <div class="gross-margin-description">
                      毛利率：毛利润与营业收入的比值，反映公司产品的盈利能力
                    </div>
                  </div>
                  <!-- 毛利率参数说明表格 -->
                  <div class="gross-margin-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>毛利率</td>
                          <td>毛利润与营业收入比值</td>
                          <td>%</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">毛利率</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">毛利率</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="grossMarginCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="grossMarginCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetGrossMarginSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyGrossMarginSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 净利率 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'net-margin' }"
                     @click.stop="openSubMenu('net-margin')">
                  <div class="submenu-content">
                    <i class="fas fa-dollar-sign text-success"></i>
                    <span>净利率</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'net-margin' }"></i>
                </div>
                
                <!-- 净利率设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'net-margin'">
                  <!-- 净利率参数说明表头 -->
                  <div class="net-margin-header">
                    <div class="net-margin-title">净利率财务指标参数设置</div>
                    <div class="net-margin-description">
                      净利率：净利润与营业收入的比值，反映公司整体盈利能力
                    </div>
                  </div>
                  <!-- 净利率参数说明表格 -->
                  <div class="net-margin-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>净利率</td>
                          <td>净利润与营业收入比值</td>
                          <td>%</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">净利率</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">净利率</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="netMarginCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="netMarginCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetNetMarginSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyNetMarginSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 营收增长率 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'revenue-growth' }"
                     @click.stop="openSubMenu('revenue-growth')">
                  <div class="submenu-content">
                    <i class="fas fa-arrow-up text-success"></i>
                    <span>营收增长率</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'revenue-growth' }"></i>
                </div>
                
                <!-- 营收增长率设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'revenue-growth'">
                  <!-- 营收增长率参数说明表头 -->
                  <div class="revenue-growth-header">
                    <div class="revenue-growth-title">营收增长率财务指标参数设置</div>
                    <div class="revenue-growth-description">
                      营收增长率：营业收入同比增长率，反映公司业务扩张速度
                    </div>
                  </div>
                  <!-- 营收增长率参数说明表格 -->
                  <div class="revenue-growth-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>营收增长率</td>
                          <td>营业收入同比增长率</td>
                          <td>%</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">营收增长率</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">营收增长率</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="revenueGrowthCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="revenueGrowthCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetRevenueGrowthSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyRevenueGrowthSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 净利润增长率 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'profit-growth' }"
                     @click.stop="openSubMenu('profit-growth')">
                  <div class="submenu-content">
                    <i class="fas fa-chart-area text-info"></i>
                    <span>净利润增长率</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'profit-growth' }"></i>
                </div>
                
                <!-- 净利润增长率设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'profit-growth'">
                  <!-- 净利润增长率参数说明表头 -->
                  <div class="profit-growth-header">
                    <div class="profit-growth-title">净利润增长率财务指标参数设置</div>
                    <div class="profit-growth-description">
                      净利润增长率：净利润同比增长率，反映公司盈利能力提升速度
                    </div>
                  </div>
                  <!-- 净利润增长率参数说明表格 -->
                  <div class="profit-growth-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>净利润增长率</td>
                          <td>净利润同比增长率</td>
                          <td>%</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">净利润增长率</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">净利润增长率</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="profitGrowthCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="profitGrowthCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetProfitGrowthSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyProfitGrowthSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 动态市盈率 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'dynamic-pe' }"
                     @click.stop="openSubMenu('dynamic-pe')">
                  <div class="submenu-content">
                    <i class="fas fa-clock text-warning"></i>
                    <span>动态市盈率</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'dynamic-pe' }"></i>
                </div>
                
                <!-- 动态市盈率设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'dynamic-pe'">
                  <!-- 动态市盈率参数说明表头 -->
                  <div class="dynamic-pe-header">
                    <div class="dynamic-pe-title">动态市盈率财务指标参数设置</div>
                    <div class="dynamic-pe-description">
                      动态市盈率：股价与预期每股收益的比值，反映股票估值水平
                    </div>
                  </div>
                  <!-- 动态市盈率参数说明表格 -->
                  <div class="dynamic-pe-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>动态市盈率</td>
                          <td>股价与预期每股收益比值</td>
                          <td>倍</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">动态市盈率</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">动态市盈率</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="dynamicPeCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="dynamicPeCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetDynamicPeSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyDynamicPeSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 市净率 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'pb-ratio' }"
                     @click.stop="openSubMenu('pb-ratio')">
                  <div class="submenu-content">
                    <i class="fas fa-balance-scale text-primary"></i>
                    <span>市净率</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'pb-ratio' }"></i>
                </div>
                
                <!-- 市净率设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'pb-ratio'">
                  <!-- 市净率参数说明表头 -->
                  <div class="pb-ratio-header">
                    <div class="pb-ratio-title">市净率财务指标参数设置</div>
                    <div class="pb-ratio-description">
                      市净率：股价与每股净资产的比值，反映股票相对净资产的价值
                    </div>
                  </div>
                  <!-- 市净率参数说明表格 -->
                  <div class="pb-ratio-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>市净率</td>
                          <td>股价与每股净资产比值</td>
                          <td>倍</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">市净率</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">市净率</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="pbRatioCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="pbRatioCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetPbRatioSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyPbRatioSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 市销率 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'ps-ratio' }"
                     @click.stop="openSubMenu('ps-ratio')">
                  <div class="submenu-content">
                    <i class="fas fa-shopping-cart text-info"></i>
                    <span>市销率</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'ps-ratio' }"></i>
                </div>
                
                <!-- 市销率设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'ps-ratio'">
                  <!-- 市销率参数说明表头 -->
                  <div class="ps-ratio-header">
                    <div class="ps-ratio-title">市销率财务指标参数设置</div>
                    <div class="ps-ratio-description">
                      市销率：股价与每股营业收入的比值，反映股票相对营业收入的价值
                    </div>
                  </div>
                  <!-- 市销率参数说明表格 -->
                  <div class="ps-ratio-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>市销率</td>
                          <td>股价与每股营业收入比值</td>
                          <td>倍</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">市销率</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">市销率</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="psRatioCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="psRatioCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetPsRatioSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyPsRatioSettings">应用设置</button>
                    </div>
                  </div>
                </div>
  
                <!-- 静态市盈率 -->
                <div class="submenu-item" 
                     :class="{ active: activeSubMenu === 'static-pe' }"
                     @click.stop="openSubMenu('static-pe')">
                  <div class="submenu-content">
                    <i class="fas fa-stop-circle text-secondary"></i>
                    <span>静态市盈率</span>
                  </div>
                  <i class="fas fa-chevron-right" :class="{ expanded: activeSubMenu === 'static-pe' }"></i>
                </div>
                
                <!-- 静态市盈率设置内容 -->
                <div class="price-settings" v-if="activeSubMenu === 'static-pe'">
                  <!-- 静态市盈率参数说明表头 -->
                  <div class="static-pe-header">
                    <div class="static-pe-title">静态市盈率财务指标参数设置</div>
                    <div class="static-pe-description">
                      静态市盈率：股价与历史每股收益的比值，反映股票历史估值水平
                    </div>
                  </div>
                  <!-- 静态市盈率参数说明表格 -->
                  <div class="static-pe-param-table">
                    <table class="param-table">
                      <thead>
                        <tr>
                          <th>参数</th>
                          <th>说明</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>静态市盈率</td>
                          <td>股价与历史每股收益比值</td>
                          <td>倍</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="param-content">
                    <div class="param-table">
                      <div class="table-row table-header">
                        <div class="table-cell">静态市盈率</div>
                        <div class="table-cell">比较符</div>
                        <div class="table-cell">值</div>
                      </div>
                      <div class="table-row">
                        <div class="table-cell">
                          <span class="price-label">静态市盈率</span>
                        </div>
                        <div class="table-cell">
                          <select v-model="staticPeCompare" class="form-select" @click.stop @focus.stop>
                            <option value="大于">大于</option>
                            <option value="小于">小于</option>
                            <option value="大于等于">大于等于</option>
                            <option value="小于等于">小于等于</option>
                            <option value="等于">等于</option>
                          </select>
                        </div>
                        <div class="table-cell">
                          <input type="number" v-model="staticPeCustomValue" class="form-control" step="0.01" @click.stop @focus.stop>
                        </div>
                      </div>
                    </div>
                    <div class="action-buttons">
                      <button class="btn-reset" @click.stop="resetStaticPeSettings">重置</button>
                      <button class="btn-apply" @click.stop="applyStaticPeSettings">应用设置</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
        </div>
  
        <!-- 右侧选股条件 -->
        <div class="conditions-container">
          <!-- 合并后的选股条件区域 -->
          <div class="filter-section">
            <div class="section-header">
              <h6 class="mb-0">选股条件</h6>
              <div class="header-actions">
                <button class="btn btn-sm btn-outline-danger" @click="clearAllConditions" v-if="selectedConditions.length > 0">
                  清除全部
                </button>
              </div>
            </div>
            <div class="filter-content">
              <div class="form-group">
                <label class="form-label">选股日期区间</label>
                <div class="date-range-container">
                  <div class="date-input-group">
                    <label class="date-label">开始日期</label>
                    <input type="date" v-model="stockSelectionStartDate" class="form-control" placeholder="年-月-日">
                  </div>
                  <div class="date-input-group">
                    <label class="date-label">结束日期</label>
                    <input type="date" v-model="stockSelectionEndDate" class="form-control" placeholder="年-月-日">
                  </div>
                </div>
              </div>
              
              <!-- 回测参数设置 -->
              <div class="form-group">
                <label class="form-label">回测参数设置</label>
                <div class="backtest-params-container">
                  <div class="param-input-group">
                    <label class="param-label">初始资金 (万元)</label>
                    <input type="number" v-model="initialCapital" class="form-control" 
                           placeholder="请输入初始资金" min="1" max="10000" step="1">
                  </div>
                  <div class="param-input-group">
                    <label class="param-label">数据频率</label>
                    <select v-model="dataFrequency" class="form-control">
                      <option value="daily">每日</option>
                      <option value="minute">分钟</option>
                      <option value="tick">tick</option>
                    </select>
                  </div>
                  <div class="param-input-group" v-if="dataFrequency === 'minute'">
                    <label class="param-label">分钟周期</label>
                    <select v-model="minuteInterval" class="form-control">
                      <option value="1">1分钟</option>
                      <option value="5">5分钟</option>
                      <option value="15">15分钟</option>
                      <option value="30">30分钟</option>
                      <option value="60">60分钟</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 选股条件列表 -->
            <div class="conditions-list">
              <div v-if="selectedConditions.length === 0" class="empty-conditions">
                <i class="fas fa-info-circle"></i>
                <span>暂无选股条件，请在左侧添加条件</span>
              </div>
              <div v-else class="condition-item" v-for="(condition, index) in selectedConditions" :key="condition.id">
                <div class="condition-content">
                  <div class="condition-title">{{ condition.title }}</div>
                  <div class="condition-details">{{ condition.details }}</div>
                </div>
                <div class="condition-actions">
                  <i class="fas fa-toggle-on condition-toggle" 
                     :class="{ 'text-muted': !condition.enabled }"
                     @click="toggleCondition(index)"
                     :title="condition.enabled ? '禁用条件' : '启用条件'"></i>
                  <i class="fas fa-trash condition-remove" 
                     @click="removeCondition(index)"
                     title="删除条件"></i>
                </div>
              </div>
            </div>
          </div>
  
          <!-- 运行回测按钮 - 在选股条件框外面 -->
          <div class="backtest-section">
            <button class="btn btn-success btn-run-backtest" @click="applyFilter">
              <i class="fas fa-chart-line"></i>
              运行回测
            </button>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { defineComponent, ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import StockFilter from './StockFilter.vue'
  
  export default defineComponent({
    name: 'MenuLayout',
    components: {
      StockFilter
    },
    setup() {
      const router = useRouter()
      const activeMenu = ref('')
      const activeSubMenu = ref('')
      const stockFilterRef = ref(null)
      const selectedConditions = ref([])
  
  
  
      // 筛选条件相关变量
      const stockSelectionStartDate = ref('2024-01-01')  // 默认值，将被API更新
      const stockSelectionEndDate = ref('2024-12-31')    // 默认值，将被API更新
      
      // 回测参数变量
      const initialCapital = ref(100) // 默认100万元
      const dataFrequency = ref('daily') // 默认每日
      const minuteInterval = ref('5') // 默认5分钟
  
      const marketIndices = [
        { label: '上证指数', value: 'sh' },
        { label: '深证指数', value: 'sz' },
        { label: '沪深300指数', value: 'hs300' }
      ]
  
      const sectorIndices = [
        { label: '交通运输', value: 'transport' },
        { label: '休闲服务', value: 'leisure' },
        { label: '传媒', value: 'media' },
        { label: '公用事业', value: 'utilities' },
        { label: '农林牧渔', value: 'agriculture' },
        { label: '化工', value: 'chemicals' },
        { label: '医药生物', value: 'pharmaceuticals' },
        { label: '商业贸易', value: 'commerce' },
        { label: '国防军工', value: 'defense' },
        { label: '家用电器', value: 'appliances' },
        { label: '建筑材料', value: 'building_materials' },
        { label: '建筑装饰', value: 'decoration' },
        { label: '房地产', value: 'real_estate' },
        { label: '有色金属', value: 'nonferrous_metals' },
        { label: '机械设备', value: 'machinery' },
        { label: '汽车', value: 'automotive' },
        { label: '电子', value: 'electronics' },
        { label: '电气设备', value: 'electrical_equipment' },
        { label: '纺织服装', value: 'textiles' },
        { label: '综合', value: 'comprehensive' },
        { label: '计算机', value: 'computer' },
        { label: '轻工制造', value: 'light_industry' },
        { label: '通信', value: 'telecommunications' },
        { label: '采掘', value: 'mining' },
        { label: '钢铁', value: 'steel' },
        { label: '银行', value: 'banking' },
        { label: '非银金融', value: 'non_banking_finance' },
        { label: '食品饮料', value: 'food_beverage' }
      ]
  
      const periods = [
        { label: '日', value: 'day' },
        { label: '周', value: 'week' },
        { label: '月', value: 'month' }
      ]
  
      const selectedIndex = ref('sh')
      const selectedPeriod = ref('day')
      const maSettings = reactive({
        short: 5,
        long: 60
      })
  
      // MA金叉死叉设置
      const maGoldenCrossChecked = ref(false)
      const maDeathCrossChecked = ref(false)
  
      // MACD设置
      const selectedMacdIndex = ref('sh')
      const selectedMacdPeriod = ref('day')
      const macdSettings = reactive({
        dif: 26,
        dea: 12,
        macd: 9
      })
      
      // 个股择时MACD设置
      const timingMacdSettings = reactive({
        dif: 26,
        dea: 12,
        macd: 9
      })
      
      // 个股择时MACD目标值
      const difTargetValue = ref(0)
      const deaTargetValue = ref(0)
      const macdTargetValue = ref(0)
      
      // 个股择时KDJ设置
      const timingKdjSettings = reactive({
        k: 9,
        d: 3,
        j: 3
      })
      
      // 个股择时KDJ目标值
      const kdjKTargetValue = ref(0)
      const kdjDTargetValue = ref(0)
      const kdjJTargetValue = ref(0)
      
      // 个股择时RSI设置
      const timingRsiSettings = reactive({
        period: 14
      })
      
      // 个股择时RSI目标值
      const rsiTargetValue = ref(0)
      
      // 个股择时BOLL设置
      const timingBollSettings = reactive({
        period: 20,
        multiplier: 2
      })
      
      // 个股择时BOLL目标值
      const bollTargetValue = ref(0)
      
      // 个股择时CR设置
      const timingCrSettings = reactive({
        period: 26
      })
      
      // 个股择时CR目标值
      const crTargetValue = ref(0)
      
      // 个股择时TRIX设置
      const timingTrixSettings = reactive({
        period: 12
      })
      
      // 个股择时TRIX目标值
      const trixTargetValue = ref(0)
  
      // MACD金叉死叉设置
      const macdGoldenCrossChecked = ref(false)
      const macdDeathCrossChecked = ref(false)
  
      // KDJ设置
      const selectedKdjIndex = ref('sh')
      const selectedKdjPeriod = ref('day')
      const kdjSettings = reactive({
        k: 9,
        d: 3,
        j: 3
      })
  
      // KDJ金叉死叉设置
      const kdjGoldenCrossChecked = ref(false)
      const kdjDeathCrossChecked = ref(false)
  
      // 板块择时相关变量
      const sectorSearchText = ref('')
      const filteredSectorOptions = ref([])
      
      // 板块择时金叉死叉设置
      const sectorMaGoldenCrossChecked = ref(false)
      const sectorMaDeathCrossChecked = ref(false)
      const sectorMacdGoldenCrossChecked = ref(false)
      const sectorMacdDeathCrossChecked = ref(false)
      const sectorKdjGoldenCrossChecked = ref(false)
      const sectorKdjDeathCrossChecked = ref(false)
  
            // 板块择时 - MA设置
      const selectedSectorIndex = ref('transport')
      const selectedSectorPeriod = ref('day')
      const sectorSettings = reactive({
        short: 5,
        long: 60
      })
  
      // 板块择时 - MACD设置
      const selectedSectorMacdIndex = ref('transport')
      const selectedSectorMacdPeriod = ref('day')
      const sectorMacdSettings = reactive({
        dif: 26,
        dea: 12,
        macd: 9
      })
  
      // 板块择时 - KDJ设置
      const selectedSectorKdjIndex = ref('transport')
      const selectedSectorKdjPeriod = ref('day')
      const sectorKdjSettings = reactive({
        k: 5,
        d: 60,
        j: 60
      })
  
            // 股票价格相关变量
      // 开盘价
      const openPriceCompare = ref('大于')
      const openPriceIndicator = ref('')

      // 收盘价
      const closePriceCompare = ref('大于')
      const closePriceIndicator = ref('')

      // 最高价
      const highPriceCompare = ref('大于')
      const highPriceIndicator = ref('')

      // 最低价
      const lowPriceCompare = ref('大于')
      const lowPriceIndicator = ref('')

      // 昨日收盘价
      const prevClosePriceCompare = ref('大于')
      const prevClosePriceIndicator = ref('')

      // 日成交均价
      const avgPriceCompare = ref('大于')
      const avgPriceIndicator = ref('')
  
      // 新增菜单相关变量
      // 涨幅
      const changeRateType = ref('single') // 'single' or 'range'
      const changeRateValue = ref('') // 单一涨幅百分比
      const changeRateRangeValue = ref('') // 区间涨幅百分比
      const changeRateRangeDays = ref('') // 区间天数
      const changeRateRangeCustomValue = ref('') // 区间涨幅自定义百分比
      const changeRateRangeDate = ref('') // 几日
      const changeRateCompare = ref('大于')
  
      // 量比
      const volumeRatioCompare = ref('大于')
      const volumeRatioIndicator = ref('量比')
      const volumeRatioCustomValue = ref('')
  
      // 成交额
      const turnoverCompare = ref('大于')
      const turnoverIndicator = ref('成交额')
      const turnoverCustomValue = ref('')
  
      // 换手率
      const turnoverRateCompare = ref('大于')
      const turnoverRateIndicator = ref('换手率')
      const turnoverRateCustomValue = ref('')
  
      // 市值
      const marketValueCompare = ref('大于')
      const marketValueIndicator = ref('市值')
      const marketValueCustomValue = ref('')
  
      // 成交量
      const volumeCompare = ref('大于')
      const volumeIndicator = ref('成交量')
      const volumeCustomValue = ref('')
  
      // 资金净流入
      const netInflowCompare = ref('大于')
      const netInflowAmount = ref(0)
  
      // 公告类相关变量
      // 股东减持
      const shareholderReductionCompare = ref('大于')
      const shareholderReductionAmount = ref(0)
      const shareholderReductionChecked = ref(false)
  
      // 股东增持
      const shareholderIncreaseCompare = ref('大于')
      const shareholderIncreaseAmount = ref(0)
      const shareholderIncreaseChecked = ref(false)
  
      // 股东分红
      const shareholderDividendCompare = ref('大于')
      const shareholderDividendAmount = ref(0)
      const shareholderDividendChecked = ref(false)
  
      // 违规问询函
      const violationInquiryCompare = ref('大于')
      const violationInquiryAmount = ref(0)
      const violationInquiryChecked = ref(false)
  
      // 业绩预告
      const performanceForecastCompare = ref('大于')
      const performanceForecastAmount = ref(0)
      const netProfitCompare = ref('大于')
      const netProfitAmount = ref(0)
      const selectedSignal = ref('profit_yoy') // 业绩预告信号
  
      // 个股择时指标信号选择
      const timingSelectedSignal = ref('') // 个股择时指标信号
  
      // 业绩公告
      const performanceAnnouncementCompare = ref('大于')
      const performanceAnnouncementAmount = ref(0)
      const netProfitAnnouncementCompare = ref('大于')
      const netProfitAnnouncementAmount = ref(0)
      const selectedSignalAnnouncement = ref('announcement_profit_yoy') // 业绩公告信号
  
      // 过滤项相关变量
      // 过滤新上市
      const filterNewListingChecked = ref(false)
      
      // 过滤北交所
      const filterBeijingChecked = ref(false)
      
      // 过滤沪深主板
      const filterMainBoardChecked = ref(false)
      
      // 过滤ST
      const filterStChecked = ref(false)
      
      // 过滤*ST
      const filterStarStChecked = ref(false)
      
      // 过滤停牌
      const filterSuspensionChecked = ref(false)
      
      // 过滤科创板
      const filterStarMarketChecked = ref(false)
      
      // 过滤创业板
      const filterGrowthBoardChecked = ref(false)
      
      // 过滤退市
      const filterDelistingChecked = ref(false)
  
      // 财务指标相关变量
      // ROA
      const roaCompare = ref('大于')
      const roaCustomValue = ref('')
      
      // ROE
      const roeCompare = ref('大于')
      const roeCustomValue = ref('')
      
      // 毛利率
      const grossMarginCompare = ref('大于')
      const grossMarginCustomValue = ref('')
      
      // 净利率
      const netMarginCompare = ref('大于')
      const netMarginCustomValue = ref('')
      
      // 营收增长率
      const revenueGrowthCompare = ref('大于')
      const revenueGrowthCustomValue = ref('')
      
      // 净利润增长率
      const profitGrowthCompare = ref('大于')
      const profitGrowthCustomValue = ref('')
      
      // 动态市盈率
      const dynamicPeCompare = ref('大于')
      const dynamicPeCustomValue = ref('')
      
      // 市净率
      const pbRatioCompare = ref('大于')
      const pbRatioCustomValue = ref('')
      
      // 市销率
      const psRatioCompare = ref('大于')
      const psRatioCustomValue = ref('')
      
      // 静态市盈率
      const staticPeCompare = ref('大于')
      const staticPeCustomValue = ref('')
  
      const toggleMenu = (menu) => {
        activeMenu.value = activeMenu.value === menu ? '' : menu
        if (!activeMenu.value) {
          activeSubMenu.value = ''
        }
      }
  
      const openSubMenu = (subMenu) => {
        // 如果点击的是当前打开的子菜单，则关闭它
        if (activeSubMenu.value === subMenu) {
          activeSubMenu.value = ''
        } else {
          // 否则打开新点击的子菜单
          activeSubMenu.value = subMenu
        }
      }
  
            const removeCondition = (index) => {
        // 直接删除条件，无需弹窗
        selectedConditions.value.splice(index, 1)
        console.log('条件已删除', selectedConditions.value[index])
      }
  
      const clearAllConditions = () => {
        selectedConditions.value = []
        console.log('所有条件已清除')
      }
  
      const toggleCondition = (index) => {
        // 不再切换启用状态，直接不做任何操作（或可选：彻底移除该功能）
        // 若要彻底移除按钮，需在模板中删除对应的开关按钮
      }
  
      const resetMaSettings = () => {
        selectedIndex.value = 'sh'
        selectedPeriod.value = 'day'
        maSettings.short = 5
        maSettings.long = 60
        maGoldenCrossChecked.value = false
        maDeathCrossChecked.value = false
      }
  
      const applyMaSettings = () => {
        // 获取市场指数名称
        const indexName = marketIndices.find(item => item.value === selectedIndex.value)?.label || selectedIndex.value
        const periodName = periods.find(item => item.value === selectedPeriod.value)?.label || selectedPeriod.value
        
        // 构建条件标题和详情
        let title = `大盘择时 - MA指标`
        let details = `${indexName} ${periodName}周期 MA(${maSettings.short},${maSettings.long})`
        
        // 添加金叉死叉信息
        const signals = []
        if (maGoldenCrossChecked.value) signals.push('金叉')
        if (maDeathCrossChecked.value) signals.push('死叉')
        if (signals.length > 0) {
          details += ` ${signals.join('、')}信号`
        }
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(), // 生成唯一ID
          type: 'market_ma',
          title: title,
          details: details,
          enabled: true,
          config: {
            index: selectedIndex.value,
            period: selectedPeriod.value,
            ma: { ...maSettings },
            goldenCross: maGoldenCrossChecked.value,
            deathCross: maDeathCrossChecked.value
          }
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        // 显示成功提示
        console.log('MA指标条件已添加到选股条件', condition)
        
        // 删除弹窗提示
        // alert('MA指标设置已成功添加到选股条件！')
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      const resetMacdSettings = () => {
        selectedMacdIndex.value = 'sh'
        selectedMacdPeriod.value = 'day'
        macdSettings.dif = 26
        macdSettings.dea = 12
        macdSettings.macd = 9
        macdGoldenCrossChecked.value = false
        macdDeathCrossChecked.value = false
      }
  
      const applyMacdSettings = () => {
        // 获取市场指数名称
        const indexName = marketIndices.find(item => item.value === selectedMacdIndex.value)?.label || selectedMacdIndex.value
        const periodName = periods.find(item => item.value === selectedMacdPeriod.value)?.label || selectedMacdPeriod.value
        
        // 构建条件标题和详情
        let title = `大盘择时 - MACD指标`
        let details = `${indexName} ${periodName}周期 MACD(${macdSettings.dif},${macdSettings.dea},${macdSettings.macd})`
        
        // 添加金叉死叉信息
        const signals = []
        if (macdGoldenCrossChecked.value) signals.push('金叉')
        if (macdDeathCrossChecked.value) signals.push('死叉')
        if (signals.length > 0) {
          details += ` ${signals.join('、')}信号`
        }
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'market_macd',
          title: title,
          details: details,
          enabled: true,
          config: {
            index: selectedMacdIndex.value,
            period: selectedMacdPeriod.value,
            settings: { ...macdSettings },
            goldenCross: macdGoldenCrossChecked.value,
            deathCross: macdDeathCrossChecked.value
          }
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('MACD指标条件已添加到选股条件', condition)
        // 删除弹窗提示
        // alert('MACD指标设置已成功添加到选股条件！')
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      const resetKdjSettings = () => {
        selectedKdjIndex.value = 'sh'
        selectedKdjPeriod.value = 'day'
        kdjSettings.k = 9
        kdjSettings.d = 3
        kdjSettings.j = 3
        kdjGoldenCrossChecked.value = false
        kdjDeathCrossChecked.value = false
      }
  
      const applyKdjSettings = () => {
        // 获取市场指数名称
        const indexName = marketIndices.find(item => item.value === selectedKdjIndex.value)?.label || selectedKdjIndex.value
        const periodName = periods.find(item => item.value === selectedKdjPeriod.value)?.label || selectedKdjPeriod.value
        
        // 构建条件标题和详情
        let title = `大盘择时 - KDJ指标`
        let details = `${indexName} ${periodName}周期 KDJ(${kdjSettings.k},${kdjSettings.d},${kdjSettings.j})`
        
        // 添加金叉死叉信息
        const signals = []
        if (kdjGoldenCrossChecked.value) signals.push('金叉')
        if (kdjDeathCrossChecked.value) signals.push('死叉')
        if (signals.length > 0) {
          details += ` ${signals.join('、')}信号`
        }
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'market_kdj',
          title: title,
          details: details,
          enabled: true,
          config: {
            index: selectedKdjIndex.value,
            period: selectedKdjPeriod.value,
            settings: { ...kdjSettings },
            goldenCross: kdjGoldenCrossChecked.value,
            deathCross: kdjDeathCrossChecked.value
          }
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('KDJ指标条件已添加到选股条件', condition)
        // 删除弹窗提示
        // alert('KDJ指标设置已成功添加到选股条件！')
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      const resetSectorSettings = () => {
        selectedSectorIndex.value = 'transport'
        selectedSectorPeriod.value = 'day'
        sectorSettings.short = 5
        sectorSettings.long = 60
        sectorMaGoldenCrossChecked.value = false
        sectorMaDeathCrossChecked.value = false
      }
  
      const applySectorSettings = () => {
        // 获取板块指数名称
        const indexName = sectorIndices.find(item => item.value === selectedSectorIndex.value)?.label || selectedSectorIndex.value
        const periodName = periods.find(item => item.value === selectedSectorPeriod.value)?.label || selectedSectorPeriod.value
        
        // 构建条件标题和详情
        let title = `板块择时 - MA指标`
        let details = `${indexName} ${periodName}周期 MA(${sectorSettings.short},${sectorSettings.long})`
        
        // 添加金叉死叉信息
        const signals = []
        if (sectorMaGoldenCrossChecked.value) signals.push('金叉')
        if (sectorMaDeathCrossChecked.value) signals.push('死叉')
        if (signals.length > 0) {
          details += ` ${signals.join('、')}信号`
        }
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'sector_ma',
          title: title,
          details: details,
          enabled: true,
          config: {
            index: selectedSectorIndex.value,
            period: selectedSectorPeriod.value,
            settings: { ...sectorSettings },
            goldenCross: sectorMaGoldenCrossChecked.value,
            deathCross: sectorMaDeathCrossChecked.value
          }
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('板块MA指标条件已添加到选股条件', condition)
        // 删除弹窗提示
        // alert('板块MA指标设置已成功添加到选股条件！')
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      const resetSectorMacdSettings = () => {
        selectedSectorMacdIndex.value = 'transport'
        selectedSectorMacdPeriod.value = 'day'
        sectorMacdSettings.dif = 26
        sectorMacdSettings.dea = 12
        sectorMacdSettings.macd = 9
        sectorMacdGoldenCrossChecked.value = false
        sectorMacdDeathCrossChecked.value = false
      }
  
      const applySectorMacdSettings = () => {
        // 获取板块指数名称
        const indexName = sectorIndices.find(item => item.value === selectedSectorMacdIndex.value)?.label || selectedSectorMacdIndex.value
        const periodName = periods.find(item => item.value === selectedSectorMacdPeriod.value)?.label || selectedSectorMacdPeriod.value
        
        // 构建条件标题和详情
        let title = `板块择时 - MACD指标`
        let details = `${indexName} ${periodName}周期 MACD(${sectorMacdSettings.dif},${sectorMacdSettings.dea},${sectorMacdSettings.macd})`
        
        // 添加金叉死叉信息
        const signals = []
        if (sectorMacdGoldenCrossChecked.value) signals.push('金叉')
        if (sectorMacdDeathCrossChecked.value) signals.push('死叉')
        if (signals.length > 0) {
          details += ` ${signals.join('、')}信号`
        }
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'sector_macd',
          title: title,
          details: details,
          enabled: true,
          config: {
            index: selectedSectorMacdIndex.value,
            period: selectedSectorMacdPeriod.value,
            settings: { ...sectorMacdSettings },
            goldenCross: sectorMacdGoldenCrossChecked.value,
            deathCross: sectorMacdDeathCrossChecked.value
          }
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('板块MACD指标条件已添加到选股条件', condition)
        // 删除弹窗提示
        // alert('板块MACD指标设置已成功添加到选股条件！')
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      const resetSectorKdjSettings = () => {
        selectedSectorKdjIndex.value = 'transport'
        selectedSectorKdjPeriod.value = 'day'
        sectorKdjSettings.k = 9
        sectorKdjSettings.d = 3
        sectorKdjSettings.j = 3
        sectorKdjGoldenCrossChecked.value = false
        sectorKdjDeathCrossChecked.value = false
      }
  
      const applySectorKdjSettings = () => {
        // 获取板块指数名称
        const indexName = sectorIndices.find(item => item.value === selectedSectorKdjIndex.value)?.label || selectedSectorKdjIndex.value
        const periodName = periods.find(item => item.value === selectedSectorKdjPeriod.value)?.label || selectedSectorKdjPeriod.value
        
        // 构建条件标题和详情
        let title = `板块择时 - KDJ指标`
        let details = `${indexName} ${periodName}周期 KDJ(${sectorKdjSettings.k},${sectorKdjSettings.d},${sectorKdjSettings.j})`
        
        // 添加金叉死叉信息
        const signals = []
        if (sectorKdjGoldenCrossChecked.value) signals.push('金叉')
        if (sectorKdjDeathCrossChecked.value) signals.push('死叉')
        if (signals.length > 0) {
          details += ` ${signals.join('、')}信号`
        }
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'sector_kdj',
          title: title,
          details: details,
          enabled: true,
          config: {
            index: selectedSectorKdjIndex.value,
            period: selectedSectorKdjPeriod.value,
            settings: { ...sectorKdjSettings },
            goldenCross: sectorKdjGoldenCrossChecked.value,
            deathCross: sectorKdjDeathCrossChecked.value
          }
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('板块KDJ指标条件已添加到选股条件', condition)
        // 删除弹窗提示
        // alert('板块KDJ指标设置已成功添加到选股条件！')
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      const resetAll = () => {
        resetMaSettings()
        resetMacdSettings()
        resetKdjSettings()
        resetSectorSettings()
        resetSectorMacdSettings()
        resetSectorKdjSettings()
        resetFilterNewListingSettings()
        resetFilterBeijingSettings()
        resetFilterMainBoardSettings()
        resetFilterStSettings()
        resetFilterStarStSettings()
        resetFilterSuspensionSettings()
        resetFilterStarMarketSettings()
        resetFilterGrowthBoardSettings()
        resetFilterDelistingSettings()
        resetRoaSettings()
        resetRoeSettings()
        resetGrossMarginSettings()
        resetNetMarginSettings()
        resetRevenueGrowthSettings()
        resetProfitGrowthSettings()
        resetDynamicPeSettings()
        resetPbRatioSettings()
        resetPsRatioSettings()
        resetStaticPeSettings()
        // 重置板块搜索
        sectorSearchText.value = ''
        filteredSectorOptions.value = sectorIndices
      }
  
      // 股票价格相关函数
      // 开盘价重置和应用函数
      const resetOpenPriceSettings = () => {
        openPriceCompare.value = '大于'
        openPriceIndicator.value = ''
      }
  
      const applyOpenPriceSettings = () => {
        // 验证是否选择了比较指标
        if (!openPriceIndicator.value) {
          alert('请选择比较指标')
          return
        }
        
        const settings = {
          signal: 'open_price',
          params: {
            compare: openPriceCompare.value,
            indicator: openPriceIndicator.value
          }
        }
        
        // 构建条件标题和详情
        let title = '股票价格 - 开盘价'
        let details = `开盘价 ${settings.params.compare} ${settings.params.indicator}`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'price_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('开盘价条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 收盘价重置和应用函数
      const resetClosePriceSettings = () => {
        closePriceCompare.value = '大于'
        closePriceIndicator.value = ''
      }
  
      const applyClosePriceSettings = () => {
        // 验证是否选择了比较指标
        if (!closePriceIndicator.value) {
          alert('请选择比较指标')
          return
        }
        
        const settings = {
          signal: 'close_price',
          params: {
            compare: closePriceCompare.value,
            indicator: closePriceIndicator.value
          }
        }
        
        // 构建条件标题和详情
        let title = '股票价格 - 收盘价'
        let details = `收盘价 ${settings.params.compare} ${settings.params.indicator}`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'price_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('收盘价条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 最高价重置和应用函数
      const resetHighPriceSettings = () => {
        highPriceCompare.value = '大于'
        highPriceIndicator.value = ''
      }
  
      const applyHighPriceSettings = () => {
        // 验证是否选择了比较指标
        if (!highPriceIndicator.value) {
          alert('请选择比较指标')
          return
        }
        
        const settings = {
          signal: 'high_price',
          params: {
            compare: highPriceCompare.value,
            indicator: highPriceIndicator.value
          }
        }
        
        // 构建条件标题和详情
        let title = '股票价格 - 最高价'
        let details = `最高价 ${settings.params.compare} ${settings.params.indicator}`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'price_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('最高价条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 最低价重置和应用函数
      const resetLowPriceSettings = () => {
        lowPriceCompare.value = '大于'
        lowPriceIndicator.value = ''
      }
  
      const applyLowPriceSettings = () => {
        // 验证是否选择了比较指标
        if (!lowPriceIndicator.value) {
          alert('请选择比较指标')
          return
        }
        
        const settings = {
          signal: 'low_price',
          params: {
            compare: lowPriceCompare.value,
            indicator: lowPriceIndicator.value
          }
        }
        
        // 构建条件标题和详情
        let title = '股票价格 - 最低价'
        let details = `最低价 ${settings.params.compare} ${settings.params.indicator}`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'price_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('最低价条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 昨日收盘价重置和应用函数
      const resetPrevClosePriceSettings = () => {
        prevClosePriceCompare.value = '大于'
        prevClosePriceIndicator.value = ''
      }
  
      const applyPrevClosePriceSettings = () => {
        // 验证是否选择了比较指标
        if (!prevClosePriceIndicator.value) {
          alert('请选择比较指标')
          return
        }
        
        const settings = {
          signal: 'prev_close_price',
          params: {
            compare: prevClosePriceCompare.value,
            indicator: prevClosePriceIndicator.value
          }
        }
        
        // 构建条件标题和详情
        let title = '股票价格 - 昨日收盘价'
        let details = `昨日收盘价 ${settings.params.compare} ${settings.params.indicator}`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'price_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('昨日收盘价条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 日成交均价重置和应用函数
      const resetAvgPriceSettings = () => {
        avgPriceCompare.value = '大于'
        avgPriceIndicator.value = ''
      }
  
      const applyAvgPriceSettings = () => {
        // 验证是否选择了比较指标
        if (!avgPriceIndicator.value) {
          alert('请选择比较指标')
          return
        }
        
        const settings = {
          signal: 'avg_price',
          params: {
            compare: avgPriceCompare.value,
            indicator: avgPriceIndicator.value
          }
        }
        
        // 构建条件标题和详情
        let title = '股票价格 - 日成交均价'
        let details = `日成交均价 ${settings.params.compare} ${settings.params.indicator}`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'price_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('日成交均价条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 新增菜单相关函数
      // 涨幅重置和应用函数
      const resetChangeRateSettings = () => {
        changeRateType.value = 'single'
        changeRateCompare.value = '大于'
        changeRateValue.value = ''
        changeRateRangeValue.value = ''
        changeRateRangeDays.value = ''
        changeRateRangeCustomValue.value = ''
        changeRateRangeDate.value = ''
      }
  
      const applyChangeRateSettings = () => {
        const settings = {
          signal: 'change_rate',
          params: {
            type: changeRateType.value,
            compare: changeRateCompare.value,
            value: changeRateValue.value,
            rangeValue: changeRateRangeValue.value,
            rangeDays: changeRateRangeDays.value,
            rangeCustomValue: changeRateRangeCustomValue.value,
            rangeDate: changeRateRangeDate.value
          }
        }
  
        // 构建条件标题和详情
        let title = '股票价格 - 涨幅'
        let details = ''
  
        if (changeRateType.value === 'single') {
          details = `涨幅 ${settings.params.compare} ${settings.params.value}%`
        } else if (changeRateType.value === 'range') {
          details = `区间涨幅(${settings.params.rangeDate}日) ${settings.params.compare} ${settings.params.rangeCustomValue}%`
        }
  
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'price_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
  
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
  
        console.log('涨幅条件已添加到选股条件', condition)
  
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 量比重置和应用函数
      const resetVolumeRatioSettings = () => {
        volumeRatioCompare.value = '大于'
        volumeRatioCustomValue.value = ''
      }
  
      const applyVolumeRatioSettings = () => {
        console.log('=== 量比函数开始执行 ===')
        console.log('量比输入值:', volumeRatioCustomValue.value)
        console.log('量比比较符:', volumeRatioCompare.value)
        
        // 清除之前添加的相同类型的条件
        selectedConditions.value = selectedConditions.value.filter(condition => 
          condition.config.signal !== 'volume_ratio'
        )
        
        const settings = {
          signal: 'volume_ratio',
          params: {
            compare: volumeRatioCompare.value,
            value: volumeRatioCustomValue.value
          }
        }
        
        // 构建条件标题和详情
        let title = '股票价格 - 量比'
        let details = `量比 ${settings.params.compare} ${settings.params.value}`
        
        console.log('量比详情:', details)
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'price_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('量比条件已添加到选股条件', condition)
        console.log('当前所有条件:', selectedConditions.value)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 成交额重置和应用函数
      const resetTurnoverSettings = () => {
        turnoverCompare.value = '大于'
        turnoverCustomValue.value = ''
      }
  
      const applyTurnoverSettings = () => {
        // 清除之前添加的相同类型的条件
        selectedConditions.value = selectedConditions.value.filter(condition => 
          condition.config.signal !== 'turnover'
        )
        
        const settings = {
          signal: 'turnover',
          params: {
            compare: turnoverCompare.value,
            value: turnoverCustomValue.value
          }
        }
        
        // 构建条件标题和详情
        let title = '股票价格 - 成交额'
        let details = `成交额 ${settings.params.compare} ${settings.params.value}`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'price_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('成交额条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 换手率重置和应用函数
      const resetTurnoverRateSettings = () => {
        turnoverRateCompare.value = '大于'
        turnoverRateCustomValue.value = ''
      }
  
      const applyTurnoverRateSettings = () => {
        // 清除之前添加的相同类型的条件
        selectedConditions.value = selectedConditions.value.filter(condition => 
          condition.config.signal !== 'turnover_rate'
        )
        
        const settings = {
          signal: 'turnover_rate',
          params: {
            compare: turnoverRateCompare.value,
            value: turnoverRateCustomValue.value
          }
        }
        
        // 构建条件标题和详情
        let title = '股票价格 - 换手率'
        let details = `换手率 ${settings.params.compare} ${settings.params.value}`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'price_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('换手率条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 市值重置和应用函数
      const resetMarketValueSettings = () => {
        marketValueCompare.value = '大于'
        marketValueCustomValue.value = ''
      }
  
      const applyMarketValueSettings = () => {
        console.log('=== 市值函数开始执行 ===')
        console.log('市值输入值:', marketValueCustomValue.value)
        console.log('市值比较符:', marketValueCompare.value)
        
        // 清除之前添加的相同类型的条件
        selectedConditions.value = selectedConditions.value.filter(condition => 
          condition.config.signal !== 'market_value'
        )
        
        const settings = {
          signal: 'market_value',
          params: {
            compare: marketValueCompare.value,
            value: marketValueCustomValue.value
          }
        }
        
        // 构建条件标题和详情
        let title = '股票价格 - 市值'
        let details = `市值 ${settings.params.compare} ${settings.params.value}`
        
        console.log('市值详情:', details)
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'price_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('市值条件已添加到选股条件', condition)
        console.log('当前所有条件:', selectedConditions.value)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 成交量重置和应用函数
      const resetVolumeSettings = () => {
        volumeCompare.value = '大于'
        volumeCustomValue.value = ''
      }
  
      const applyVolumeSettings = () => {
        // 清除之前添加的相同类型的条件
        selectedConditions.value = selectedConditions.value.filter(condition => 
          condition.config.signal !== 'volume'
        )
        
        const settings = {
          signal: 'volume',
          params: {
            compare: volumeCompare.value,
            value: volumeCustomValue.value
          }
        }
        
        // 构建条件标题和详情
        let title = '股票价格 - 成交量'
        let details = `成交量 ${settings.params.compare} ${settings.params.value}`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'price_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('成交量条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 资金净流入重置和应用函数
      const resetNetInflowSettings = () => {
        netInflowCompare.value = '大于'
        netInflowAmount.value = 0
      }
  
      const applyNetInflowSettings = () => {
        console.log('资金净流入输入值:', netInflowAmount.value, '类型:', typeof netInflowAmount.value)
        
        const settings = {
          signal: 'net_inflow',
          params: {
            compare: netInflowCompare.value,
            amount: netInflowAmount.value || 0
          }
        }
        
        // 构建条件标题和详情
        let title = '股票价格 - 资金净流入'
        let details = `资金净流入 ${settings.params.compare} ${settings.params.amount}万元`
        
        console.log('资金净流入详情:', details)
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'price_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('资金净流入条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 公告类相关函数
      // 股东减持重置和应用函数
      const resetShareholderReductionSettings = () => {
        shareholderReductionCompare.value = '大于'
        shareholderReductionAmount.value = 0
        shareholderReductionChecked.value = false
      }
  
      const applyShareholderReductionSettings = () => {
        const settings = {
          signal: 'shareholder_reduction',
          params: {
            compare: shareholderReductionCompare.value,
            amount: shareholderReductionAmount.value
          }
        }
        
        // 构建条件标题和详情
        let title = '公告类 - 股东减持'
        let details = '股东减持'
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'announcement_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('股东减持条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 股东增持重置和应用函数
      const resetShareholderIncreaseSettings = () => {
        shareholderIncreaseCompare.value = '大于'
        shareholderIncreaseAmount.value = 0
        shareholderIncreaseChecked.value = false
      }
  
      const applyShareholderIncreaseSettings = () => {
        const settings = {
          signal: 'shareholder_increase',
          params: {
            compare: shareholderIncreaseCompare.value,
            amount: shareholderIncreaseAmount.value
          }
        }
        
        // 构建条件标题和详情
        let title = '公告类 - 股东增持'
        let details = '股东增持'
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'announcement_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('股东增持条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 股东分红重置和应用函数
      const resetShareholderDividendSettings = () => {
        shareholderDividendCompare.value = '大于'
        shareholderDividendAmount.value = 0
        shareholderDividendChecked.value = false
      }
  
      const applyShareholderDividendSettings = () => {
        const settings = {
          signal: 'shareholder_dividend',
          params: {
            compare: shareholderDividendCompare.value,
            amount: shareholderDividendAmount.value
          }
        }
        
        // 构建条件标题和详情
        let title = '公告类 - 股东分红'
        let details = '股东分红'
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'announcement_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('股东分红条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 违规问询函重置和应用函数
      const resetViolationInquirySettings = () => {
        violationInquiryCompare.value = '大于'
        violationInquiryAmount.value = 0
        violationInquiryChecked.value = false
      }
  
      const applyViolationInquirySettings = () => {
        const settings = {
          signal: 'violation_inquiry',
          params: {
            compare: violationInquiryCompare.value,
            amount: violationInquiryAmount.value
          }
        }
        
        // 构建条件标题和详情
        let title = '公告类 - 违规问询函'
        let details = '违规问询函'
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'announcement_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('违规问询函条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 过滤项相关函数
      // 过滤新上市重置和应用函数
      const resetFilterNewListingSettings = () => {
        filterNewListingChecked.value = false
      }
  
      const applyFilterNewListingSettings = () => {
        const settings = {
          signal: 'filter_new_listing',
          params: {
            checked: filterNewListingChecked.value
          }
        }
        
        // 构建条件标题和详情
        let title = '过滤项 - 新上市'
        let details = `过滤新上市公司`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'filter_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('过滤新上市条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 过滤北交所重置和应用函数
      const resetFilterBeijingSettings = () => {
        filterBeijingChecked.value = false
      }
  
      const applyFilterBeijingSettings = () => {
        const settings = {
          signal: 'filter_beijing',
          params: {
            checked: filterBeijingChecked.value
          }
        }
        
        // 构建条件标题和详情
        let title = '过滤项 - 北交所'
        let details = `过滤北交所股票`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'filter_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('过滤北交所条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 过滤沪深主板重置和应用函数
      const resetFilterMainBoardSettings = () => {
        filterMainBoardChecked.value = false
      }
  
      const applyFilterMainBoardSettings = () => {
        const settings = {
          signal: 'filter_main_board',
          params: {
            checked: filterMainBoardChecked.value
          }
        }
        
        // 构建条件标题和详情
        let title = '过滤项 - 沪深主板'
        let details = `过滤沪深主板股票`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'filter_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('过滤沪深主板条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 过滤ST重置和应用函数
      const resetFilterStSettings = () => {
        filterStChecked.value = false
      }
  
      const applyFilterStSettings = () => {
        const settings = {
          type: 'filter_st',
          checked: filterStChecked.value
        }
        
        // 构建条件标题和详情
        let title = '过滤项 - ST股票'
        let details = `过滤ST股票`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'filter_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('过滤ST条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 过滤*ST重置和应用函数
      const resetFilterStarStSettings = () => {
        filterStarStChecked.value = false
      }
  
      const applyFilterStarStSettings = () => {
        const settings = {
          type: 'filter_star_st',
          checked: filterStarStChecked.value
        }
        
        // 构建条件标题和详情
        let title = '过滤项 - *ST股票'
        let details = `过滤*ST股票`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'filter_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('过滤*ST条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 过滤停牌重置和应用函数
      const resetFilterSuspensionSettings = () => {
        filterSuspensionChecked.value = false
      }
  
      const applyFilterSuspensionSettings = () => {
        const settings = {
          type: 'filter_suspension',
          checked: filterSuspensionChecked.value
        }
        
        // 构建条件标题和详情
        let title = '过滤项 - 停牌'
        let details = `过滤停牌股票`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'filter_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('过滤停牌条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 过滤科创板重置和应用函数
      const resetFilterStarMarketSettings = () => {
        filterStarMarketChecked.value = false
      }
  
      const applyFilterStarMarketSettings = () => {
        const settings = {
          type: 'filter_star_market',
          checked: filterStarMarketChecked.value
        }
        
        // 构建条件标题和详情
        let title = '过滤项 - 科创板'
        let details = `过滤科创板股票`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'filter_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('过滤科创板条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 过滤创业板重置和应用函数
      const resetFilterGrowthBoardSettings = () => {
        filterGrowthBoardChecked.value = false
      }
  
      const applyFilterGrowthBoardSettings = () => {
        const settings = {
          type: 'filter_growth_board',
          checked: filterGrowthBoardChecked.value
        }
        
        // 构建条件标题和详情
        let title = '过滤项 - 创业板'
        let details = `过滤创业板股票`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'filter_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('过滤创业板条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 过滤退市重置和应用函数
      const resetFilterDelistingSettings = () => {
        filterDelistingChecked.value = false
      }
  
      const applyFilterDelistingSettings = () => {
        const settings = {
          type: 'filter_delisting',
          checked: filterDelistingChecked.value
        }
        
        // 构建条件标题和详情
        let title = '过滤项 - 退市'
        let details = `过滤退市股票`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'filter_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('过滤退市条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 财务指标相关函数
      // ROA重置和应用函数
      const resetRoaSettings = () => {
        roaCompare.value = '大于'
        roaCustomValue.value = ''
      }
  
      const applyRoaSettings = () => {
        const settings = {
          type: 'roa',
          compare: roaCompare.value,
          value: roaCustomValue.value
        }
        
        // 构建条件标题和详情
        let title = '财务指标 - ROA'
        let details = `ROA ${settings.compare} ${settings.value}%`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'financial_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('ROA条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // ROE重置和应用函数
      const resetRoeSettings = () => {
        roeCompare.value = '大于'
        roeCustomValue.value = ''
      }
  
      const applyRoeSettings = () => {
        const settings = {
          type: 'roe',
          compare: roeCompare.value,
          value: roeCustomValue.value
        }
        
        // 构建条件标题和详情
        let title = '财务指标 - ROE'
        let details = `ROE ${settings.compare} ${settings.value}%`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'financial_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('ROE条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 毛利率重置和应用函数
      const resetGrossMarginSettings = () => {
        grossMarginCompare.value = '大于'
        grossMarginCustomValue.value = ''
      }
  
      const applyGrossMarginSettings = () => {
        const settings = {
          type: 'gross_margin',
          compare: grossMarginCompare.value,
          value: grossMarginCustomValue.value
        }
        
        // 构建条件标题和详情
        let title = '财务指标 - 毛利率'
        let details = `毛利率 ${settings.compare} ${settings.value}%`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'financial_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('毛利率条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 净利率重置和应用函数
      const resetNetMarginSettings = () => {
        netMarginCompare.value = '大于'
        netMarginCustomValue.value = ''
      }
  
      const applyNetMarginSettings = () => {
        const settings = {
          type: 'net_margin',
          compare: netMarginCompare.value,
          value: netMarginCustomValue.value
        }
        
        // 构建条件标题和详情
        let title = '财务指标 - 净利率'
        let details = `净利率 ${settings.compare} ${settings.value}%`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'financial_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('净利率条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 营收增长率重置和应用函数
      const resetRevenueGrowthSettings = () => {
        revenueGrowthCompare.value = '大于'
        revenueGrowthCustomValue.value = ''
      }
  
      const applyRevenueGrowthSettings = () => {
        const settings = {
          type: 'revenue_growth',
          compare: revenueGrowthCompare.value,
          value: revenueGrowthCustomValue.value
        }
        
        // 构建条件标题和详情
        let title = '财务指标 - 营收增长率'
        let details = `营收增长率 ${settings.compare} ${settings.value}%`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'financial_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('营收增长率条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 净利润增长率重置和应用函数
      const resetProfitGrowthSettings = () => {
        profitGrowthCompare.value = '大于'
        profitGrowthCustomValue.value = ''
      }
  
      const applyProfitGrowthSettings = () => {
        const settings = {
          signal: 'profit_growth',
          params: {
            compare: profitGrowthCompare.value,
            value: profitGrowthCustomValue.value
          }
        }
        
        // 构建条件标题和详情
        let title = '财务指标 - 净利润增长率'
        let details = `净利润增长率 ${settings.params.compare} ${settings.params.value}%`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'financial_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('净利润增长率条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 动态市盈率重置和应用函数
      const resetDynamicPeSettings = () => {
        dynamicPeCompare.value = '大于'
        dynamicPeCustomValue.value = ''
      }
  
      const applyDynamicPeSettings = () => {
        const settings = {
          signal: 'dynamic_pe',
          params: {
            compare: dynamicPeCompare.value,
            value: dynamicPeCustomValue.value
          }
        }
        
        // 构建条件标题和详情
        let title = '财务指标 - 动态市盈率'
        let details = `动态市盈率 ${settings.params.compare} ${settings.params.value}`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'financial_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('动态市盈率条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 市净率重置和应用函数
      const resetPbRatioSettings = () => {
        pbRatioCompare.value = '大于'
        pbRatioCustomValue.value = ''
      }
  
      const applyPbRatioSettings = () => {
        const settings = {
          signal: 'pb_ratio',
          params: {
            compare: pbRatioCompare.value,
            value: pbRatioCustomValue.value
          }
        }
        
        // 构建条件标题和详情
        let title = '财务指标 - 市净率'
        let details = `市净率 ${settings.params.compare} ${settings.params.value}`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'financial_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('市净率条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 市销率重置和应用函数
      const resetPsRatioSettings = () => {
        psRatioCompare.value = '大于'
        psRatioCustomValue.value = ''
      }
  
      const applyPsRatioSettings = () => {
        const settings = {
          signal: 'ps_ratio',
          params: {
            compare: psRatioCompare.value,
            value: psRatioCustomValue.value
          }
        }
        
        // 构建条件标题和详情
        let title = '财务指标 - 市销率'
        let details = `市销率 ${settings.params.compare} ${settings.params.value}`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'financial_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('市销率条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 静态市盈率重置和应用函数
      const resetStaticPeSettings = () => {
        staticPeCompare.value = '大于'
        staticPeCustomValue.value = ''
      }
  
      const applyStaticPeSettings = () => {
        const settings = {
          signal: 'static_pe',
          params: {
            compare: staticPeCompare.value,
            value: staticPeCustomValue.value
          }
        }
        
        // 构建条件标题和详情
        let title = '财务指标 - 静态市盈率'
        let details = `静态市盈率 ${settings.params.compare} ${settings.params.value}`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'financial_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('静态市盈率条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 业绩预告重置和应用函数
      const resetPerformanceForecastSettings = () => {
        performanceForecastCompare.value = '大于'
        performanceForecastAmount.value = 0
        netProfitCompare.value = '大于'
        netProfitAmount.value = 0
        selectedSignal.value = 'profit_yoy'
      }
  
      const applyPerformanceForecastSettings = () => {
        const settings = {
          signal: 'performance_forecast',
          params: {}
        }
  
        if (selectedSignal.value === 'profit_yoy') {
          settings.params = {
            compare: performanceForecastCompare.value,
            value: performanceForecastAmount.value,
            type: 'percentage'
          }
        } else if (selectedSignal.value === 'net_profit') {
          settings.params = {
            compare: netProfitCompare.value,
            value: netProfitAmount.value,
            type: 'amount'
          }
        }
        
        // 构建条件标题和详情
        let title = '公告类 - 业绩预告'
        let details = ''
  
        if (selectedSignal.value === 'profit_yoy') {
          details = `业绩预告 ${settings.params.compare} ${settings.params.value}%`
        } else if (selectedSignal.value === 'net_profit') {
          details = `业绩预告 ${settings.params.compare} ${settings.params.value}万元`
        }
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'announcement_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('业绩预告条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 业绩公告重置和应用函数
      const resetPerformanceAnnouncementSettings = () => {
        performanceAnnouncementCompare.value = '大于'
        performanceAnnouncementAmount.value = 0
        netProfitAnnouncementCompare.value = '大于'
        netProfitAnnouncementAmount.value = 0
        selectedSignalAnnouncement.value = 'announcement_profit_yoy'
      }
  
      const applyPerformanceAnnouncementSettings = () => {
        const settings = {
          signal: 'performance_announcement',
          params: {}
        }
  
        if (selectedSignalAnnouncement.value === 'announcement_profit_yoy') {
          settings.params = {
            compare: performanceAnnouncementCompare.value,
            value: performanceAnnouncementAmount.value,
            type: 'percentage'
          }
        } else if (selectedSignalAnnouncement.value === 'announcement_net_profit') {
          settings.params = {
            compare: netProfitAnnouncementCompare.value,
            value: netProfitAnnouncementAmount.value,
            type: 'amount'
          }
        }
        
        // 构建条件标题和详情
        let title = '公告类 - 业绩公告'
        let details = ''
  
        if (selectedSignalAnnouncement.value === 'announcement_profit_yoy') {
          details = `业绩公告 ${settings.params.compare} ${settings.params.value}%`
        } else if (selectedSignalAnnouncement.value === 'announcement_net_profit') {
          details = `业绩公告 ${settings.params.compare} ${settings.params.value}万元`
        }
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'announcement_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('业绩公告条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      const applyAll = () => {
        applyMaSettings()
        applyMacdSettings()
        applyKdjSettings()
        applySectorSettings()
        applySectorMacdSettings()
        applySectorKdjSettings()
        applyShareholderReductionSettings()
        applyShareholderIncreaseSettings()
        applyShareholderDividendSettings()
        applyViolationInquirySettings()
        applyPerformanceForecastSettings()
        applyPerformanceAnnouncementSettings()
      }
  
      const searchText = ref('')
      const showDropdown = ref('')
      const filteredOptions = ref([...marketIndices])
  
      const toggleDropdown = (type) => {
        showDropdown.value = showDropdown.value === type ? '' : type
      }
  
      const filterOptions = () => {
        filteredOptions.value = marketIndices.filter(option => 
          option.label.toLowerCase().includes(searchText.value.toLowerCase())
        )
      }
  
      const selectOption = (option) => {
        selectedIndex.value = option.value
        searchText.value = option.label
        showDropdown.value = ''
      }
  
      const filterSectorOptions = () => {
        if (!sectorSearchText.value) {
          filteredSectorOptions.value = sectorIndices
        } else {
          filteredSectorOptions.value = sectorIndices.filter(option =>
            option.label.toLowerCase().includes(sectorSearchText.value.toLowerCase())
          )
        }
      }
  
      const selectSectorOption = (option) => {
        // 根据当前激活的子菜单设置对应的变量
        if (activeSubMenu.value === 'sector-ma') {
          selectedSectorIndex.value = option.value
        } else if (activeSubMenu.value === 'sector-macd') {
          selectedSectorMacdIndex.value = option.value
        } else if (activeSubMenu.value === 'sector-kdj') {
          selectedSectorKdjIndex.value = option.value
        }
        showDropdown.value = ''
        sectorSearchText.value = ''
      }
  
      // 获取可用的日期范围
      const loadAvailableDateRanges = async () => {
        try {
          console.log('📅 获取可用的日期范围...')
          const response = await fetch('http://localhost:8002/api/available-date-ranges/')
          const result = await response.json()
          
          console.log('📊 日期范围API响应:', result)
          
          if (result.status === 'success' && result.default_range) {
            const defaultRange = result.default_range
            
            // 更新日期字段
            stockSelectionStartDate.value = defaultRange.start_date_formatted
            stockSelectionEndDate.value = defaultRange.end_date_formatted
            
            console.log('✅ 已设置默认日期范围:')
            console.log(`   开始日期: ${stockSelectionStartDate.value}`)
            console.log(`   结束日期: ${stockSelectionEndDate.value}`)
            console.log(`   策略名称: ${defaultRange.strategy_name}`)
            console.log(`   交易数量: ${defaultRange.trades_count}`)
            
            // 可以在这里显示一个提示信息
            if (result.available_ranges.length > 1) {
              console.log(`💡 发现 ${result.available_ranges.length} 个可用的日期范围，已自动选择最新的`)
            }
          } else {
            console.warn('⚠️ 未能获取默认日期范围，使用预设值')
          }
        } catch (error) {
          console.error('❌ 获取日期范围失败:', error)
          console.log('🔄 使用默认日期范围 2024-01-01 至 2024-12-31')
        }
      }

      // 点击外部关闭下拉框
      onMounted(() => {
        document.addEventListener('click', () => {
          showDropdown.value = ''
        })
        // 初始化板块选项
        filteredSectorOptions.value = sectorIndices
        
        // 加载可用的日期范围
        loadAvailableDateRanges()
      })
  
      // MA设置相关的状态
      const shortMA = ref(5)
      const longMA = ref(5)
      const shortMACompare = ref('大于')
      const longMACompare = ref('大于')
      const customFloat = ref(0)
  
      // 添加MACD相关的响应式变量
      const macdValue = ref(0)
      const macdCompare = ref('大于')
      const macdCustomValue = ref(0)
  
      // 添加DEA相关的响应式变量
      const deaValue = ref(0)
      const deaCompare = ref('大于')
      const deaCustomValue = ref(0)
  
      // 添加DIF相关的响应式变量
      const difValue = ref(0)
      const difCompare = ref('大于')
      const difCustomValue = ref(0)
  
      // 添加金叉相关的响应式变量
      const goldenDifPeriod = ref(12)
      const goldenDeaPeriod = ref(26)
      const goldenMacdPeriod = ref(9)
      const goldenConfirmDays = ref(2)
      const goldenSlope = ref(0.01)
  
      // 添加死叉相关的响应式变量
      const deathDifPeriod = ref(12)
      const deathDeaPeriod = ref(26)
      const deathMacdPeriod = ref(9)
      const deathConfirmDays = ref(2)
      const deathSlope = ref(-0.01)
  
      // MA设置相关的方法
      const selectSignal = (signal) => {
        selectedSignal.value = selectedSignal.value === signal ? '' : signal // 再次点击同一个按钮会取消选择
        // 不要影响activeSubMenu，保持子菜单打开状态
      }
  
      // 个股择时指标信号选择方法
      const selectTimingSignal = (signal) => {
        // 如果点击的是当前已选中的信号，则取消选择
        if (timingSelectedSignal.value === signal) {
          timingSelectedSignal.value = ''
        } else {
          timingSelectedSignal.value = signal
        }
        // 不要影响activeSubMenu，保持子菜单打开状态
      }
  
      const resetMASettings = () => {
        if (selectedSignal.value === 'ma' || timingSelectedSignal.value === 'ma') {
          maShortPeriod.value = 5
          maLongPeriod.value = 20
          maCompare.value = '大于'
          maCustomValue.value = 0
        } else if (selectedSignal.value === 'ma_golden_cross' || selectedSignal.value === 'ma_death_cross' || 
                   timingSelectedSignal.value === 'ma_golden_cross' || timingSelectedSignal.value === 'ma_death_cross') {
          maShortPeriod.value = 5
          maLongPeriod.value = 20
          maCrossCompare.value = '大于'
          maCrossCustomValue.value = 0
        } else if (selectedSignal.value === 'ma_bull' || selectedSignal.value === 'ma_bear' ||
                   timingSelectedSignal.value === 'ma_bull' || timingSelectedSignal.value === 'ma_bear') {
          maShortPeriod.value = 5
          maLongPeriod.value = 20
          maTrendCompare.value = '大于'
          maTrendCustomValue.value = 0
        } else if (selectedSignal.value === 'ma_bottom_divergence' || selectedSignal.value === 'ma_top_divergence' ||
                   timingSelectedSignal.value === 'ma_bottom_divergence' || timingSelectedSignal.value === 'ma_top_divergence') {
          maShortPeriod.value = 5
          maLongPeriod.value = 20
          maDivergenceCompare.value = '大于'
          maDivergenceCustomValue.value = 0
        } else if (selectedSignal.value === 'macd' || timingSelectedSignal.value === 'macd') {
          macdCustomValue.value = 0
          macdCompare.value = '大于'
          macdTargetValue.value = 0
          timingMacdSettings.dif = 26
          timingMacdSettings.dea = 12
          timingMacdSettings.macd = 9
        } else if (selectedSignal.value === 'dea' || timingSelectedSignal.value === 'dea') {
          deaCustomValue.value = 0
          deaCompare.value = '大于'
          deaTargetValue.value = 0
          timingMacdSettings.dif = 26
          timingMacdSettings.dea = 12
          timingMacdSettings.macd = 9
        } else if (selectedSignal.value === 'dif' || timingSelectedSignal.value === 'dif') {
          difCustomValue.value = 0
          difCompare.value = '大于'
          difTargetValue.value = 0
          timingMacdSettings.dif = 26
          timingMacdSettings.dea = 12
          timingMacdSettings.macd = 9
        } else if (selectedSignal.value === 'golden_cross' || timingSelectedSignal.value === 'golden_cross') {
          goldenDifPeriod.value = 12
          goldenDeaPeriod.value = 26
          goldenMacdPeriod.value = 9
          goldenConfirmDays.value = 2
          goldenSlope.value = 0.01
        } else if (selectedSignal.value === 'death_cross' || timingSelectedSignal.value === 'death_cross') {
          deathDifPeriod.value = 12
          deathDeaPeriod.value = 26
          deathMacdPeriod.value = 9
          deathConfirmDays.value = 2
          deathSlope.value = -0.01
        } else if (selectedSignal.value === 'bull' || selectedSignal.value === 'bear' ||
                   timingSelectedSignal.value === 'bull' || timingSelectedSignal.value === 'bear') {
          macdShortPeriod.value = 12
          macdLongPeriod.value = 26
          macdTrendPeriod.value = 9
          macdTrendCompare.value = '大于'
          macdTrendCustomValue.value = 0
        } else if (selectedSignal.value === 'bottom_divergence' || selectedSignal.value === 'top_divergence' ||
                   timingSelectedSignal.value === 'bottom_divergence' || timingSelectedSignal.value === 'top_divergence') {
          macdShortPeriod.value = 12
          macdLongPeriod.value = 26
          macdDivergencePeriod.value = 9
          macdDivergenceCompare.value = '大于'
          macdDivergenceCustomValue.value = 0
        } else if (selectedSignal.value === 'cr' || timingSelectedSignal.value === 'cr') {
          crValue.value = 0
          crAValue.value = 0
          crBValue.value = 0
          crCValue.value = 0
          crDValue.value = 0
        } else if (selectedSignal.value === 'atr' || timingSelectedSignal.value === 'atr') {
          atrShortPeriod.value = 14
          atrCompare.value = '大于'
          atrCustomValue.value = 0
        } else if (selectedSignal.value === 'cci' || timingSelectedSignal.value === 'cci') {
          cciShortPeriod.value = 14
          cciCompare.value = '大于'
          cciCustomValue.value = 0
        } else if (selectedSignal.value === 'bbic' || timingSelectedSignal.value === 'bbic') {
          bbicPeriod1.value = 5
          bbicPeriod2.value = 10
          bbicPeriod3.value = 20
          bbicPeriod4.value = 60
        } else if (selectedSignal.value === 'multi_bull' || timingSelectedSignal.value === 'multi_bull') {
          multiBullPeriod1.value = 5
          multiBullPeriod2.value = 10
          multiBullPeriod3.value = 20
          multiBullPeriod4.value = 60
        } else if (selectedSignal.value === 'ema' || timingSelectedSignal.value === 'ema') {
          emaShortPeriod.value = 12
          emaLongPeriod.value = 26
          emaCompare.value = '大于'
          emaCustomValue.value = 0
        } else if (selectedSignal.value === 'ema_golden_cross' || selectedSignal.value === 'ema_death_cross' ||
                   timingSelectedSignal.value === 'ema_golden_cross' || timingSelectedSignal.value === 'ema_death_cross') {
          emaShortPeriod.value = 6
          emaLongPeriod.value = 12
          emaCrossCompare.value = '大于'
          emaCrossCustomValue.value = 0
        } else if (selectedSignal.value === 'ema_bull' || selectedSignal.value === 'ema_bear' ||
                   timingSelectedSignal.value === 'ema_bull' || timingSelectedSignal.value === 'ema_bear') {
          emaShortPeriod.value = 14
          emaLongPeriod.value = 28
          emaTrendCompare.value = '大于'
          emaTrendCustomValue.value = 0
        } else if (selectedSignal.value === 'trix' || timingSelectedSignal.value === 'trix') {
          trixShortPeriod.value = 12
          trixLongPeriod.value = 26
          trixCompare.value = '大于'
          trixCustomValue.value = 0
        } else if (selectedSignal.value === 'trix_golden_cross' || selectedSignal.value === 'trix_death_cross' ||
                   timingSelectedSignal.value === 'trix_golden_cross' || timingSelectedSignal.value === 'trix_death_cross') {
          trixShortPeriod.value = 12
          trixLongPeriod.value = 26
          trixCrossCompare.value = '大于'
          trixCrossCustomValue.value = 0
        } else if (selectedSignal.value === 'kdj_k' || timingSelectedSignal.value === 'kdj_k') {
          kdjKCustomValue.value = 0
          kdjKCompare.value = '大于'
          kdjKTargetValue.value = 0
          timingKdjSettings.k = 9
          timingKdjSettings.d = 3
          timingKdjSettings.j = 3
        } else if (selectedSignal.value === 'kdj_d' || timingSelectedSignal.value === 'kdj_d') {
          kdjDCustomValue.value = 0
          kdjDCompare.value = '大于'
          kdjDTargetValue.value = 0
          timingKdjSettings.k = 9
          timingKdjSettings.d = 3
          timingKdjSettings.j = 3
        } else if (selectedSignal.value === 'kdj_j' || timingSelectedSignal.value === 'kdj_j') {
          kdjJCustomValue.value = 0
          kdjJCompare.value = '大于'
          kdjJTargetValue.value = 0
          timingKdjSettings.k = 9
          timingKdjSettings.d = 3
          timingKdjSettings.j = 3
        } else if (selectedSignal.value === 'kdj_golden_cross' || timingSelectedSignal.value === 'kdj_golden_cross') {
          kdjGoldenKPeriod.value = 9
          kdjGoldenDPeriod.value = 3
          kdjGoldenJPeriod.value = 3
        } else if (selectedSignal.value === 'kdj_death_cross' || timingSelectedSignal.value === 'kdj_death_cross') {
          kdjDeathKPeriod.value = 9
          kdjDeathDPeriod.value = 3
          kdjDeathJPeriod.value = 3
        } else if (selectedSignal.value === 'kdj_bull' || selectedSignal.value === 'kdj_bear' ||
                   timingSelectedSignal.value === 'kdj_bull' || timingSelectedSignal.value === 'kdj_bear') {
          kdjShortPeriod.value = 9
          kdjLongPeriod.value = 3
          kdjTrendCompare.value = '大于'
          kdjTrendCustomValue.value = 0
        } else if (selectedSignal.value === 'rsi' || timingSelectedSignal.value === 'rsi') {
          rsiCustomValue.value = 0
          rsiCompare.value = '大于'
          rsiTargetValue.value = 0
          timingRsiSettings.period = 14
        } else if (selectedSignal.value === 'rsi_golden_cross' || selectedSignal.value === 'rsi_death_cross' ||
                   timingSelectedSignal.value === 'rsi_golden_cross' || timingSelectedSignal.value === 'rsi_death_cross') {
          rsiCrossCustomValue.value = 0
          rsiCrossCompare.value = '大于'
          rsiTargetValue.value = 0
          timingRsiSettings.period = 14
        } else if (selectedSignal.value === 'boll' || timingSelectedSignal.value === 'boll') {
          bollShortPeriod.value = 20
          bollLongPeriod.value = 2
          bollCompare.value = '大于'
          bollCustomValue.value = 0
        } else if (selectedSignal.value === 'boll_upper' || selectedSignal.value === 'boll_middle' || selectedSignal.value === 'boll_lower' ||
                   timingSelectedSignal.value === 'boll_upper' || timingSelectedSignal.value === 'boll_middle' || timingSelectedSignal.value === 'boll_lower') {
          bollShortPeriod.value = 20
          bollLongPeriod.value = 2
          bollCompare.value = '大于'
          bollCustomValue.value = 0
        } else if (selectedSignal.value === 'boll_break_upper' || selectedSignal.value === 'boll_break_lower' ||
                   timingSelectedSignal.value === 'boll_break_upper' || timingSelectedSignal.value === 'boll_break_lower') {
          bollShortPeriod.value = 20
          bollLongPeriod.value = 2
          bollCompare.value = '大于'
          bollCustomValue.value = 0
        } else if (selectedSignal.value === 'kdj_k' || timingSelectedSignal.value === 'kdj_k') {
          kdjKValue.value = 9
          kdjKCompare.value = '大于'
          kdjKCustomValue.value = 0
        } else if (selectedSignal.value === 'kdj_d' || timingSelectedSignal.value === 'kdj_d') {
          kdjDValue.value = 3
          kdjDCompare.value = '大于'
          kdjDCustomValue.value = 0
        } else if (selectedSignal.value === 'kdj_j' || timingSelectedSignal.value === 'kdj_j') {
          kdjJValue.value = 3
          kdjJCompare.value = '大于'
          kdjJCustomValue.value = 0
        } else if (selectedSignal.value === 'kdj_golden_cross' || timingSelectedSignal.value === 'kdj_golden_cross') {
          kdjGoldenKPeriod.value = 9
          kdjGoldenDPeriod.value = 3
          kdjGoldenJPeriod.value = 3
        } else if (selectedSignal.value === 'kdj_death_cross' || timingSelectedSignal.value === 'kdj_death_cross') {
          kdjDeathKPeriod.value = 9
          kdjDeathDPeriod.value = 3
          kdjDeathJPeriod.value = 3
        } else if (selectedSignal.value === 'kdj_bull' || selectedSignal.value === 'kdj_bear' ||
                   timingSelectedSignal.value === 'kdj_bull' || timingSelectedSignal.value === 'kdj_bear') {
          kdjShortPeriod.value = 9
          kdjLongPeriod.value = 3
          kdjTrendJPeriod.value = 3
          kdjTrendCompare.value = '大于'
          kdjTrendCustomValue.value = 0
        } else if (selectedSignal.value === 'kdj_bottom_divergence' || selectedSignal.value === 'kdj_top_divergence' ||
                   timingSelectedSignal.value === 'kdj_bottom_divergence' || timingSelectedSignal.value === 'kdj_top_divergence') {
          kdjShortPeriod.value = 9
          kdjLongPeriod.value = 3
          kdjDivergenceJPeriod.value = 3
          kdjDivergenceCompare.value = '大于'
          kdjDivergenceCustomValue.value = 0
        } else if (selectedSignal.value === 'rsi') {
          rsiCustomValue.value = 0
          rsiCompare.value = '大于'
          rsiTargetValue.value = 0
          timingRsiSettings.period = 14
        } else if (selectedSignal.value === 'rsi_golden_cross' || selectedSignal.value === 'rsi_death_cross') {
          rsiCrossCustomValue.value = 0
          rsiCrossCompare.value = '大于'
          rsiTargetValue.value = 0
          timingRsiSettings.period = 14
        } else if (selectedSignal.value === 'rsi_bull' || selectedSignal.value === 'rsi_bear') {
          rsiTrendCustomValue.value = 0
          rsiTrendCompare.value = '大于'
          rsiTargetValue.value = 0
          timingRsiSettings.period = 14
        } else if (selectedSignal.value === 'rsi_bottom_divergence' || selectedSignal.value === 'rsi_top_divergence') {
          rsiDivergenceCustomValue.value = 0
          rsiDivergenceCompare.value = '大于'
          rsiTargetValue.value = 0
          timingRsiSettings.period = 14
  
        } else if (selectedSignal.value === 'cr') {
          crShortPeriod.value = 26
          crLongPeriod.value = 10
          crCompare.value = '大于'
          crCustomValue.value = 0
        } else if (selectedSignal.value === 'cr_golden_cross' || selectedSignal.value === 'cr_death_cross') {
          crShortPeriod.value = 26
          crLongPeriod.value = 10
          crCrossCompare.value = '大于'
          crCrossCustomValue.value = 0
        } else if (selectedSignal.value === 'cr_bull' || selectedSignal.value === 'cr_bear') {
          crShortPeriod.value = 26
          crLongPeriod.value = 10
          crTrendCompare.value = '大于'
          crTrendCustomValue.value = 0
        } else if (selectedSignal.value === 'cr_bottom_divergence' || selectedSignal.value === 'cr_top_divergence') {
          crShortPeriod.value = 26
          crLongPeriod.value = 10
          crDivergenceCompare.value = '大于'
          crDivergenceCustomValue.value = 0
        } else if (selectedSignal.value === 'atr') {
          atrShortPeriod.value = 14
          atrCompare.value = '大于'
          atrCustomValue.value = 0
        } else if (selectedSignal.value === 'atr_bull' || selectedSignal.value === 'atr_bear') {
          atrShortPeriod.value = 14
          atrTrendCompare.value = '大于'
          atrTrendCustomValue.value = 0
        } else if (selectedSignal.value === 'trix') {
          trixShortPeriod.value = 12
          trixLongPeriod.value = 9
          trixCompare.value = '大于'
          trixCustomValue.value = 0
        } else if (selectedSignal.value === 'trix_golden_cross' || selectedSignal.value === 'trix_death_cross') {
          trixShortPeriod.value = 12
          trixLongPeriod.value = 9
          trixCrossCompare.value = '大于'
          trixCrossCustomValue.value = 0
        } else if (selectedSignal.value === 'cci') {
          cciShortPeriod.value = 14
          cciCompare.value = '大于'
          cciCustomValue.value = 0
        } else if (selectedSignal.value === 'cci_bull' || selectedSignal.value === 'cci_bear') {
          cciShortPeriod.value = 14
          cciTrendCompare.value = '大于'
          cciTrendCustomValue.value = 0
        } else if (selectedSignal.value === 'ema') {
          emaShortPeriod.value = 12
          emaLongPeriod.value = 26
          emaCompare.value = '大于'
          emaCustomValue.value = 0
        } else if (selectedSignal.value === 'ema_golden_cross' || selectedSignal.value === 'ema_death_cross') {
          emaShortPeriod.value = 6
          emaLongPeriod.value = 12
          emaCrossCompare.value = '大于'
          emaCrossCustomValue.value = 0
        } else if (selectedSignal.value === 'ema_bull' || selectedSignal.value === 'ema_bear') {
          emaShortPeriod.value = 14
          emaLongPeriod.value = 28
          emaTrendCompare.value = '大于'
          emaTrendCustomValue.value = 0
        } else if (selectedSignal.value === 'multi_bull') {
          multiBullPeriod1.value = 5
          multiBullPeriod2.value = 10
          multiBullPeriod3.value = 20
          multiBullPeriod4.value = 60
        }
      }
  
      const applyMASettings = () => {
        // 判断当前是否在个股择时指标菜单中
        const isTimingMenu = activeSubMenu.value && activeSubMenu.value.startsWith('timing-')
        
        const settings = {
          signal: isTimingMenu ? timingSelectedSignal.value : selectedSignal.value,
          params: {}
        }
  
        const currentSignal = isTimingMenu ? timingSelectedSignal.value : selectedSignal.value
        
        if (currentSignal === 'ma') {
          settings.params = {
            shortPeriod: maShortPeriod.value,
            longPeriod: maLongPeriod.value,
            compare: maCompare.value,
            value: maCustomValue.value
          }
        } else if (currentSignal === 'ma_golden_cross' || currentSignal === 'ma_death_cross') {
          settings.params = {
            shortPeriod: maShortPeriod.value,
            longPeriod: maLongPeriod.value,
            compare: maCrossCompare.value,
            value: maCrossCustomValue.value
          }
        } else if (currentSignal === 'ma_bull' || currentSignal === 'ma_bear') {
          settings.params = {
            shortPeriod: maShortPeriod.value,
            longPeriod: maLongPeriod.value,
            compare: maTrendCompare.value,
            value: maTrendCustomValue.value
          }
        } else if (currentSignal === 'ma_bottom_divergence' || currentSignal === 'ma_top_divergence') {
          settings.params = {
            shortPeriod: maShortPeriod.value,
            longPeriod: maLongPeriod.value,
            compare: maDivergenceCompare.value,
            value: maDivergenceCustomValue.value
          }
        } else if (currentSignal === 'macd') {
          settings.params = {
            value: macdCustomValue.value,
            compare: macdCompare.value,
            customValue: macdTargetValue.value,
            dif: timingMacdSettings.dif,
            dea: timingMacdSettings.dea,
            macd: timingMacdSettings.macd
          }
        } else if (currentSignal === 'dea') {
          settings.params = {
            value: deaCustomValue.value,
            compare: deaCompare.value,
            customValue: deaTargetValue.value,
            dif: timingMacdSettings.dif,
            dea: timingMacdSettings.dea,
            macd: timingMacdSettings.macd
          }
        } else if (currentSignal === 'dif') {
          settings.params = {
            value: difCustomValue.value,
            compare: difCompare.value,
            customValue: difTargetValue.value,
            dif: timingMacdSettings.dif,
            dea: timingMacdSettings.dea,
            macd: timingMacdSettings.macd
          }
        } else if (currentSignal === 'golden_cross') {
          console.log('MACD金叉参数:', {
            difPeriod: goldenDifPeriod.value,
            deaPeriod: goldenDeaPeriod.value,
            macdPeriod: goldenMacdPeriod.value,
            confirmDays: goldenConfirmDays.value,
            slope: goldenSlope.value
          })
          settings.params = {
            difPeriod: goldenDifPeriod.value,
            deaPeriod: goldenDeaPeriod.value,
            macdPeriod: goldenMacdPeriod.value,
            confirmDays: goldenConfirmDays.value,
            slope: goldenSlope.value
          }
        } else if (currentSignal === 'death_cross') {
          console.log('MACD死叉参数:', {
            difPeriod: deathDifPeriod.value,
            deaPeriod: deathDeaPeriod.value,
            macdPeriod: deathMacdPeriod.value,
            confirmDays: deathConfirmDays.value,
            slope: deathSlope.value
          })
          settings.params = {
            difPeriod: deathDifPeriod.value,
            deaPeriod: deathDeaPeriod.value,
            macdPeriod: deathMacdPeriod.value,
            confirmDays: deathConfirmDays.value,
            slope: deathSlope.value
          }
        } else if (currentSignal === 'bull' || currentSignal === 'bear') {
          settings.params = {
            shortPeriod: macdShortPeriod.value,
            longPeriod: macdLongPeriod.value,
            macdPeriod: macdTrendPeriod.value,
            compare: macdTrendCompare.value,
            value: macdTrendCustomValue.value
          }
        } else if (currentSignal === 'bottom_divergence' || currentSignal === 'top_divergence') {
          console.log('MACD背离参数:', {
            shortPeriod: macdShortPeriod.value,
            longPeriod: macdLongPeriod.value,
            macdPeriod: macdDivergencePeriod.value,
            compare: macdDivergenceCompare.value,
            value: macdDivergenceCustomValue.value
          })
          settings.params = {
            shortPeriod: macdShortPeriod.value,
            longPeriod: macdLongPeriod.value,
            macdPeriod: macdDivergencePeriod.value,
            compare: macdDivergenceCompare.value,
            value: macdDivergenceCustomValue.value
          }
        } else if (currentSignal === 'kdj_k') {
          settings.params = {
            value: kdjKCustomValue.value,
            compare: kdjKCompare.value,
            customValue: kdjKTargetValue.value,
            k: timingKdjSettings.k,
            d: timingKdjSettings.d,
            j: timingKdjSettings.j
          }
        } else if (currentSignal === 'kdj_d') {
          settings.params = {
            value: kdjDCustomValue.value,
            compare: kdjDCompare.value,
            customValue: kdjDTargetValue.value,
            k: timingKdjSettings.k,
            d: timingKdjSettings.d,
            j: timingKdjSettings.j
          }
        } else if (currentSignal === 'kdj_j') {
          settings.params = {
            value: kdjJCustomValue.value,
            compare: kdjJCompare.value,
            customValue: kdjJTargetValue.value,
            k: timingKdjSettings.k,
            d: timingKdjSettings.d,
            j: timingKdjSettings.j
          }
        } else if (currentSignal === 'kdj_golden_cross') {
          settings.params = {
            kPeriod: kdjGoldenKPeriod.value,
            dPeriod: kdjGoldenDPeriod.value,
            jPeriod: kdjGoldenJPeriod.value
          }
        } else if (currentSignal === 'kdj_death_cross') {
          settings.params = {
            kPeriod: kdjDeathKPeriod.value,
            dPeriod: kdjDeathDPeriod.value,
            jPeriod: kdjDeathJPeriod.value
          }
        } else if (currentSignal === 'kdj_bull' || currentSignal === 'kdj_bear') {
          settings.params = {
            shortPeriod: kdjShortPeriod.value,
            longPeriod: kdjLongPeriod.value,
            jPeriod: kdjTrendJPeriod.value,
            compare: kdjTrendCompare.value,
            value: kdjTrendCustomValue.value
          }
        } else if (currentSignal === 'kdj_bottom_divergence' || currentSignal === 'kdj_top_divergence') {
          settings.params = {
            shortPeriod: kdjShortPeriod.value,
            longPeriod: kdjLongPeriod.value,
            jPeriod: kdjDivergenceJPeriod.value,
            compare: kdjDivergenceCompare.value,
            value: kdjDivergenceCustomValue.value
          }
        } else if (currentSignal === 'rsi') {
          settings.params = {
            value: rsiCustomValue.value,
            compare: rsiCompare.value,
            customValue: rsiTargetValue.value,
            period: timingRsiSettings.period
          }
        } else if (currentSignal === 'rsi_golden_cross' || currentSignal === 'rsi_death_cross') {
          settings.params = {
            value: rsiCrossCustomValue.value,
            compare: rsiCrossCompare.value,
            customValue: rsiTargetValue.value,
            period: timingRsiSettings.period
          }
        } else if (currentSignal === 'rsi_bull' || currentSignal === 'rsi_bear') {
          settings.params = {
            value: rsiTrendCustomValue.value,
            compare: rsiTrendCompare.value,
            customValue: rsiTargetValue.value,
            period: timingRsiSettings.period
          }
        } else if (currentSignal === 'rsi_bottom_divergence' || currentSignal === 'rsi_top_divergence') {
          settings.params = {
            value: rsiDivergenceCustomValue.value,
            compare: rsiDivergenceCompare.value,
            customValue: rsiTargetValue.value,
            period: timingRsiSettings.period
          }
        } else if (currentSignal === 'boll') {
          settings.params = {
            value: bollCustomValue.value,
            compare: bollCompare.value,
            customValue: bollTargetValue.value,
            period: timingBollSettings.period,
            multiplier: timingBollSettings.multiplier
          }
        } else if (currentSignal === 'boll_upper' || currentSignal === 'boll_middle' || currentSignal === 'boll_lower') {
          settings.params = {
            value: bollCustomValue.value,
            compare: bollCompare.value,
            customValue: bollTargetValue.value,
            period: timingBollSettings.period,
            multiplier: timingBollSettings.multiplier
          }
        } else if (currentSignal === 'boll_break_upper' || currentSignal === 'boll_break_lower') {
          settings.params = {
            value: bollCustomValue.value,
            compare: bollCompare.value,
            customValue: bollTargetValue.value,
            period: timingBollSettings.period,
            multiplier: timingBollSettings.multiplier
          }
        } else if (currentSignal === 'cr') {
          settings.params = {
            value: crCustomValue.value,
            compare: crCompare.value,
            customValue: crTargetValue.value,
            period: timingCrSettings.period
          }
        } else if (currentSignal === 'cr_golden_cross' || currentSignal === 'cr_death_cross') {
          settings.params = {
            value: crCrossCustomValue.value,
            compare: crCrossCompare.value,
            customValue: crTargetValue.value,
            period: timingCrSettings.period
          }
        } else if (currentSignal === 'cr_bull' || currentSignal === 'cr_bear') {
          settings.params = {
            value: crTrendCustomValue.value,
            compare: crTrendCompare.value,
            customValue: crTargetValue.value,
            period: timingCrSettings.period
          }
        } else if (currentSignal === 'cr_bottom_divergence' || currentSignal === 'cr_top_divergence') {
          settings.params = {
            value: crDivergenceCustomValue.value,
            compare: crDivergenceCompare.value,
            customValue: crTargetValue.value,
            period: timingCrSettings.period
          }
        } else if (currentSignal === 'atr') {
          settings.params = {
            period: atrShortPeriod.value,
            compare: atrCompare.value,
            value: atrCustomValue.value
          }
        } else if (currentSignal === 'atr_bull' || currentSignal === 'atr_bear') {
          settings.params = {
            period: atrShortPeriod.value,
            compare: atrTrendCompare.value,
            value: atrTrendCustomValue.value
          }
        } else if (currentSignal === 'trix') {
          settings.params = {
            value: trixCustomValue.value,
            compare: trixCompare.value,
            customValue: trixTargetValue.value,
            period: timingTrixSettings.period
          }
        } else if (currentSignal === 'trix_golden_cross' || currentSignal === 'trix_death_cross') {
          settings.params = {
            value: trixCrossCustomValue.value,
            compare: trixCrossCompare.value,
            customValue: trixTargetValue.value,
            period: timingTrixSettings.period
          }
        } else if (currentSignal === 'cci') {
          settings.params = {
            period: cciShortPeriod.value,
            compare: cciCompare.value,
            value: cciCustomValue.value
          }
        } else if (currentSignal === 'cci_bull' || currentSignal === 'cci_bear') {
          settings.params = {
            period: cciShortPeriod.value,
            compare: cciTrendCompare.value,
            value: cciTrendCustomValue.value
          }
        } else if (currentSignal === 'ema') {
          settings.params = {
            shortPeriod: emaShortPeriod.value,
            longPeriod: emaLongPeriod.value,
            compare: emaCompare.value,
            value: emaCustomValue.value
          }
        } else if (currentSignal === 'ema_golden_cross' || currentSignal === 'ema_death_cross') {
          settings.params = {
            shortPeriod: emaShortPeriod.value,
            longPeriod: emaLongPeriod.value,
            compare: emaCrossCompare.value,
            value: emaCrossCustomValue.value
          }
        } else if (currentSignal === 'ema_bull' || currentSignal === 'ema_bear') {
          settings.params = {
            shortPeriod: emaShortPeriod.value,
            longPeriod: emaLongPeriod.value,
            compare: emaTrendCompare.value,
            value: emaTrendCustomValue.value
          }
        } else if (currentSignal === 'multi_bull') {
          settings.params = {
            period1: multiBullPeriod1.value,
            period2: multiBullPeriod2.value,
            period3: multiBullPeriod3.value,
            period4: multiBullPeriod4.value
          }
        }
  
        // 构建条件标题和详情
        let title = '个股择时指标'
        let details = ''
        
        // 根据不同的信号类型构建详情
        if (currentSignal.startsWith('macd') || currentSignal === 'dif' || currentSignal === 'dea' || 
            currentSignal === 'golden_cross' || currentSignal === 'death_cross' || 
            currentSignal === 'bull' || currentSignal === 'bear' || 
            currentSignal === 'bottom_divergence' || currentSignal === 'top_divergence') {
          title = '个股择时 - MACD指标'
          if (currentSignal === 'macd') {
            details = `MACD(${settings.params.dif},${settings.params.dea},${settings.params.macd}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'dif') {
            details = `DIF(${settings.params.dif},${settings.params.dea},${settings.params.macd}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'dea') {
            details = `DEA(${settings.params.dif},${settings.params.dea},${settings.params.macd}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'golden_cross') {
            console.log('MACD金叉详情构建:', settings.params)
            details = `MACD金叉 DIF(${settings.params.difPeriod}) DEA(${settings.params.deaPeriod}) MACD(${settings.params.macdPeriod})`
          } else if (currentSignal === 'death_cross') {
            console.log('MACD死叉详情构建:', settings.params)
            details = `MACD死叉 DIF(${settings.params.difPeriod}) DEA(${settings.params.deaPeriod}) MACD(${settings.params.macdPeriod})`
          } else if (currentSignal === 'bull') {
            details = `MACD多头 DIF(${settings.params.shortPeriod}) DEA(${settings.params.longPeriod}) MACD(${settings.params.macdPeriod}) ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'bear') {
            details = `MACD空头 DIF(${settings.params.shortPeriod}) DEA(${settings.params.longPeriod}) MACD(${settings.params.macdPeriod}) ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'bottom_divergence') {
            console.log('MACD底背离详情构建:', settings.params)
            details = `MACD底背离 DIF(${settings.params.shortPeriod}) DEA(${settings.params.longPeriod}) MACD(${settings.params.macdPeriod}) ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'top_divergence') {
            console.log('MACD顶背离详情构建:', settings.params)
            details = `MACD顶背离 DIF(${settings.params.shortPeriod}) DEA(${settings.params.longPeriod}) MACD(${settings.params.macdPeriod}) ${settings.params.compare} ${settings.params.value}`
          }
        } else if (currentSignal.startsWith('ma')) {
          title = '个股择时 - MA指标'
          if (currentSignal === 'ma') {
            details = `MA(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'ma_golden_cross') {
            details = `MA(${settings.params.shortPeriod},${settings.params.longPeriod}) 金叉 ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'ma_death_cross') {
            details = `MA(${settings.params.shortPeriod},${settings.params.longPeriod}) 死叉 ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'ma_bull') {
            details = `MA(${settings.params.shortPeriod},${settings.params.longPeriod}) 多头 ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'ma_bear') {
            details = `MA(${settings.params.shortPeriod},${settings.params.longPeriod}) 空头 ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'ma_bottom_divergence') {
            details = `MA(${settings.params.shortPeriod},${settings.params.longPeriod}) 底背离 ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'ma_top_divergence') {
            details = `MA(${settings.params.shortPeriod},${settings.params.longPeriod}) 顶背离 ${settings.params.compare} ${settings.params.value}`
          }
        } else if (currentSignal.startsWith('kdj')) {
          title = '个股择时 - KDJ指标'
          if (currentSignal === 'kdj_k') {
            details = `KDJ_K(${settings.params.k},${settings.params.d},${settings.params.j}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'kdj_d') {
            details = `KDJ_D(${settings.params.k},${settings.params.d},${settings.params.j}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'kdj_j') {
            details = `KDJ_J(${settings.params.k},${settings.params.d},${settings.params.j}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'kdj_golden_cross') {
            details = `KDJ金叉 K(${settings.params.kPeriod}) D(${settings.params.dPeriod}) J(${settings.params.jPeriod})`
          } else if (currentSignal === 'kdj_death_cross') {
            details = `KDJ死叉 K(${settings.params.kPeriod}) D(${settings.params.dPeriod}) J(${settings.params.jPeriod})`
          } else if (currentSignal === 'kdj_bull') {
            details = `KDJ多头 K(${settings.params.shortPeriod}) D(${settings.params.longPeriod}) J(${settings.params.jPeriod}) ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'kdj_bear') {
            details = `KDJ空头 K(${settings.params.shortPeriod}) D(${settings.params.longPeriod}) J(${settings.params.jPeriod}) ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'kdj_bottom_divergence') {
            details = `KDJ底背离 K(${settings.params.shortPeriod}) D(${settings.params.longPeriod}) J(${settings.params.jPeriod}) ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'kdj_top_divergence') {
            details = `KDJ顶背离 K(${settings.params.shortPeriod}) D(${settings.params.longPeriod}) J(${settings.params.jPeriod}) ${settings.params.compare} ${settings.params.value}`
          }
        } else if (currentSignal.startsWith('rsi')) {
          title = '个股择时 - RSI指标'
          if (currentSignal === 'rsi') {
            details = `RSI(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'rsi_golden_cross') {
            details = `RSI金叉(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'rsi_death_cross') {
            details = `RSI死叉(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'rsi_bull') {
            details = `RSI多头(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'rsi_bear') {
            details = `RSI空头(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'rsi_bottom_divergence') {
            details = `RSI底背离(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'rsi_top_divergence') {
            details = `RSI顶背离(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          }
        } else if (currentSignal.startsWith('boll')) {
          title = '个股择时 - BOLL指标'
          if (currentSignal === 'boll') {
            details = `BOLL(${settings.params.period},${settings.params.multiplier}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'boll_upper') {
            details = `BOLL上线(${settings.params.period},${settings.params.multiplier}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'boll_middle') {
            details = `BOLL中线(${settings.params.period},${settings.params.multiplier}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'boll_lower') {
            details = `BOLL下线(${settings.params.period},${settings.params.multiplier}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'boll_break_upper') {
            details = `BOLL突破上轨(${settings.params.period},${settings.params.multiplier}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'boll_break_lower') {
            details = `BOLL突破下轨(${settings.params.period},${settings.params.multiplier}) ${settings.params.compare} ${settings.params.customValue}`
          }
        } else if (currentSignal.startsWith('cr')) {
          title = '个股择时 - CR指标'
          if (currentSignal === 'cr') {
            details = `CR(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'cr_golden_cross') {
            details = `CR金叉(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'cr_death_cross') {
            details = `CR死叉(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'cr_bull') {
            details = `CR多头(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'cr_bear') {
            details = `CR空头(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'cr_bottom_divergence') {
            details = `CR底背离(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'cr_top_divergence') {
            details = `CR顶背离(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          }
        } else if (currentSignal.startsWith('atr')) {
          title = '个股择时 - ATR指标'
          if (currentSignal === 'atr') {
            details = `ATR(${settings.params.period}) ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'atr_bull') {
            details = `ATR多头 ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'atr_bear') {
            details = `ATR空头 ${settings.params.compare} ${settings.params.value}`
          }
        } else if (currentSignal.startsWith('trix')) {
          title = '个股择时 - TRIX指标'
          if (currentSignal === 'trix') {
            details = `TRIX(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'trix_golden_cross') {
            details = `TRIX金叉(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          } else if (currentSignal === 'trix_death_cross') {
            details = `TRIX死叉(${settings.params.period}) ${settings.params.compare} ${settings.params.customValue}`
          }
        } else if (currentSignal.startsWith('cci')) {
          title = '个股择时 - CCI指标'
          if (currentSignal === 'cci') {
            details = `CCI(${settings.params.period}) ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'cci_bull') {
            details = `CCI多头 ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'cci_bear') {
            details = `CCI空头 ${settings.params.compare} ${settings.params.value}`
          }
        } else if (currentSignal.startsWith('ema')) {
          title = '个股择时 - EMA指标'
          if (currentSignal === 'ema') {
            details = `EMA(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'ema_golden_cross') {
            details = `EMA金叉(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'ema_death_cross') {
            details = `EMA死叉(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'ema_bull') {
            details = `EMA多头(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
          } else if (currentSignal === 'ema_bear') {
            details = `EMA空头(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
          }
        } else if (currentSignal === 'multi_bull') {
          title = '个股择时 - 四周期多头排列'
          details = `四周期多头排列(${settings.params.period1},${settings.params.period2},${settings.params.period3},${settings.params.period4})`
        }
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'timing_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('个股择时指标条件已添加到选股条件', condition)
        // 删除弹窗提示
        // alert('个股择时指标设置已成功添加到选股条件！')
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      // 参数相关的状态
      const paramValue = ref(0)
      const compareOperator = ref('大于')
      const customValue = ref(0)
  
      // 金叉死叉参数
      const difPeriod = ref(12)
      const deaPeriod = ref(26)
      const macdPeriod = ref(9)
  
      // 多空头参数
      const trendPeriod = ref(20)
      const confirmPeriod = ref(5)
      const deviation = ref(0.1)
  
      // 背离参数
      const divergencePeriod = ref(20)
      const divergenceRange = ref(0.1)
  
      // 获取参数标签
      const getParamLabel = (signal) => {
        const labels = {
          'macd': 'MACD值',
          'dea': 'DEA值',
          'dif': 'DIF值',
          'golden_cross': '金叉周期',
          'death_cross': '死叉周期',
          'bull': '多头周期',
          'bear': '空头周期',
          'bottom_divergence': '底背离周期',
          'top_divergence': '顶背离周期',
          'boll': 'BOLL值',
          'boll_upper': 'BOLL上线',
          'boll_middle': 'BOLL中线',
          'boll_lower': 'BOLL下线',
          'boll_break_upper': 'BOLL突破上轨',
          'boll_break_lower': 'BOLL突破下轨',
          'ema': 'EMA值',
          'ema_golden_cross': 'EMA金叉',
          'ema_death_cross': 'EMA死叉',
          'ema_bull': 'EMA多头',
          'ema_bear': 'EMA空头'
        }
        return labels[signal] || signal
      }
  
      // 获取周期placeholder
      const getPeriodPlaceholder = (signal) => {
        const placeholders = {
          'macd': '输入MACD值',
          'dea': '输入DEA值',
          'dif': '输入DIF值',
          'boll': '输入BOLL值',
          'boll_upper': '输入BOLL上线值',
          'boll_middle': '输入BOLL中线值',
          'boll_lower': '输入BOLL下线值',
          'boll_break_upper': '输入BOLL突破上轨值',
          'boll_break_lower': '输入BOLL突破下轨值',
          'ema': '输入EMA值',
          'ema_golden_cross': '输入EMA金叉值',
          'ema_death_cross': '输入EMA死叉值',
          'ema_bull': '输入EMA多头值',
          'ema_bear': '输入EMA空头值'
        }
        return placeholders[signal] || '输入参数值'
      }
  
      // 重置设置
      const resetSettings = () => {
        if (['macd', 'dea', 'dif'].includes(selectedSignal.value)) {
          paramValue.value = 0
          compareOperator.value = '大于'
          customValue.value = 0
        } else if (['golden_cross', 'death_cross'].includes(selectedSignal.value)) {
          difPeriod.value = 12
          deaPeriod.value = 26
          macdPeriod.value = 9
        } else if (['bull', 'bear'].includes(selectedSignal.value)) {
          trendPeriod.value = 20
          confirmPeriod.value = 5
          deviation.value = 0.1
        } else if (['top_divergence', 'bottom_divergence'].includes(selectedSignal.value)) {
          divergencePeriod.value = 20
          confirmPeriod.value = 5
          divergenceRange.value = 0.1
        }
      }
  
      // 应用设置
      const applySettings = () => {
        const settings = {
          signal: selectedSignal.value,
          params: {}
        }
  
        if (['macd', 'dea', 'dif'].includes(selectedSignal.value)) {
          settings.params = {
            period: paramValue.value,
            operator: compareOperator.value,
            value: customValue.value
          }
        } else if (['golden_cross', 'death_cross'].includes(selectedSignal.value)) {
          settings.params = {
            difPeriod: difPeriod.value,
            deaPeriod: deaPeriod.value,
            macdPeriod: macdPeriod.value
          }
        } else if (['bull', 'bear'].includes(selectedSignal.value)) {
          settings.params = {
            trendPeriod: trendPeriod.value,
            confirmPeriod: confirmPeriod.value,
            deviation: deviation.value
          }
        } else if (['top_divergence', 'bottom_divergence'].includes(selectedSignal.value)) {
          settings.params = {
            divergencePeriod: divergencePeriod.value,
            confirmPeriod: confirmPeriod.value,
            divergenceRange: divergenceRange.value
          }
        }
  
        console.log('应用设置', settings)
      }
  
      // MA指标相关的响应式变量
      const maShortPeriod = ref(5)
      const maLongPeriod = ref(20)
      const maCompare = ref('大于')
      const maCustomValue = ref(0)
      const maCrossCompare = ref('大于')
      const maCrossCustomValue = ref(0)
      const maTrendCompare = ref('大于')
      const maTrendCustomValue = ref(0)
      const maDivergenceCompare = ref('大于')
      const maDivergenceCustomValue = ref(0)
      
      // MACD指标相关的响应式变量
      const macdShortPeriod = ref(12)
      const macdLongPeriod = ref(26)
      const macdTrendPeriod = ref(9)
      const macdTrendCompare = ref('大于')
      const macdTrendCustomValue = ref(0)
      const macdDivergencePeriod = ref(9)
      const macdDivergenceCompare = ref('大于')
      const macdDivergenceCustomValue = ref(0)
      
      // KDJ指标相关的响应式变量
      const kdjKValue = ref(9)
      const kdjKCompare = ref('大于')
      const kdjKCustomValue = ref(0)
      const kdjDValue = ref(3)
      const kdjDCompare = ref('大于')
      const kdjDCustomValue = ref(0)
      const kdjJValue = ref(3)
      const kdjJCompare = ref('大于')
      const kdjJCustomValue = ref(0)
      const kdjGoldenKPeriod = ref(9)
      const kdjGoldenDPeriod = ref(3)
      const kdjGoldenJPeriod = ref(3)
      const kdjDeathKPeriod = ref(9)
      const kdjDeathDPeriod = ref(3)
      const kdjDeathJPeriod = ref(3)
      const kdjShortPeriod = ref(9)
      const kdjLongPeriod = ref(3)
      const kdjTrendJPeriod = ref(3)
      const kdjTrendCompare = ref('大于')
      const kdjTrendCustomValue = ref(0)
      const kdjDivergenceJPeriod = ref(3)
      const kdjDivergenceCompare = ref('大于')
      const kdjDivergenceCustomValue = ref(0)
      
      // RSI指标相关的响应式变量
      const rsiShortPeriod = ref(6)
      const rsiLongPeriod = ref(12)
      const rsiCompare = ref('大于')
      const rsiCustomValue = ref(0)
      const rsiCrossCompare = ref('大于')
      const rsiCrossCustomValue = ref(0)
      const rsiTrendCompare = ref('大于')
      const rsiTrendCustomValue = ref(0)
      const rsiDivergenceCompare = ref('大于')
      const rsiDivergenceCustomValue = ref(0)
      
      // BOLL指标相关的响应式变量
      const bollShortPeriod = ref(20)
      const bollLongPeriod = ref(2)
      const bollCompare = ref('大于')
      const bollCustomValue = ref(0)
  
      // BOLL指标重置设置函数
      const resetBOLLSettings = () => {
        bollShortPeriod.value = 20
        bollLongPeriod.value = 2
        bollCompare.value = '大于'
        bollCustomValue.value = 0
      }
  
      // BOLL指标应用设置函数
      const applyBOLLSettings = () => {
        const currentSignal = timingSelectedSignal.value || selectedSignal.value
        const settings = {
          signal: currentSignal,
          params: {
            shortPeriod: bollShortPeriod.value,
            longPeriod: bollLongPeriod.value,
            compare: bollCompare.value,
            value: bollCustomValue.value
          }
        }
  
        // 构建条件标题和详情
        let title = '个股择时 - BOLL指标'
        let details = ''
  
        if (currentSignal === 'boll') {
          details = `BOLL(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
        } else if (currentSignal === 'boll_upper') {
          details = `BOLL上线(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
        } else if (currentSignal === 'boll_middle') {
          details = `BOLL中线(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
        } else if (currentSignal === 'boll_lower') {
          details = `BOLL下线(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
        } else if (currentSignal === 'boll_break_upper') {
          details = `BOLL突破上轨(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
        } else if (currentSignal === 'boll_break_lower') {
          details = `BOLL突破下轨(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
        }
  
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'timing_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
  
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
  
        console.log('BOLL指标条件已添加到选股条件', condition)
  
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      
      // CR指标相关的响应式变量
      const crValue = ref(26)
      const crAValue = ref(10)
      const crBValue = ref(20)
      const crCValue = ref(40)
      const crDValue = ref(62)
      
      const resetCRSettings = () => {
        crValue.value = 26
        crAValue.value = 10
        crBValue.value = 20
        crCValue.value = 40
        crDValue.value = 62
      }
      
      const applyCRSettings = () => {
        const settings = {
          signal: selectedSignal.value,
          params: {
            cr: crValue.value,
            a: crAValue.value,
            b: crBValue.value,
            c: crCValue.value,
            d: crDValue.value
          }
        }
        
        // 构建条件标题和详情
        let title = '个股择时 - CR指标'
        let details = `CR(${settings.params.cr},${settings.params.a},${settings.params.b},${settings.params.c},${settings.params.d})`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'timing_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('CR指标条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
      
      // ATR指标相关的响应式变量
      const atrShortPeriod = ref(14)
      const atrLongPeriod = ref(1)
      const atrCompare = ref('大于')
      const atrCustomValue = ref(0)
      const atrCrossCompare = ref('大于')
      const atrCrossCustomValue = ref(0)
      const atrTrendCompare = ref('大于')
      const atrTrendCustomValue = ref(0)
      const atrDivergenceCompare = ref('大于')
      const atrDivergenceCustomValue = ref(0)
      
      // TRIX指标相关的响应式变量
      const trixShortPeriod = ref(12)
      const trixLongPeriod = ref(9)
      const trixCompare = ref('大于')
      const trixCustomValue = ref(0)
      const trixCrossCompare = ref('大于')
      const trixCrossCustomValue = ref(0)
      const trixTrendCompare = ref('大于')
      const trixTrendCustomValue = ref(0)
      const trixDivergenceCompare = ref('大于')
      const trixDivergenceCustomValue = ref(0)
      
      // CCI指标相关的响应式变量
      const cciShortPeriod = ref(14)
      const cciLongPeriod = ref(1)
      const cciCompare = ref('大于')
      const cciCustomValue = ref(0)
      const cciCrossCompare = ref('大于')
      const cciCrossCustomValue = ref(0)
      const cciTrendCompare = ref('大于')
      const cciTrendCustomValue = ref(0)
      const cciDivergenceCompare = ref('大于')
      const cciDivergenceCustomValue = ref(0)
      
      // EMA指标相关的响应式变量
      const emaShortPeriod = ref(12)
      const emaLongPeriod = ref(26)
      const emaCompare = ref('大于')
      const emaCustomValue = ref(0)
      const emaCrossCompare = ref('大于')
      const emaCrossCustomValue = ref(0)
      const emaTrendCompare = ref('大于')
      const emaTrendCustomValue = ref(0)
  
      
      // 四周期多头排列指标相关的响应式变量
      const multiBullCompare = ref('大于')
      const multiBullCustomValue = ref(0)
      
      // 在个股择时指标submenu下插入RSI菜单项
      const resetRSISettings = () => {
        if (selectedSignal.value === 'rsi') {
          rsiShortPeriod.value = 6
          rsiLongPeriod.value = 12
          rsiCompare.value = '大于'
          rsiCustomValue.value = 0
        } else if (selectedSignal.value === 'rsi_golden_cross' || selectedSignal.value === 'rsi_death_cross') {
          rsiShortPeriod.value = 6
          rsiLongPeriod.value = 12
          rsiCrossCompare.value = '大于'
          rsiCrossCustomValue.value = 0
        } else if (selectedSignal.value === 'rsi_bull' || selectedSignal.value === 'rsi_bear') {
          rsiShortPeriod.value = 14
          rsiLongPeriod.value = 28
          rsiTrendCompare.value = '大于'
          rsiTrendCustomValue.value = 0
        } else if (selectedSignal.value === 'rsi_bottom_divergence' || selectedSignal.value === 'rsi_top_divergence') {
          rsiShortPeriod.value = 14
          rsiLongPeriod.value = 28
          rsiDivergenceCompare.value = '大于'
          rsiDivergenceCustomValue.value = 0
        }
      }
      const applyRSISettings = () => {
        const settings = { signal: selectedSignal.value, params: {} }
        if (selectedSignal.value === 'rsi') {
          settings.params = {
            shortPeriod: rsiShortPeriod.value,
            longPeriod: rsiLongPeriod.value,
            compare: rsiCompare.value,
            value: rsiCustomValue.value
          }
        } else if (selectedSignal.value === 'rsi_golden_cross' || selectedSignal.value === 'rsi_death_cross') {
          settings.params = {
            shortPeriod: rsiShortPeriod.value,
            longPeriod: rsiLongPeriod.value,
            compare: rsiCrossCompare.value,
            value: rsiCrossCustomValue.value
          }
        } else if (selectedSignal.value === 'rsi_bull' || selectedSignal.value === 'rsi_bear') {
          settings.params = {
            shortPeriod: rsiShortPeriod.value,
            longPeriod: rsiLongPeriod.value,
            compare: rsiTrendCompare.value,
            value: rsiTrendCustomValue.value
          }
        } else if (selectedSignal.value === 'rsi_bottom_divergence' || selectedSignal.value === 'rsi_top_divergence') {
          settings.params = {
            shortPeriod: rsiShortPeriod.value,
            longPeriod: rsiLongPeriod.value,
            compare: rsiDivergenceCompare.value,
            value: rsiDivergenceCustomValue.value
          }
        }
        console.log('应用RSI设置', settings)
      }
  
      // 在个股择时指标submenu下插入BOLL、CR、ATR、TRIX菜单项
      const bbicPeriod1 = ref(6)
      const bbicPeriod2 = ref(12)
      const bbicPeriod3 = ref(18)
      const bbicPeriod4 = ref(24)
      const bbicCompare = ref('大于')
      const bbicCustomValue = ref(0)
      const bbicTargetValue = ref(0)
      
      const resetEMASettings = () => {
        const currentSignal = timingSelectedSignal.value || selectedSignal.value
        
        if (currentSignal === 'ema') {
          emaShortPeriod.value = 12
          emaLongPeriod.value = 26
          emaCompare.value = '大于'
          emaCustomValue.value = 0
        } else if (currentSignal === 'ema_golden_cross' || currentSignal === 'ema_death_cross') {
          emaShortPeriod.value = 6
          emaLongPeriod.value = 12
          emaCrossCompare.value = '大于'
          emaCrossCustomValue.value = 0
        } else if (currentSignal === 'ema_bull' || currentSignal === 'ema_bear') {
          emaShortPeriod.value = 14
          emaLongPeriod.value = 28
          emaTrendCompare.value = '大于'
          emaTrendCustomValue.value = 0
        }
      }
      
      const applyEMASettings = () => {
        const currentSignal = timingSelectedSignal.value || selectedSignal.value
        const settings = {
          signal: currentSignal,
          params: {}
        }
  
        if (currentSignal === 'ema') {
          settings.params = {
            shortPeriod: emaShortPeriod.value,
            longPeriod: emaLongPeriod.value,
            compare: emaCompare.value,
            value: emaCustomValue.value
          }
        } else if (currentSignal === 'ema_golden_cross' || currentSignal === 'ema_death_cross') {
          settings.params = {
            shortPeriod: emaShortPeriod.value,
            longPeriod: emaLongPeriod.value,
            compare: emaCrossCompare.value,
            value: emaCrossCustomValue.value
          }
        } else if (currentSignal === 'ema_bull' || currentSignal === 'ema_bear') {
          settings.params = {
            shortPeriod: emaShortPeriod.value,
            longPeriod: emaLongPeriod.value,
            compare: emaTrendCompare.value,
            value: emaTrendCustomValue.value
          }
        }
  
        // 构建条件标题和详情
        let title = '个股择时 - EMA指标'
        let details = ''
  
        if (currentSignal === 'ema') {
          details = `EMA(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
        } else if (currentSignal === 'ema_golden_cross') {
          details = `EMA金叉(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
        } else if (currentSignal === 'ema_death_cross') {
          details = `EMA死叉(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
        } else if (currentSignal === 'ema_bull') {
          details = `EMA多头(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
        } else if (currentSignal === 'ema_bear') {
          details = `EMA空头(${settings.params.shortPeriod},${settings.params.longPeriod}) ${settings.params.compare} ${settings.params.value}`
        }
  
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'timing_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
  
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
  
        console.log('EMA指标条件已添加到选股条件', condition)
  
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
      const resetBBICSettings = () => {
        bbicPeriod1.value = 5
        bbicPeriod2.value = 10
        bbicPeriod3.value = 20
        bbicPeriod4.value = 60
        bbicCompare.value = '大于'
        bbicCustomValue.value = 0
        bbicTargetValue.value = 0
      }
      const applyBBICSettings = () => {
        const settings = {
          signal: timingSelectedSignal.value || selectedSignal.value,
          params: {
            period1: bbicPeriod1.value,
            period2: bbicPeriod2.value,
            period3: bbicPeriod3.value,
            period4: bbicPeriod4.value,
            compare: bbicCompare.value,
            customValue: bbicCustomValue.value,
            targetValue: bbicTargetValue.value
          }
        }
        
        // 构建条件标题和详情
        let title = '个股择时 - BBIC指标'
        let details = `BBIC(${settings.params.period1},${settings.params.period2},${settings.params.period3},${settings.params.period4}) ${settings.params.compare} ${settings.params.targetValue}`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'timing_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('BBIC指标条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
      const multiBullPeriod1 = ref(5)
      const multiBullPeriod2 = ref(10)
      const multiBullPeriod3 = ref(20)
      const multiBullPeriod4 = ref(60)
      const resetMultiBullSettings = () => {
        multiBullPeriod1.value = 5
        multiBullPeriod2.value = 10
        multiBullPeriod3.value = 20
        multiBullPeriod4.value = 60
      }
      const applyMultiBullSettings = () => {
        const settings = {
          signal: selectedSignal.value,
          params: {
            period1: multiBullPeriod1.value,
            period2: multiBullPeriod2.value,
            period3: multiBullPeriod3.value,
            period4: multiBullPeriod4.value
          }
        }
        
        // 构建条件标题和详情
        let title = '个股择时 - 四周期多头排列'
        let details = `四周期多头排列 MA(${settings.params.period1},${settings.params.period2},${settings.params.period3},${settings.params.period4})`
        
        // 创建条件对象
        const condition = {
          id: Date.now() + Math.random(),
          type: 'timing_indicator',
          title: title,
          details: details,
          enabled: true,
          config: settings
        }
        
        // 添加到选股条件列表
        selectedConditions.value.push(condition)
        
        console.log('四周期多头排列条件已添加到选股条件', condition)
        
        // 应用设置后关闭子菜单
        activeSubMenu.value = ''
      }
  
  
  
      // 辅助函数：从条件对象中确定择时类型
      const getTimingTypeFromCondition = (condition) => {
        if (condition.type?.includes('market_')) return '大盘择时'
        if (condition.type?.includes('sector_')) return '板块择时'
        if (condition.type?.includes('stock_')) return '个股择时'
        if (condition.title?.includes('大盘择时')) return '大盘择时'
        if (condition.title?.includes('板块择时')) return '板块择时'
        if (condition.title?.includes('个股择时')) return '个股择时'
        return '个股择时' // 默认
      }

      // 运行回测函数
      const applyFilter = async () => {
        console.log('🚀 运行回测', {
          stockSelectionStartDate: stockSelectionStartDate.value,
          stockSelectionEndDate: stockSelectionEndDate.value,
          initialCapital: initialCapital.value,
          dataFrequency: dataFrequency.value,
          minuteInterval: minuteInterval.value,
          selectedConditions: selectedConditions.value
        })
        
        // 收集当前筛选条件
        const filterParams = {
          // 选股日期区间
          stockSelectionStartDate: stockSelectionStartDate.value,
          stockSelectionEndDate: stockSelectionEndDate.value,
          // 回测参数
          initialCapital: initialCapital.value,
          dataFrequency: dataFrequency.value,
          minuteInterval: minuteInterval.value,
          // 选中的条件
          selectedConditions: selectedConditions.value,
          // 当前选中的指标类型
          activeSubMenu: activeSubMenu.value,
          // 添加时间戳确保参数唯一性
          timestamp: Date.now()
        }
        
        console.log('📊 即将传递的参数:', filterParams)
        
        try {
          // 调用启动回测API
          const startDate = stockSelectionStartDate.value.replace(/-/g, '')
          const endDate = stockSelectionEndDate.value.replace(/-/g, '')
          const backtestData = {
            start_date: startDate,
            end_date: endDate,
            initial_capital: initialCapital.value * 10000, // 转换为元
            data_frequency: dataFrequency.value,
            minute_interval: minuteInterval.value
          }
          
          console.log('🚀 启动回测API调用，参数:', backtestData)
          
          // 处理选中的指标条件
          const indicators = []
          const indicatorDetails = {}
          
          // 分析选中的条件，按择时类型分类
          selectedConditions.value.forEach(condition => {
            const conditionType = condition.type || condition.category
            const timingType = condition.timingType || getTimingTypeFromCondition(condition) || '个股择时' // 默认为个股择时
            
            console.log('📊 处理条件:', condition)
            
            if (conditionType === 'market_ma' || conditionType === 'sector_ma' || conditionType === 'stock_ma' || conditionType === 'MA指标设置') {
              indicators.push('MA')
              if (!indicatorDetails.MA) indicatorDetails.MA = []
              indicatorDetails.MA.push({
                timingType: timingType,
                shortPeriod: condition.config?.ma?.short || condition.shortPeriod || 5,
                longPeriod: condition.config?.ma?.long || condition.longPeriod || 20,
                ...condition
              })
            } else if (conditionType === 'market_macd' || conditionType === 'sector_macd' || conditionType === 'stock_macd' || conditionType === 'MACD指标') {
              indicators.push('MACD')
              if (!indicatorDetails.MACD) indicatorDetails.MACD = []
              indicatorDetails.MACD.push({
                timingType: timingType,
                ...condition
              })
            } else if (conditionType === 'market_kdj' || conditionType === 'sector_kdj' || conditionType === 'stock_kdj' || conditionType === 'KDJ指标') {
              indicators.push('KDJ')
              if (!indicatorDetails.KDJ) indicatorDetails.KDJ = []
              indicatorDetails.KDJ.push({
                timingType: timingType,
                ...condition
              })
            }
          })
          
          // 去重指标数组
          const uniqueIndicators = [...new Set(indicators)]
          
          // 更新回测数据，包含指标信息
          const backtestDataWithIndicators = {
            ...backtestData,
            indicators: uniqueIndicators,
            indicator_details: indicatorDetails,
            strategy_type: 'indicator_driven' // 指标驱动策略
          }
          
          console.log('🎯 包含指标的回测参数:', backtestDataWithIndicators)
          
          const response = await fetch('http://localhost:8002/api/backtest/run/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(backtestDataWithIndicators)
          })
          
          console.log('📡 API响应状态:', response.status)
          console.log('📡 API响应头:', response.headers)
          
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`)
          }
          
          const result = await response.json()
          console.log('🎯 回测启动结果:', result)
          
          if (result.status === 'success') {
            console.log('✅ 回测启动成功，准备跳转...')
            // 立即跳转到回测详情页面
            router.push({
              name: 'BacktestDetails',
              query: filterParams
            })
          } else {
            console.error('❌ 启动回测失败:', result.message)
            alert('启动回测失败: ' + result.message)
          }
        } catch (error) {
          console.error('❌ 调用回测API失败:', error)
          console.error('❌ 错误详情:', {
            name: error.name,
            message: error.message,
            stack: error.stack
          })
          
          // 显示详细的错误信息
          alert(`API调用失败: ${error.message}\n\n请检查:\n1. 后端服务是否在8002端口运行\n2. 网络连接是否正常\n3. 浏览器控制台的详细错误信息`)
          
          // 即使API调用失败，也跳转到回测页面（使用模拟数据）
          console.log('⚠️ 使用模拟数据继续跳转...')
          router.push({
            name: 'BacktestDetails',
            query: filterParams
          })
        }
      }
  
      return {
        activeMenu,
        activeSubMenu,
        stockFilterRef,
        selectedConditions,

        // 筛选条件相关变量
        stockSelectionStartDate,
        stockSelectionEndDate,
        
        // 回测参数变量
        initialCapital,
        dataFrequency,
        minuteInterval,
        
        // 筛选条件函数
        applyFilter,
        marketIndices,
        periods,
        selectedIndex,
        selectedPeriod,
        maSettings,
        selectedMacdIndex,
        selectedMacdPeriod,
        macdSettings,
        selectedKdjIndex,
        selectedKdjPeriod,
        kdjSettings,
        // 金叉死叉设置
        maGoldenCrossChecked,
        maDeathCrossChecked,
        macdGoldenCrossChecked,
        macdDeathCrossChecked,
        kdjGoldenCrossChecked,
        kdjDeathCrossChecked,
        // 板块择时相关变量
        sectorIndices,
        sectorSearchText,
        filteredSectorOptions,
        sectorMaGoldenCrossChecked,
        sectorMaDeathCrossChecked,
        sectorMacdGoldenCrossChecked,
        sectorMacdDeathCrossChecked,
        sectorKdjGoldenCrossChecked,
        sectorKdjDeathCrossChecked,
        // 板块择时相关函数
        filterSectorOptions,
        selectSectorOption,
        selectedSectorIndex,
        selectedSectorPeriod,
        sectorSettings,
        selectedSectorMacdIndex,
        selectedSectorMacdPeriod,
        sectorMacdSettings,
        selectedSectorKdjIndex,
        selectedSectorKdjPeriod,
        sectorKdjSettings,
        toggleMenu,
        openSubMenu,
        removeCondition,
        toggleCondition,
        clearAllConditions,
        resetMaSettings,
        applyMaSettings,
        resetMacdSettings,
        applyMacdSettings,
        resetKdjSettings,
        applyKdjSettings,
        resetSectorSettings,
        applySectorSettings,
        resetSectorMacdSettings,
        applySectorMacdSettings,
        resetSectorKdjSettings,
        applySectorKdjSettings,
        resetAll,
        applyAll,
        searchText,
        showDropdown,
        filteredOptions,
        toggleDropdown,
        filterOptions,
        selectOption,
        // MA设置相关的状态
        selectedSignal, // 'golden', 'short', 'long'
        timingSelectedSignal, // 个股择时指标信号
        shortMA,
        longMA,
        shortMACompare,
        longMACompare,
        customFloat,
        // 添加新的返回值
        macdValue,
        macdCompare,
        macdCustomValue,
        deaValue,
        deaCompare,
        deaCustomValue,
        difValue,
        difCompare,
        difCustomValue,
        difTargetValue,
        deaTargetValue,
        macdTargetValue,
        timingMacdSettings,
        timingKdjSettings,
        kdjKTargetValue,
        kdjDTargetValue,
        kdjJTargetValue,
        timingRsiSettings,
        rsiTargetValue,
        timingBollSettings,
        bollTargetValue,
        timingCrSettings,
        crTargetValue,
        timingTrixSettings,
        trixTargetValue,
        // MA设置相关的方法
        selectSignal,
        selectTimingSignal,
        resetMASettings,
        applyMASettings,
        // 参数相关的状态
        paramValue,
        compareOperator,
        customValue,
        difPeriod,
        deaPeriod,
        macdPeriod,
        trendPeriod,
        confirmPeriod,
        deviation,
        divergencePeriod,
        divergenceRange,
        // 获取参数标签
        getParamLabel,
        // 获取周期placeholder
        getPeriodPlaceholder,
        // 重置设置
        resetSettings,
        // 应用设置
        applySettings,
        // 添加金叉相关的变量
        goldenDifPeriod,
        goldenDeaPeriod,
        goldenMacdPeriod,
        goldenConfirmDays,
        goldenSlope,
        // 添加死叉相关的变量
        deathDifPeriod,
        deathDeaPeriod,
        deathMacdPeriod,
        deathConfirmDays,
        deathSlope,
        rsiShortPeriod,
        rsiLongPeriod,
        rsiCompare,
        rsiCustomValue,
        rsiCrossCompare,
        rsiCrossCustomValue,
        rsiTrendCompare,
        rsiTrendCustomValue,
        rsiDivergenceCompare,
        rsiDivergenceCustomValue,
        resetRSISettings,
        applyRSISettings,
        // MA指标相关的变量
        maShortPeriod,
        maLongPeriod,
        maCompare,
        maCustomValue,
        maCrossCompare,
        maCrossCustomValue,
        maTrendCompare,
        maTrendCustomValue,
        maDivergenceCompare,
        maDivergenceCustomValue,
        // MACD指标相关的变量
        macdShortPeriod,
        macdLongPeriod,
        macdTrendCompare,
        macdTrendCustomValue,
        macdDivergenceCompare,
        macdDivergenceCustomValue,
        // KDJ指标相关的变量
        kdjKValue,
        kdjKCompare,
        kdjKCustomValue,
        kdjDValue,
        kdjDCompare,
        kdjDCustomValue,
        kdjJValue,
        kdjJCompare,
        kdjJCustomValue,
        kdjGoldenKPeriod,
        kdjGoldenDPeriod,
        kdjGoldenJPeriod,
        kdjShortPeriod,
        kdjLongPeriod,
        kdjTrendCompare,
        kdjTrendCustomValue,
        kdjDivergenceCompare,
        kdjDivergenceCustomValue,
        // RSI指标相关的变量
        rsiShortPeriod,
        rsiLongPeriod,
        rsiCompare,
        rsiCustomValue,
        rsiCrossCompare,
        rsiCrossCustomValue,
        rsiTrendCompare,
        rsiTrendCustomValue,
        rsiDivergenceCompare,
        rsiDivergenceCustomValue,
        // BOLL指标相关的变量
        bollShortPeriod,
        bollLongPeriod,
        bollCompare,
        bollCustomValue,
        resetBOLLSettings,
        applyBOLLSettings,
  
  
        // CR指标相关的变量
        crValue,
        crAValue,
        crBValue,
        crCValue,
        crDValue,
        // ATR指标相关的变量
        atrShortPeriod,
        atrCompare,
        atrCustomValue,
        atrTrendCompare,
        atrTrendCustomValue,
        // TRIX指标相关的变量
        trixShortPeriod,
        trixLongPeriod,
        trixCompare,
        trixCustomValue,
        trixCrossCompare,
        trixCrossCustomValue,
        // CCI指标相关的变量
        cciShortPeriod,
        cciCompare,
        cciCustomValue,
        cciTrendCompare,
        cciTrendCustomValue,
        // EMA指标相关的变量
        emaShortPeriod,
        emaLongPeriod,
        emaCompare,
        emaCustomValue,
        emaCrossCompare,
        emaCrossCustomValue,
        emaTrendCompare,
        emaTrendCustomValue,
        // 四周期多头排列指标相关的变量
        multiBullPeriod1,
        multiBullPeriod2,
        multiBullPeriod3,
        multiBullPeriod4,
        // 股票价格相关的变量
        openPriceCompare,
        openPriceIndicator,
        closePriceCompare,
        closePriceIndicator,
        highPriceCompare,
        highPriceIndicator,
        lowPriceCompare,
        lowPriceIndicator,
        prevClosePriceCompare,
        prevClosePriceIndicator,
        avgPriceCompare,
        avgPriceIndicator,
        // 股票价格相关的函数
        resetOpenPriceSettings,
        applyOpenPriceSettings,
        resetClosePriceSettings,
        applyClosePriceSettings,
        resetHighPriceSettings,
        applyHighPriceSettings,
        resetLowPriceSettings,
        applyLowPriceSettings,
        resetPrevClosePriceSettings,
        applyPrevClosePriceSettings,
        resetAvgPriceSettings,
        applyAvgPriceSettings,
        // 新增菜单相关变量
        changeRateCompare,
        changeRateRangeCustomValue,
        volumeRatioCompare,
        volumeRatioCustomValue,
        turnoverCompare,
        turnoverCustomValue,
        turnoverIndicator,
        turnoverRateCompare,
        turnoverRateIndicator,
        turnoverRateCustomValue,
        marketValueCompare,
        marketValueIndicator,
        marketValueCustomValue,
        volumeCompare,
        volumeIndicator,
        volumeCustomValue,
        netInflowCompare,
        netInflowAmount,
        // 新增菜单相关函数
        resetChangeRateSettings,
        applyChangeRateSettings,
        resetVolumeRatioSettings,
        applyVolumeRatioSettings,
        resetTurnoverSettings,
        applyTurnoverSettings,
        resetTurnoverRateSettings,
        applyTurnoverRateSettings,
        resetMarketValueSettings,
        applyMarketValueSettings,
        resetVolumeSettings,
        applyVolumeSettings,
        resetNetInflowSettings,
        applyNetInflowSettings,
        // 公告类相关变量
        shareholderReductionCompare,
        shareholderReductionAmount,
        shareholderReductionChecked,
        shareholderIncreaseCompare,
        shareholderIncreaseAmount,
        shareholderIncreaseChecked,
        shareholderDividendCompare,
        shareholderDividendAmount,
        shareholderDividendChecked,
        violationInquiryCompare,
        violationInquiryAmount,
        violationInquiryChecked,
        performanceForecastCompare,
        performanceForecastAmount,
        netProfitCompare,
        netProfitAmount,
        selectedSignal,
        performanceAnnouncementCompare,
        performanceAnnouncementAmount,
        netProfitAnnouncementCompare,
        netProfitAnnouncementAmount,
        selectedSignalAnnouncement,
        // 公告类相关函数
        resetShareholderReductionSettings,
        applyShareholderReductionSettings,
        resetShareholderIncreaseSettings,
        applyShareholderIncreaseSettings,
        resetShareholderDividendSettings,
        applyShareholderDividendSettings,
        resetViolationInquirySettings,
        applyViolationInquirySettings,
        resetPerformanceForecastSettings,
        applyPerformanceForecastSettings,
        resetPerformanceAnnouncementSettings,
        applyPerformanceAnnouncementSettings,
        // 涨幅菜单相关变量
        changeRateType,
        changeRateValue,
        changeRateRangeValue,
        changeRateRangeDays,
        changeRateRangeCustomValue,
        // 涨幅菜单相关函数
        resetChangeRateSettings,
        applyChangeRateSettings,
        // 过滤项相关变量
        filterNewListingChecked,
        filterBeijingChecked,
        filterMainBoardChecked,
        filterStChecked,
        filterStarStChecked,
        filterSuspensionChecked,
        filterStarMarketChecked,
        filterGrowthBoardChecked,
        filterDelistingChecked,
        // 过滤项相关函数
        resetFilterNewListingSettings,
        applyFilterNewListingSettings,
        resetFilterBeijingSettings,
        applyFilterBeijingSettings,
        resetFilterMainBoardSettings,
        applyFilterMainBoardSettings,
        resetFilterStSettings,
        applyFilterStSettings,
        resetFilterStarStSettings,
        applyFilterStarStSettings,
        resetFilterSuspensionSettings,
        applyFilterSuspensionSettings,
        resetFilterStarMarketSettings,
        applyFilterStarMarketSettings,
        resetFilterGrowthBoardSettings,
        applyFilterGrowthBoardSettings,
        resetFilterDelistingSettings,
        applyFilterDelistingSettings,
        // 财务指标相关变量
        roaCompare,
        roaCustomValue,
        roeCompare,
        roeCustomValue,
        grossMarginCompare,
        grossMarginCustomValue,
        netMarginCompare,
        netMarginCustomValue,
        revenueGrowthCompare,
        revenueGrowthCustomValue,
        profitGrowthCompare,
        profitGrowthCustomValue,
        dynamicPeCompare,
        dynamicPeCustomValue,
        pbRatioCompare,
        pbRatioCustomValue,
        psRatioCompare,
        psRatioCustomValue,
        staticPeCompare,
        staticPeCustomValue,
        // 财务指标相关函数
        resetRoaSettings,
        applyRoaSettings,
        resetRoeSettings,
        applyRoeSettings,
        resetGrossMarginSettings,
        applyGrossMarginSettings,
        resetNetMarginSettings,
        applyNetMarginSettings,
        resetRevenueGrowthSettings,
        applyRevenueGrowthSettings,
        resetProfitGrowthSettings,
        applyProfitGrowthSettings,
        resetDynamicPeSettings,
        applyDynamicPeSettings,
        resetPbRatioSettings,
        applyPbRatioSettings,
        resetPsRatioSettings,
        applyPsRatioSettings,
        resetStaticPeSettings,
        applyStaticPeSettings,
        // BBIC指标相关的变量
        bbicPeriod1,
        bbicPeriod2,
        bbicPeriod3,
        bbicPeriod4,
        bbicCompare,
        bbicCustomValue,
        bbicTargetValue,
        resetBBICSettings,
        applyBBICSettings,
        resetEMASettings,
        applyEMASettings,
        resetCRSettings,
        applyCRSettings,
        resetMultiBullSettings,
        applyMultiBullSettings
      }
    }
  })
  </script>
  
  <style scoped>
  .menu-layout {
    min-height: 100vh;
    background-color: #f5f7fa;
    padding: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  
  .content-wrapper {
    flex: 1;
    display: flex;
    gap: 20px;
    padding: 20px;
    max-width: none;
    width: 100%;
    height: 100vh;
    overflow: hidden;
  }
  
  .menu-container {
    width: 480px;
    min-width: 400px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    flex-shrink: 0;
  }
  
  .conditions-container {
    flex: 1;
    min-width: 480px;
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
    display: flex;
    flex-direction: column;
  }
  
  /* 右侧容器滚动条样式 */
  .conditions-container::-webkit-scrollbar {
    width: 6px;
  }
  
  .conditions-container::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
  }
  
  .conditions-container::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
  }
  
  .conditions-container::-webkit-scrollbar-thumb:hover {
    background: #a8b3c0;
  }
  
  /* 筛选条件样式 */
  .filter-section {
    margin-bottom: 15px;
    padding: 12px;
    background: #f8f9fa;
    border-radius: 6px;
    border: 1px solid #e9ecef;
  }
  
  .section-header {
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid #dee2e6;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .section-header h6 {
    color: #495057;
    font-weight: 600;
    margin: 0;
  }
  
  .form-group {
    margin-bottom: 12px;
  }
  
  .form-label {
    display: block;
    margin-bottom: 5px;
    font-size: 14px;
    font-weight: 500;
    color: #495057;
  }
  
  .form-control,
  .form-select {
    width: 100%;
    padding: 6px 10px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 13px;
    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
  }
  
  .form-control:focus,
  .form-select:focus {
    border-color: #4a90e2;
    outline: 0;
    box-shadow: 0 0 0 0.2rem rgba(74, 144, 226, 0.25);
  }
  
  .date-range {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .date-separator {
    color: #6c757d;
    font-size: 14px;
  }
  
  .btn-run-backtest {
    width: 100%;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 500;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }
  
  .btn-run-backtest {
    background: #007bff;
    color: white;
  }
  
  .btn-run-backtest:hover {
    background: #0056b3;
  }
  
  .conditions-list {
    max-height: 400px;
    overflow-y: auto;
    border-top: 1px solid #e9ecef;
    padding-top: 15px;
    margin-top: 15px;
  }
  
  .empty-conditions {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 30px 15px;
    color: #999;
    text-align: center;
  }
  
  .empty-conditions i {
    font-size: 48px;
    margin-bottom: 16px;
    color: #ddd;
  }
  
  .empty-conditions span {
    font-size: 14px;
  }
  
  .condition-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    margin-bottom: 6px;
    background: #f8f9fa;
    border-radius: 6px;
    border-left: 4px solid #4a90e2;
    transition: all 0.3s ease;
  }
  
  .condition-item:hover {
    background: #e3f2fd;
    transform: translateX(2px);
  }
  
  .condition-content {
    flex: 1;
    margin-right: 12px;
  }
  
  .condition-title {
    font-weight: 500;
    color: #333;
    margin-bottom: 4px;
    font-size: 14px;
  }
  
  .condition-details {
    color: #666;
    font-size: 12px;
  }
  
  .condition-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  
  .condition-toggle {
    display: none; /* 隐藏绿色开关按钮 */
  }
  
  .condition-remove {
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: all 0.2s ease;
    font-size: 14px;
    color: #f44336;
  }
  
  .condition-remove:hover {
    background: rgba(244, 67, 54, 0.1);
  }
  
  .backtest-section {
    margin-top: auto;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    text-align: center;
  }
  
  .menu-header {
    padding: 20px;
    font-size: 16px;
    font-weight: 500;
    border-bottom: 1px solid #eee;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .menu-list {
    flex: 1;
    overflow-y: auto;
    max-height: 70vh;
    min-height: 0;
    padding: 10px 0;
    display: flex;
    flex-direction: column;
  }
  
  /* 响应式设计 */
  @media (max-width: 1200px) {
    .content-wrapper {
      gap: 16px;
      padding: 16px;
    }
    
    .menu-container {
      width: 420px;
      min-width: 380px;
    }
    
    .conditions-container {
      min-width: 420px;
    }
  }
  
  @media (max-width: 768px) {
    .content-wrapper {
      flex-direction: column;
      padding: 12px;
      gap: 12px;
      height: auto;
      min-height: 100vh;
      overflow: visible;
    }
    
    .menu-container {
      width: 100%;
      min-width: auto;
      height: auto;
      max-height: 45vh;
      flex-shrink: 0;
    }
    
    .conditions-container {
      width: 100%;
      min-width: auto;
      height: auto;
      flex: 1;
      min-height: 45vh;
    }
    
    .menu-list {
      max-height: 35vh;
    }
    
    .section-header h6 {
      font-size: 16px;
    }
    
    .form-control, .form-select {
      height: 40px;
      padding: 10px 14px;
    }
    
    .menu-header {
      padding: 16px;
      font-size: 15px;
    }
    
    .menu-item-header {
      padding: 12px 20px;
      min-height: 48px;
    }
    
    .submenu-item {
      padding: 10px 20px;
      min-height: 40px;
    }
  }
  
  @media (max-width: 480px) {
    .content-wrapper {
      padding: 8px;
      gap: 8px;
    }
    
    .menu-container {
      max-height: 40vh;
    }
    
    .conditions-container {
      min-height: 40vh;
      padding: 12px;
    }
    
    .menu-item-header {
      padding: 10px 16px;
      min-height: 44px;
    }
    
    .submenu-item {
      padding: 8px 16px;
      min-height: 36px;
    }
    
    .section-header {
      margin-bottom: 10px;
      padding-bottom: 8px;
    }
    
    .section-header h6 {
      font-size: 15px;
    }
    
    .form-group {
      margin-bottom: 12px;
    }
    
    .form-label {
      font-size: 13px;
      margin-bottom: 6px;
    }
    
    .form-control, .form-select {
      height: 36px;
      padding: 8px 12px;
      font-size: 13px;
    }
    
    .btn-run-backtest {
      padding: 10px 16px;
      font-size: 14px;
    }
    
    .condition-item {
      padding: 12px 16px;
      margin-bottom: 8px;
    }
    
    .empty-conditions {
      padding: 24px 16px;
    }
    
    .empty-conditions i {
      font-size: 40px;
      margin-bottom: 12px;
    }
    
    .empty-conditions span {
      font-size: 13px;
    }
  }
  
  @media (max-width: 360px) {
    .content-wrapper {
      padding: 6px;
      gap: 6px;
    }
    
    .menu-container {
      max-height: 35vh;
    }
    
    .conditions-container {
      min-height: 35vh;
      padding: 10px;
    }
    
    .menu-item-header {
      padding: 8px 12px;
      min-height: 40px;
    }
    
    .submenu-item {
      padding: 6px 12px;
      min-height: 32px;
    }
    
    .section-header h6 {
      font-size: 14px;
    }
    
    .form-control, .form-select {
      height: 32px;
      padding: 6px 10px;
      font-size: 12px;
    }
    
    .btn-run-backtest {
      padding: 8px 12px;
      font-size: 13px;
    }
  }
  
  /* 美化滚动条 */
  .menu-list::-webkit-scrollbar,
  .submenu::-webkit-scrollbar,
  .ma-settings::-webkit-scrollbar,
  .price-settings::-webkit-scrollbar,
  .param-content::-webkit-scrollbar {
    width: 8px;
  }
  
  .menu-list::-webkit-scrollbar-track,
  .submenu::-webkit-scrollbar-track,
  .ma-settings::-webkit-scrollbar-track,
  .price-settings::-webkit-scrollbar-track,
  .param-content::-webkit-scrollbar-track {
    background: #f8f9fa;
    border-radius: 4px;
  }
  
  .menu-list::-webkit-scrollbar-thumb,
  .submenu::-webkit-scrollbar-thumb,
  .ma-settings::-webkit-scrollbar-thumb,
  .price-settings::-webkit-scrollbar-thumb,
  .param-content::-webkit-scrollbar-thumb {
    background: #c1c7d0;
    border-radius: 4px;
    border: 2px solid #f8f9fa;
  }
  
  .menu-list::-webkit-scrollbar-thumb:hover,
  .submenu::-webkit-scrollbar-thumb:hover,
  .ma-settings::-webkit-scrollbar-thumb:hover,
  .price-settings::-webkit-scrollbar-thumb:hover,
  .param-content::-webkit-scrollbar-thumb:hover {
    background: #a8b3c0;
  }
  
  .menu-item {
    border-bottom: 1px solid #eee;
    margin-bottom: 8px;
    position: relative;
  }
  
  .menu-item:last-child {
    border-bottom: none;
  }
  
  /* 调整菜单项的内边距，让内容更加舒适 */
  .menu-item-header {
    padding: 12px 25px;
    display: flex;
    align-items: center;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    min-height: 44px;
    -webkit-tap-highlight-color: transparent;
    touch-action: manipulation;
  }
  
  .menu-item-header:hover {
    background-color: #f8f9fa;
    transform: translateX(2px);
  }
  
  .menu-item.active .menu-item-header {
    background-color: #f0f7ff;
    color: #4a90e2;
    border-right: 3px solid #4a90e2;
  }
  
  .menu-item.active .menu-item-header::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: #4a90e2;
  }
  
  .menu-item i {
    margin-right: 10px;
  }
  
  .count {
    margin-left: auto;
    background: #f5f7fa;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 12px;
    color: #999;
  }
  
  .arrow {
    margin-left: 10px;
    transition: transform 0.3s;
  }
  
  .arrow.expanded {
    transform: rotate(90deg);
  }
  
  .submenu {
    background: #f8f9fa;
    max-height: 60vh;
    overflow-y: auto;
  }
  
  .submenu-item {
    padding: 10px 25px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    min-height: 40px;
    -webkit-tap-highlight-color: transparent;
    touch-action: manipulation;
  }
  
  .submenu-item:hover {
    background-color: #f0f7ff;
    color: #4a90e2;
    transform: translateX(3px);
  }
  
  .submenu-item.active {
    background-color: #e3f2fd;
    color: #4a90e2;
    border-left: 3px solid #4a90e2;
    margin-left: 3px;
  }
  
  .submenu-item.active::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: #4a90e2;
  }
  
  .menu-footer {
    padding: 15px;
    display: flex;
    gap: 10px;
    border-top: 1px solid #eee;
  }
  
  .btn-reset,
  .btn-apply {
    flex: 1;
    padding: 8px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s;
  }
  
  .btn-reset {
    border: 1px solid #ddd;
    background: white;
    color: #666;
  }
  
  .btn-apply {
    background: #4a90e2;
    border: none;
    color: white;
  }
  
  .btn-reset:hover {
    background-color: #f8f9fa;
  }
  
  .btn-apply:hover {
    opacity: 0.9;
  }
  
  .content-area {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
  }
  
  /* 条件样式 - 已合并到section-header中 */
  
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
    width: 100px;
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
  
    .ma-settings {
    padding: 20px 25px;
    background: #f8f9fa;
    border-top: 1px solid #eee;
    max-height: 50vh;
    overflow-y: auto;
  }
  
  .price-settings {
    padding: 20px 25px;
    background: #f8f9fa;
    border-top: 1px solid #eee;
    max-height: 50vh;
    overflow-y: auto;
  }
  
    .price-label {
      display: inline-block;
      padding: 8px 12px;
      background: #e3f2fd;
      color: #1976d2;
      border-radius: 4px;
      font-weight: 500;
      font-size: 14px;
    }
  
  .setting-group {
    margin-bottom: 20px;
  }
  
  .setting-label {
    font-size: 14px;
    color: #666;
    margin-bottom: 10px;
  }
  
  /* 调整按钮组的布局 */
  .button-group {
    display: flex;
    gap: 15px;
  }
  
  .index-btn,
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
  
  .index-btn:hover,
  .period-btn:hover {
    border-color: #4a90e2;
    color: #4a90e2;
  }
  
  .index-btn.active,
  .period-btn.active {
    background: #4a90e2;
    color: white;
    border-color: #4a90e2;
  }
  
  /* 调整输入框组的布局 */
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
  }
  
  .unit {
    color: #999;
    font-size: 14px;
  }
  
  .action-buttons {
    display: flex;
    gap: 10px;
    margin-top: 20px;
  }
  
  .submenu-content {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .submenu-item i.fa-chevron-right {
    color: #999;
    font-size: 12px;
    transition: transform 0.3s;
  }
  
  .submenu-item i.fa-chevron-right.expanded {
    transform: rotate(90deg);
    color: #4a90e2;
  }
  
  .submenu-item:hover i.fa-chevron-right {
    color: #4a90e2;
  }
  
  .submenu-item.active {
    background-color: #f0f7ff;
    color: #4a90e2;
  }
  
  .submenu-item.active i.fa-chevron-right {
    color: #4a90e2;
  }
  
  .search-select {
    position: relative;
    width: 100%;
  }
  
  .select-input {
    position: relative;
    width: 100%;
  }
  
  .select-input input {
    width: 100%;
    padding: 8px 30px 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    color: #333;
    background: white;
    cursor: pointer;
  }
  
  .select-input input:focus {
    outline: none;
    border-color: #4a90e2;
  }
  
  .select-input i {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: #999;
    transition: transform 0.3s;
  }
  
  .select-input i.expanded {
    transform: translateY(-50%) rotate(180deg);
  }
  
  .select-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    max-height: 200px;
    overflow-y: auto;
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-top: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    z-index: 1000;
  }
  
  .dropdown-item {
    padding: 8px 12px;
    cursor: pointer;
    transition: all 0.3s;
  }
  
  .dropdown-item:hover {
    background: #f0f7ff;
    color: #4a90e2;
  }
  
  .dropdown-item.active {
    background: #4a90e2;
    color: white;
  }
  
  /* 美化滚动条 */
  .select-dropdown::-webkit-scrollbar {
    width: 6px;
  }
  
  .select-dropdown::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
  }
  
  .select-dropdown::-webkit-scrollbar-thumb {
    background: #ccc;
    border-radius: 3px;
  }
  
  .select-dropdown::-webkit-scrollbar-thumb:hover {
    background: #999;
  }
  
  .third-level-menu {
    padding: 20px;
  }
  
  .setting-group {
    margin-bottom: 20px;
  }
  
  .setting-label {
    font-weight: 500;
    margin-bottom: 10px;
    color: #333;
  }
  
  .button-group {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 8px;
  }
  
  .signal-btn {
    flex: 1;
    padding: 8px 16px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background: white;
    color: #495057;
    cursor: pointer;
    transition: all 0.2s ease-in-out;
    font-size: 14px;
    white-space: nowrap;
    position: relative;
    overflow: hidden;
    z-index: 10;
    pointer-events: auto;
  }
  
  .signal-btn::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    background: rgba(34, 139, 230, 0.1);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    transition: width 0.4s ease-out, height 0.4s ease-out;
  }
  
  .signal-btn:hover {
    background: #f8f9fa;
    border-color: #228be6;
    color: #228be6;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }
  
  .signal-btn:active {
    transform: translateY(1px);
    box-shadow: none;
  }
  
  .signal-btn:hover::before {
    width: 200px;
    height: 200px;
  }
  
  .signal-btn.active {
    background: #228be6;
    color: white;
    border-color: #228be6;
    box-shadow: 0 2px 4px rgba(34, 139, 230, 0.2);
  }
  
  .signal-btn.active:hover {
    background: #1c7ed6;
    transform: translateY(-1px);
  }
  
  .signal-btn:focus {
    outline: none;
    box-shadow: 0 0 0 2px rgba(34, 139, 230, 0.2);
  }
  
  .button-group {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 8px;
  }
  
  .ma-params {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }
  
  .param-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 15px;
  }
  
  .input-group {
    display: flex;
    gap: 10px;
    align-items: center;
  }
  
  .form-control {
    padding: 6px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    width: 100px;
  }
  
  .form-select {
    padding: 6px 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    width: 100px;  /* 调整宽度以适应中文 */
  }
  
  .compare-group {
    width: 100px;
  }
  
  .btn {
    padding: 8px 16px;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    transition: all 0.3s;
  }
  
  .btn-primary {
    background: #228be6;
    color: white;
  }
  
  .btn-primary:hover {
    background: #1c7ed6;
  }
  
  .btn-secondary {
    background: #e9ecef;
    color: #495057;
  }
  
  .btn-secondary:hover {
    background: #dee2e6;
  }
  
  .param-row {
    display: flex;
    gap: 15px;
    align-items: center;
    flex-wrap: wrap;
  }
  
  .param-item span {
    font-size: 14px;
    color: #495057;
  }
  
  .form-control {
    width: 80px;
    height: 32px;
    padding: 4px 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
  }
  
  .form-select {
    width: 100px;
    height: 32px;
    padding: 4px 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    background-color: white;
  }
  
  .action-buttons {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    margin-top: 20px;
  }
  
  .btn-reset, .btn-apply {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s;
  }
  
  .btn-reset {
    background: #e9ecef;
    color: #495057;
  }
  
  .btn-reset:hover {
    background: #dee2e6;
  }
  
  .btn-apply {
    background: #228be6;
    color: white;
  }
  
  .btn-apply:hover {
    background: #1c7ed6;
  }
  
  .param-table {
    background: #fff;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 20px;
  }
  
  .table-row {
    display: flex;
    align-items: center;
    border-bottom: 1px solid #eee;
  }
  
  .table-header {
    background: #f8f9fa;
    font-weight: 500;
    color: #495057;
  }
  
  .table-cell {
    flex: 1;
    padding: 12px;
    text-align: center;
  }
  
  .table-header .table-cell {
    font-size: 14px;
  }
  
  .form-control, .form-select {
    width: 100%;
    height: 32px;
    padding: 4px 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    text-align: center;
  }
  
  .form-select {
    background-color: white;
  }
  
  .action-buttons {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    margin-top: 20px;
  }
  
  .btn-reset, .btn-apply {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s;
  }
  
  .btn-reset {
    background: #e9ecef;
    color: #495057;
  }
  
  .btn-reset:hover {
    background: #dee2e6;
  }
  
  .btn-apply {
    background: #228be6;
    color: white;
  }
  
  .btn-apply:hover {
    background: #1c7ed6;
  }
  
  .param-content {
    margin-top: 20px;
    animation: fadeIn 0.3s ease-in-out;
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .indicator-section {
    margin-bottom: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    border: 1px solid #e9ecef;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }
  
  .section-title {
    font-size: 14px;
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 12px;
    padding-left: 8px;
    position: relative;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .section-title::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 4px;
    height: 16px;
    background: #4a90e2;
    border-radius: 2px;
  }
  
  .button-group {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 0 5px;
  }
  
  .signal-btn {
    flex: 1;
    min-width: 110px;
    padding: 8px 16px;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    background: white;
    color: #495057;
    cursor: pointer;
    transition: all 0.3s ease-in-out;
    font-size: 13px;
    text-align: center;
    font-weight: 500;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  }
  
  .signal-btn:hover {
    background: #f8f9fa;
    color: #4a90e2;
    border-color: #4a90e2;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .signal-btn.active {
    background: #4a90e2;
    color: white;
    border-color: #4a90e2;
    box-shadow: 0 2px 4px rgba(74,144,226,0.3);
  }
  
  .param-content {
    margin-top: 15px;
    background: white;
    border-radius: 8px;
    padding: 20px;
    border: 1px solid #e9ecef;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    max-height: 40vh;
    overflow-y: auto;
  }
  
  .param-table {
    width: 100%;
  }
  
  .table-row {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .table-header {
    margin-bottom: 8px;
  }
  
  .table-cell {
    flex: 1;
    text-align: center;
    font-size: 13px;
    color: #495057;
  }
  
  .form-control, .form-select {
    width: 100%;
    height: 30px;
    padding: 4px 8px;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    font-size: 13px;
    background: white;
  }
  
  .form-control:focus, .form-select:focus {
    border-color: #4a90e2;
    outline: none;
    box-shadow: 0 0 0 3px rgba(74,144,226,0.1);
  }
  
  .action-buttons {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
    margin-top: 15px;
  }
  
  .btn-reset, .btn-apply {
    padding: 6px 16px;
    border: none;
    border-radius: 4px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-reset {
    background: #e9ecef;
    color: #495057;
  }
  
  .btn-reset:hover {
    background: #dee2e6;
  }
  
  .btn-apply {
    background: #228be6;
    color: white;
  }
  
  .btn-apply:hover {
    background: #1c7ed6;
  }
  
  .submenu {
   min-height: 0 !important;
   height: auto !important;
   margin: 0 !important;
   padding: 0 !important;
  }
  
  /* 移除重复的menu-list样式定义 */
  
  /* 财务指标菜单专用样式 */
  .financial-submenu {
    max-height: 350px !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    background: #f8f9fa !important;
    position: relative !important;
    min-height: 200px !important;
  }
  
  .financial-submenu .submenu-item {
    padding: 12px 25px !important;
    min-height: 44px !important;
    flex-shrink: 0 !important;
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
  }
  
  /* 财务指标菜单滚动条样式 */
  .financial-submenu::-webkit-scrollbar {
    width: 8px !important;
    display: block !important;
  }
  
  .financial-submenu::-webkit-scrollbar-track {
    background: #f8f9fa !important;
    border-radius: 4px !important;
  }
  
  .financial-submenu::-webkit-scrollbar-thumb {
    background: #c1c7d0 !important;
    border-radius: 4px !important;
    border: 2px solid #f8f9fa !important;
  }
  
  .financial-submenu::-webkit-scrollbar-thumb:hover {
    background: #a8b3c0 !important;
  }
  
  /* 确保滚动条始终显示 */
  .financial-submenu {
    scrollbar-width: thin !important;
    scrollbar-color: #c1c7d0 #f8f9fa !important;
  }
  
  /* 响应式财务指标菜单 */
  @media (max-height: 800px) {
    .financial-submenu {
      max-height: 350px !important;
    }
  }
  
  @media (max-height: 600px) {
    .financial-submenu {
      max-height: 300px !important;
    }
    
    .financial-submenu .submenu-item {
      padding: 10px 25px !important;
      min-height: 40px !important;
    }
  }
  
  /* 时间区间选择器样式 */
  .date-range-container {
    display: flex;
    gap: 12px;
    margin-top: 8px;
  }
  
  .date-input-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  .date-label {
    font-size: 12px;
    color: #6c757d;
    font-weight: 500;
    margin-bottom: 2px;
  }
  
  .date-input-group .form-control {
    height: 36px;
    font-size: 13px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 8px 12px;
    transition: border-color 0.2s;
  }
  
  .date-input-group .form-control:focus {
    border-color: #228be6;
    outline: none;
    box-shadow: 0 0 0 2px rgba(34, 139, 230, 0.2);
  }
  
  /* 响应式时间区间选择器 */
  @media (max-width: 768px) {
    .date-range-container {
      flex-direction: column;
      gap: 8px;
    }
    
    .date-input-group {
      flex: none;
    }
  }
  
  /* 价格指标选择器优化样式 */
  .form-select option[disabled] {
    color: #6c757d;
    font-style: italic;
  }
  
  .form-select:invalid {
    color: #6c757d;
  }
  
  .form-select:valid {
    color: #495057;
  }
  
  /* 表格样式优化 */
  .param-table .table-header {
    background-color: #f8f9fa;
    font-weight: 600;
    color: #495057;
  }
  
  .param-table .table-cell {
    padding: 12px 8px;
    border-bottom: 1px solid #e9ecef;
  }
  
  .price-label {
    font-weight: 500;
    color: #228be6;
  }
  
  /* 按钮样式优化 */
  .action-buttons {
    margin-top: 16px;
    display: flex;
    gap: 8px;
    justify-content: flex-end;
  }
  
  .btn-reset, .btn-apply {
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s;
  }
  
  .btn-reset {
    background: #e9ecef;
    color: #495057;
    border: 1px solid #ced4da;
  }
  
  .btn-reset:hover {
    background: #dee2e6;
    border-color: #adb5bd;
  }
  
  .btn-apply {
    background: #228be6;
    color: white;
    border: 1px solid #228be6;
  }
  
  .btn-apply:hover {
    background: #1c7ed6;
    border-color: #1c7ed6;
  }
  
  /* MACD表头样式 */
  .macd-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  }
  
  .macd-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 4px;
    text-align: center;
  }
  
  .macd-description {
    font-size: 11px;
    opacity: 0.9;
    text-align: center;
    line-height: 1.4;
  }
  
  /* MACD参数表格样式 */
  .macd-param-table {
    margin-bottom: 16px;
  }
  
  .macd-param-table .param-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .macd-param-table .param-table th {
    background: #f8f9fa;
    color: #495057;
    font-weight: 600;
    font-size: 12px;
    padding: 8px 12px;
    text-align: center;
    border-bottom: 1px solid #dee2e6;
  }
  
  .macd-param-table .param-table td {
    padding: 8px 12px;
    font-size: 12px;
    text-align: center;
    border-bottom: 1px solid #f1f3f4;
  }
  
  .macd-param-table .param-table tr:last-child td {
    border-bottom: none;
  }
  
  .macd-param-table .param-table td:first-child {
    font-weight: 600;
    color: #228be6;
  }
  
  .macd-param-table .param-table td:nth-child(2) {
    text-align: left;
    color: #6c757d;
  }
  
  .macd-param-table .param-table td:last-child {
    font-weight: 600;
    color: #28a745;
  }
  
  /* MACD帮助提示样式 */
  .macd-help {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 12px;
    margin-top: 16px;
  }
  
  .help-icon {
    color: #228be6;
    font-size: 16px;
    margin-top: 2px;
  }
  
  .help-content {
    flex: 1;
  }
  
  .help-title {
    font-size: 13px;
    font-weight: 600;
    color: #495057;
    margin-bottom: 4px;
  }
  
  .help-text {
    font-size: 12px;
    color: #6c757d;
    line-height: 1.4;
  }
  
  /* MA表头样式 */
  .ma-header {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
  }
  
  .ma-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 4px;
    text-align: center;
  }
  
  .ma-description {
    font-size: 11px;
    opacity: 0.9;
    text-align: center;
    line-height: 1.4;
  }
  
  /* MA参数表格样式 */
  .ma-param-table {
    margin-bottom: 16px;
  }
  
  .ma-param-table .param-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .ma-param-table .param-table th {
    background: #f8f9fa;
    color: #495057;
    font-weight: 600;
    font-size: 12px;
    padding: 8px 12px;
    text-align: center;
    border-bottom: 1px solid #dee2e6;
  }
  
  .ma-param-table .param-table td {
    padding: 8px 12px;
    font-size: 12px;
    text-align: center;
    border-bottom: 1px solid #f1f3f4;
  }
  
  .ma-param-table .param-table tr:last-child td {
    border-bottom: none;
  }
  
  .ma-param-table .param-table td:first-child {
    font-weight: 600;
    color: #28a745;
  }
  
  .ma-param-table .param-table td:nth-child(2) {
    text-align: left;
    color: #6c757d;
  }
  
  .ma-param-table .param-table td:last-child {
    font-weight: 600;
    color: #28a745;
  }
  
  /* MA帮助提示样式 */
  .ma-help {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 12px;
    margin-top: 16px;
  }
  
  /* KDJ表头样式 */
  .kdj-header {
    background: linear-gradient(135deg, #fd7e14 0%, #ffc107 100%);
    color: white;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(253, 126, 20, 0.3);
  }
  
  .kdj-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 4px;
    text-align: center;
  }
  
  .kdj-description {
    font-size: 11px;
    opacity: 0.9;
    text-align: center;
    line-height: 1.4;
  }
  
  /* KDJ参数表格样式 */
  .kdj-param-table {
    margin-bottom: 16px;
  }
  
  .kdj-param-table .param-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .kdj-param-table .param-table th {
    background: #f8f9fa;
    color: #495057;
    font-weight: 600;
    font-size: 12px;
    padding: 8px 12px;
    text-align: center;
    border-bottom: 1px solid #dee2e6;
  }
  
  .kdj-param-table .param-table td {
    padding: 8px 12px;
    font-size: 12px;
    text-align: center;
    border-bottom: 1px solid #f1f3f4;
  }
  
  .kdj-param-table .param-table tr:last-child td {
    border-bottom: none;
  }
  
  .kdj-param-table .param-table td:first-child {
    font-weight: 600;
    color: #fd7e14;
  }
  
  .kdj-param-table .param-table td:nth-child(2) {
    text-align: left;
    color: #6c757d;
  }
  
  .kdj-param-table .param-table td:last-child {
    font-weight: 600;
    color: #fd7e14;
  }
  
  /* KDJ帮助提示样式 */
  .kdj-help {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 12px;
    margin-top: 16px;
  }
  
  /* MACD参数输入框样式 */
  .macd-param-inputs {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .macd-param-inputs .ma-input-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding: 8px 0;
  }
  
  .macd-param-inputs .ma-input-row:last-child {
    margin-bottom: 0;
  }
  
  .macd-param-inputs .ma-input-row label {
    font-size: 13px;
    font-weight: 500;
    color: #495057;
    min-width: 120px;
    margin-right: 12px;
  }
  
  .macd-param-inputs .input-with-unit {
    display: flex;
    align-items: center;
    flex: 1;
    max-width: 200px;
  }
  
  .macd-param-inputs .ma-input {
    flex: 1;
    height: 36px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 13px;
    transition: border-color 0.2s;
    background: white;
  }
  
  .macd-param-inputs .ma-input:focus {
    border-color: #228be6;
    outline: none;
    box-shadow: 0 0 0 2px rgba(34, 139, 230, 0.2);
  }
  
  .macd-param-inputs .unit {
    margin-left: 8px;
    font-size: 12px;
    color: #6c757d;
    font-weight: 500;
  }
  
  /* KDJ参数输入框样式 */
  .kdj-param-inputs {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .kdj-param-inputs .ma-input-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding: 8px 0;
  }
  
  .kdj-param-inputs .ma-input-row:last-child {
    margin-bottom: 0;
  }
  
  .kdj-param-inputs .ma-input-row label {
    font-size: 13px;
    font-weight: 500;
    color: #495057;
    min-width: 120px;
    margin-right: 12px;
  }
  
  .kdj-param-inputs .input-with-unit {
    display: flex;
    align-items: center;
    flex: 1;
    max-width: 200px;
  }
  
  .kdj-param-inputs .ma-input {
    flex: 1;
    height: 36px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 13px;
    transition: border-color 0.2s;
    background: white;
  }
  
  .kdj-param-inputs .ma-input:focus {
    border-color: #fd7e14;
    outline: none;
    box-shadow: 0 0 0 2px rgba(253, 126, 20, 0.2);
  }
  
  .kdj-param-inputs .unit {
    margin-left: 8px;
    font-size: 12px;
    color: #6c757d;
    font-weight: 500;
  }
  
  /* RSI参数输入框样式 */
  .rsi-param-inputs {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .rsi-param-inputs .ma-input-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding: 8px 0;
  }
  
  .rsi-param-inputs .ma-input-row:last-child {
    margin-bottom: 0;
  }
  
  .rsi-param-inputs .ma-input-row label {
    font-size: 13px;
    font-weight: 500;
    color: #495057;
    min-width: 120px;
    margin-right: 12px;
  }
  
  .rsi-param-inputs .input-with-unit {
    display: flex;
    align-items: center;
    flex: 1;
    max-width: 200px;
  }
  
  .rsi-param-inputs .ma-input {
    flex: 1;
    height: 36px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 13px;
    transition: border-color 0.2s;
    background: white;
  }
  
  .rsi-param-inputs .ma-input:focus {
    border-color: #e83e8c;
    outline: none;
    box-shadow: 0 0 0 2px rgba(232, 62, 140, 0.2);
  }
  
  .rsi-param-inputs .unit {
    margin-left: 8px;
    font-size: 12px;
    color: #6c757d;
    font-weight: 500;
  }
  
  /* RSI表头样式 */
  .rsi-header {
    background: linear-gradient(135deg, #e83e8c, #fd7e14);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .rsi-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .rsi-description {
    font-size: 13px;
    opacity: 0.9;
  }
  
  .rsi-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* KDJ表头样式 */
  .kdj-header {
    background: linear-gradient(135deg, #fd7e14, #ffc107);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .kdj-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .kdj-description {
    font-size: 13px;
    opacity: 0.9;
  }
  
  .kdj-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* BOLL参数输入框样式 */
  .boll-param-inputs {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .boll-param-inputs .ma-input-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding: 8px 0;
  }
  
  .boll-param-inputs .ma-input-row:last-child {
    margin-bottom: 0;
  }
  
  .boll-param-inputs .ma-input-row label {
    font-size: 13px;
    font-weight: 500;
    color: #495057;
    min-width: 120px;
    margin-right: 12px;
  }
  
  .boll-param-inputs .input-with-unit {
    display: flex;
    align-items: center;
    flex: 1;
    max-width: 200px;
  }
  
  .boll-param-inputs .ma-input {
    flex: 1;
    height: 36px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 13px;
    transition: border-color 0.2s;
    background: white;
  }
  
  .boll-param-inputs .ma-input:focus {
    border-color: #28a745;
    outline: none;
    box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.2);
  }
  
  .boll-param-inputs .unit {
    margin-left: 8px;
    font-size: 12px;
    color: #6c757d;
    font-weight: 500;
  }
  
  /* BOLL表头样式 */
  .boll-header {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .boll-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .boll-description {
    font-size: 13px;
    opacity: 0.9;
  }
  
  .boll-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* CR参数输入框样式 */
  .cr-param-inputs {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .cr-param-inputs .ma-input-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding: 8px 0;
  }
  
  .cr-param-inputs .ma-input-row:last-child {
    margin-bottom: 0;
  }
  
  .cr-param-inputs .ma-input-row label {
    font-size: 13px;
    font-weight: 500;
    color: #495057;
    min-width: 120px;
    margin-right: 12px;
  }
  
  .cr-param-inputs .input-with-unit {
    display: flex;
    align-items: center;
    flex: 1;
    max-width: 200px;
  }
  
  .cr-param-inputs .ma-input {
    flex: 1;
    height: 36px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 13px;
    transition: border-color 0.2s;
    background: white;
  }
  
  .cr-param-inputs .ma-input:focus {
    border-color: #6f42c1;
    outline: none;
    box-shadow: 0 0 0 2px rgba(111, 66, 193, 0.2);
  }
  
  .cr-param-inputs .unit {
    margin-left: 8px;
    font-size: 12px;
    color: #6c757d;
    font-weight: 500;
  }
  
  /* CR表头样式 */
  .cr-header {
    background: linear-gradient(135deg, #6f42c1, #e83e8c);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .cr-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .cr-description {
    font-size: 13px;
    opacity: 0.9;
  }
  
  .cr-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* TRIX参数输入框样式 */
  .trix-param-inputs {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .trix-param-inputs .ma-input-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding: 8px 0;
  }
  
  .trix-param-inputs .ma-input-row:last-child {
    margin-bottom: 0;
  }
  
  .trix-param-inputs .ma-input-row label {
    font-size: 13px;
    font-weight: 500;
    color: #495057;
    min-width: 120px;
    margin-right: 12px;
  }
  
  .trix-param-inputs .input-with-unit {
    display: flex;
    align-items: center;
    flex: 1;
    max-width: 200px;
  }
  
  .trix-param-inputs .ma-input {
    flex: 1;
    height: 36px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 13px;
    transition: border-color 0.2s;
    background: white;
  }
  
  .trix-param-inputs .ma-input:focus {
    border-color: #17a2b8;
    outline: none;
    box-shadow: 0 0 0 2px rgba(23, 162, 184, 0.2);
  }
  
  .trix-param-inputs .unit {
    margin-left: 8px;
    font-size: 12px;
    color: #6c757d;
    font-weight: 500;
  }
  
  /* TRIX表头样式 */
  .trix-header {
    background: linear-gradient(135deg, #17a2b8, #20c997);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .trix-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .trix-description {
    font-size: 13px;
    opacity: 0.9;
  }
  
  .trix-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* ATR表头样式 */
  .atr-header {
    background: linear-gradient(135deg, #6c757d, #495057);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .atr-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .atr-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .atr-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* CCI表头样式 */
  .cci-header {
    background: linear-gradient(135deg, #ffc107, #fd7e14);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .cci-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .cci-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .cci-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 四周期多头排列表头样式 */
  .multi-bull-header {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .multi-bull-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .multi-bull-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .multi-bull-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* EMA表头样式 */
  .ema-header {
    background: linear-gradient(135deg, #007bff, #6610f2);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .ema-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .ema-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .ema-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 股票价格指标表头样式 */
  .open-price-header {
    background: linear-gradient(135deg, #ffc107, #fd7e14);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .open-price-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .open-price-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .open-price-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .close-price-header {
    background: linear-gradient(135deg, #17a2b8, #6f42c1);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .close-price-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .close-price-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .close-price-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .high-price-header {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .high-price-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .high-price-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .high-price-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .low-price-header {
    background: linear-gradient(135deg, #dc3545, #c82333);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .low-price-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .low-price-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .low-price-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .prev-close-price-header {
    background: linear-gradient(135deg, #6c757d, #495057);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .prev-close-price-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .prev-close-price-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .prev-close-price-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .avg-price-header {
    background: linear-gradient(135deg, #e83e8c, #fd7e14);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .avg-price-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .avg-price-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .avg-price-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 涨幅表头样式 */
  .change-rate-header {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .change-rate-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .change-rate-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .change-rate-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 量比表头样式 */
  .volume-ratio-header {
    background: linear-gradient(135deg, #007bff, #6610f2);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .volume-ratio-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .volume-ratio-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .volume-ratio-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 成交额表头样式 */
  .turnover-header {
    background: linear-gradient(135deg, #ffc107, #fd7e14);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .turnover-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .turnover-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .turnover-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 换手率表头样式 */
  .turnover-rate-header {
    background: linear-gradient(135deg, #17a2b8, #6f42c1);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .turnover-rate-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .turnover-rate-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .turnover-rate-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 市值表头样式 */
  .market-value-header {
    background: linear-gradient(135deg, #dc3545, #c82333);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .market-value-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .market-value-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .market-value-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 成交量表头样式 */
  .volume-header {
    background: linear-gradient(135deg, #6c757d, #495057);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .volume-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .volume-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .volume-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 资金净流入表头样式 */
  .net-inflow-header {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .net-inflow-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .net-inflow-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .net-inflow-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 股东减持表头样式 */
  .shareholder-reduction-header {
    background: linear-gradient(135deg, #dc3545, #c82333);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .shareholder-reduction-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .shareholder-reduction-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .shareholder-reduction-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 股东增持表头样式 */
  .shareholder-increase-header {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .shareholder-increase-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .shareholder-increase-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .shareholder-increase-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 股东分红表头样式 */
  .shareholder-dividend-header {
    background: linear-gradient(135deg, #ffc107, #fd7e14);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .shareholder-dividend-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .shareholder-dividend-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .shareholder-dividend-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 违规问询函表头样式 */
  .violation-inquiry-header {
    background: linear-gradient(135deg, #6c757d, #495057);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .violation-inquiry-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .violation-inquiry-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .violation-inquiry-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 业绩预告表头样式 */
  .performance-forecast-header {
    background: linear-gradient(135deg, #17a2b8, #6f42c1);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .performance-forecast-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .performance-forecast-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .performance-forecast-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 业绩公告表头样式 */
  .performance-announcement-header {
    background: linear-gradient(135deg, #007bff, #6610f2);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .performance-announcement-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .performance-announcement-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .performance-announcement-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 过滤新上市表头样式 */
  .filter-new-listing-header {
    background: linear-gradient(135deg, #ffc107, #fd7e14);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .filter-new-listing-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .filter-new-listing-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .filter-new-listing-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 过滤北交所表头样式 */
  .filter-beijing-header {
    background: linear-gradient(135deg, #007bff, #6610f2);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .filter-beijing-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .filter-beijing-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .filter-beijing-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 过滤沪深主板表头样式 */
  .filter-main-board-header {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .filter-main-board-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .filter-main-board-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .filter-main-board-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 过滤ST表头样式 */
  .filter-st-header {
    background: linear-gradient(135deg, #dc3545, #c82333);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .filter-st-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .filter-st-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .filter-st-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* ROA表头样式 */
  .roa-header {
    background: linear-gradient(135deg, #007bff, #6610f2);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .roa-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .roa-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .roa-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* ROE表头样式 */
  .roe-header {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .roe-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .roe-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .roe-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 过滤*ST表头样式 */
  .filter-star-st-header {
    background: linear-gradient(135deg, #dc3545, #c82333);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .filter-star-st-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .filter-star-st-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .filter-star-st-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 过滤停牌表头样式 */
  .filter-suspension-header {
    background: linear-gradient(135deg, #ffc107, #fd7e14);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .filter-suspension-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .filter-suspension-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .filter-suspension-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 过滤科创板表头样式 */
  .filter-star-market-header {
    background: linear-gradient(135deg, #17a2b8, #6f42c1);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .filter-star-market-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .filter-star-market-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .filter-star-market-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 过滤创业板表头样式 */
  .filter-growth-board-header {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .filter-growth-board-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .filter-growth-board-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .filter-growth-board-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 过滤退市表头样式 */
  .filter-delisting-header {
    background: linear-gradient(135deg, #dc3545, #c82333);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .filter-delisting-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .filter-delisting-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .filter-delisting-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 毛利率表头样式 */
  .gross-margin-header {
    background: linear-gradient(135deg, #ffc107, #fd7e14);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .gross-margin-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .gross-margin-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .gross-margin-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 净利率表头样式 */
  .net-margin-header {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .net-margin-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .net-margin-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .net-margin-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 营收增长率表头样式 */
  .revenue-growth-header {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .revenue-growth-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .revenue-growth-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .revenue-growth-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 净利润增长率表头样式 */
  .profit-growth-header {
    background: linear-gradient(135deg, #17a2b8, #6f42c1);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .profit-growth-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .profit-growth-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .profit-growth-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 动态市盈率表头样式 */
  .dynamic-pe-header {
    background: linear-gradient(135deg, #ffc107, #fd7e14);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .dynamic-pe-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .dynamic-pe-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .dynamic-pe-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 市净率表头样式 */
  .pb-ratio-header {
    background: linear-gradient(135deg, #007bff, #6610f2);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .pb-ratio-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .pb-ratio-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .pb-ratio-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 市销率表头样式 */
  .ps-ratio-header {
    background: linear-gradient(135deg, #17a2b8, #6f42c1);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .ps-ratio-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .ps-ratio-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .ps-ratio-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* 静态市盈率表头样式 */
  .static-pe-header {
    background: linear-gradient(135deg, #6c757d, #495057);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .static-pe-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .static-pe-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .static-pe-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  /* BBIC表头样式 */
  .bbic-header {
    background: linear-gradient(135deg, #dc3545, #c82333);
    color: white;
    padding: 16px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
  }
  
  .bbic-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  
  .bbic-description {
    font-size: 14px;
    opacity: 0.9;
  }
  
  .bbic-param-table {
    background: white;
    border: 1px solid #e9ecef;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .bbic-param-inputs {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  /* 回测参数设置样式 */
  .backtest-params-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 8px;
  }

  .param-input-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .param-label {
    font-size: 12px;
    font-weight: 500;
    color: #666;
    margin: 0;
  }

  .backtest-params-container .form-control {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    transition: border-color 0.2s ease;
  }

  .backtest-params-container .form-control:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
  }

  /* 响应式调整 */
  @media (min-width: 768px) {
    .backtest-params-container {
      flex-direction: row;
      align-items: end;
    }
    
    .param-input-group {
      flex: 1;
    }
  }

  
  </style> 