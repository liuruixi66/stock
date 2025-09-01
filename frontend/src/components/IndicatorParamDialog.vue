<template>
  <div v-if="show" class="modal-overlay" @click="onClose">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>{{ indicator?.name }}参数设置</h3>
        <button class="close-btn" @click="onClose">×</button>
      </div>

      <div class="modal-body">
        <!-- 大盘择时指标的市场设置 -->
        <div v-if="isMarketTimingIndicator" class="market-timing-settings">
          <!-- 市场指数选择 -->
          <div class="setting-group">
            <label>市场指数</label>
            <input type="text" :value="marketIndex" @input="$emit('update:marketIndex', $event.target.value)" class="setting-input" placeholder="上证指数" />
          </div>

          <!-- 周期选择 -->
          <div class="setting-group">
            <label>周期选择</label>
            <div class="period-buttons">
              <button 
                :class="['period-btn', { active: period === 'D' }]" 
                @click="$emit('update:period', 'D')"
              >日</button>
              <button 
                :class="['period-btn', { active: period === 'W' }]" 
                @click="$emit('update:period', 'W')"
              >周</button>
              <button 
                :class="['period-btn', { active: period === 'M' }]" 
                @click="$emit('update:period', 'M')"
              >月</button>
            </div>
          </div>
        </div>

        <!-- 板块择时指标 - 不显示市场设置 -->
        <div v-if="isSectorTimingIndicator" class="sector-timing-settings">
          <!-- 这里不显示市场指数和周期选择 -->
        </div>

        <!-- 个股择时指标 - 不显示市场设置 -->
        <div v-if="isIndividualTimingIndicator" class="individual-timing-settings">
          <!-- 这里不显示市场指数和周期选择 -->
        </div>

        <!-- MA指标参数设置 - 大盘择时（包含市场指数和周期选择） -->
        <div v-if="(indicator?.name || '').includes('MA') && !(indicator?.name || '').includes('MACD') && isTechnicalIndicator && indicator?.category === 'trend'" class="ma-section">
          <div class="ma-header">
            <div class="ma-title">大盘MA指标参数设置</div>
            <div class="ma-description">MA: 移动平均线, 短线: 短期均线, 长线: 长期均线</div>
          </div>

          <!-- MA参数表格 -->
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
                  <td class="param-name">MA短线</td>
                  <td>短期移动平均线周期</td>
                  <td class="param-default">5</td>
                </tr>
                <tr>
                  <td class="param-name">MA长线</td>
                  <td>长期移动平均线周期</td>
                  <td class="param-default">60</td>
            </tr>
          </tbody>
        </table>
      </div>

                  <!-- MA参数输入框 -->
        <div class="ma-param-inputs">
          <div class="ma-input-row">
            <label>MA短线 (日均线)</label>
            <div class="input-with-unit">
              <input type="number" :value="maShort" @input="$emit('update:maShort', toNumber($event.target.value))" class="ma-input" placeholder="5">
              <span class="unit">日</span>
            </div>
          </div>
          <div class="ma-input-row">
            <label>MA长线 (日均线)</label>
            <div class="input-with-unit">
              <input type="number" :value="maLong" @input="$emit('update:maLong', toNumber($event.target.value))" class="ma-input" placeholder="60">
              <span class="unit">日</span>
            </div>
          </div>
        </div>

        <!-- MA信号设置 -->
        <div class="ma-signal-settings">
          <div class="ma-input-row">
            <label>金叉信号</label>
            <div class="checkbox-wrapper">
              <input type="checkbox" v-model="maGoldenCrossChecked" @change="updateMaSettings">
              <span class="checkbox-label">启用金叉信号</span>
            </div>
          </div>
          <div class="ma-input-row">
            <label>死叉信号</label>
            <div class="checkbox-wrapper">
              <input type="checkbox" v-model="maDeathCrossChecked" @change="updateMaSettings">
              <span class="checkbox-label">启用死叉信号</span>
            </div>
          </div>
        </div>
        </div>

        <!-- MA指标参数设置 - 板块择时（包含板块指数和周期选择） -->
        <div v-if="(indicator?.name || '').includes('MA') && !(indicator?.name || '').includes('MACD') && indicator?.category === 'block'" class="macd-section">
          <div class="macd-header">
            <div class="macd-title">板块MA指标参数设置</div>
            <div class="macd-description">MA：移动平均线，短线：短期均线，长线：长期均线</div>
          </div>

          <!-- 板块指数选择 -->
          <div class="setting-group">
            <div class="setting-label">板块指数</div>
            <div class="sector-index-display">
              <div class="sector-index-value">{{ getSectorIndexLabel(selectedSectorIndex) }}</div>
              <i class="fas fa-chevron-down sector-dropdown-icon"></i>
            </div>
            <div class="sector-search-hint">请输入板块名称</div>
            <div class="sector-search-input">
              <input 
                type="text" 
                placeholder="请输入搜索关键词"
                class="sector-search-field"
              >
              <i class="fas fa-chevron-down search-dropdown-icon"></i>
            </div>
          </div>

          <!-- 周期选择 -->
          <div class="setting-group">
            <div class="setting-label">周期选择</div>
            <div class="period-button-group">
              <button 
                v-for="period in periods" 
                :key="period.value"
                :class="['period-button', { active: selectedSectorPeriod === period.value }]"
                @click="selectedSectorPeriod = period.value"
              >
                {{ period.label }}
              </button>
            </div>
          </div>

          <!-- MA参数表格 -->
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
                  <td class="param-name">MA短线</td>
                  <td>短期移动平均线周期</td>
                  <td class="param-default">5</td>
                </tr>
                <tr>
                  <td class="param-name">MA长线</td>
                  <td>长期移动平均线周期</td>
                  <td class="param-default">60</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- MA参数输入框 -->
          <div class="macd-param-inputs">
            <div class="ma-input-row">
              <label>MA短线（日均线）</label>
              <div class="input-with-unit">
                <input type="number" v-model="sectorMaShort" class="ma-input" placeholder="5">
                <span class="unit">日</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>MA长线（日均线）</label>
              <div class="input-with-unit">
                <input type="number" v-model="sectorMaLong" class="ma-input" placeholder="60">
                <span class="unit">日</span>
              </div>
            </div>
          </div>

          <!-- MA信号设置 -->
          <div class="macd-signal-settings">
            <div class="ma-input-row">
              <label>金叉</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="sectorMaGoldenCrossChecked">
                <span class="checkbox-label">启用金叉信号</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>死叉</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="sectorMaDeathCrossChecked">
                <span class="checkbox-label">启用死叉信号</span>
              </div>
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

        <!-- MA指标参数设置 - 个股择时（不包含市场指数和周期选择） -->
        <div v-if="(indicator?.name || '').includes('MA') && !(indicator?.name || '').includes('MACD') && indicator?.category === 'stock'" class="macd-section">
          <div class="macd-header">
            <div class="macd-title">个股MA指标参数设置</div>
            <div class="ma-description">
              MA：移动平均线，短线：短期均线，长线：长期均线
            </div>
          </div>
          
          <!-- MA参数说明表格 -->
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
                  @click="selectTimingSignal('ma')"
                >
                  MA
                </button>
              </div>
            </div>
          </div>
          
          
          <!-- 交叉信号 -->
          <div class="indicator-section">
            <div class="section-title">交叉信号</div>
            <div class="button-group">
              <button 
                :class="['signal-btn', { active: timingSelectedSignal === 'ma_golden_cross' }]"
                @click="selectTimingSignal('ma_golden_cross')"
              >
                MA金叉
              </button>
              <button 
                :class="['signal-btn', { active: timingSelectedSignal === 'ma_death_cross' }]"
                @click="selectTimingSignal('ma_death_cross')"
              >
                MA死叉
              </button>
            </div>
          </div>
          
          <div v-if="timingSelectedSignal === 'ma_golden_cross' || timingSelectedSignal === 'ma_death_cross' || timingSelectedSignal === 'ma'" class="param-content">
            <div class="param-table">
              <div class="table-row table-header">
                <div class="table-cell">MA短线</div>
                <div class="table-cell">MA长线</div>
                <div class="table-cell">比较符</div>
                <div class="table-cell">数值</div>
              </div>
              <div class="table-row">
                <div class="table-cell">
                  <input type="number" v-model="maShortPeriod" class="form-control" placeholder="5">
                </div>
                <div class="table-cell">
                  <input type="number" v-model="maLongPeriod" class="form-control" placeholder="20">
                </div>
                <div class="table-cell">
                  <select v-model="maActiveCompare" class="form-select">
                    <option value="大于">大于</option>
                    <option value="小于">小于</option>
                    <option value="大于等于">大于等于</option>
                    <option value="小于等于">小于等于</option>
                    <option value="等于">等于</option>
                  </select>
                </div>
                <div class="table-cell">
                  <input type="number" v-model="maActiveValue" class="form-control" step="0.01">
                </div>
              </div>
            </div>
            <div class="action-buttons">
              <button class="btn-reset" @click="resetMASettings">重置</button>
              <button class="btn-apply" @click="applyMASettings">应用设置</button>
            </div>
          </div>
          
          <!-- 趋势信号 -->
          <div class="indicator-section">
            <div class="section-title">趋势信号</div>
            <div class="button-group">
              <button 
                :class="['signal-btn', { active: timingSelectedSignal === 'ma_bull' }]"
                @click="selectTimingSignal('ma_bull')"
              >
                MA多头
              </button>
              <button 
                :class="['signal-btn', { active: timingSelectedSignal === 'ma_bear' }]"
                @click="selectTimingSignal('ma_bear')"
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
                  <input type="number" v-model="maShortPeriod" class="form-control" placeholder="5">
                </div>
                <div class="table-cell">
                  <input type="number" v-model="maLongPeriod" class="form-control" placeholder="20">
                </div>
                <div class="table-cell">
                  <select v-model="maTrendCompare" class="form-select">
                    <option value="大于">大于</option>
                    <option value="小于">小于</option>
                    <option value="大于等于">大于等于</option>
                    <option value="小于等于">小于等于</option>
                    <option value="等于">等于</option>
                  </select>
                </div>
                <div class="table-cell">
                  <input type="number" v-model="maTrendCustomValue" class="form-control" step="0.01">
                </div>
              </div>
            </div>
            <div class="action-buttons">
              <button class="btn-reset" @click="resetMASettings">重置</button>
              <button class="btn-apply" @click="applyMASettings">应用设置</button>
            </div>
          </div>
          
          <!-- 背离信号 -->
          <div class="indicator-section">
            <div class="section-title">背离信号</div>
            <div class="button-group">
              <button 
                :class="['signal-btn', { active: timingSelectedSignal === 'ma_bottom_divergence' }]"
                @click="selectTimingSignal('ma_bottom_divergence')"
              >
                MA底背离
              </button>
              <button 
                :class="['signal-btn', { active: timingSelectedSignal === 'ma_top_divergence' }]"
                @click="selectTimingSignal('ma_top_divergence')"
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
                  <input type="number" v-model="maShortPeriod" class="form-control" placeholder="5">
                </div>
                <div class="table-cell">
                  <input type="number" v-model="maLongPeriod" class="form-control" placeholder="20">
                </div>
                <div class="table-cell">
                  <select v-model="maDivergenceCompare" class="form-select">
                    <option value="大于">大于</option>
                    <option value="小于">小于</option>
                    <option value="大于等于">大于等于</option>
                    <option value="小于等于">小于等于</option>
                    <option value="等于">等于</option>
                  </select>
                </div>
                <div class="table-cell">
                  <input type="number" v-model="maDivergenceCustomValue" class="form-control" step="0.01">
                </div>
              </div>
            </div>
            <div class="action-buttons">
              <button class="btn-reset" @click="resetMASettings">重置</button>
              <button class="btn-apply" @click="applyMASettings">应用设置</button>
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

        <!-- KDJ指标设置 - 大盘择时 -->
        <div v-if="(indicator?.name || '').includes('KDJ') && isTechnicalIndicator && indicator?.category === 'trend'" class="kdj-section">
          <div class="kdj-header">
            <div class="kdj-title">KDJ指标参数设置</div>
            <div class="kdj-description">KDJ：随机指标，K：快速线，D：慢速线，J：信号线</div>
          </div>

          <!-- KDJ参数表格 -->
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
                  <td class="param-name">K</td>
                  <td>快速随机指标周期</td>
                  <td class="param-default">9</td>
                </tr>
                <tr>
                  <td class="param-name">D</td>
                  <td>慢速随机指标周期</td>
                  <td class="param-default">3</td>
                </tr>
                <tr>
                  <td class="param-name">J</td>
                  <td>信号线平滑周期</td>
                  <td class="param-default">3</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- KDJ参数输入框 -->
          <div class="kdj-param-inputs">
            <div class="ma-input-row">
              <label>K（随机指标）</label>
              <div class="input-with-unit">
                <input type="number" v-model="kdjSettings.k" @input="updateKdjSettings" class="ma-input" placeholder="9">
                <span class="unit">日</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>D（随机指标）</label>
              <div class="input-with-unit">
                <input type="number" v-model="kdjSettings.d" @input="updateKdjSettings" class="ma-input" placeholder="3">
                <span class="unit">日</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>J（随机指标）</label>
              <div class="input-with-unit">
                <input type="number" v-model="kdjSettings.j" @input="updateKdjSettings" class="ma-input" placeholder="3">
                <span class="unit">日</span>
              </div>
            </div>
          </div>

          <!-- KDJ信号设置 -->
          <div class="kdj-signal-settings">
            <div class="ma-input-row">
              <label>金叉信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="kdjGoldenCrossChecked" @change="updateKdjSettings">
                <span class="checkbox-label">启用金叉信号</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>死叉信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="kdjDeathCrossChecked" @change="updateKdjSettings">
                <span class="checkbox-label">启用死叉信号</span>
              </div>
            </div>
          </div>
        </div>

        <!-- KDJ指标设置 - 板块择时 -->
        <div v-if="(indicator?.name || '').includes('KDJ') && isTechnicalIndicator && indicator?.category === 'block'" class="kdj-section">
          <div class="kdj-header">
            <div class="kdj-title">板块KDJ指标参数设置</div>
            <div class="kdj-description">KDJ：随机指标，K：快速线，D：慢速线，J：信号线</div>
          </div>

          <!-- 板块指数选择 -->
          <div class="setting-group">
            <div class="setting-label">板块指数</div>
            <div class="sector-index-display">
              <div class="sector-index-value">{{ getSectorIndexLabel(selectedSectorKdjIndex) }}</div>
              <i class="fas fa-chevron-down sector-dropdown-icon"></i>
            </div>
            <div class="sector-search-hint">请输入板块名称</div>
            <div class="sector-search-input">
              <input 
                type="text" 
                placeholder="请输入搜索关键词"
                class="sector-search-field"
              >
              <i class="fas fa-chevron-down search-dropdown-icon"></i>
            </div>
          </div>

          <!-- 周期选择 -->
          <div class="setting-group">
            <div class="setting-label">周期选择</div>
            <div class="period-button-group">
              <button 
                v-for="period in periods" 
                :key="period.value"
                :class="['period-button', { active: selectedSectorKdjPeriod === period.value }]"
                @click="selectedSectorKdjPeriod = period.value"
              >
                {{ period.label }}
              </button>
            </div>
          </div>

          <!-- KDJ参数表格 -->
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
                  <td class="param-name">K</td>
                  <td>快速随机指标周期</td>
                  <td class="param-default">9</td>
                </tr>
                <tr>
                  <td class="param-name">D</td>
                  <td>慢速随机指标周期</td>
                  <td class="param-default">3</td>
                </tr>
                <tr>
                  <td class="param-name">J</td>
                  <td>信号线平滑周期</td>
                  <td class="param-default">3</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- KDJ参数输入框 -->
          <div class="kdj-param-inputs">
            <div class="ma-input-row">
              <label>K（随机指标）</label>
              <div class="input-with-unit">
                <input type="number" v-model="sectorKdjSettings.k" class="ma-input" placeholder="9">
                <span class="unit">日</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>D（随机指标）</label>
              <div class="input-with-unit">
                <input type="number" v-model="sectorKdjSettings.d" class="ma-input" placeholder="3">
                <span class="unit">日</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>J（随机指标）</label>
              <div class="input-with-unit">
                <input type="number" v-model="sectorKdjSettings.j" class="ma-input" placeholder="3">
                <span class="unit">日</span>
              </div>
            </div>
          </div>

          <!-- KDJ信号设置 -->
          <div class="kdj-signal-settings">
            <div class="ma-input-row">
              <label>金叉信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="sectorKdjGoldenCrossChecked">
                <span class="checkbox-label">启用金叉信号</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>死叉信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="sectorKdjDeathCrossChecked">
                <span class="checkbox-label">启用死叉信号</span>
              </div>
            </div>
          </div>

          <!-- KDJ帮助提示 -->
          <div class="ma-help">
            <div class="help-icon">
              <i class="fas fa-info-circle"></i>
            </div>
            <div class="help-content">
              <div class="help-title">板块KDJ指标说明</div>
              <div class="help-text">
                板块KDJ指标通过计算板块指数的KDJ来判断趋势。当K线上穿D线时产生金叉信号，
                下穿时产生死叉信号，用于判断板块买入卖出时机。
              </div>
            </div>
          </div>
        </div>

        <!-- MACD指标参数设置 - 大盘择时 -->
        <div v-if="(indicator?.name || '').includes('MACD') && isTechnicalIndicator && indicator?.category === 'trend'" class="macd-section">
          <div class="macd-header">
            <div class="macd-title">MACD指标参数设置</div>
            <div class="macd-description">DIF: 快线EMA, DEA: 慢线EMA, MACD: 信号线周期</div>
          </div>

          <!-- MACD参数表格 -->
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
                  <td class="param-name">DIF</td>
                  <td>快线指数移动平均线周期</td>
                  <td class="param-default">26</td>
                </tr>
                <tr>
                  <td class="param-name">DEA</td>
                  <td>慢线指数移动平均线周期</td>
                  <td class="param-default">12</td>
                </tr>
                <tr>
                  <td class="param-name">MACD</td>
                  <td>信号线平滑周期</td>
                  <td class="param-default">9</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- MACD参数输入框 -->
          <div class="macd-param-inputs">
            <div class="ma-input-row">
              <label>DIF (快线周期)</label>
              <div class="input-with-unit">
                <input type="number" v-model="macdSettings.fast" @input="updateMacdSettings" class="ma-input" placeholder="26">
                <span class="unit">日</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>DEA (慢线周期)</label>
              <div class="input-with-unit">
                <input type="number" v-model="macdSettings.slow" @input="updateMacdSettings" class="ma-input" placeholder="12">
                <span class="unit">日</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>MACD (信号线)</label>
              <div class="input-with-unit">
                <input type="number" v-model="macdSettings.signal" @input="updateMacdSettings" class="ma-input" placeholder="9">
                <span class="unit">日</span>
              </div>
            </div>
          </div>

          <!-- MACD信号设置 -->
          <div class="macd-signal-settings">
            <div class="ma-input-row">
              <label>金叉</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="macdGoldenCrossChecked" @change="updateMacdSettings">
                <span class="checkbox-label">启用金叉信号</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>死叉</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="macdDeathCrossChecked" @change="updateMacdSettings">
                <span class="checkbox-label">启用死叉信号</span>
              </div>
            </div>
          </div>
        </div>

        <!-- MACD指标参数设置 - 板块择时 -->
        <div v-if="(indicator?.name || '').includes('MACD') && isTechnicalIndicator && indicator?.category === 'block'" class="macd-section">
          <div class="macd-header">
            <div class="macd-title">板块MACD指标参数设置</div>
            <div class="macd-description">DIF: 快线EMA, DEA: 慢线EMA, MACD: 信号线周期</div>
          </div>

          <!-- 板块指数选择 -->
          <div class="setting-group">
            <div class="setting-label">板块指数</div>
            <div class="sector-index-display">
              <div class="sector-index-value">{{ getSectorIndexLabel(selectedSectorMacdIndex) }}</div>
              <i class="fas fa-chevron-down sector-dropdown-icon"></i>
            </div>
            <div class="sector-search-hint">请输入板块名称</div>
            <div class="sector-search-input">
              <input 
                type="text" 
                placeholder="请输入搜索关键词"
                class="sector-search-field"
              >
              <i class="fas fa-chevron-down search-dropdown-icon"></i>
            </div>
          </div>

          <!-- 周期选择 -->
          <div class="setting-group">
            <div class="setting-label">周期选择</div>
            <div class="period-button-group">
              <button 
                v-for="period in periods" 
                :key="period.value"
                :class="['period-button', { active: selectedSectorMacdPeriod === period.value }]"
                @click="selectedSectorMacdPeriod = period.value"
              >
                {{ period.label }}
              </button>
            </div>
          </div>

          <!-- MACD参数表格 -->
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
                  <td class="param-name">DIF</td>
                  <td>快线指数移动平均线周期</td>
                  <td class="param-default">26</td>
                </tr>
                <tr>
                  <td class="param-name">DEA</td>
                  <td>慢线指数移动平均线周期</td>
                  <td class="param-default">12</td>
                </tr>
                <tr>
                  <td class="param-name">MACD</td>
                  <td>信号线平滑周期</td>
                  <td class="param-default">9</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- MACD参数输入框 -->
          <div class="macd-param-inputs">
            <div class="ma-input-row">
              <label>DIF (快线周期)</label>
              <div class="input-with-unit">
                <input type="number" v-model="sectorMacdSettings.fast" class="ma-input" placeholder="26">
                <span class="unit">日</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>DEA (慢线周期)</label>
              <div class="input-with-unit">
                <input type="number" v-model="sectorMacdSettings.slow" class="ma-input" placeholder="12">
                <span class="unit">日</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>MACD (信号线)</label>
              <div class="input-with-unit">
                <input type="number" v-model="sectorMacdSettings.signal" class="ma-input" placeholder="9">
                <span class="unit">日</span>
              </div>
            </div>
          </div>

          <!-- MACD信号设置 -->
          <div class="macd-signal-settings">
            <div class="ma-input-row">
              <label>金叉</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="sectorMacdGoldenCrossChecked">
                <span class="checkbox-label">启用金叉信号</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>死叉</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="sectorMacdDeathCrossChecked">
                <span class="checkbox-label">启用死叉信号</span>
              </div>
            </div>
          </div>

          <!-- MACD帮助提示 -->
          <div class="ma-help">
            <div class="help-icon">
              <i class="fas fa-info-circle"></i>
            </div>
            <div class="help-content">
              <div class="help-title">板块MACD指标说明</div>
              <div class="help-text">
                板块MACD指标通过计算板块指数的MACD来判断趋势。当DIF上穿DEA时产生金叉信号，
                下穿时产生死叉信号，用于判断板块买入卖出时机。
              </div>
            </div>
          </div>
        </div>

        <!-- RSI指标参数设置 -->
        <div v-if="(indicator?.name || '').includes('RSI') && isTechnicalIndicator" class="rsi-section">
          <div class="rsi-header">
            <div class="rsi-title">RSI指标参数设置</div>
            <div class="rsi-description">RSI：相对强弱指数，用于判断超买超卖状态</div>
          </div>

          <!-- RSI参数表格 -->
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
                  <td class="param-name">RSI周期</td>
                  <td>相对强弱指数计算周期</td>
                  <td class="param-default">14</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- RSI参数输入框 -->
          <div class="rsi-param-inputs">
            <div class="ma-input-row">
              <label>RSI周期</label>
              <div class="input-with-unit">
                <input type="number" v-model="rsiSettings.period" @input="updateRsiSettings" class="ma-input" placeholder="14">
                <span class="unit">日</span>
              </div>
            </div>
          </div>

          <!-- RSI信号设置 -->
          <div class="rsi-signal-settings">
            <div class="ma-input-row">
              <label>超买信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="rsiOverboughtChecked" @change="updateRsiSettings">
                <span class="checkbox-label">启用超买信号</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>超卖信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="rsiOversoldChecked" @change="updateRsiSettings">
                <span class="checkbox-label">启用超卖信号</span>
              </div>
            </div>
          </div>
        </div>

        <!-- BOLL指标参数设置 -->
        <div v-if="(indicator?.name || '').includes('BOLL') && isTechnicalIndicator" class="boll-section">
          <div class="boll-header">
            <div class="boll-title">BOLL指标参数设置</div>
            <div class="boll-description">布林带：移动平均线 + 标准差通道</div>
          </div>

          <!-- BOLL参数表格 -->
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
                  <td class="param-name">周期</td>
                  <td>移动平均线周期</td>
                  <td class="param-default">20</td>
                </tr>
                <tr>
                  <td class="param-name">倍数</td>
                  <td>标准差倍数</td>
                  <td class="param-default">2</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- BOLL参数输入框 -->
          <div class="boll-param-inputs">
            <div class="ma-input-row">
              <label>周期</label>
              <div class="input-with-unit">
                <input type="number" v-model="bollSettings.period" @input="updateBollSettings" class="ma-input" placeholder="20">
                <span class="unit">日</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>倍数</label>
              <div class="input-with-unit">
                <input type="number" v-model="bollSettings.multiplier" @input="updateBollSettings" class="ma-input" placeholder="2" step="0.1">
                <span class="unit">倍</span>
              </div>
            </div>
          </div>

          <!-- BOLL信号设置 -->
          <div class="boll-signal-settings">
            <div class="ma-input-row">
              <label>上轨信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="bollUpperChecked" @change="updateBollSettings">
                <span class="checkbox-label">启用上轨信号</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>下轨信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="bollLowerChecked" @change="updateBollSettings">
                <span class="checkbox-label">启用下轨信号</span>
              </div>
            </div>
          </div>
        </div>

        <!-- CR指标参数设置 -->
        <div v-if="(indicator?.name || '').includes('CR')" class="cr-section">
          <div class="cr-header">
            <div class="cr-title">CR指标参数设置</div>
            <div class="cr-description">CR：能量指标，反映多空双方力量对比</div>
          </div>

          <!-- CR参数表格 -->
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
                  <td class="param-name">CR周期</td>
                  <td>能量指标计算周期</td>
                  <td class="param-default">26</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- CR参数输入框 -->
          <div class="cr-param-inputs">
            <div class="ma-input-row">
              <label>CR周期</label>
              <div class="input-with-unit">
                <input type="number" v-model="crSettings.period" @input="updateCrSettings" class="ma-input" placeholder="26">
                <span class="unit">日</span>
              </div>
            </div>
          </div>

          <!-- CR信号设置 -->
          <div class="cr-signal-settings">
            <div class="ma-input-row">
              <label>多头信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="crBullChecked" @change="updateCrSettings">
                <span class="checkbox-label">启用多头信号</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>空头信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="crBearChecked" @change="updateCrSettings">
                <span class="checkbox-label">启用空头信号</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ATR指标参数设置 -->
        <div v-if="(indicator?.name || '').includes('ATR')" class="atr-section">
          <div class="atr-header">
            <div class="atr-title">ATR指标参数设置</div>
            <div class="atr-description">ATR：平均真实波幅，衡量市场波动性</div>
          </div>

          <!-- ATR参数表格 -->
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
                  <td class="param-name">ATR周期</td>
                  <td>平均真实波幅周期</td>
                  <td class="param-default">14</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- ATR参数输入框 -->
          <div class="atr-param-inputs">
            <div class="ma-input-row">
              <label>ATR周期</label>
              <div class="input-with-unit">
                <input type="number" v-model="atrSettings.period" @input="updateAtrSettings" class="ma-input" placeholder="14">
                <span class="unit">日</span>
              </div>
            </div>
          </div>

          <!-- ATR信号设置 -->
          <div class="atr-signal-settings">
            <div class="ma-input-row">
              <label>高波动信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="atrHighVolChecked" @change="updateAtrSettings">
                <span class="checkbox-label">启用高波动信号</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>低波动信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="atrLowVolChecked" @change="updateAtrSettings">
                <span class="checkbox-label">启用低波动信号</span>
              </div>
            </div>
          </div>
        </div>

        <!-- TRIX指标参数设置 -->
        <div v-if="(indicator?.name || '').includes('TRIX')" class="trix-section">
          <div class="trix-header">
            <div class="trix-title">TRIX指标参数设置</div>
            <div class="trix-description">TRIX：三重指数平滑移动平均线</div>
          </div>

          <!-- TRIX参数表格 -->
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
                  <td class="param-name">TRIX周期</td>
                  <td>三重指数平滑周期</td>
                  <td class="param-default">12</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- TRIX参数输入框 -->
          <div class="trix-param-inputs">
            <div class="ma-input-row">
              <label>TRIX周期</label>
              <div class="input-with-unit">
                <input type="number" v-model="trixSettings.period" @input="updateTrixSettings" class="ma-input" placeholder="12">
                <span class="unit">日</span>
              </div>
            </div>
          </div>

          <!-- TRIX信号设置 -->
          <div class="trix-signal-settings">
            <div class="ma-input-row">
              <label>金叉信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="trixGoldenCrossChecked" @change="updateTrixSettings">
                <span class="checkbox-label">启用金叉信号</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>死叉信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="trixDeathCrossChecked" @change="updateTrixSettings">
                <span class="checkbox-label">启用死叉信号</span>
              </div>
            </div>
          </div>
        </div>

        <!-- CCI指标参数设置 -->
        <div v-if="(indicator?.name || '').includes('CCI') && isTechnicalIndicator" class="cci-section">
          <div class="cci-header">
            <div class="cci-title">CCI指标参数设置</div>
            <div class="cci-description">CCI：顺势指标，衡量价格偏离度</div>
          </div>

          <!-- CCI参数表格 -->
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
                  <td class="param-name">CCI周期</td>
                  <td>顺势指标计算周期</td>
                  <td class="param-default">14</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- CCI参数输入框 -->
          <div class="cci-param-inputs">
            <div class="ma-input-row">
              <label>CCI周期</label>
              <div class="input-with-unit">
                <input type="number" v-model="cciSettings.period" @input="updateCciSettings" class="ma-input" placeholder="14">
                <span class="unit">日</span>
              </div>
            </div>
          </div>

          <!-- CCI信号设置 -->
          <div class="cci-signal-settings">
            <div class="ma-input-row">
              <label>超买信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="cciOverboughtChecked" @change="updateCciSettings">
                <span class="checkbox-label">启用超买信号</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>超卖信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="cciOversoldChecked" @change="updateCciSettings">
                <span class="checkbox-label">启用超卖信号</span>
              </div>
            </div>
          </div>
        </div>

        <!-- BBIC指标参数设置 -->
        <div v-if="(indicator?.name || '').includes('BBIC')" class="bbic-section">
          <div class="bbic-header">
            <div class="bbic-title">BBIC指标参数设置</div>
            <div class="bbic-description">BBIC：布林带宽度指标</div>
          </div>

          <!-- BBIC参数表格 -->
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
                  <td class="param-name">BBIC周期</td>
                  <td>布林带宽度计算周期</td>
                  <td class="param-default">20</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- BBIC参数输入框 -->
          <div class="bbic-param-inputs">
            <div class="ma-input-row">
              <label>BBIC周期</label>
              <div class="input-with-unit">
                <input type="number" v-model="bbicSettings.period" @input="updateBbicSettings" class="ma-input" placeholder="20">
                <span class="unit">日</span>
              </div>
            </div>
          </div>

          <!-- BBIC信号设置 -->
          <div class="bbic-signal-settings">
            <div class="ma-input-row">
              <label>扩张信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="bbicExpansionChecked" @change="updateBbicSettings">
                <span class="checkbox-label">启用扩张信号</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>收缩信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="bbicContractionChecked" @change="updateBbicSettings">
                <span class="checkbox-label">启用收缩信号</span>
              </div>
            </div>
          </div>
        </div>

        <!-- EMA指标参数设置 -->
        <div v-if="(indicator?.name || '').includes('EMA')" class="ema-section">
          <div class="ema-header">
            <div class="ema-title">EMA指标参数设置</div>
            <div class="ema-description">EMA：指数移动平均线</div>
          </div>

          <!-- EMA参数表格 -->
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
                  <td class="param-name">EMA周期</td>
                  <td>指数移动平均线周期</td>
                  <td class="param-default">12</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- EMA参数输入框 -->
          <div class="ema-param-inputs">
            <div class="ma-input-row">
              <label>EMA周期</label>
              <div class="input-with-unit">
                <input type="number" v-model="emaSettings.period" @input="updateEmaSettings" class="ma-input" placeholder="12">
                <span class="unit">日</span>
              </div>
            </div>
          </div>

          <!-- EMA信号设置 -->
          <div class="ema-signal-settings">
            <div class="ma-input-row">
              <label>金叉信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="emaGoldenCrossChecked" @change="updateEmaSettings">
                <span class="checkbox-label">启用金叉信号</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>死叉信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="emaDeathCrossChecked" @change="updateEmaSettings">
                <span class="checkbox-label">启用死叉信号</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 四周期多头排列参数设置 -->
        <div v-if="(indicator?.name || '').includes('四周期多头排列')" class="four-period-section">
          <div class="four-period-header">
            <div class="four-period-title">四周期多头排列参数设置</div>
            <div class="four-period-description">四周期多头排列：短期、中期、长期均线多头排列</div>
          </div>

          <!-- 四周期参数表格 -->
          <div class="four-period-param-table">
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
                  <td class="param-name">短期周期</td>
                  <td>短期移动平均线周期</td>
                  <td class="param-default">5</td>
                </tr>
                <tr>
                  <td class="param-name">中期周期</td>
                  <td>中期移动平均线周期</td>
                  <td class="param-default">10</td>
                </tr>
                <tr>
                  <td class="param-name">长期周期</td>
                  <td>长期移动平均线周期</td>
                  <td class="param-default">20</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 四周期参数输入框 -->
          <div class="four-period-param-inputs">
            <div class="ma-input-row">
              <label>短期周期</label>
              <div class="input-with-unit">
                <input type="number" v-model="fourPeriodSettings.short" @input="updateFourPeriodSettings" class="ma-input" placeholder="5">
                <span class="unit">日</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>中期周期</label>
              <div class="input-with-unit">
                <input type="number" v-model="fourPeriodSettings.medium" @input="updateFourPeriodSettings" class="ma-input" placeholder="10">
                <span class="unit">日</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>长期周期</label>
              <div class="input-with-unit">
                <input type="number" v-model="fourPeriodSettings.long" @input="updateFourPeriodSettings" class="ma-input" placeholder="20">
                <span class="unit">日</span>
              </div>
            </div>
          </div>

          <!-- 四周期信号设置 -->
          <div class="four-period-signal-settings">
            <div class="ma-input-row">
              <label>多头排列信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="fourPeriodBullChecked" @change="updateFourPeriodSettings">
                <span class="checkbox-label">启用多头排列信号</span>
              </div>
            </div>
            <div class="ma-input-row">
              <label>空头排列信号</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="fourPeriodBearChecked" @change="updateFourPeriodSettings">
                <span class="checkbox-label">启用空头排列信号</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 开盘价参数设置 -->
        <div v-if="(indicator?.name || '').includes('开盘价')" class="open-price-section">
          <!-- 橙色标题栏 -->
          <div class="open-price-orange-header">
            <div class="open-price-orange-title">股票开盘价指标参数设置</div>
          </div>
          
          <!-- 指标描述 -->
          <div class="open-price-description">
            开盘价:股票当日开盘时的价格,反映市场开盘情绪
          </div>
          
          <!-- 参数说明表格 -->
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
                  <td class="param-name">开盘价</td>
                  <td>股票当日开盘价格</td>
                  <td class="param-default">收盘价、最高价、最低价、昨日收盘价、日成交均价</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 比较设置 -->
          <div class="open-price-comparison-settings">
            <div class="comparison-header">
              <div class="comparison-title">开盘价</div>
              <div class="comparison-operator">比较符</div>
              <div class="comparison-indicator">比较指标</div>
            </div>
            <div class="comparison-inputs">
              <div class="open-price-label">开盘价</div>
              <div class="operator-select">
                <select v-model="openPriceSettings.compare" @change="updateOpenPriceSettings" class="comparison-select">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
              <div class="indicator-select">
                <select v-model="openPriceSettings.indicator" @change="updateOpenPriceSettings" class="comparison-select">
                  <option value="">请选择比较指标</option>
                  <option value="收盘价">收盘价</option>
                  <option value="最高价">最高价</option>
                  <option value="最低价">最低价</option>
                  <option value="昨日收盘价">昨日收盘价</option>
                  <option value="日成交均价">日成交均价</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- 收盘价参数设置 -->
        <div v-if="(indicator?.name || '').includes('收盘价') && !(indicator?.name || '').includes('昨日收盘价') && isSectorTimingIndicator" class="close-price-section">
          <!-- 橙色标题栏 -->
          <div class="close-price-orange-header">
            <div class="close-price-orange-title">股票收盘价指标参数设置</div>
          </div>
          
          <!-- 指标描述 -->
          <div class="close-price-description">
            收盘价:股票当日收盘时的价格,反映当日交易结果
          </div>
          
          <!-- 参数说明表格 -->
          <div class="close-price-param-table">
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
                  <td class="param-name">收盘价</td>
                  <td>股票当日收盘价格</td>
                  <td class="param-default">开盘价、最高价、最低价、昨日收盘价、日成交均价</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 比较设置 -->
          <div class="close-price-comparison-settings">
            <div class="comparison-header">
              <div class="comparison-title">收盘价</div>
              <div class="comparison-operator">比较符</div>
              <div class="comparison-indicator">比较指标</div>
            </div>
            <div class="comparison-inputs">
              <div class="close-price-label">收盘价</div>
              <div class="operator-select">
                <select v-model="closePriceSettings.compare" @change="updateClosePriceSettings" class="comparison-select">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
              <div class="indicator-select">
                <select v-model="closePriceSettings.indicator" @change="updateClosePriceSettings" class="comparison-select">
                  <option value="">请选择比较指标</option>
                  <option value="开盘价">开盘价</option>
                  <option value="最高价">最高价</option>
                  <option value="最低价">最低价</option>
                  <option value="昨日收盘价">昨日收盘价</option>
                  <option value="日成交均价">日成交均价</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- 最高价参数设置 -->
        <div v-if="(indicator?.name || '').includes('最高价')" class="high-price-section">
          <!-- 橙色标题栏 -->
          <div class="high-price-orange-header">
            <div class="high-price-orange-title">股票最高价指标参数设置</div>
          </div>
          
          <!-- 指标描述 -->
          <div class="high-price-description">
            最高价:股票当日交易中的最高价格,反映当日价格上限
          </div>
          
          <!-- 参数说明表格 -->
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
                  <td class="param-name">最高价</td>
                  <td>股票当日最高价格</td>
                  <td class="param-default">开盘价、收盘价、最低价、昨日收盘价、日成交均价</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 比较设置 -->
          <div class="high-price-comparison-settings">
            <div class="comparison-header">
              <div class="comparison-title">最高价</div>
              <div class="comparison-operator">比较符</div>
              <div class="comparison-indicator">比较指标</div>
            </div>
            <div class="comparison-inputs">
              <div class="high-price-label">最高价</div>
              <div class="operator-select">
                <select v-model="highPriceSettings.compare" @change="updateHighPriceSettings" class="comparison-select">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
              <div class="indicator-select">
                <select v-model="highPriceSettings.indicator" @change="updateHighPriceSettings" class="comparison-select">
                  <option value="">请选择比较指标</option>
                  <option value="开盘价">开盘价</option>
                  <option value="收盘价">收盘价</option>
                  <option value="最低价">最低价</option>
                  <option value="昨日收盘价">昨日收盘价</option>
                  <option value="日成交均价">日成交均价</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- 最低价参数设置 -->
        <div v-if="(indicator?.name || '').includes('最低价')" class="low-price-section">
          <!-- 橙色标题栏 -->
          <div class="low-price-orange-header">
            <div class="low-price-orange-title">股票最低价指标参数设置</div>
          </div>
          
          <!-- 指标描述 -->
          <div class="low-price-description">
            最低价:股票当日交易中的最低价格,反映当日价格下限
          </div>
          
          <!-- 参数说明表格 -->
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
                  <td class="param-name">最低价</td>
                  <td>股票当日最低价格</td>
                  <td class="param-default">开盘价、收盘价、最高价、昨日收盘价、日成交均价</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 比较设置 -->
          <div class="low-price-comparison-settings">
            <div class="comparison-header">
              <div class="comparison-title">最低价</div>
              <div class="comparison-operator">比较符</div>
              <div class="comparison-indicator">比较指标</div>
            </div>
            <div class="comparison-inputs">
              <div class="low-price-label">最低价</div>
              <div class="operator-select">
                <select v-model="lowPriceSettings.compare" @change="updateLowPriceSettings" class="comparison-select">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
              <div class="indicator-select">
                <select v-model="lowPriceSettings.indicator" @change="updateLowPriceSettings" class="comparison-select">
                  <option value="">请选择比较指标</option>
                  <option value="开盘价">开盘价</option>
                  <option value="收盘价">收盘价</option>
                  <option value="最高价">最高价</option>
                  <option value="昨日收盘价">昨日收盘价</option>
                  <option value="日成交均价">日成交均价</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- 昨日收盘价参数设置 -->
        <div v-if="(indicator?.name || '').includes('昨日收盘价') && isSectorTimingIndicator" class="prev-close-price-section">
          <!-- 橙色标题栏 -->
          <div class="prev-close-price-orange-header">
            <div class="prev-close-price-orange-title">股票昨日收盘价指标参数设置</div>
          </div>
          
          <!-- 指标描述 -->
          <div class="prev-close-price-description">
            昨日收盘价:股票前一交易日的收盘价格,用于计算涨跌幅
          </div>
          
          <!-- 参数说明表格 -->
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
                  <td class="param-name">昨日收盘价</td>
                  <td>股票前一交易日收盘价格</td>
                  <td class="param-default">开盘价、收盘价、最高价、最低价、日成交均价</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 比较设置 -->
          <div class="prev-close-price-comparison-settings">
            <div class="comparison-header">
              <div class="comparison-title">昨日收盘价</div>
              <div class="comparison-operator">比较符</div>
              <div class="comparison-indicator">比较指标</div>
            </div>
            <div class="comparison-inputs">
              <div class="prev-close-price-label">昨日收盘价</div>
              <div class="operator-select">
                <select v-model="prevClosePriceSettings.compare" @change="updatePrevClosePriceSettings" class="comparison-select">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
              <div class="indicator-select">
                <select v-model="prevClosePriceSettings.indicator" @change="updatePrevClosePriceSettings" class="comparison-select">
                  <option value="">请选择比较指标</option>
                  <option value="开盘价">开盘价</option>
                  <option value="收盘价">收盘价</option>
                  <option value="最高价">最高价</option>
                  <option value="最低价">最低价</option>
                  <option value="日成交均价">日成交均价</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- 日成交均价参数设置 -->
        <div v-if="(indicator?.name || '').includes('日成交均价') && isSectorTimingIndicator" class="avg-price-section">
          <div class="avg-price-header">
            <div class="avg-price-title">日成交均价参数设置</div>
            <div class="avg-price-description">日成交均价：股票当日成交金额除以成交量的平均价格</div>
          </div>

          <!-- 日成交均价参数表格 -->
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
                  <td class="param-name">日成交均价</td>
                  <td>股票当日成交平均价格</td>
                  <td class="param-default">开盘价、收盘价、最高价、最低价、昨日收盘价</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 日成交均价参数输入框 -->
          <div class="avg-price-param-inputs">
            <div class="ma-input-row">
              <label>比较符</label>
              <div class="input-with-unit">
                <select v-model="avgPriceSettings.compare" @change="updateAvgPriceSettings" class="ma-input">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
            </div>
            <div class="ma-input-row">
              <label>比较指标</label>
              <div class="input-with-unit">
                <select v-model="avgPriceSettings.indicator" @change="updateAvgPriceSettings" class="ma-input">
                  <option value="">请选择比较指标</option>
                  <option value="开盘价">开盘价</option>
                  <option value="收盘价">收盘价</option>
                  <option value="最高价">最高价</option>
                  <option value="最低价">最低价</option>
                  <option value="昨日收盘价">昨日收盘价</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- 涨幅参数设置 -->
        <div v-if="(indicator?.name || '').includes('涨幅') && isSectorTimingIndicator" class="change-rate-section">
          <div class="change-rate-header">
            <div class="change-rate-title">涨幅参数设置</div>
            <div class="change-rate-description">涨幅：股票价格相对于基准价格的变动百分比，反映价格变动幅度</div>
          </div>

          <!-- 涨幅参数表格 -->
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
                  <td class="param-name">涨幅</td>
                  <td>股票价格变动百分比</td>
                  <td class="param-default">%</td>
                </tr>
                <tr>
                  <td class="param-name">区间涨幅</td>
                  <td>指定时间段内的价格变动百分比</td>
                  <td class="param-default">%</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 涨幅信号选择 -->
          <div class="change-rate-signal-settings">
            <div class="ma-input-row">
              <label>信号类型</label>
              <div class="input-with-unit">
                <select v-model="changeRateSettings.type" @change="updateChangeRateSettings" class="ma-input">
                  <option value="single">涨幅</option>
                  <option value="range">区间涨幅</option>
                </select>
              </div>
            </div>
          </div>

          <!-- 涨幅参数输入框 -->
          <div class="change-rate-param-inputs">
            <div class="ma-input-row">
              <label>比较符</label>
              <div class="input-with-unit">
                <select v-model="changeRateSettings.compare" @change="updateChangeRateSettings" class="ma-input">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
            </div>
            <div class="ma-input-row">
              <label>百分比值</label>
              <div class="input-with-unit">
                <input type="number" v-model="changeRateSettings.value" @input="updateChangeRateSettings" class="ma-input" placeholder="0.00" step="0.01">
                <span class="unit">%</span>
              </div>
            </div>
            <div v-if="changeRateSettings.type === 'range'" class="ma-input-row">
              <label>区间天数</label>
              <div class="input-with-unit">
                <input type="number" v-model="changeRateSettings.days" @input="updateChangeRateSettings" class="ma-input" placeholder="5">
                <span class="unit">日</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 量比参数设置 -->
        <div v-if="(indicator?.name || '').includes('量比') && isSectorTimingIndicator" class="volume-ratio-section">
          <div class="volume-ratio-header">
            <div class="volume-ratio-title">量比参数设置</div>
            <div class="volume-ratio-description">量比：当前成交量与过去5日平均成交量的比值，反映交易活跃度</div>
          </div>

          <!-- 量比参数表格 -->
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
                  <td class="param-name">量比</td>
                  <td>当前成交量与5日平均成交量比值</td>
                  <td class="param-default">1.0为正常水平</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 量比参数输入框 -->
          <div class="volume-ratio-param-inputs">
            <div class="ma-input-row">
              <label>比较符</label>
              <div class="input-with-unit">
                <select v-model="volumeRatioSettings.compare" @change="updateVolumeRatioSettings" class="ma-input">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
            </div>
            <div class="ma-input-row">
              <label>量比值</label>
              <div class="input-with-unit">
                <input type="number" v-model="volumeRatioSettings.value" @input="updateVolumeRatioSettings" class="ma-input" placeholder="1.00" step="0.01">
              </div>
            </div>
          </div>
        </div>

        <!-- 成交额参数设置 -->
        <div v-if="(indicator?.name || '').includes('成交额') && isSectorTimingIndicator" class="turnover-section">
          <div class="turnover-header">
            <div class="turnover-title">成交额参数设置</div>
            <div class="turnover-description">成交额：股票当日成交的总金额，反映市场交易规模</div>
          </div>

          <!-- 成交额参数表格 -->
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
                  <td class="param-name">成交额</td>
                  <td>股票当日成交总金额</td>
                  <td class="param-default">万元</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 成交额参数输入框 -->
          <div class="turnover-param-inputs">
            <div class="ma-input-row">
              <label>比较符</label>
              <div class="input-with-unit">
                <select v-model="turnoverSettings.compare" @change="updateTurnoverSettings" class="ma-input">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
            </div>
            <div class="ma-input-row">
              <label>成交额</label>
              <div class="input-with-unit">
                <input type="number" v-model="turnoverSettings.value" @input="updateTurnoverSettings" class="ma-input" placeholder="0.00" step="0.01">
                <span class="unit">万元</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 换手率参数设置 -->
        <div v-if="(indicator?.name || '').includes('换手率') && isSectorTimingIndicator" class="turnover-rate-section">
          <div class="turnover-rate-header">
            <div class="turnover-rate-title">换手率参数设置</div>
            <div class="turnover-rate-description">换手率：股票成交量与流通股本的比值，反映股票交易活跃度</div>
          </div>

          <!-- 换手率参数表格 -->
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
                  <td class="param-name">换手率</td>
                  <td>成交量与流通股本比值</td>
                  <td class="param-default">%</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 换手率参数输入框 -->
          <div class="turnover-rate-param-inputs">
            <div class="ma-input-row">
              <label>比较符</label>
              <div class="input-with-unit">
                <select v-model="turnoverRateSettings.compare" @change="updateTurnoverRateSettings" class="ma-input">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
            </div>
            <div class="ma-input-row">
              <label>换手率</label>
              <div class="input-with-unit">
                <input type="number" v-model="turnoverRateSettings.value" @input="updateTurnoverRateSettings" class="ma-input" placeholder="0.00" step="0.01">
                <span class="unit">%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 市值参数设置 -->
        <div v-if="(indicator?.name || '').includes('市值') && isSectorTimingIndicator" class="market-value-section">
          <div class="market-value-header">
            <div class="market-value-title">市值参数设置</div>
            <div class="market-value-description">市值：股票总股本乘以当前股价，反映公司整体价值</div>
          </div>

          <!-- 市值参数表格 -->
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
                  <td class="param-name">市值</td>
                  <td>总股本乘以当前股价</td>
                  <td class="param-default">亿元</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 市值参数输入框 -->
          <div class="market-value-param-inputs">
            <div class="ma-input-row">
              <label>比较符</label>
              <div class="input-with-unit">
                <select v-model="marketValueSettings.compare" @change="updateMarketValueSettings" class="ma-input">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
            </div>
            <div class="ma-input-row">
              <label>市值</label>
              <div class="input-with-unit">
                <input type="number" v-model="marketValueSettings.value" @input="updateMarketValueSettings" class="ma-input" placeholder="0.00" step="0.01">
                <span class="unit">亿元</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ROA参数设置 -->
        <div v-if="(indicator?.name || '').includes('ROA')" class="roa-section">
          <!-- 紫色标题栏 -->
          <div class="roa-purple-header">
            <div class="roa-purple-title">ROA: 总资产收益率,反映公司利用总资产创造利润的能力</div>
          </div>
          
          <!-- 参数表格 -->
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
                  <td class="param-name">ROA</td>
                  <td>总资产收益率</td>
                  <td class="param-unit">%</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 比较设置 -->
          <div class="roa-comparison-settings">
            <div class="comparison-header">
              <div class="comparison-title">ROA</div>
              <div class="comparison-operator">比较符</div>
              <div class="comparison-value">值</div>
            </div>
            <div class="comparison-inputs">
              <div class="roa-label">ROA</div>
              <div class="operator-select">
                <select v-model="roaSettings.compare" @change="updateRoaSettings" class="comparison-select">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
              <div class="value-input">
                <input type="number" v-model="roaSettings.value" @input="updateRoaSettings" class="comparison-input" step="0.01" placeholder="">
              </div>
            </div>
          </div>
        </div>

        <!-- ROE参数设置 -->
        <div v-if="(indicator?.name || '').includes('ROE')" class="roe-section">
          <!-- 紫色标题栏 -->
          <div class="roe-purple-header">
            <div class="roe-purple-title">ROE: 净资产收益率,反映公司利用股东权益创造利润的能力</div>
          </div>
          
          <!-- 参数表格 -->
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
                  <td class="param-name">ROE</td>
                  <td>净资产收益率</td>
                  <td class="param-unit">%</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 比较设置 -->
          <div class="roe-comparison-settings">
            <div class="comparison-header">
              <div class="comparison-title">ROE</div>
              <div class="comparison-operator">比较符</div>
              <div class="comparison-value">值</div>
            </div>
            <div class="comparison-inputs">
              <div class="roe-label">ROE</div>
              <div class="operator-select">
                <select v-model="roeSettings.compare" @change="updateRoeSettings" class="comparison-select">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
              <div class="value-input">
                <input type="number" v-model="roeSettings.value" @input="updateRoeSettings" class="comparison-input" step="0.01" placeholder="">
              </div>
            </div>
          </div>
        </div>

        <!-- 毛利率参数设置 -->
        <div v-if="(indicator?.name || '').includes('毛利率')" class="gross-margin-section">
          <!-- 紫色标题栏 -->
          <div class="gross-margin-purple-header">
            <div class="gross-margin-purple-title">毛利率: 毛利润与营业收入的比值,反映公司产品盈利能力</div>
          </div>
          
          <!-- 参数表格 -->
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
                  <td class="param-name">毛利率</td>
                  <td>毛利润与营业收入比值</td>
                  <td class="param-unit">%</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 比较设置 -->
          <div class="gross-margin-comparison-settings">
            <div class="comparison-header">
              <div class="comparison-title">毛利率</div>
              <div class="comparison-operator">比较符</div>
              <div class="comparison-value">值</div>
            </div>
            <div class="comparison-inputs">
              <div class="gross-margin-label">毛利率</div>
              <div class="operator-select">
                <select v-model="grossMarginSettings.compare" @change="updateGrossMarginSettings" class="comparison-select">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
              <div class="value-input">
                <input type="number" v-model="grossMarginSettings.value" @input="updateGrossMarginSettings" class="comparison-input" step="0.01" placeholder="">
              </div>
            </div>
          </div>
        </div>

        <!-- 净利率参数设置 -->
        <div v-if="(indicator?.name || '').includes('净利率')" class="net-margin-section">
          <!-- 紫色标题栏 -->
          <div class="net-margin-purple-header">
            <div class="net-margin-purple-title">净利率: 净利润与营业收入的比值,反映公司整体盈利能力</div>
          </div>
          
          <!-- 参数表格 -->
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
                  <td class="param-name">净利率</td>
                  <td>净利润与营业收入比值</td>
                  <td class="param-unit">%</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 比较设置 -->
          <div class="net-margin-comparison-settings">
            <div class="comparison-header">
              <div class="comparison-title">净利率</div>
              <div class="comparison-operator">比较符</div>
              <div class="comparison-value">值</div>
            </div>
            <div class="comparison-inputs">
              <div class="net-margin-label">净利率</div>
              <div class="operator-select">
                <select v-model="netMarginSettings.compare" @change="updateNetMarginSettings" class="comparison-select">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
              <div class="value-input">
                <input type="number" v-model="netMarginSettings.value" @input="updateNetMarginSettings" class="comparison-input" step="0.01" placeholder="">
              </div>
            </div>
          </div>
        </div>

        <!-- 营收增长率参数设置 -->
        <div v-if="(indicator?.name || '').includes('营收增长率')" class="revenue-growth-section">
          <!-- 紫色标题栏 -->
          <div class="revenue-growth-purple-header">
            <div class="revenue-growth-purple-title">营收增长率: 营业收入同比增长率,反映公司业务扩张速度</div>
          </div>
          
          <!-- 参数表格 -->
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
                  <td class="param-name">营收增长率</td>
                  <td>营业收入同比增长率</td>
                  <td class="param-unit">%</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 比较设置 -->
          <div class="revenue-growth-comparison-settings">
            <div class="comparison-header">
              <div class="comparison-title">营收增长率</div>
              <div class="comparison-operator">比较符</div>
              <div class="comparison-value">值</div>
            </div>
            <div class="comparison-inputs">
              <div class="revenue-growth-label">营收增长率</div>
              <div class="operator-select">
                <select v-model="revenueGrowthSettings.compare" @change="updateRevenueGrowthSettings" class="comparison-select">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
              <div class="value-input">
                <input type="number" v-model="revenueGrowthSettings.value" @input="updateRevenueGrowthSettings" class="comparison-input" step="0.01" placeholder="">
              </div>
            </div>
          </div>
        </div>

        <!-- 净利润增长率参数设置 -->
        <div v-if="(indicator?.name || '').includes('净利润增长率')" class="profit-growth-section">
          <!-- 紫色标题栏 -->
          <div class="profit-growth-purple-header">
            <div class="profit-growth-purple-title">净利润增长率: 净利润同比增长率,反映公司盈利能力提升速度</div>
          </div>
          
          <!-- 参数表格 -->
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
                  <td class="param-name">净利润增长率</td>
                  <td>净利润同比增长率</td>
                  <td class="param-unit">%</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 比较设置 -->
          <div class="profit-growth-comparison-settings">
            <div class="comparison-header">
              <div class="comparison-title">净利润增长率</div>
              <div class="comparison-operator">比较符</div>
              <div class="comparison-value">值</div>
            </div>
            <div class="comparison-inputs">
              <div class="profit-growth-label">净利润增长率</div>
              <div class="operator-select">
                <select v-model="profitGrowthSettings.compare" @change="updateProfitGrowthSettings" class="comparison-select">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
              <div class="value-input">
                <input type="number" v-model="profitGrowthSettings.value" @input="updateProfitGrowthSettings" class="comparison-input" step="0.01" placeholder="">
              </div>
            </div>
          </div>
        </div>

        <!-- 动态市盈率参数设置 -->
        <div v-if="(indicator?.name || '').includes('动态市盈率')" class="dynamic-pe-section">
          <!-- 紫色标题栏 -->
          <div class="dynamic-pe-purple-header">
            <div class="dynamic-pe-purple-title">动态市盈率: 股价与预期每股收益的比值,反映股票估值水平</div>
          </div>
          
          <!-- 参数表格 -->
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
                  <td class="param-name">动态市盈率</td>
                  <td>股价与预期每股收益比值</td>
                  <td class="param-unit">倍</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 比较设置 -->
          <div class="dynamic-pe-comparison-settings">
            <div class="comparison-header">
              <div class="comparison-title">动态市盈率</div>
              <div class="comparison-operator">比较符</div>
              <div class="comparison-value">值</div>
            </div>
            <div class="comparison-inputs">
              <div class="dynamic-pe-label">动态市盈率</div>
              <div class="operator-select">
                <select v-model="dynamicPeSettings.compare" @change="updateDynamicPeSettings" class="comparison-select">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
              <div class="value-input">
                <input type="number" v-model="dynamicPeSettings.value" @input="updateDynamicPeSettings" class="comparison-input" step="0.01" placeholder="">
              </div>
            </div>
          </div>
        </div>

        <!-- 市净率参数设置 -->
        <div v-if="(indicator?.name || '').includes('市净率')" class="pb-ratio-section">
          <!-- 紫色标题栏 -->
          <div class="pb-ratio-purple-header">
            <div class="pb-ratio-purple-title">市净率: 股价与每股净资产的比值</div>
          </div>
          
          <!-- 参数表格 -->
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
                  <td class="param-name">市净率</td>
                  <td>股价与每股净资产比值</td>
                  <td class="param-unit">倍</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 比较设置 -->
          <div class="pb-ratio-comparison-settings">
            <div class="comparison-header">
              <div class="comparison-title">市净率</div>
              <div class="comparison-operator">比较符</div>
              <div class="comparison-value">值</div>
            </div>
            <div class="comparison-inputs">
              <div class="pb-ratio-label">市净率</div>
              <div class="operator-select">
                <select v-model="pbRatioSettings.compare" @change="updatePbRatioSettings" class="comparison-select">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
              <div class="value-input">
                <input type="number" v-model="pbRatioSettings.value" @input="updatePbRatioSettings" class="comparison-input" step="0.01" placeholder="">
              </div>
            </div>
          </div>
        </div>

        <!-- 市销率参数设置 -->
        <div v-if="(indicator?.name || '').includes('市销率')" class="ps-ratio-section">
          <!-- 紫色标题栏 -->
          <div class="ps-ratio-purple-header">
            <div class="ps-ratio-purple-title">市销率: 股价与每股营业收入的比值</div>
          </div>
          
          <!-- 参数表格 -->
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
                  <td class="param-name">市销率</td>
                  <td>股价与每股营业收入比值</td>
                  <td class="param-unit">倍</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 比较设置 -->
          <div class="ps-ratio-comparison-settings">
            <div class="comparison-header">
              <div class="comparison-title">市销率</div>
              <div class="comparison-operator">比较符</div>
              <div class="comparison-value">值</div>
            </div>
            <div class="comparison-inputs">
              <div class="ps-ratio-label">市销率</div>
              <div class="operator-select">
                <select v-model="psRatioSettings.compare" @change="updatePsRatioSettings" class="comparison-select">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
              <div class="value-input">
                <input type="number" v-model="psRatioSettings.value" @input="updatePsRatioSettings" class="comparison-input" step="0.01" placeholder="">
              </div>
            </div>
          </div>
        </div>

        <!-- 股东减持参数设置 -->
        <div v-if="(indicator?.name || '').includes('股东减持')" class="shareholder-reduction-section">
          <div class="shareholder-reduction-header">
            <div class="shareholder-reduction-title">股东减持指标参数设置</div>
            <div class="shareholder-reduction-description">股东减持：公司股东减少持股数量的行为，可能影响股价走势</div>
          </div>
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
          <div class="shareholder-reduction-param-inputs">
            <div class="ma-input-row">
              <label>是否启用</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="shareholderReductionChecked" @change="updateShareholderReductionSettings">
                <span class="checkbox-label">启用股东减持监控</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 股东增持参数设置 -->
        <div v-if="(indicator?.name || '').includes('股东增持')" class="shareholder-increase-section">
          <div class="shareholder-increase-header">
            <div class="shareholder-increase-title">股东增持指标参数设置</div>
            <div class="shareholder-increase-description">股东增持：公司股东增加持股数量的行为，通常被视为积极信号</div>
          </div>
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
          <div class="shareholder-increase-param-inputs">
            <div class="ma-input-row">
              <label>是否启用</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="shareholderIncreaseChecked" @change="updateShareholderIncreaseSettings">
                <span class="checkbox-label">启用股东增持监控</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 股东分红参数设置 -->
        <div v-if="(indicator?.name || '').includes('股东分红')" class="shareholder-dividend-section">
          <div class="shareholder-dividend-header">
            <div class="shareholder-dividend-title">股东分红指标参数设置</div>
            <div class="shareholder-dividend-description">股东分红：公司向股东分配利润的行为，反映公司盈利能力和股东回报</div>
          </div>
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
          <div class="shareholder-dividend-param-inputs">
            <div class="ma-input-row">
              <label>是否启用</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="shareholderDividendChecked" @change="updateShareholderDividendSettings">
                <span class="checkbox-label">启用股东分红监控</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 违规问询函参数设置 -->
        <div v-if="(indicator?.name || '').includes('违规问询函')" class="violation-inquiry-section">
          <div class="violation-inquiry-header">
            <div class="violation-inquiry-title">违规问询函指标参数设置</div>
            <div class="violation-inquiry-description">违规问询函：监管机构对公司违规行为的问询，可能影响公司声誉和股价</div>
          </div>
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
          <div class="violation-inquiry-param-inputs">
            <div class="ma-input-row">
              <label>是否启用</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="violationInquiryChecked" @change="updateViolationInquirySettings">
                <span class="checkbox-label">启用违规问询函监控</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 业绩预告参数设置 -->
        <div v-if="(indicator?.name || '').includes('业绩预告')" class="performance-forecast-section">
          <div class="performance-forecast-header">
            <div class="performance-forecast-title">业绩预告指标参数设置</div>
            <div class="performance-forecast-description">业绩预告：公司对未来业绩的预测公告，影响投资者对公司前景的判断</div>
          </div>
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
          <div class="performance-forecast-param-inputs">
            <div class="ma-input-row">
              <label>指标类型</label>
              <div class="input-with-unit">
                <select v-model="performanceForecastSettings.type" @change="updatePerformanceForecastSettings" class="ma-input">
                  <option value="profit_yoy">净利润同比去年涨幅</option>
                  <option value="net_profit">净利润</option>
                </select>
              </div>
            </div>
            <div class="ma-input-row">
              <label>比较符</label>
              <div class="input-with-unit">
                <select v-model="performanceForecastSettings.compare" @change="updatePerformanceForecastSettings" class="ma-input">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
            </div>
            <div class="ma-input-row">
              <label>{{ performanceForecastSettings.type === 'profit_yoy' ? '净利润同比涨幅' : '净利润' }}</label>
              <div class="input-with-unit">
                <input type="number" v-model="performanceForecastSettings.value" @input="updatePerformanceForecastSettings" class="ma-input" step="0.01">
                <span class="unit">{{ performanceForecastSettings.type === 'profit_yoy' ? '%' : '万元' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 成交量参数设置 -->
        <div v-if="(indicator?.name || '').includes('成交量') && isSectorTimingIndicator" class="volume-section">
          <div class="volume-header">
            <div class="volume-title">成交量参数设置</div>
            <div class="volume-description">成交量：股票当日成交的股票数量，反映市场交易活跃度</div>
          </div>

          <!-- 成交量参数表格 -->
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
                  <td class="param-name">成交量</td>
                  <td>股票当日成交数量</td>
                  <td class="param-default">万股</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 成交量参数输入框 -->
          <div class="volume-param-inputs">
            <div class="ma-input-row">
              <label>比较符</label>
              <div class="input-with-unit">
                <select v-model="volumeSettings.compare" @change="updateVolumeSettings" class="ma-input">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
            </div>
            <div class="ma-input-row">
              <label>成交量</label>
              <div class="input-with-unit">
                <input type="number" v-model="volumeSettings.value" @input="updateVolumeSettings" class="ma-input" placeholder="0.00" step="0.01">
                <span class="unit">万股</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 资金净流入参数设置 -->
        <div v-if="(indicator?.name || '').includes('资金净流入') && isSectorTimingIndicator" class="capital-inflow-section">
          <div class="capital-inflow-header">
            <div class="capital-inflow-title">资金净流入参数设置</div>
            <div class="capital-inflow-description">资金净流入：主力资金流入与流出的差额，反映资金流向趋势</div>
          </div>

          <!-- 资金净流入参数表格 -->
          <div class="capital-inflow-param-table">
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
                  <td class="param-name">资金净流入</td>
                  <td>主力资金流入与流出差额</td>
                  <td class="param-default">万元</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 资金净流入参数输入框 -->
          <div class="capital-inflow-param-inputs">
            <div class="ma-input-row">
              <label>比较符</label>
              <div class="input-with-unit">
                <select v-model="netInflowSettings.compare" @change="updateNetInflowSettings" class="ma-input">
                  <option value="大于">大于</option>
                  <option value="小于">小于</option>
                  <option value="大于等于">大于等于</option>
                  <option value="小于等于">小于等于</option>
                  <option value="等于">等于</option>
                </select>
              </div>
            </div>
            <div class="ma-input-row">
              <label>资金净流入</label>
              <div class="input-with-unit">
                <input type="number" v-model="netInflowSettings.value" @input="updateNetInflowSettings" class="ma-input" placeholder="0.00" step="0.01">
                <span class="unit">万元</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 过滤新上市参数设置 -->
        <div v-if="(indicator?.name || '').includes('过滤新上市')" class="filter-new-listed-section">
          <div class="filter-new-listed-header">
            <div class="filter-new-listed-title">过滤新上市参数设置</div>
            <div class="filter-new-listed-description">过滤新上市：过滤新上市的股票，避免新股波动影响</div>
          </div>

          <!-- 过滤新上市参数表格 -->
          <div class="filter-new-listed-param-table">
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
                  <td class="param-name">过滤新上市</td>
                  <td>过滤新上市的股票</td>
                  <td class="param-default">布尔值</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 过滤新上市参数设置 -->
          <div class="filter-new-listed-param-inputs">
            <div class="ma-input-row">
              <label>是否启用过滤</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="filterNewListedChecked" @change="updateFilterNewListedSettings">
                <span class="checkbox-label">启用新上市过滤</span>
              </div>
            </div>
            
          </div>
        </div>

        <!-- 过滤北交所参数设置 -->
        <div v-if="(indicator?.name || '').includes('过滤北交所')" class="filter-bse-section">
          <div class="filter-bse-header">
            <div class="filter-bse-title">过滤北交所参数设置</div>
            <div class="filter-bse-description">过滤北交所：过滤北京证券交易所的股票</div>
          </div>

          <!-- 过滤北交所参数表格 -->
          <div class="filter-bse-param-table">
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
                  <td class="param-name">过滤北交所</td>
                  <td>过滤北京证券交易所股票</td>
                  <td class="param-default">布尔值</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 过滤北交所参数设置 -->
          <div class="filter-bse-param-inputs">
            <div class="ma-input-row">
              <label>是否启用过滤</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="filterBseChecked" @change="updateFilterBseSettings">
                <span class="checkbox-label">启用北交所过滤</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 过滤沪深主板参数设置 -->
        <div v-if="(indicator?.name || '').includes('过滤沪深主板')" class="filter-main-board-section">
          <div class="filter-main-board-header">
            <div class="filter-main-board-title">过滤沪深主板参数设置</div>
            <div class="filter-main-board-description">过滤上海和深圳证券交易所主板的股票</div>
          </div>

          <!-- 过滤沪深主板参数表格 -->
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
                  <td class="param-name">过滤沪深主板</td>
                  <td>过滤上海和深圳主板股票</td>
                  <td class="param-default">布尔值</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 过滤沪深主板参数设置 -->
          <div class="filter-main-board-param-inputs">
            <div class="ma-input-row">
              <label>是否启用过滤</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="filterMainBoardChecked" @change="updateFilterMainBoardSettings">
                <span class="checkbox-label">启用沪深主板过滤</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 过滤ST参数设置 -->
        <div v-if="(indicator?.name || '').includes('过滤ST')" class="filter-st-section">
          <div class="filter-st-header">
            <div class="filter-st-title">过滤ST参数设置</div>
            <div class="filter-st-description">过滤ST：过滤特别处理股票，避免风险较大的股票</div>
          </div>

          <!-- 过滤ST参数表格 -->
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
                  <td class="param-name">过滤ST</td>
                  <td>过滤特别处理股票</td>
                  <td class="param-default">布尔值</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 过滤ST参数设置 -->
          <div class="filter-st-param-inputs">
            <div class="ma-input-row">
              <label>是否启用过滤</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="filterStChecked" @change="updateFilterStSettings">
                <span class="checkbox-label">启用ST过滤</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 过滤*ST参数设置 -->
        <div v-if="(indicator?.name || '').includes('过滤*ST')" class="filter-ast-section">
          <div class="filter-ast-header">
            <div class="filter-ast-title">过滤*ST参数设置</div>
            <div class="filter-ast-description">过滤*ST：过滤退市风险警示股票，避免高风险股票</div>
          </div>

          <!-- 过滤*ST参数表格 -->
          <div class="filter-ast-param-table">
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
                  <td class="param-name">过滤*ST</td>
                  <td>过滤退市风险警示股票</td>
                  <td class="param-default">布尔值</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 过滤*ST参数设置 -->
          <div class="filter-ast-param-inputs">
            <div class="ma-input-row">
              <label>是否启用过滤</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="filterAstChecked" @change="updateFilterAstSettings">
                <span class="checkbox-label">启用*ST过滤</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 过滤停牌参数设置 -->
        <div v-if="(indicator?.name || '').includes('过滤停牌')" class="filter-suspended-section">
          <div class="filter-suspended-header">
            <div class="filter-suspended-title">过滤停牌参数设置</div>
            <div class="filter-suspended-description">过滤停牌：过滤停牌的股票，避免无法交易的股票</div>
          </div>

          <!-- 过滤停牌参数表格 -->
          <div class="filter-suspended-param-table">
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
                  <td class="param-name">过滤停牌</td>
                  <td>过滤停牌的股票</td>
                  <td class="param-default">布尔值</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 过滤停牌参数设置 -->
          <div class="filter-suspended-param-inputs">
            <div class="ma-input-row">
              <label>是否启用过滤</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="filterSuspendedChecked" @change="updateFilterSuspendedSettings">
                <span class="checkbox-label">启用停牌过滤</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 过滤科创板参数设置 -->
        <div v-if="(indicator?.name || '').includes('过滤科创板')" class="filter-star-section">
          <div class="filter-star-header">
            <div class="filter-star-title">过滤科创板参数设置</div>
            <div class="filter-star-description">过滤科创板：过滤上海证券交易所科创板的股票</div>
          </div>

          <!-- 过滤科创板参数表格 -->
          <div class="filter-star-param-table">
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
                  <td class="param-name">过滤科创板</td>
                  <td>过滤科创板股票</td>
                  <td class="param-default">布尔值</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 过滤科创板参数设置 -->
          <div class="filter-star-param-inputs">
            <div class="ma-input-row">
              <label>是否启用过滤</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="filterStarChecked" @change="updateFilterStarSettings">
                <span class="checkbox-label">启用科创板过滤</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 过滤创业板参数设置 -->
        <div v-if="(indicator?.name || '').includes('过滤创业板')" class="filter-chinext-section">
          <div class="filter-chinext-header">
            <div class="filter-chinext-title">过滤创业板参数设置</div>
            <div class="filter-chinext-description">过滤创业板：过滤深圳证券交易所创业板的股票</div>
          </div>

          <!-- 过滤创业板参数表格 -->
          <div class="filter-chinext-param-table">
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
                  <td class="param-name">过滤创业板</td>
                  <td>过滤创业板股票</td>
                  <td class="param-default">布尔值</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 过滤创业板参数设置 -->
          <div class="filter-chinext-param-inputs">
            <div class="ma-input-row">
              <label>是否启用过滤</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="filterChinextChecked" @change="updateFilterChinextSettings">
                <span class="checkbox-label">启用创业板过滤</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 过滤退市参数设置 -->
        <div v-if="(indicator?.name || '').includes('过滤退市')" class="filter-delisted-section">
          <div class="filter-delisted-header">
            <div class="filter-delisted-title">过滤退市参数设置</div>
            <div class="filter-delisted-description">过滤退市：过滤退市的股票，避免已退市的股票</div>
          </div>

          <!-- 过滤退市参数表格 -->
          <div class="filter-delisted-param-table">
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
                  <td class="param-name">过滤退市</td>
                  <td>过滤退市的股票</td>
                  <td class="param-default">布尔值</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 过滤退市参数设置 -->
          <div class="filter-delisted-param-inputs">
            <div class="ma-input-row">
              <label>是否启用过滤</label>
              <div class="checkbox-wrapper">
                <input type="checkbox" v-model="filterDelistedChecked" @change="updateFilterDelistedSettings">
                <span class="checkbox-label">启用退市过滤</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-actions">
        <button class="save-btn" @click="$emit('save')">保存参数</button>
        <button class="reset-btn" @click="$emit('reset')">重置默认</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';

export default {
  name: 'IndicatorParamDialog',
  props: {
    show: { type: Boolean, default: false },
    indicator: { type: Object, default: () => ({}) },
    marketIndex: { type: String, default: '上证指数' },
    period: { type: String, default: 'D' }, // D/W/M
    maShort: { type: Number, default: 5 },
    maLong: { type: Number, default: 20 }
  },
  emits: ['close', 'save', 'reset', 'update:marketIndex', 'update:period', 'update:maShort', 'update:maLong', 'update:indicator'],
  setup() {
    // KDJ 设置
    const kdjSettings = ref({
      k: 9,
      d: 3,
      j: 3
    });
    const kdjGoldenCrossChecked = ref(true);
    const kdjDeathCrossChecked = ref(true);

    // MACD 设置
    const macdSettings = ref({
      fast: 12,
      slow: 26,
      signal: 9
    });
    const macdGoldenCrossChecked = ref(true);
    const macdDeathCrossChecked = ref(true);

    // MA 设置
    const maGoldenCrossChecked = ref(true);
    const maDeathCrossChecked = ref(true);

    // RSI 设置
    const rsiSettings = ref({
      period: 14
    });
    const rsiOverboughtChecked = ref(true);
    const rsiOversoldChecked = ref(true);

    // BOLL 设置
    const bollSettings = ref({
      period: 20,
      multiplier: 2
    });
    const bollUpperChecked = ref(true);
    const bollLowerChecked = ref(true);

    // CR 设置
    const crSettings = ref({
      period: 26
    });
    const crBullChecked = ref(true);
    const crBearChecked = ref(true);

    // ATR 设置
    const atrSettings = ref({
      period: 14
    });
    const atrHighVolChecked = ref(true);
    const atrLowVolChecked = ref(true);

    // TRIX 设置
    const trixSettings = ref({
      period: 12
    });
    const trixGoldenCrossChecked = ref(true);
    const trixDeathCrossChecked = ref(true);

    // CCI 设置
    const cciSettings = ref({
      period: 14
    });
    const cciOverboughtChecked = ref(true);
    const cciOversoldChecked = ref(true);

    // BBIC 设置
    const bbicSettings = ref({
      period: 20
    });
    const bbicExpansionChecked = ref(true);
    const bbicContractionChecked = ref(true);

    // EMA 设置
    const emaSettings = ref({
      period: 12
    });
    const emaGoldenCrossChecked = ref(true);
    const emaDeathCrossChecked = ref(true);

    // 板块择时设置
    const selectedSectorIndex = ref('transport');
    const selectedSectorPeriod = ref('D');
    const sectorMaShort = ref(5);
    const sectorMaLong = ref(60);
    const sectorMaGoldenCrossChecked = ref(true);
    const sectorMaDeathCrossChecked = ref(true);

    // 板块择时MACD设置
    const selectedSectorMacdIndex = ref('transport');
    const selectedSectorMacdPeriod = ref('D');
    const sectorMacdSettings = ref({
      fast: 26,
      slow: 12,
      signal: 9
    });
    const sectorMacdGoldenCrossChecked = ref(true);
    const sectorMacdDeathCrossChecked = ref(true);

    // 板块择时KDJ设置
    const selectedSectorKdjIndex = ref('transport');
    const selectedSectorKdjPeriod = ref('D');
    const sectorKdjSettings = ref({
      k: 9,
      d: 3,
      j: 3
    });
    const sectorKdjGoldenCrossChecked = ref(true);
    const sectorKdjDeathCrossChecked = ref(true);

    // 周期选项
    const periods = ref([
      { value: 'D', label: '日' },
      { value: 'W', label: '周' },
      { value: 'M', label: '月' }
    ]);

    // 个股择时MA指标设置
    const timingSelectedSignal = ref('ma');
    const maShortPeriod = ref(5);
    const maLongPeriod = ref(20);
    const maCompare = ref('大于');
    const maCustomValue = ref(0);
    const maCrossCompare = ref('大于');
    const maCrossCustomValue = ref(0);
    const maTrendCompare = ref('大于');
    const maTrendCustomValue = ref(0);
    const maDivergenceCompare = ref('大于');
    const maDivergenceCustomValue = ref(0);

    // 代理：避免模板中 v-model 使用三元表达式
    const maActiveCompare = computed({
      get() {
        return timingSelectedSignal.value === 'ma' ? maCompare.value : maCrossCompare.value;
      },
      set(val) {
        if (timingSelectedSignal.value === 'ma') {
          maCompare.value = val;
        } else {
          maCrossCompare.value = val;
        }
      }
    });

    const maActiveValue = computed({
      get() {
        return timingSelectedSignal.value === 'ma' ? maCustomValue.value : maCrossCustomValue.value;
      },
      set(val) {
        if (timingSelectedSignal.value === 'ma') {
          maCustomValue.value = val;
        } else {
          maCrossCustomValue.value = val;
        }
      }
    });

    // 四周期多头排列设置
    const fourPeriodSettings = ref({
      short: 5,
      medium: 10,
      long: 20
    });
    const fourPeriodBullChecked = ref(true);
    const fourPeriodBearChecked = ref(true);

    // 开盘价设置
    const openPriceSettings = ref({
      compare: '大于',
      indicator: ''
    });

    // 收盘价设置
    const closePriceSettings = ref({
      compare: '大于',
      indicator: ''
    });

    // 最高价设置
    const highPriceSettings = ref({
      compare: '大于',
      indicator: ''
    });

    // 最低价设置
    const lowPriceSettings = ref({
      compare: '大于',
      indicator: ''
    });

    // 昨日收盘价设置
    const prevClosePriceSettings = ref({
      compare: '大于',
      indicator: ''
    });

    // 日成交均价设置
    const avgPriceSettings = ref({
      compare: '大于',
      indicator: ''
    });

    // 涨幅设置
    const changeRateSettings = ref({
      type: 'single',
      compare: '大于',
      value: 0,
      days: 5
    });

    // 量比设置
    const volumeRatioSettings = ref({
      compare: '大于',
      value: 1.0
    });

    // 成交额设置
    const turnoverSettings = ref({
      compare: '大于',
      value: 0
    });

    // 换手率设置
    const turnoverRateSettings = ref({
      compare: '大于',
      value: 0
    });

    // 市值设置
    const marketValueSettings = ref({
      compare: '大于',
      value: 0
    });

    // 成交量设置
    const volumeSettings = ref({
      compare: '大于',
      value: 0
    });

    // 资金净流入设置
    const netInflowSettings = ref({
      compare: '大于',
      value: 0
    });

    // 过滤新上市设置
    const filterNewListedSettings = ref({
      days: 30
    });
    const filterNewListedChecked = ref(false);

    // 过滤北交所设置
    const filterBseChecked = ref(false);

    // 过滤沪深主板设置
    const filterMainBoardChecked = ref(false);

    // 过滤ST设置
    const filterStChecked = ref(false);

    // 过滤*ST设置
    const filterAstChecked = ref(false);

    // 过滤停牌设置
    const filterSuspendedChecked = ref(false);

    // 过滤科创板设置
    const filterStarChecked = ref(false);

    // 过滤创业板设置
    const filterChinextChecked = ref(false);

    // 过滤退市设置
    const filterDelistedChecked = ref(false);

    // 新增：财务指标设置
    const roaSettings = ref({ compare: '大于', value: 0 });
    const roeSettings = ref({ compare: '大于', value: 0 });
    const grossMarginSettings = ref({ compare: '大于', value: 0 });
    const netMarginSettings = ref({ compare: '大于', value: 0 });
    const revenueGrowthSettings = ref({ compare: '大于', value: 0 });
    const profitGrowthSettings = ref({ compare: '大于', value: 0 });
    const dynamicPeSettings = ref({ compare: '大于', value: 0 });
    const pbRatioSettings = ref({ compare: '大于', value: 0 });
    const psRatioSettings = ref({ compare: '大于', value: 0 });

    // 新增：公告类指标设置
    const shareholderReductionChecked = ref(false);
    const shareholderIncreaseChecked = ref(false);
    const shareholderDividendChecked = ref(false);
    const violationInquiryChecked = ref(false);
    const performanceForecastSettings = ref({
      type: 'profit_yoy',
      compare: '大于',
      value: 0
    });

    return {
      kdjSettings,
      kdjGoldenCrossChecked,
      kdjDeathCrossChecked,
      macdSettings,
      macdGoldenCrossChecked,
      macdDeathCrossChecked,
      maGoldenCrossChecked,
      maDeathCrossChecked,
      rsiSettings,
      rsiOverboughtChecked,
      rsiOversoldChecked,
      bollSettings,
      bollUpperChecked,
      bollLowerChecked,
      crSettings,
      crBullChecked,
      crBearChecked,
      atrSettings,
      atrHighVolChecked,
      atrLowVolChecked,
      trixSettings,
      trixGoldenCrossChecked,
      trixDeathCrossChecked,
      cciSettings,
      cciOverboughtChecked,
      cciOversoldChecked,
      bbicSettings,
      bbicExpansionChecked,
      bbicContractionChecked,
      emaSettings,
      emaGoldenCrossChecked,
      emaDeathCrossChecked,
      selectedSectorIndex,
      selectedSectorPeriod,
      sectorMaShort,
      sectorMaLong,
      sectorMaGoldenCrossChecked,
      sectorMaDeathCrossChecked,
      selectedSectorMacdIndex,
      selectedSectorMacdPeriod,
      sectorMacdSettings,
      sectorMacdGoldenCrossChecked,
      sectorMacdDeathCrossChecked,
      selectedSectorKdjIndex,
      selectedSectorKdjPeriod,
      sectorKdjSettings,
      sectorKdjGoldenCrossChecked,
      sectorKdjDeathCrossChecked,
      periods,
      timingSelectedSignal,
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
      maActiveCompare,
      maActiveValue,
      fourPeriodSettings,
      fourPeriodBullChecked,
      fourPeriodBearChecked,
      openPriceSettings,
      closePriceSettings,
      highPriceSettings,
      lowPriceSettings,
      prevClosePriceSettings,
      avgPriceSettings,
      changeRateSettings,
      volumeRatioSettings,
      turnoverSettings,
      turnoverRateSettings,
      marketValueSettings,
      volumeSettings,
      netInflowSettings,
      filterNewListedSettings,
      filterNewListedChecked,
      filterBseChecked,
      filterMainBoardChecked,
      filterStChecked,
      filterAstChecked,
      filterSuspendedChecked,
      filterStarChecked,
      filterChinextChecked,
      filterDelistedChecked,
      // 新增返回
      roaSettings,
      roeSettings,
      grossMarginSettings,
      netMarginSettings,
      revenueGrowthSettings,
      profitGrowthSettings,
      dynamicPeSettings,
      pbRatioSettings,
      psRatioSettings,
      shareholderReductionChecked,
      shareholderIncreaseChecked,
      shareholderDividendChecked,
      violationInquiryChecked,
      performanceForecastSettings
    };
  },
  computed: {
    isTechnicalIndicator() {
      if (!this.indicator?.name) return false;
      // 大盘择时指标需要显示市场指数和周期选择
      const marketTimingIndicators = ['MA', 'MACD', 'KDJ', 'RSI', 'BOLL', 'CCI', 'WR', 'DMI'];
      return marketTimingIndicators.some(indicator => this.indicator.name.includes(indicator));
    },
    isSectorTimingIndicator() {
      if (!this.indicator?.category) return false;
      // 板块择时（block）的指标不需要显示市场指数和周期选择
      return this.indicator.category === 'block';
    },
    isIndividualTimingIndicator() {
      if (!this.indicator?.category) return false;
      // 个股择时（stock）的指标不需要显示市场指数和周期选择
      return this.indicator.category === 'stock';
    },
    isMarketTimingIndicator() {
      if (!this.indicator?.category) return false;
      // 只有大盘择时（trend）的指标才显示市场指数和周期选择
      return this.indicator.category === 'trend';
    }
  },
  methods: {
    onClose() {
      this.$emit('close');
    },
    toNumber(val) {
      const n = Number(val);
      return Number.isFinite(n) ? n : 0;
    },
    updateParamValue(idx, value) {
      console.log('🔄 updateParamValue 被调用', idx, value);
      if (this.indicator && this.indicator.parameters && this.indicator.parameters[idx]) {
        this.indicator.parameters[idx].value = value;
        console.log('📝 参数已更新', this.indicator.parameters[idx]);
        // 通知父组件更新指标数据
        this.$emit('update:indicator', this.indicator);
        console.log('📤 已发射 update:indicator 事件');
      }
    },
    updateKdjSettings() {
      // 更新KDJ指标参数
      if (this.indicator && this.indicator.parameters) {
        const kParam = this.indicator.parameters.find(p => p.name === 'K周期');
        const dParam = this.indicator.parameters.find(p => p.name === 'D周期');
        const jParam = this.indicator.parameters.find(p => p.name === 'J周期');
        
        if (kParam) kParam.value = this.kdjSettings.k.toString();
        if (dParam) dParam.value = this.kdjSettings.d.toString();
        if (jParam) jParam.value = this.kdjSettings.j.toString();
        
        // 添加或更新金叉死叉参数
        let goldenCrossParam = this.indicator.parameters.find(p => p.name === '金叉信号');
        let deathCrossParam = this.indicator.parameters.find(p => p.name === '死叉信号');
        
        if (!goldenCrossParam) {
          goldenCrossParam = { name: '金叉信号', value: 'true', description: '启用金叉信号', default: 'true' };
          this.indicator.parameters.push(goldenCrossParam);
        }
        if (!deathCrossParam) {
          deathCrossParam = { name: '死叉信号', value: 'true', description: '启用死叉信号', default: 'true' };
          this.indicator.parameters.push(deathCrossParam);
        }
        
        goldenCrossParam.value = this.kdjGoldenCrossChecked.toString();
        deathCrossParam.value = this.kdjDeathCrossChecked.toString();
        
        // 通知父组件更新指标数据
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateMacdSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let fastParam = this.indicator.parameters.find(p => p.name === '快线周期');
        let slowParam = this.indicator.parameters.find(p => p.name === '慢线周期');
        let signalParam = this.indicator.parameters.find(p => p.name === '信号线周期');
        let goldenCrossParam = this.indicator.parameters.find(p => p.name === '金叉信号');
        let deathCrossParam = this.indicator.parameters.find(p => p.name === '死叉信号');
        
        if (!fastParam) {
          fastParam = { name: '快线周期', value: '26', description: 'DIF快线周期', default: '26' };
          this.indicator.parameters.push(fastParam);
        }
        if (!slowParam) {
          slowParam = { name: '慢线周期', value: '12', description: 'DEA慢线周期', default: '12' };
          this.indicator.parameters.push(slowParam);
        }
        if (!signalParam) {
          signalParam = { name: '信号线周期', value: '9', description: 'MACD信号线周期', default: '9' };
          this.indicator.parameters.push(signalParam);
        }
        if (!goldenCrossParam) {
          goldenCrossParam = { name: '金叉信号', value: 'true', description: '启用金叉信号', default: 'true' };
          this.indicator.parameters.push(goldenCrossParam);
        }
        if (!deathCrossParam) {
          deathCrossParam = { name: '死叉信号', value: 'true', description: '启用死叉信号', default: 'true' };
          this.indicator.parameters.push(deathCrossParam);
        }
        
        fastParam.value = this.macdSettings.fast.toString();
        slowParam.value = this.macdSettings.slow.toString();
        signalParam.value = this.macdSettings.signal.toString();
        goldenCrossParam.value = this.macdGoldenCrossChecked.toString();
        deathCrossParam.value = this.macdDeathCrossChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateMaSettings() {
      // 更新MA指标参数
      if (this.indicator && this.indicator.parameters) {
        // 添加或更新金叉死叉参数
        let goldenCrossParam = this.indicator.parameters.find(p => p.name === '金叉信号');
        let deathCrossParam = this.indicator.parameters.find(p => p.name === '死叉信号');
        
        if (!goldenCrossParam) {
          goldenCrossParam = { name: '金叉信号', value: 'true', description: '启用金叉信号', default: 'true' };
          this.indicator.parameters.push(goldenCrossParam);
        }
        if (!deathCrossParam) {
          deathCrossParam = { name: '死叉信号', value: 'true', description: '启用死叉信号', default: 'true' };
          this.indicator.parameters.push(deathCrossParam);
        }
        
        goldenCrossParam.value = this.maGoldenCrossChecked.toString();
        deathCrossParam.value = this.maDeathCrossChecked.toString();
        
        // 通知父组件更新指标数据
        this.$emit('update:indicator', this.indicator);
      }
    },
    getMaPeriodValue() {
      // 获取MA周期值，优先从指标参数中获取
      if (this.indicator && this.indicator.parameters) {
        const periodParam = this.indicator.parameters.find(p => p.name === '周期');
        if (periodParam && periodParam.value) {
          return parseInt(periodParam.value);
        }
      }
      // 如果没有找到，返回默认值
      return 20;
    },
    updateMaPeriod(event) {
      // 更新MA周期参数
      const value = this.toNumber(event.target.value);
      if (this.indicator && this.indicator.parameters) {
        let periodParam = this.indicator.parameters.find(p => p.name === '周期');
        if (!periodParam) {
          periodParam = { name: '周期', value: '20', description: '计算移动平均的周期数', default: '20' };
          this.indicator.parameters.push(periodParam);
        }
        periodParam.value = value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    getSectorIndexLabel(value) {
      const sectorMap = {
        'transport': '交通运输',
        'leisure': '休闲服务',
        'media': '传媒',
        'utilities': '公用事业',
        'agriculture': '农林牧渔',
        'chemicals': '化工',
        'pharmaceuticals': '医药生物',
        'commerce': '商业贸易',
        'defense': '国防军工',
        'appliances': '家用电器',
        'building_materials': '建筑材料',
        'decoration': '建筑装饰',
        'real_estate': '房地产',
        'nonferrous_metals': '有色金属',
        'machinery': '机械设备',
        'automotive': '汽车',
        'electronics': '电子',
        'electrical_equipment': '电气设备',
        'textiles': '纺织服装',
        'comprehensive': '综合',
        'computer': '计算机',
        'light_industry': '轻工制造',
        'telecommunications': '通信',
        'mining': '采掘',
        'steel': '钢铁',
        'banking': '银行',
        'non_banking_finance': '非银金融',
        'food_beverage': '食品饮料'
      };
      return sectorMap[value] || '交通运输';
    },
    selectTimingSignal(signal) {
      this.timingSelectedSignal = signal;
    },
    resetMASettings() {
      this.maShortPeriod = 5;
      this.maLongPeriod = 20;
      this.maCompare = '大于';
      this.maCustomValue = 0;
      this.maCrossCompare = '大于';
      this.maCrossCustomValue = 0;
      this.maTrendCompare = '大于';
      this.maTrendCustomValue = 0;
      this.maDivergenceCompare = '大于';
      this.maDivergenceCustomValue = 0;
    },
    applyMASettings() {
      // 应用MA设置逻辑
      console.log('应用MA设置:', {
        signal: this.timingSelectedSignal,
        shortPeriod: this.maShortPeriod,
        longPeriod: this.maLongPeriod,
        compare: this.maCompare,
        customValue: this.maCustomValue
      });
    },
    updateRsiSettings() {
      // 更新RSI指标参数
      if (this.indicator && this.indicator.parameters) {
        const periodParam = this.indicator.parameters.find(p => p.name === 'RSI周期');
        if (periodParam) periodParam.value = this.rsiSettings.period.toString();
        
        // 添加或更新超买超卖参数
        let overboughtParam = this.indicator.parameters.find(p => p.name === '超买信号');
        let oversoldParam = this.indicator.parameters.find(p => p.name === '超卖信号');
        
        if (!overboughtParam) {
          overboughtParam = { name: '超买信号', value: 'true', description: '启用超买信号', default: 'true' };
          this.indicator.parameters.push(overboughtParam);
        }
        if (!oversoldParam) {
          oversoldParam = { name: '超卖信号', value: 'true', description: '启用超卖信号', default: 'true' };
          this.indicator.parameters.push(oversoldParam);
        }
        
        overboughtParam.value = this.rsiOverboughtChecked.toString();
        oversoldParam.value = this.rsiOversoldChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateBollSettings() {
      // 更新BOLL指标参数
      if (this.indicator && this.indicator.parameters) {
        const periodParam = this.indicator.parameters.find(p => p.name === '周期');
        const multiplierParam = this.indicator.parameters.find(p => p.name === '倍数');
        
        if (periodParam) periodParam.value = this.bollSettings.period.toString();
        if (multiplierParam) multiplierParam.value = this.bollSettings.multiplier.toString();
        
        // 添加或更新上下轨参数
        let upperParam = this.indicator.parameters.find(p => p.name === '上轨信号');
        let lowerParam = this.indicator.parameters.find(p => p.name === '下轨信号');
        
        if (!upperParam) {
          upperParam = { name: '上轨信号', value: 'true', description: '启用上轨信号', default: 'true' };
          this.indicator.parameters.push(upperParam);
        }
        if (!lowerParam) {
          lowerParam = { name: '下轨信号', value: 'true', description: '启用下轨信号', default: 'true' };
          this.indicator.parameters.push(lowerParam);
        }
        
        upperParam.value = this.bollUpperChecked.toString();
        lowerParam.value = this.bollLowerChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateCrSettings() {
      // 更新CR指标参数
      if (this.indicator && this.indicator.parameters) {
        const periodParam = this.indicator.parameters.find(p => p.name === 'CR周期');
        if (periodParam) periodParam.value = this.crSettings.period.toString();
        
        // 添加或更新多空参数
        let bullParam = this.indicator.parameters.find(p => p.name === '多头信号');
        let bearParam = this.indicator.parameters.find(p => p.name === '空头信号');
        
        if (!bullParam) {
          bullParam = { name: '多头信号', value: 'true', description: '启用多头信号', default: 'true' };
          this.indicator.parameters.push(bullParam);
        }
        if (!bearParam) {
          bearParam = { name: '空头信号', value: 'true', description: '启用空头信号', default: 'true' };
          this.indicator.parameters.push(bearParam);
        }
        
        bullParam.value = this.crBullChecked.toString();
        bearParam.value = this.crBearChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateAtrSettings() {
      // 更新ATR指标参数
      if (this.indicator && this.indicator.parameters) {
        const periodParam = this.indicator.parameters.find(p => p.name === 'ATR周期');
        if (periodParam) periodParam.value = this.atrSettings.period.toString();
        
        // 添加或更新波动参数
        let highVolParam = this.indicator.parameters.find(p => p.name === '高波动信号');
        let lowVolParam = this.indicator.parameters.find(p => p.name === '低波动信号');
        
        if (!highVolParam) {
          highVolParam = { name: '高波动信号', value: 'true', description: '启用高波动信号', default: 'true' };
          this.indicator.parameters.push(highVolParam);
        }
        if (!lowVolParam) {
          lowVolParam = { name: '低波动信号', value: 'true', description: '启用低波动信号', default: 'true' };
          this.indicator.parameters.push(lowVolParam);
        }
        
        highVolParam.value = this.atrHighVolChecked.toString();
        lowVolParam.value = this.atrLowVolChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateTrixSettings() {
      // 更新TRIX指标参数
      if (this.indicator && this.indicator.parameters) {
        const periodParam = this.indicator.parameters.find(p => p.name === 'TRIX周期');
        if (periodParam) periodParam.value = this.trixSettings.period.toString();
        
        // 添加或更新金叉死叉参数
        let goldenCrossParam = this.indicator.parameters.find(p => p.name === '金叉信号');
        let deathCrossParam = this.indicator.parameters.find(p => p.name === '死叉信号');
        
        if (!goldenCrossParam) {
          goldenCrossParam = { name: '金叉信号', value: 'true', description: '启用金叉信号', default: 'true' };
          this.indicator.parameters.push(goldenCrossParam);
        }
        if (!deathCrossParam) {
          deathCrossParam = { name: '死叉信号', value: 'true', description: '启用死叉信号', default: 'true' };
          this.indicator.parameters.push(deathCrossParam);
        }
        
        goldenCrossParam.value = this.trixGoldenCrossChecked.toString();
        deathCrossParam.value = this.trixDeathCrossChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateCciSettings() {
      // 更新CCI指标参数
      if (this.indicator && this.indicator.parameters) {
        const periodParam = this.indicator.parameters.find(p => p.name === 'CCI周期');
        if (periodParam) periodParam.value = this.cciSettings.period.toString();
        
        // 添加或更新超买超卖参数
        let overboughtParam = this.indicator.parameters.find(p => p.name === '超买信号');
        let oversoldParam = this.indicator.parameters.find(p => p.name === '超卖信号');
        
        if (!overboughtParam) {
          overboughtParam = { name: '超买信号', value: 'true', description: '启用超买信号', default: 'true' };
          this.indicator.parameters.push(overboughtParam);
        }
        if (!oversoldParam) {
          oversoldParam = { name: '超卖信号', value: 'true', description: '启用超卖信号', default: 'true' };
          this.indicator.parameters.push(oversoldParam);
        }
        
        overboughtParam.value = this.cciOverboughtChecked.toString();
        oversoldParam.value = this.cciOversoldChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateBbicSettings() {
      // 更新BBIC指标参数
      if (this.indicator && this.indicator.parameters) {
        const periodParam = this.indicator.parameters.find(p => p.name === 'BBIC周期');
        if (periodParam) periodParam.value = this.bbicSettings.period.toString();
        
        // 添加或更新扩张收缩参数
        let expansionParam = this.indicator.parameters.find(p => p.name === '扩张信号');
        let contractionParam = this.indicator.parameters.find(p => p.name === '收缩信号');
        
        if (!expansionParam) {
          expansionParam = { name: '扩张信号', value: 'true', description: '启用扩张信号', default: 'true' };
          this.indicator.parameters.push(expansionParam);
        }
        if (!contractionParam) {
          contractionParam = { name: '收缩信号', value: 'true', description: '启用收缩信号', default: 'true' };
          this.indicator.parameters.push(contractionParam);
        }
        
        expansionParam.value = this.bbicExpansionChecked.toString();
        contractionParam.value = this.bbicContractionChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateEmaSettings() {
      // 更新EMA指标参数
      if (this.indicator && this.indicator.parameters) {
        const periodParam = this.indicator.parameters.find(p => p.name === 'EMA周期');
        if (periodParam) periodParam.value = this.emaSettings.period.toString();
        
        // 添加或更新金叉死叉参数
        let goldenCrossParam = this.indicator.parameters.find(p => p.name === '金叉信号');
        let deathCrossParam = this.indicator.parameters.find(p => p.name === '死叉信号');
        
        if (!goldenCrossParam) {
          goldenCrossParam = { name: '金叉信号', value: 'true', description: '启用金叉信号', default: 'true' };
          this.indicator.parameters.push(goldenCrossParam);
        }
        if (!deathCrossParam) {
          deathCrossParam = { name: '死叉信号', value: 'true', description: '启用死叉信号', default: 'true' };
          this.indicator.parameters.push(deathCrossParam);
        }
        
        goldenCrossParam.value = this.emaGoldenCrossChecked.toString();
        deathCrossParam.value = this.emaDeathCrossChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateFourPeriodSettings() {
      // 更新四周期多头排列参数
      if (this.indicator && this.indicator.parameters) {
        const shortParam = this.indicator.parameters.find(p => p.name === '短期周期');
        const mediumParam = this.indicator.parameters.find(p => p.name === '中期周期');
        const longParam = this.indicator.parameters.find(p => p.name === '长期周期');
        
        if (shortParam) shortParam.value = this.fourPeriodSettings.short.toString();
        if (mediumParam) mediumParam.value = this.fourPeriodSettings.medium.toString();
        if (longParam) longParam.value = this.fourPeriodSettings.long.toString();
        
        // 添加或更新多空排列参数
        let bullParam = this.indicator.parameters.find(p => p.name === '多头排列信号');
        let bearParam = this.indicator.parameters.find(p => p.name === '空头排列信号');
        
        if (!bullParam) {
          bullParam = { name: '多头排列信号', value: 'true', description: '启用多头排列信号', default: 'true' };
          this.indicator.parameters.push(bullParam);
        }
        if (!bearParam) {
          bearParam = { name: '空头排列信号', value: 'true', description: '启用空头排列信号', default: 'true' };
          this.indicator.parameters.push(bearParam);
        }
        
        bullParam.value = this.fourPeriodBullChecked.toString();
        bearParam.value = this.fourPeriodBearChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateOpenPriceSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let indicatorParam = this.indicator.parameters.find(p => p.name === '比较指标');
        
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!indicatorParam) {
          indicatorParam = { name: '比较指标', value: '', description: '比较的指标', default: '' };
          this.indicator.parameters.push(indicatorParam);
        }
        
        compareParam.value = this.openPriceSettings.compare;
        indicatorParam.value = this.openPriceSettings.indicator;
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateClosePriceSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let indicatorParam = this.indicator.parameters.find(p => p.name === '比较指标');
        
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!indicatorParam) {
          indicatorParam = { name: '比较指标', value: '', description: '比较的指标', default: '' };
          this.indicator.parameters.push(indicatorParam);
        }
        
        compareParam.value = this.closePriceSettings.compare;
        indicatorParam.value = this.closePriceSettings.indicator;
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateHighPriceSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let indicatorParam = this.indicator.parameters.find(p => p.name === '比较指标');
        
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!indicatorParam) {
          indicatorParam = { name: '比较指标', value: '', description: '比较的指标', default: '' };
          this.indicator.parameters.push(indicatorParam);
        }
        
        compareParam.value = this.highPriceSettings.compare;
        indicatorParam.value = this.highPriceSettings.indicator;
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateLowPriceSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let indicatorParam = this.indicator.parameters.find(p => p.name === '比较指标');
        
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!indicatorParam) {
          indicatorParam = { name: '比较指标', value: '', description: '比较的指标', default: '' };
          this.indicator.parameters.push(indicatorParam);
        }
        
        compareParam.value = this.lowPriceSettings.compare;
        indicatorParam.value = this.lowPriceSettings.indicator;
        this.$emit('update:indicator', this.indicator);
      }
    },
    updatePrevClosePriceSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let indicatorParam = this.indicator.parameters.find(p => p.name === '比较指标');
        
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!indicatorParam) {
          indicatorParam = { name: '比较指标', value: '', description: '比较的指标', default: '' };
          this.indicator.parameters.push(indicatorParam);
        }
        
        compareParam.value = this.prevClosePriceSettings.compare;
        indicatorParam.value = this.prevClosePriceSettings.indicator;
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateAvgPriceSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let indicatorParam = this.indicator.parameters.find(p => p.name === '比较指标');
        
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!indicatorParam) {
          indicatorParam = { name: '比较指标', value: '', description: '比较的指标', default: '' };
          this.indicator.parameters.push(indicatorParam);
        }
        
        compareParam.value = this.avgPriceSettings.compare;
        indicatorParam.value = this.avgPriceSettings.indicator;
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateChangeRateSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let typeParam = this.indicator.parameters.find(p => p.name === '信号类型');
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === '百分比值');
        let daysParam = this.indicator.parameters.find(p => p.name === '区间天数');
        
        if (!typeParam) {
          typeParam = { name: '信号类型', value: 'single', description: '涨幅信号类型', default: 'single' };
          this.indicator.parameters.push(typeParam);
        }
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: '百分比值', value: '0', description: '涨幅百分比', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        if (!daysParam) {
          daysParam = { name: '区间天数', value: '5', description: '区间涨幅天数', default: '5' };
          this.indicator.parameters.push(daysParam);
        }
        
        typeParam.value = this.changeRateSettings.type;
        compareParam.value = this.changeRateSettings.compare;
        valueParam.value = this.changeRateSettings.value.toString();
        if (this.changeRateSettings.type === 'range') daysParam.value = this.changeRateSettings.days.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateVolumeRatioSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === '量比值');
        
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: '量比值', value: '1.0', description: '量比值', default: '1.0' };
          this.indicator.parameters.push(valueParam);
        }
        
        compareParam.value = this.volumeRatioSettings.compare;
        valueParam.value = this.volumeRatioSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateTurnoverSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === '成交额');
        
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: '成交额', value: '0', description: '成交额(万元)', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        
        compareParam.value = this.turnoverSettings.compare;
        valueParam.value = this.turnoverSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateTurnoverRateSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === '换手率');
        
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: '换手率', value: '0', description: '换手率(%)', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        
        compareParam.value = this.turnoverRateSettings.compare;
        valueParam.value = this.turnoverRateSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateMarketValueSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === '市值');
        
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: '市值', value: '0', description: '市值(亿元)', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        
        compareParam.value = this.marketValueSettings.compare;
        valueParam.value = this.marketValueSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateVolumeSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === '成交量');
        
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: '成交量', value: '0', description: '成交量(万股)', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        
        compareParam.value = this.volumeSettings.compare;
        valueParam.value = this.volumeSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateNetInflowSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === '资金净流入');
        
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: '资金净流入', value: '0', description: '资金净流入(万元)', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        
        compareParam.value = this.netInflowSettings.compare;
        valueParam.value = this.netInflowSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateFilterNewListedSettings() {
      // 更新过滤新上市参数
      if (this.indicator && this.indicator.parameters) {
        const daysParam = this.indicator.parameters.find(p => p.name === '上市天数限制');
        const filterParam = this.indicator.parameters.find(p => p.name === '过滤新上市');
        
        if (daysParam) daysParam.value = this.filterNewListedSettings.days.toString();
        if (filterParam) filterParam.value = this.filterNewListedChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateFilterBseSettings() {
      // 更新过滤北交所参数
      if (this.indicator && this.indicator.parameters) {
        const filterBseParam = this.indicator.parameters.find(p => p.name === '过滤北交所');
        if (filterBseParam) filterBseParam.value = this.filterBseChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateFilterMainBoardSettings() {
      // 更新过滤沪深主板参数
      if (this.indicator && this.indicator.parameters) {
        const filterMainBoardParam = this.indicator.parameters.find(p => p.name === '过滤沪深主板');
        if (filterMainBoardParam) filterMainBoardParam.value = this.filterMainBoardChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateFilterStSettings() {
      // 更新过滤ST参数
      if (this.indicator && this.indicator.parameters) {
        const filterStParam = this.indicator.parameters.find(p => p.name === '过滤ST');
        if (filterStParam) filterStParam.value = this.filterStChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateFilterAstSettings() {
      // 更新过滤*ST参数
      if (this.indicator && this.indicator.parameters) {
        const filterAstParam = this.indicator.parameters.find(p => p.name === '过滤*ST');
        if (filterAstParam) filterAstParam.value = this.filterAstChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateFilterSuspendedSettings() {
      // 更新过滤停牌参数
      if (this.indicator && this.indicator.parameters) {
        const filterSuspendedParam = this.indicator.parameters.find(p => p.name === '过滤停牌');
        if (filterSuspendedParam) filterSuspendedParam.value = this.filterSuspendedChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateFilterStarSettings() {
      // 更新过滤科创板参数
      if (this.indicator && this.indicator.parameters) {
        const filterStarParam = this.indicator.parameters.find(p => p.name === '过滤科创板');
        if (filterStarParam) filterStarParam.value = this.filterStarChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateFilterChinextSettings() {
      // 更新过滤创业板参数
      if (this.indicator && this.indicator.parameters) {
        const filterChinextParam = this.indicator.parameters.find(p => p.name === '过滤创业板');
        if (filterChinextParam) filterChinextParam.value = this.filterChinextChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateFilterDelistedSettings() {
      // 更新过滤退市参数
      if (this.indicator && this.indicator.parameters) {
        const filterDelistedParam = this.indicator.parameters.find(p => p.name === '过滤退市');
        if (filterDelistedParam) filterDelistedParam.value = this.filterDelistedChecked.toString();
        
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateRoaSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === 'ROA');
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: 'ROA', value: '0', description: '总资产收益率(%)', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        compareParam.value = this.roaSettings.compare;
        valueParam.value = this.roaSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateRoeSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === 'ROE');
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: 'ROE', value: '0', description: '净资产收益率(%)', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        compareParam.value = this.roeSettings.compare;
        valueParam.value = this.roeSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateGrossMarginSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === '毛利率');
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: '毛利率', value: '0', description: '毛利率(%)', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        compareParam.value = this.grossMarginSettings.compare;
        valueParam.value = this.grossMarginSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateNetMarginSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === '净利率');
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: '净利率', value: '0', description: '净利率(%)', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        compareParam.value = this.netMarginSettings.compare;
        valueParam.value = this.netMarginSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateRevenueGrowthSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === '营收增长率');
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: '营收增长率', value: '0', description: '营业收入同比增长率(%)', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        compareParam.value = this.revenueGrowthSettings.compare;
        valueParam.value = this.revenueGrowthSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateProfitGrowthSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === '净利润增长率');
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: '净利润增长率', value: '0', description: '净利润同比增长率(%)', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        compareParam.value = this.profitGrowthSettings.compare;
        valueParam.value = this.profitGrowthSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateDynamicPeSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === '动态市盈率');
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: '动态市盈率', value: '0', description: '动态市盈率(倍)', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        compareParam.value = this.dynamicPeSettings.compare;
        valueParam.value = this.dynamicPeSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updatePbRatioSettings() {
      if (this.indicator && this.indicator.parameters) {
        const compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        const valueParam = this.indicator.parameters.find(p => p.name === '市净率');
        if (compareParam) compareParam.value = this.pbRatioSettings.compare;
        if (valueParam) valueParam.value = this.pbRatioSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updatePsRatioSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === '市销率');
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: '市销率', value: '0', description: '市销率(倍)', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        compareParam.value = this.psRatioSettings.compare;
        valueParam.value = this.psRatioSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    // 新增：公告类指标更新方法
    updateShareholderReductionSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let param = this.indicator.parameters.find(p => p.name === '股东减持');
        if (!param) {
          param = { name: '股东减持', value: 'false', description: '启用股东减持监控', default: 'false' };
          this.indicator.parameters.push(param);
        }
        param.value = this.shareholderReductionChecked.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateShareholderIncreaseSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let param = this.indicator.parameters.find(p => p.name === '股东增持');
        if (!param) {
          param = { name: '股东增持', value: 'false', description: '启用股东增持监控', default: 'false' };
          this.indicator.parameters.push(param);
        }
        param.value = this.shareholderIncreaseChecked.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateShareholderDividendSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let param = this.indicator.parameters.find(p => p.name === '股东分红');
        if (!param) {
          param = { name: '股东分红', value: 'false', description: '启用股东分红监控', default: 'false' };
          this.indicator.parameters.push(param);
        }
        param.value = this.shareholderDividendChecked.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updateViolationInquirySettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let param = this.indicator.parameters.find(p => p.name === '违规问询函');
        if (!param) {
          param = { name: '违规问询函', value: 'false', description: '启用违规问询函监控', default: 'false' };
          this.indicator.parameters.push(param);
        }
        param.value = this.violationInquiryChecked.toString();
        this.$emit('update:indicator', this.indicator);
      }
    },
    updatePerformanceForecastSettings() {
      if (this.indicator) {
        if (!this.indicator.parameters) this.indicator.parameters = [];
        let typeParam = this.indicator.parameters.find(p => p.name === '指标类型');
        let compareParam = this.indicator.parameters.find(p => p.name === '比较符');
        let valueParam = this.indicator.parameters.find(p => p.name === '数值');
        
        if (!typeParam) {
          typeParam = { name: '指标类型', value: 'profit_yoy', description: '业绩预告指标类型', default: 'profit_yoy' };
          this.indicator.parameters.push(typeParam);
        }
        if (!compareParam) {
          compareParam = { name: '比较符', value: '大于', description: '比较方式', default: '大于' };
          this.indicator.parameters.push(compareParam);
        }
        if (!valueParam) {
          valueParam = { name: '数值', value: '0', description: '业绩预告数值', default: '0' };
          this.indicator.parameters.push(valueParam);
        }
        
        typeParam.value = this.performanceForecastSettings.type;
        compareParam.value = this.performanceForecastSettings.compare;
        valueParam.value = this.performanceForecastSettings.value.toString();
        this.$emit('update:indicator', this.indicator);
      }
    }
  }
};
</script>

<style scoped>
/* 模态框基础样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease-out;
  position: relative;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background-color: #f8f9fa;
}

.modal-body {
  padding: 20px 24px;
}

/* 设置组样式 */
.setting-group {
  margin-bottom: 20px;
}

.setting-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #495057;
  font-size: 14px;
}

.setting-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  transition: border-color 0.2s;
}

.setting-input:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

/* 周期选择按钮 */
.period-buttons {
  display: flex;
  gap: 8px;
}

.period-btn {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #ced4da;
  background: white;
  color: #495057;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.period-btn.active {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

.period-btn:hover:not(.active) {
  border-color: #409eff;
  color: #409eff;
}

/* MA指标区域 */
.ma-section {
  margin-top: 20px;
}

.ma-header {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.ma-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.ma-description {
  font-size: 13px;
  opacity: 0.9;
}

/* MA参数表格 */
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

/* MA参数输入框 */
.ma-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.ma-input-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 8px 0;
}

.ma-input-row:last-child {
  margin-bottom: 0;
}

.ma-input-row label {
  font-size: 13px;
  font-weight: 500;
  color: #495057;
  min-width: 120px;
  margin-right: 12px;
}

.input-with-unit {
  display: flex;
  align-items: center;
  flex: 1;
  max-width: 200px;
}

.ma-input {
  flex: 1;
  height: 36px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 13px;
  transition: border-color 0.2s;
  background: white;
}

.ma-input:focus {
  border-color: #28a745;
  outline: none;
  box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.2);
}

.unit {
  margin-left: 8px;
  font-size: 12px;
  color: #6c757d;
  font-weight: 500;
}

/* 复选框样式 */
.checkbox-wrapper {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.checkbox-wrapper input[type="checkbox"] {
  margin-right: 8px;
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.checkbox-label {
  font-size: 13px;
  color: #495057;
  cursor: pointer;
}

/* MA信号设置样式 */
.ma-signal-settings {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* MA指标说明框样式 */
.ma-description-box {
  background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
  border: 1px solid #bbdefb;
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.description-title {
  font-size: 14px;
  font-weight: 600;
  color: #1976d2;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

.description-title::before {
  content: "ℹ️";
  margin-right: 8px;
  font-size: 16px;
}

.description-content {
  font-size: 13px;
  color: #424242;
  line-height: 1.5;
}

.description-content p {
  margin: 0 0 8px 0;
}

.description-content ul {
  margin: 8px 0;
  padding-left: 20px;
}

.description-content li {
  margin-bottom: 4px;
}

.description-content strong {
  color: #1976d2;
  font-weight: 600;
}

/* 板块择时MA指标样式优化 */
.setting-group {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.setting-label {
  font-size: 14px;
  font-weight: 600;
  color: #495057;
  margin-bottom: 8px;
}

/* 板块指数选择样式 */
.sector-index-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.sector-index-display:hover {
  border-color: #409eff;
}

.sector-index-value {
  font-size: 14px;
  color: #495057;
  font-weight: 500;
}

.sector-dropdown-icon {
  color: #6c757d;
  font-size: 12px;
  transition: transform 0.2s;
}

.sector-dropdown-icon.expanded {
  transform: rotate(180deg);
}

.sector-search-hint {
  font-size: 12px;
  color: #6c757d;
  margin-bottom: 6px;
  font-weight: 500;
}

.sector-search-input {
  position: relative;
}

.sector-search-field {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.sector-search-field:focus {
  border-color: #409eff;
}

.search-dropdown-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #6c757d;
  font-size: 12px;
}

/* 周期选择按钮样式 */
.period-button-group {
  display: flex;
  gap: 8px;
}

.period-button {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: white;
  color: #495057;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
}

.period-button:hover {
  border-color: #409eff;
  background: #f0f8ff;
}

.period-button.active {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

/* MA参数设置标题块样式 */
.ma-settings-header {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  text-align: center;
}

.ma-settings-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.ma-settings-description {
  font-size: 14px;
  opacity: 0.9;
  line-height: 1.4;
}

/* KDJ指标区域 */
.kdj-section {
  margin-top: 20px;
}

.kdj-header {
  background: linear-gradient(135deg, #fd7e14 0%, #ffc107 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
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

/* KDJ参数表格 */
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

/* KDJ参数输入框 */
.kdj-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.kdj-param-inputs .ma-input {
  border-color: #fd7e14;
}

.kdj-param-inputs .ma-input:focus {
  border-color: #fd7e14;
  box-shadow: 0 0 0 2px rgba(253, 126, 20, 0.2);
}

/* KDJ信号设置样式 */
.kdj-signal-settings {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* MACD指标区域 */
.macd-section {
  margin-top: 20px;
}

.macd-header {
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.macd-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.macd-description {
  font-size: 13px;
  opacity: 0.9;
}

/* MACD参数表格 */
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
  color: #8b5cf6;
}

.macd-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.macd-param-table .param-table td:last-child {
  font-weight: 600;
  color: #10b981;
}

/* MACD参数输入框 */
.macd-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.macd-param-inputs .ma-input {
  border-color: #8b5cf6;
}

.macd-param-inputs .ma-input:focus {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
}

/* MACD信号设置 */
.macd-signal-settings {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* RSI指标区域 */
.rsi-section {
  margin-top: 20px;
}

.rsi-header {
  background: linear-gradient(135deg, #e83e8c 0%, #fd7e14 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
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

/* RSI参数表格 */
.rsi-param-table {
  margin-bottom: 16px;
}

.rsi-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.rsi-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.rsi-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.rsi-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.rsi-param-table .param-table td:first-child {
  font-weight: 600;
  color: #e83e8c;
}

.rsi-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.rsi-param-table .param-table td:last-child {
  font-weight: 600;
  color: #e83e8c;
}

/* RSI参数输入框 */
.rsi-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.rsi-param-inputs .ma-input {
  border-color: #e83e8c;
}

.rsi-param-inputs .ma-input:focus {
  border-color: #e83e8c;
  box-shadow: 0 0 0 2px rgba(232, 62, 140, 0.2);
}

/* RSI信号设置样式 */
.rsi-signal-settings {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* BOLL指标区域 */
.boll-section {
  margin-top: 20px;
}

.boll-header {
  background: linear-gradient(135deg, #6f42c1 0%, #e83e8c 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
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

/* BOLL参数表格 */
.boll-param-table {
  margin-bottom: 16px;
}

.boll-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.boll-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.boll-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.boll-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.boll-param-table .param-table td:last-child {
  font-weight: 600;
  color: #6f42c1;
}

/* BOLL参数输入框 */
.boll-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.boll-param-inputs .ma-input {
  border-color: #6f42c1;
}

.boll-param-inputs .ma-input:focus {
  border-color: #6f42c1;
  box-shadow: 0 0 0 2px rgba(111, 66, 193, 0.2);
}

/* BOLL信号设置样式 */
.boll-signal-settings {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* CR指标区域 */
.cr-section {
  margin-top: 20px;
}

.cr-header {
  background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
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

/* CR参数表格 */
.cr-param-table {
  margin-bottom: 16px;
}

.cr-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.cr-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.cr-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.cr-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.cr-param-table .param-table td:first-child {
  font-weight: 600;
  color: #20c997;
}

.cr-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.cr-param-table .param-table td:last-child {
  font-weight: 600;
  color: #20c997;
}

/* CR参数输入框 */
.cr-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.cr-param-inputs .ma-input {
  border-color: #20c997;
}

.cr-param-inputs .ma-input:focus {
  border-color: #20c997;
  box-shadow: 0 0 0 2px rgba(32, 201, 151, 0.2);
}

/* CR信号设置样式 */
.cr-signal-settings {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* ATR指标区域 */
.atr-section {
  margin-top: 20px;
}

.atr-header {
  background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.atr-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.atr-description {
  font-size: 13px;
  opacity: 0.9;
}

/* ATR参数表格 */
.atr-param-table {
  margin-bottom: 16px;
}

.atr-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.atr-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.atr-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.atr-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.atr-param-table .param-table td:first-child {
  font-weight: 600;
  color: #dc3545;
}

.atr-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.atr-param-table .param-table td:last-child {
  font-weight: 600;
  color: #dc3545;
}

/* ATR参数输入框 */
.atr-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.atr-param-inputs .ma-input {
  border-color: #dc3545;
}

.atr-param-inputs .ma-input:focus {
  border-color: #dc3545;
  box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.2);
}

/* ATR信号设置样式 */
.atr-signal-settings {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* TRIX指标区域 */
.trix-section {
  margin-top: 20px;
}

.trix-header {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
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

/* TRIX参数表格 */
.trix-param-table {
  margin-bottom: 16px;
}

.trix-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.trix-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.trix-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.trix-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.trix-param-table .param-table td:first-child {
  font-weight: 600;
  color: #28a745;
}

.trix-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.trix-param-table .param-table td:last-child {
  font-weight: 600;
  color: #28a745;
}

/* TRIX参数输入框 */
.trix-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.trix-param-inputs .ma-input {
  border-color: #28a745;
}

.trix-param-inputs .ma-input:focus {
  border-color: #28a745;
  box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.2);
}

/* TRIX信号设置样式 */
.trix-signal-settings {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* CCI指标区域 */
.cci-section {
  margin-top: 20px;
}

.cci-header {
  background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.cci-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.cci-description {
  font-size: 13px;
  opacity: 0.9;
}

/* CCI参数表格 */
.cci-param-table {
  margin-bottom: 16px;
}

.cci-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.cci-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.cci-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.cci-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.cci-param-table .param-table td:first-child {
  font-weight: 600;
  color: #ffc107;
}

.cci-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.cci-param-table .param-table td:last-child {
  font-weight: 600;
  color: #ffc107;
}

/* CCI参数输入框 */
.cci-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.cci-param-inputs .ma-input {
  border-color: #ffc107;
}

.cci-param-inputs .ma-input:focus {
  border-color: #ffc107;
  box-shadow: 0 0 0 2px rgba(255, 193, 7, 0.2);
}

/* CCI信号设置样式 */
.cci-signal-settings {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* BBIC指标区域 */
.bbic-section {
  margin-top: 20px;
}

.bbic-header {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.bbic-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.bbic-description {
  font-size: 13px;
  opacity: 0.9;
}

/* BBIC参数表格 */
.bbic-param-table {
  margin-bottom: 16px;
}

.bbic-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.bbic-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.bbic-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.bbic-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.bbic-param-table .param-table td:first-child {
  font-weight: 600;
  color: #6c757d;
}

.bbic-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.bbic-param-table .param-table td:last-child {
  font-weight: 600;
  color: #6c757d;
}

/* BBIC参数输入框 */
.bbic-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.bbic-param-inputs .ma-input {
  border-color: #6c757d;
}

.bbic-param-inputs .ma-input:focus {
  border-color: #6c757d;
  box-shadow: 0 0 0 2px rgba(108, 117, 125, 0.2);
}

/* BBIC信号设置样式 */
.bbic-signal-settings {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* EMA指标区域 */
.ema-section {
  margin-top: 20px;
}

.ema-header {
  background: linear-gradient(135deg, #007bff 0%, #6610f2 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.ema-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.ema-description {
  font-size: 13px;
  opacity: 0.9;
}

/* EMA参数表格 */
.ema-param-table {
  margin-bottom: 16px;
}

.ema-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.ema-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.ema-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.ema-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.ema-param-table .param-table td:first-child {
  font-weight: 600;
  color: #007bff;
}

.ema-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.ema-param-table .param-table td:last-child {
  font-weight: 600;
  color: #007bff;
}

/* EMA参数输入框 */
.ema-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.ema-param-inputs .ma-input {
  border-color: #007bff;
}

.ema-param-inputs .ma-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.2);
}

/* EMA信号设置样式 */
.ema-signal-settings {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 四周期多头排列指标区域 */
.four-period-section {
  margin-top: 20px;
}

.four-period-header {
  background: linear-gradient(135deg, #17a2b8 0%, #20c997 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.four-period-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.four-period-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 四周期参数表格 */
.four-period-param-table {
  margin-bottom: 16px;
}

.four-period-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.four-period-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.four-period-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.four-period-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.four-period-param-table .param-table td:first-child {
  font-weight: 600;
  color: #17a2b8;
}

.four-period-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.four-period-param-table .param-table td:last-child {
  font-weight: 600;
  color: #17a2b8;
}

/* 四周期参数输入框 */
.four-period-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.four-period-param-inputs .ma-input {
  border-color: #17a2b8;
}

.four-period-param-inputs .ma-input:focus {
  border-color: #17a2b8;
  box-shadow: 0 0 0 2px rgba(23, 162, 184, 0.2);
}

/* 四周期信号设置样式 */
.four-period-signal-settings {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 模态框操作按钮 */
.modal-actions {
  padding: 20px 24px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid #e9ecef;
  background: #f8f9fa;
  border-radius: 0 0 12px 12px;
}

.save-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
}

.save-btn:hover {
  background: linear-gradient(135deg, #218838 0%, #1ea085 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4);
}

.save-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
}

.reset-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(108, 117, 125, 0.3);
}

.reset-btn:hover {
  background: linear-gradient(135deg, #5a6268 0%, #343a40 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(108, 117, 125, 0.4);
}

.reset-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(108, 117, 125, 0.3);
}

/* 开盘价参数设置 */
.open-price-section {
  margin-top: 20px;
}

.open-price-header {
  background: linear-gradient(135deg, #f97316 0%, #eab308 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(249, 115, 22, 0.2);
}

.open-price-orange-title {
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}

.open-price-description {
  background: #f8f9fa;
  color: #374151;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
  text-align: center;
  border-left: 4px solid #f97316;
}

.open-price-comparison-settings {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 16px;
}

.open-price-label {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  color: #ffffff;
  padding: 8px 16px;
  border-radius: 6px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
  transition: all 0.2s ease;
}

.open-price-label:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

/* 收盘价参数设置 */
.close-price-section {
  margin-top: 20px;
}

.close-price-header {
  background: linear-gradient(135deg, #f97316 0%, #eab308 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(249, 115, 22, 0.2);
}

.close-price-orange-title {
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}

.close-price-description {
  background: #f8f9fa;
  color: #374151;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
  text-align: center;
  border-left: 4px solid #f97316;
}

.close-price-comparison-settings {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 16px;
}

.close-price-label {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  color: #ffffff;
  padding: 8px 16px;
  border-radius: 6px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
  transition: all 0.2s ease;
}

.close-price-label:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

/* 最高价参数设置 */
.high-price-section {
  margin-top: 20px;
}

.high-price-header {
  background: linear-gradient(135deg, #f97316 0%, #eab308 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(249, 115, 22, 0.2);
}

.high-price-orange-title {
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}

.high-price-description {
  background: #f8f9fa;
  color: #374151;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
  text-align: center;
  border-left: 4px solid #f97316;
}

.high-price-comparison-settings {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 16px;
}

.high-price-label {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  color: #ffffff;
  padding: 8px 16px;
  border-radius: 6px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
  transition: all 0.2s ease;
}

.high-price-label:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

/* 最低价样式 */
.low-price-orange-header {
  background: linear-gradient(135deg, #f97316 0%, #eab308 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(249, 115, 22, 0.2);
}

.low-price-orange-title {
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}

.low-price-description {
  background: #f8f9fa;
  color: #374151;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
  text-align: center;
  border-left: 4px solid #f97316;
}

.low-price-comparison-settings {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 16px;
}

.low-price-label {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  color: #ffffff;
  padding: 8px 16px;
  border-radius: 6px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
  transition: all 0.2s ease;
}

.low-price-label:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3);
}

.turnover-rate-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.turnover-rate-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 换手率参数表格 */
.turnover-rate-param-table {
  margin-bottom: 16px;
}

.turnover-rate-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.turnover-rate-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.turnover-rate-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.turnover-rate-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.turnover-rate-param-table .param-table td:first-child {
  font-weight: 600;
  color: #20c997;
}

.turnover-rate-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.turnover-rate-param-table .param-table td:last-child {
  font-weight: 600;
  color: #20c997;
}

/* 换手率参数输入框 */
.turnover-rate-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.turnover-rate-param-inputs .ma-input {
  border-color: #20c997;
}

.turnover-rate-param-inputs .ma-input:focus {
  border-color: #20c997;
  box-shadow: 0 0 0 2px rgba(32, 201, 151, 0.2);
}

/* 市值参数设置 */
.market-value-section {
  margin-top: 20px;
}

.market-value-header {
  background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.market-value-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.market-value-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 市值参数表格 */
.market-value-param-table {
  margin-bottom: 16px;
}

.market-value-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.market-value-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.market-value-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.market-value-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.market-value-param-table .param-table td:first-child {
  font-weight: 600;
  color: #20c997;
}

.market-value-param-table .param-table td:last-child {
  font-weight: 600;
  color: #20c997;
}

/* 市值参数输入框 */
.market-value-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.market-value-param-inputs .ma-input {
  border-color: #20c997;
}

.market-value-param-inputs .ma-input:focus {
  border-color: #20c997;
  box-shadow: 0 0 0 2px rgba(32, 201, 151, 0.2);
}

/* 成交量参数设置 */
.volume-section {
  margin-top: 20px;
}

.volume-header {
  background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.volume-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.volume-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 成交量参数表格 */
.volume-param-table {
  margin-bottom: 16px;
}

.volume-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.volume-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.volume-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.volume-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.volume-param-table .param-table td:first-child {
  font-weight: 600;
  color: #20c997;
}

.volume-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.volume-param-table .param-table td:last-child {
  font-weight: 600;
  color: #20c997;
}

/* 成交量参数输入框 */
.volume-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.volume-param-inputs .ma-input {
  border-color: #20c997;
}

.volume-param-inputs .ma-input:focus {
  border-color: #20c997;
  box-shadow: 0 0 0 2px rgba(32, 201, 151, 0.2);
}

/* 资金净流入参数设置 */
.net-inflow-section {
  margin-top: 20px;
}

.net-inflow-header {
  background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.net-inflow-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.net-inflow-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 资金净流入参数表格 */
.net-inflow-param-table {
  margin-bottom: 16px;
}

.net-inflow-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.net-inflow-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.net-inflow-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.net-inflow-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.net-inflow-param-table .param-table td:first-child {
  font-weight: 600;
  color: #20c997;
}

.net-inflow-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.net-inflow-param-table .param-table td:last-child {
  font-weight: 600;
  color: #20c997;
}

/* 资金净流入参数输入框 */
.net-inflow-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.net-inflow-param-inputs .ma-input {
  border-color: #20c997;
}

.net-inflow-param-inputs .ma-input:focus {
  border-color: #20c997;
  box-shadow: 0 0 0 2px rgba(32, 201, 151, 0.2);
}

/* 过滤新上市参数设置 */
.filter-new-listed-section {
  margin-top: 20px;
}

.filter-new-listed-header {
  background: linear-gradient(135deg, #17a2b8 0%, #20c997 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.filter-new-listed-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.filter-new-listed-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 过滤新上市参数表格 */
.filter-new-listed-param-table {
  margin-bottom: 16px;
}

.filter-new-listed-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-new-listed-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.filter-new-listed-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.filter-new-listed-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.filter-new-listed-param-table .param-table td:first-child {
  font-weight: 600;
  color: #17a2b8;
}

.filter-new-listed-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.filter-new-listed-param-table .param-table td:last-child {
  font-weight: 600;
  color: #17a2b8;
}

/* 过滤新上市参数输入框 */
.filter-new-listed-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-new-listed-param-inputs .ma-input {
  border-color: #17a2b8;
}

.filter-new-listed-param-inputs .ma-input:focus {
  border-color: #17a2b8;
  box-shadow: 0 0 0 2px rgba(23, 162, 184, 0.2);
}

/* 过滤北交所参数设置 */
.filter-bse-section {
  margin-top: 20px;
}

.filter-bse-header {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.filter-bse-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.filter-bse-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 过滤北交所参数表格 */
.filter-bse-param-table {
  margin-bottom: 16px;
}

.filter-bse-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-bse-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.filter-bse-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.filter-bse-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.filter-bse-param-table .param-table td:first-child {
  font-weight: 600;
  color: #6c757d;
}

.filter-bse-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.filter-bse-param-table .param-table td:last-child {
  font-weight: 600;
  color: #6c757d;
}

/* 过滤北交所参数设置 */
.filter-bse-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-bse-param-inputs .ma-input {
  border-color: #6c757d;
}

.filter-bse-param-inputs .ma-input:focus {
  border-color: #6c757d;
  box-shadow: 0 0 0 2px rgba(108, 117, 125, 0.2);
}

/* 过滤沪深主板参数设置 */
.filter-main-board-section {
  margin-top: 20px;
}

.filter-main-board-header {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.filter-main-board-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.filter-main-board-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 过滤沪深主板参数表格 */
.filter-main-board-param-table {
  margin-bottom: 16px;
}

.filter-main-board-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-main-board-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.filter-main-board-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.filter-main-board-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.filter-main-board-param-table .param-table td:first-child {
  font-weight: 600;
  color: #6c757d;
}

.filter-main-board-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.filter-main-board-param-table .param-table td:last-child {
  font-weight: 600;
  color: #6c757d;
}

/* 过滤沪深主板参数设置 */
.filter-main-board-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-main-board-param-inputs .ma-input {
  border-color: #6c757d;
}

.filter-main-board-param-inputs .ma-input:focus {
  border-color: #6c757d;
  box-shadow: 0 0 0 2px rgba(108, 117, 125, 0.2);
}

/* 过滤ST参数设置 */
.filter-st-section {
  margin-top: 20px;
}

.filter-st-header {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.filter-st-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.filter-st-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 过滤ST参数表格 */
.filter-st-param-table {
  margin-bottom: 16px;
}

.filter-st-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-st-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.filter-st-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.filter-st-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.filter-st-param-table .param-table td:first-child {
  font-weight: 600;
  color: #6c757d;
}

.filter-st-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.filter-st-param-table .param-table td:last-child {
  font-weight: 600;
  color: #6c757d;
}

/* 过滤ST参数设置 */
.filter-st-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-st-param-inputs .ma-input {
  border-color: #6c757d;
}

.filter-st-param-inputs .ma-input:focus {
  border-color: #6c757d;
  box-shadow: 0 0 0 2px rgba(108, 117, 125, 0.2);
}

/* 过滤*ST参数设置 */
.filter-ast-section {
  margin-top: 20px;
}

.filter-ast-header {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.filter-ast-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.filter-ast-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 过滤*ST参数表格 */
.filter-ast-param-table {
  margin-bottom: 16px;
}

.filter-ast-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-ast-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.filter-ast-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.filter-ast-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.filter-ast-param-table .param-table td:first-child {
  font-weight: 600;
  color: #6c757d;
}

.filter-ast-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.filter-ast-param-table .param-table td:last-child {
  font-weight: 600;
  color: #6c757d;
}

/* 过滤*ST参数设置 */
.filter-ast-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-ast-param-inputs .ma-input {
  border-color: #6c757d;
}

.filter-ast-param-inputs .ma-input:focus {
  border-color: #6c757d;
  box-shadow: 0 0 0 2px rgba(108, 117, 125, 0.2);
}

/* 过滤停牌参数设置 */
.filter-suspended-section {
  margin-top: 20px;
}

.filter-suspended-header {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.filter-suspended-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.filter-suspended-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 过滤停牌参数表格 */
.filter-suspended-param-table {
  margin-bottom: 16px;
}

.filter-suspended-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-suspended-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.filter-suspended-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.filter-suspended-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.filter-suspended-param-table .param-table td:first-child {
  font-weight: 600;
  color: #6c757d;
}

.filter-suspended-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.filter-suspended-param-table .param-table td:last-child {
  font-weight: 600;
  color: #6c757d;
}

/* 过滤停牌参数设置 */
.filter-suspended-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-suspended-param-inputs .ma-input {
  border-color: #6c757d;
}

.filter-suspended-param-inputs .ma-input:focus {
  border-color: #6c757d;
  box-shadow: 0 0 0 2px rgba(108, 117, 125, 0.2);
}

/* 过滤科创板参数设置 */
.filter-star-section {
  margin-top: 20px;
}

.filter-star-header {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.filter-star-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.filter-star-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 过滤科创板参数表格 */
.filter-star-param-table {
  margin-bottom: 16px;
}

.filter-star-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-star-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.filter-star-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.filter-star-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.filter-star-param-table .param-table td:first-child {
  font-weight: 600;
  color: #6c757d;
}

.filter-star-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.filter-star-param-table .param-table td:last-child {
  font-weight: 600;
  color: #6c757d;
}

/* 过滤科创板参数设置 */
.filter-star-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-star-param-inputs .ma-input {
  border-color: #6c757d;
}

.filter-star-param-inputs .ma-input:focus {
  border-color: #6c757d;
  box-shadow: 0 0 0 2px rgba(108, 117, 125, 0.2);
}

/* 过滤创业板参数设置 */
.filter-chinext-section {
  margin-top: 20px;
}

.filter-chinext-header {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.filter-chinext-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.filter-chinext-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 过滤创业板参数表格 */
.filter-chinext-param-table {
  margin-bottom: 16px;
}

.filter-chinext-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-chinext-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.filter-chinext-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.filter-chinext-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.filter-chinext-param-table .param-table td:first-child {
  font-weight: 600;
  color: #6c757d;
}

.filter-chinext-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.filter-chinext-param-table .param-table td:last-child {
  font-weight: 600;
  color: #6c757d;
}

/* 过滤创业板参数设置 */
.filter-chinext-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-chinext-param-inputs .ma-input {
  border-color: #6c757d;
}

.filter-chinext-param-inputs .ma-input:focus {
  border-color: #6c757d;
  box-shadow: 0 0 0 2px rgba(108, 117, 125, 0.2);
}

/* 过滤退市参数设置 */
.filter-delisted-section {
  margin-top: 20px;
}

.filter-delisted-header {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.filter-delisted-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.filter-delisted-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 过滤退市参数表格 */
.filter-delisted-param-table {
  margin-bottom: 16px;
}

.filter-delisted-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-delisted-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.filter-delisted-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.filter-delisted-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.filter-delisted-param-table .param-table td:first-child {
  font-weight: 600;
  color: #6c757d;
}

.filter-delisted-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.filter-delisted-param-table .param-table td:last-child {
  font-weight: 600;
  color: #6c757d;
}

/* 过滤退市参数设置 */
.filter-delisted-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-delisted-param-inputs .ma-input {
  border-color: #6c757d;
}

.filter-delisted-param-inputs .ma-input:focus {
  border-color: #6c757d;
  box-shadow: 0 0 0 2px rgba(108, 117, 125, 0.2);
}

/* 财务指标通用样式 */
.finance-section,
.roa-section,
.roe-section,
.gross-margin-section,
.net-margin-section,
.revenue-growth-section,
.profit-growth-section,
.dynamic-pe-section,
.pb-ratio-section,
.ps-ratio-section {
  margin-top: 20px;
}

/* 财务指标紫色标题栏通用样式 */
.roa-purple-header,
.roe-purple-header,
.gross-margin-purple-header,
.net-margin-purple-header,
.revenue-growth-purple-header,
.profit-growth-purple-header,
.dynamic-pe-purple-header,
.pb-ratio-purple-header,
.ps-ratio-purple-header {
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(139, 92, 246, 0.2);
}

.roa-purple-title,
.roe-purple-title,
.gross-margin-purple-title,
.net-margin-purple-title,
.revenue-growth-purple-title,
.profit-growth-purple-title,
.dynamic-pe-purple-title,
.pb-ratio-purple-title,
.ps-ratio-purple-title {
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}

/* 比较设置样式 */
.roa-comparison-settings,
.roe-comparison-settings,
.gross-margin-comparison-settings,
.net-margin-comparison-settings,
.revenue-growth-comparison-settings,
.profit-growth-comparison-settings,
.dynamic-pe-comparison-settings,
.pb-ratio-comparison-settings,
.ps-ratio-comparison-settings,
.open-price-comparison-settings,
.close-price-comparison-settings,
.high-price-comparison-settings,
.low-price-comparison-settings,
.prev-close-price-comparison-settings {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 16px;
}

.comparison-header {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  padding: 12px 16px;
  border-radius: 6px 6px 0 0;
}

.comparison-title,
.comparison-operator,
.comparison-indicator {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
  text-align: center;
}

.comparison-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
  align-items: center;
  padding: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .comparison-header,
  .comparison-inputs {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .comparison-header {
    text-align: center;
  }
}

/* 财务指标标签通用样式 */
.roa-label,
.roe-label,
.gross-margin-label,
.net-margin-label,
.revenue-growth-label,
.profit-growth-label,
.dynamic-pe-label,
.pb-ratio-label,
.ps-ratio-label {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  color: #ffffff;
  padding: 8px 16px;
  border-radius: 6px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
  transition: all 0.2s ease;
}

.roa-label:hover,
.roe-label:hover,
.gross-margin-label:hover,
.net-margin-label:hover,
.revenue-growth-label:hover,
.profit-growth-label:hover,
.dynamic-pe-label:hover,
.pb-ratio-label:hover,
.ps-ratio-label:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

/* 股票价格标签样式 */
.open-price-label,
.close-price-label,
.high-price-label,
.low-price-label,
.prev-close-price-label {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #ffffff;
  padding: 8px 16px;
  border-radius: 6px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
  transition: all 0.2s ease;
}

.open-price-label:hover,
.close-price-label:hover,
.high-price-label:hover,
.low-price-label:hover,
.prev-close-price-label:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3);
}

.operator-select {
  display: flex;
  justify-content: center;
}

.comparison-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #ffffff;
  font-size: 14px;
  color: #374151;
  transition: all 0.2s ease;
}

.comparison-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.value-input {
  display: flex;
  justify-content: center;
}

.comparison-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #ffffff;
  font-size: 14px;
  color: #374151;
  transition: all 0.2s ease;
}

.comparison-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.comparison-input::placeholder {
  color: #9ca3af;
}

/* 开盘价样式 */
.open-price-orange-header {
  background: linear-gradient(135deg, #f97316 0%, #eab308 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(249, 115, 22, 0.2);
}

.open-price-orange-title {
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}

.open-price-description {
  background: #f8f9fa;
  color: #374151;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
  text-align: center;
  border-left: 4px solid #f97316;
}

.open-price-comparison-settings {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 16px;
}

.open-price-label {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  color: #ffffff;
  padding: 8px 16px;
  border-radius: 6px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
  transition: all 0.2s ease;
}

.open-price-label:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

.indicator-select {
  display: flex;
  justify-content: center;
}

/* 收盘价样式 */
.close-price-orange-header {
  background: linear-gradient(135deg, #f97316 0%, #eab308 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(249, 115, 22, 0.2);
}

.close-price-orange-title {
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}

.close-price-description {
  background: #f8f9fa;
  color: #374151;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
  text-align: center;
  border-left: 4px solid #f97316;
}

.close-price-comparison-settings {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 16px;
}

.close-price-label {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  color: #ffffff;
  padding: 8px 16px;
  border-radius: 6px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
  transition: all 0.2s ease;
}

.close-price-label:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

/* 最高价样式 */
.high-price-orange-header {
  background: linear-gradient(135deg, #f97316 0%, #eab308 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(249, 115, 22, 0.2);
}

.high-price-orange-title {
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}

.high-price-description {
  background: #f8f9fa;
  color: #374151;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
  text-align: center;
  border-left: 4px solid #f97316;
}

.high-price-comparison-settings {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 16px;
}

.high-price-label {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  color: #ffffff;
  padding: 8px 16px;
  border-radius: 6px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
  transition: all 0.2s ease;
}

.high-price-label:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

/* 最低价样式 */
.low-price-orange-header {
  background: linear-gradient(135deg, #f97316 0%, #eab308 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(249, 115, 22, 0.2);
}

.low-price-orange-title {
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}

.low-price-description {
  background: #f8f9fa;
  color: #374151;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
  text-align: center;
  border-left: 4px solid #f97316;
}

.low-price-comparison-settings {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 16px;
}

.low-price-label {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  color: #ffffff;
  padding: 8px 16px;
  border-radius: 6px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
  transition: all 0.2s ease;
}

.low-price-label:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3);
}

/* 昨日收盘价样式 */
.prev-close-price-orange-header {
  background: linear-gradient(135deg, #f97316 0%, #eab308 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(249, 115, 22, 0.2);
}

.prev-close-price-orange-title {
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}

.prev-close-price-description {
  background: #f8f9fa;
  color: #374151;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
  text-align: center;
  border-left: 4px solid #f97316;
}

.prev-close-price-comparison-settings {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 16px;
}

.prev-close-price-label {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #ffffff;
  padding: 8px 16px;
  border-radius: 6px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
  transition: all 0.2s ease;
}

.prev-close-price-label:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3);
}

.finance-header,
.roa-header,
.roe-header,
.gross-margin-header,
.net-margin-header,
.revenue-growth-header,
.profit-growth-header,
.dynamic-pe-header,
.pb-ratio-header,
.ps-ratio-header {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.finance-title,
.roa-title,
.roe-title,
.gross-margin-title,
.net-margin-title,
.revenue-growth-title,
.profit-growth-title,
.dynamic-pe-title,
.pb-ratio-title,
.ps-ratio-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.finance-description,
.roa-description,
.roe-description,
.gross-margin-description,
.net-margin-description,
.revenue-growth-description,
.profit-growth-description,
.dynamic-pe-description,
.pb-ratio-description,
.ps-ratio-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 通用表格样式（覆盖到本组件内所有.param-table） */
.param-table {
  width: 100%;
  border-collapse: collapse;
  background: #ffffff;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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

.param-name {
  font-weight: 600;
  color: #3b82f6;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-radius: 4px;
  padding: 4px 8px;
}

.param-default {
  font-weight: 600;
  color: #10b981;
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  border-radius: 4px;
  padding: 4px 8px;
  display: inline-block;
  min-width: 60px;
  text-align: center;
}

/* 表格行悬停效果 */
.param-table tbody tr:hover {
  background-color: #f8f9fa;
  transition: background-color 0.2s ease;
}

/* 表格边框样式 */
.param-table {
  border: 1px solid #e9ecef;
}

.param-table th {
  border-bottom: 2px solid #dee2e6;
  font-weight: 700;
  text-transform: uppercase;
  font-size: 11px;
  letter-spacing: 0.5px;
}

/* 财务指标输入卡片样式 */
.finance-param-inputs,
.roa-param-inputs,
.roe-param-inputs,
.gross-margin-param-inputs,
.net-margin-param-inputs,
.revenue-growth-param-inputs,
.profit-growth-param-inputs,
.dynamic-pe-param-inputs,
.pb-ratio-param-inputs,
.ps-ratio-param-inputs {
  background: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 公告类指标通用样式 */
.shareholder-reduction-section,
.shareholder-increase-section,
.shareholder-dividend-section,
.violation-inquiry-section,
.performance-forecast-section {
  margin-top: 20px;
}

.shareholder-reduction-header,
.shareholder-increase-header,
.shareholder-dividend-header,
.violation-inquiry-header,
.performance-forecast-header {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  color: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.shareholder-reduction-title,
.shareholder-increase-title,
.shareholder-dividend-title,
.violation-inquiry-title,
.performance-forecast-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.shareholder-reduction-description,
.shareholder-increase-description,
.shareholder-dividend-description,
.violation-inquiry-description,
.performance-forecast-description {
  font-size: 13px;
  opacity: 0.9;
}

/* 公告类参数表格 */
.shareholder-reduction-param-table,
.shareholder-increase-param-table,
.shareholder-dividend-param-table,
.violation-inquiry-param-table,
.performance-forecast-param-table {
  margin-bottom: 16px;
}

.shareholder-reduction-param-table .param-table,
.shareholder-increase-param-table .param-table,
.shareholder-dividend-param-table .param-table,
.violation-inquiry-param-table .param-table,
.performance-forecast-param-table .param-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.shareholder-reduction-param-table .param-table th,
.shareholder-increase-param-table .param-table th,
.shareholder-dividend-param-table .param-table th,
.violation-inquiry-param-table .param-table th,
.performance-forecast-param-table .param-table th {
  background: #f8f9fa;
  color: #495057;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 12px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.shareholder-reduction-param-table .param-table td,
.shareholder-increase-param-table .param-table td,
.shareholder-dividend-param-table .param-table td,
.violation-inquiry-param-table .param-table td,
.performance-forecast-param-table .param-table td {
  padding: 8px 12px;
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid #f1f3f4;
}

.shareholder-reduction-param-table .param-table tr:last-child td,
.shareholder-increase-param-table .param-table tr:last-child td,
.shareholder-dividend-param-table .param-table tr:last-child td,
.violation-inquiry-param-table .param-table tr:last-child td,
.performance-forecast-param-table .param-table tr:last-child td {
  border-bottom: none;
}

.shareholder-reduction-param-table .param-table td:first-child,
.shareholder-increase-param-table .param-table td:first-child,
.shareholder-dividend-param-table .param-table td:first-child,
.violation-inquiry-param-table .param-table td:first-child,
.performance-forecast-param-table .param-table td:first-child {
  font-weight: 600;
  color: #06b6d4;
}

.shareholder-reduction-param-table .param-table td:nth-child(2),
.shareholder-increase-param-table .param-table td:nth-child(2),
.shareholder-dividend-param-table .param-table td:nth-child(2),
.violation-inquiry-param-table .param-table td:nth-child(2),
.performance-forecast-param-table .param-table td:nth-child(2) {
  text-align: left;
  color: #6c757d;
}

.shareholder-reduction-param-table .param-table td:last-child,
.shareholder-increase-param-table .param-table td:last-child,
.shareholder-dividend-param-table .param-table td:last-child,
.violation-inquiry-param-table .param-table td:last-child,
.performance-forecast-param-table .param-table td:last-child {
  font-weight: 600;
  color: #6c757d;
}

/* 公告类参数输入框 */
.shareholder-reduction-param-inputs,
.shareholder-increase-param-inputs,
.shareholder-dividend-param-inputs,
.violation-inquiry-param-inputs,
.performance-forecast-param-inputs {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 日成交均价样式 */
.avg-price-section {
  margin-top: 20px;
}

.avg-price-header {
  background: linear-gradient(135deg, #f97316 0%, #eab308 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(249, 115, 22, 0.2);
}

.avg-price-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.avg-price-description {
  font-size: 13px;
  opacity: 0.9;
}

.avg-price-param-table {
  margin-bottom: 16px;
}

.avg-price-param-inputs {
  background: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.ma-input-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.ma-input-row:last-child {
  margin-bottom: 0;
}

.ma-input-row label {
  width: 80px;
  font-weight: 600;
  color: #495057;
  font-size: 14px;
}

.input-with-unit {
  flex: 1;
  margin-left: 12px;
}

.ma-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background: #ffffff;
  transition: border-color 0.2s ease;
}

.ma-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 单位标签样式 */
.unit {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #ffffff;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  margin-left: 8px;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
}

/* 数字输入框样式 */
input[type="number"] {
  -moz-appearance: textfield;
}

input[type="number"]::-webkit-outer-spin-button,
input[type="number"]::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

/* 下拉选择框样式 */
select.ma-input {
  cursor: pointer;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 8px center;
  background-repeat: no-repeat;
  background-size: 16px;
  padding-right: 32px;
}

select.ma-input:focus {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%233b82f6' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
}

/* 涨幅样式 */
.change-rate-section {
  margin-top: 20px;
}

.change-rate-header {
  background: linear-gradient(135deg, #f97316 0%, #eab308 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(249, 115, 22, 0.2);
}

.change-rate-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.change-rate-description {
  font-size: 13px;
  opacity: 0.9;
}

.change-rate-param-table {
  margin-bottom: 16px;
}

.change-rate-param-inputs {
  background: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 量比样式 */
.volume-ratio-section {
  margin-top: 20px;
}

.volume-ratio-header {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(6, 182, 212, 0.2);
}

.volume-ratio-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.volume-ratio-description {
  font-size: 13px;
  opacity: 0.9;
}

.volume-ratio-param-table {
  margin-bottom: 16px;
}

.volume-ratio-param-inputs {
  background: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 成交额样式 */
.turnover-section {
  margin-top: 20px;
}

.turnover-header {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2);
}

.turnover-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.turnover-description {
  font-size: 13px;
  opacity: 0.9;
}

.turnover-param-table {
  margin-bottom: 16px;
}

.turnover-param-inputs {
  background: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 成交额样式 - 兼容旧名称 */
.transaction-amount-section {
  margin-top: 20px;
}

.transaction-amount-header {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2);
}

.transaction-amount-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.transaction-amount-description {
  font-size: 13px;
  opacity: 0.9;
}

.transaction-amount-param-table {
  margin-bottom: 16px;
}

.transaction-amount-param-inputs {
  background: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 换手率样式 */
.turnover-rate-section {
  margin-top: 20px;
}

.turnover-rate-header {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(139, 92, 246, 0.2);
}

.turnover-rate-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.turnover-rate-description {
  font-size: 13px;
  opacity: 0.9;
}

.turnover-rate-param-table {
  margin-bottom: 16px;
}

.turnover-rate-param-inputs {
  background: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 市值样式 */
.market-value-section {
  margin-top: 20px;
}

.market-value-header {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(245, 158, 11, 0.2);
}

.market-value-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.market-value-description {
  font-size: 13px;
  opacity: 0.9;
}

.market-value-param-table {
  margin-bottom: 16px;
}

.market-value-param-inputs {
  background: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 成交量样式 */
.trading-volume-section {
  margin-top: 20px;
}

.trading-volume-header {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(239, 68, 68, 0.2);
}

.trading-volume-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.trading-volume-description {
  font-size: 13px;
  opacity: 0.9;
}

.trading-volume-param-table {
  margin-bottom: 16px;
}

.trading-volume-param-inputs {
  background: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 资金净流入样式 */
.capital-inflow-section {
  margin-top: 20px;
}

.capital-inflow-header {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  color: #ffffff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(6, 182, 212, 0.2);
}

.capital-inflow-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.capital-inflow-description {
  font-size: 13px;
  opacity: 0.9;
}

.capital-inflow-param-table {
  margin-bottom: 16px;
}

.capital-inflow-param-inputs {
  background: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 通用输入框样式 */
.param-input-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.param-input-row:last-child {
  margin-bottom: 0;
}

.param-input-row label {
  width: 80px;
  font-weight: 600;
  color: #495057;
  font-size: 14px;
}

.param-input-with-unit {
  flex: 1;
  margin-left: 12px;
}

.param-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background: #ffffff;
  transition: border-color 0.2s ease;
}

.param-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 按钮样式 */
.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

.btn-save {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #ffffff;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
}

.btn-save:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3);
}

.btn-reset {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: #ffffff;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(107, 114, 128, 0.2);
}

.btn-reset:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(107, 114, 128, 0.3);
}

/* 通用：个股MA参数矩阵与输入样式统一 */
.param-content .param-table {
  margin-top: 8px;
}
.param-content .table-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  align-items: center;
  padding: 8px 0;
}
.param-content .table-header {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
}
.param-content .table-cell {
  text-align: center;
}
.param-content .form-control,
.param-content .form-select {
  width: 100%;
  height: 36px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 13px;
  background-color: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.param-content .form-control:focus,
.param-content .form-select:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.12);
}

/* 信号按钮：更清晰的激活与悬停态 */
.button-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.signal-btn {
  border: 1px solid #dcdfe6;
  background: #ffffff;
  color: #606266;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.signal-btn:hover:not(.active) {
  border-color: #409eff;
  color: #409eff;
}
.signal-btn.active {
  background: #409eff;
  color: #ffffff;
  border-color: #409eff;
}

/* 操作按钮：应用设置为主按钮 */
.btn-apply {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
  color: #ffffff;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.25);
}
.btn-apply:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(64, 158, 255, 0.35);
}

</style> 
