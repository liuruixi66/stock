<template>
  <div class="strategy-container">
    <!-- 顶部导航Tab -->
    <div class="strategy-tabs">
      <div class="tab active">择股设置</div>
      <div class="tab">交易模型</div>
      <div class="tab">大盘择时</div>
      <div class="tab">股指对冲</div>
    </div>

    <!-- 筛选区 -->
    <div class="strategy-filters">
      <div class="filter-row">
        <span>我的股票池：</span>
        <select><option>全部股票</option></select>
        <button class="plus-btn">+</button>
        <span>系统股票池：</span>
        <select><option>全部股票</option></select>
        <span>申万：</span>
        <select><option>申万2014</option></select>
        <span>一级行业：</span>
        <select><option>全部</option></select>
        <span>二级行业：</span>
        <select><option>全部</option></select>
        <span>ST股票：</span>
        <select><option>包含ST</option></select>
        <label><input type="checkbox">过滤停牌股票</label>
      </div>
      <div class="filter-row">
        <span>指数成份：</span>
        <select><option>全部</option></select>
        <span>上市板块：</span>
        <select><option>全部</option></select>
        <span>行业板块：</span>
        <select><option>全部</option></select>
        <span>地域板块：</span>
        <select><option>全部</option></select>
        <span>企业性质：</span>
        <select><option>全部</option></select>
        <span>融资融券：</span>
        <select><option>全部</option></select>
        <span>科创板：</span>
        <select><option>排除科创板</option></select>
      </div>
    </div>

    <!-- 指标选择区 -->
    <div class="strategy-indicator-panel">
      <input class="indicator-search" placeholder="搜索财务选项与指标" />
      <div class="indicator-tabs">
        <div class="indicator-tab active">行情</div>
        <div class="indicator-tab">技术指标</div>
        <div class="indicator-tab">财务指标</div>
        <div class="indicator-tab">财报公司</div>
        <div class="indicator-tab">分析师</div>
        <div class="indicator-tab">大盘指标</div>
        <div class="indicator-tab">自定义</div>
      </div>
      <div class="indicator-list">
        <div class="indicator-group">
          <span>乖离率</span><span>EMA</span><span>相对波动率</span><span>CCI</span><span>WQ价格类</span>
        </div>
        <div class="indicator-group">
          <span>波动率</span><span>MACD</span><span>市值中性化</span><span>历史贝塔</span><span>WQ重价</span>
        </div>
        <div class="indicator-group">
          <span>MA</span><span>TRIX</span><span>重比</span><span>多头排列标记</span>
        </div>
        <div class="indicator-group">
          <span>成交量形态</span><span>K线形态</span><span>KDJ</span><span>布林线</span><span>ATR</span>
        </div>
        <div class="indicator-group">
          <span>RSI</span><span>BBIC</span><span>ILLIQ</span>
        </div>
      </div>
    </div>

    <!-- 选股条件区 -->
    <div class="strategy-condition-panel">
      <div class="condition-tabs">
        <div class="condition-tab active">筛选条件 <span class="badge">2</span></div>
        <div class="condition-tab">排名条件</div>
      </div>
      <div class="condition-list">
        <div class="condition-row">
          <span>指标</span>
          <select><option>开盘价</option></select>
          <span>比较符</span>
          <select><option>大于</option></select>
          <span>值</span>
          <input type="number" value="10" />
          <span class="condition-action"><i class="fas fa-times"></i></span>
          <span class="condition-action"><i class="fas fa-check"></i></span>
        </div>
        <div class="condition-row">
          <span>指标</span>
          <select><option>市盈率</option></select>
          <span>比较符</span>
          <select><option>小于</option></select>
          <span>值</span>
          <input type="number" value="30" />
          <span class="condition-action"><i class="fas fa-times"></i></span>
          <span class="condition-action"><i class="fas fa-check"></i></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 这里可以添加交互逻辑
</script>

<style scoped>
.strategy-container {
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  padding: 0 0 24px 0;
  margin: 0 auto;
  min-width: 1200px;
}
.strategy-tabs {
  display: flex;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 24px;
  height: 48px;
  align-items: center;
  background: #fafbfc;
}
.tab {
  padding: 0 24px;
  height: 48px;
  line-height: 48px;
  cursor: pointer;
  font-weight: 500;
  color: #606266;
  border-bottom: 2px solid transparent;
}
.tab.active {
  color: #409eff;
  border-bottom: 2px solid #409eff;
  background: #fff;
}
.strategy-filters {
  padding: 16px 24px 0 24px;
}
.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.filter-row select, .filter-row input[type="checkbox"] {
  margin-right: 8px;
}
.plus-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  border: none;
  font-size: 18px;
  margin: 0 8px;
  cursor: pointer;
}
.strategy-indicator-panel {
  padding: 16px 24px 0 24px;
}
.indicator-search {
  width: 320px;
  height: 32px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 0 12px;
  margin-bottom: 12px;
}
.indicator-tabs {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
}
.indicator-tab {
  padding: 4px 16px;
  border-radius: 4px 4px 0 0;
  background: #f5f7fa;
  color: #606266;
  cursor: pointer;
  font-size: 14px;
}
.indicator-tab.active {
  background: #fff;
  color: #409eff;
  font-weight: 500;
  border-bottom: 2px solid #409eff;
}
.indicator-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 24px;
  margin-bottom: 8px;
}
.indicator-group {
  display: flex;
  gap: 12px;
  margin-bottom: 4px;
}
.strategy-condition-panel {
  padding: 16px 24px 0 24px;
}
.condition-tabs {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
}
.condition-tab {
  padding: 4px 16px;
  border-radius: 4px 4px 0 0;
  background: #f5f7fa;
  color: #606266;
  cursor: pointer;
  font-size: 14px;
}
.condition-tab.active {
  background: #fff;
  color: #409eff;
  font-weight: 500;
  border-bottom: 2px solid #409eff;
}
.badge {
  background: #409eff;
  color: #fff;
  border-radius: 8px;
  padding: 2px 8px;
  font-size: 12px;
  margin-left: 4px;
}
.condition-list {
  margin-top: 8px;
}
.condition-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.condition-row input[type="number"] {
  width: 60px;
  height: 28px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 0 8px;
}
.condition-action {
  margin-left: 8px;
  color: #409eff;
  cursor: pointer;
  font-size: 16px;
}
</style> 