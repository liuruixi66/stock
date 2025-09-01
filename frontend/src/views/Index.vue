<template>
  <div class="home-container">

    <!-- 功能入口区 -->
    <div class="card entry-card">
      <div class="entry-title">功能入口</div>
      <div class="entry-grid">
        <router-link to="/menu-layout" class="entry-item filter">
          <i class="fa fa-filter"></i><span>选股中心</span>
        </router-link>
        <div class="entry-item strategy"><i class="fa fa-chess-knight"></i><span>策略管理</span></div>
        <div class="entry-item trade"><i class="fa fa-exchange-alt"></i><span>交易管理</span></div>
        <router-link to="/earnings-overview" class="entry-item earnings">
          <i class="fa fa-chart-line"></i><span>收益概述</span>
        </router-link>
        <router-link to="/transaction-details" class="entry-item transaction">
          <i class="fa fa-list-alt"></i><span>交易详情</span>
        </router-link>
      </div>
    </div>


    <!-- 热门策略与收益展示 -->
    <div class="card hot-strategy-card">
      <div class="hot-strategy-title">热门策略与收益展示</div>
      <div class="hot-strategy-grid">
        <div v-for="item in strategyList" :key="item.name" class="hot-strategy-item">
          <div class="hot-strategy-name">{{ item.name }}</div>
          <div class="hot-strategy-profit up">{{ item.profit > 0 ? '+' : ''}}{{ item.profit }}%</div>
          <div class="hot-strategy-desc">{{ item.desc }}</div>
          <div class="profit-bar-outer">
            <div class="profit-bar-inner" :style="{ width: Math.min(Math.abs(item.profit), 100) + '%', background: item.profit >= 0 ? '#34d399' : '#f87171' }"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

interface StrategyItem {
  name: string;
  profit: number;
  desc: string;
}

const strategyList = ref<StrategyItem[]>([]);

onMounted(async () => {
  // TODO: 替换为你的后端接口地址
  try {
    const res = await fetch('/api/hot-strategy');
    if (res.ok) {
      const data = await res.json();
      strategyList.value = data;
    } else {
      // mock数据，接口异常时展示
      strategyList.value = [
        { name: '均线多头策略', profit: 18.2, desc: '近一年收益，回撤低，适合稳健投资' },
        { name: '突破平台策略', profit: 25.7, desc: '捕捉强势股，收益高，风险适中' },
        { name: '低ATR成长策略', profit: 12.4, desc: '波动小，适合长期持有' },
        { name: '海龟交易法则', profit: 30.1, desc: '趋势跟踪，收益弹性大' },
      ];
    }
  } catch {
    strategyList.value = [
      { name: '均线多头策略', profit: 18.2, desc: '近一年收益，回撤低，适合稳健投资' },
      { name: '突破平台策略', profit: 25.7, desc: '捕捉强势股，收益高，风险适中' },
      { name: '低ATR成长策略', profit: 12.4, desc: '波动小，适合长期持有' },
      { name: '海龟交易法则', profit: 30.1, desc: '趋势跟踪，收益弹性大' },
    ];
  }
});
</script>
/* 热门策略收益可视化条样式 */
.profit-bar-outer {
  width: 100%;
  height: 10px;
  background: #f3f4f6;
  border-radius: 6px;
  margin-top: 8px;
  margin-bottom: 2px;
  overflow: hidden;
}
.profit-bar-inner {
  height: 100%;
  border-radius: 6px;
  transition: width 0.5s;
}

// ...existing code...
<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 10px 30px 10px;
}
.card {
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.07);
  margin-bottom: 28px;
  padding: 28px 32px;
}
.welcome-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.welcome-left {
  display: flex;
  flex-direction: column;
}
.main-title {
  font-size: 2.1em;
  font-weight: bold;
  margin-bottom: 8px;
}
.subtitle {
  color: #6b7280;
  font-size: 1.1em;
}
.welcome-avatar {
  width: 56px;
  height: 56px;
  background: #f3f4f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2em;
  color: #9ca3af;
}
.entry-card {
  padding: 24px 32px 18px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.entry-title {
  align-self: flex-start;
  margin-bottom: 18px;
  font-size: 1.15em;
  font-weight: bold;
}
.entry-grid {
  display: flex;
  flex-direction: row;
  justify-content: center;
  gap: 32px;
  width: 100%;
}
.entry-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  border-radius: 10px;
  padding: 18px 0 10px 0;
  font-size: 1.08em;
  font-weight: 500;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
  box-shadow: 0 2px 6px rgba(0,0,0,0.04);
  min-width: 160px;
  max-width: 200px;
}
.entry-item i {
  font-size: 2.6em;
  margin-bottom: 12px;
}
.entry-item.home { background: #eff6ff; color: #2563eb; }
.entry-item.data { background: #f3e8ff; color: #7c3aed; }
.entry-item.filter { background: #ecfdf5; color: #059669; }
.entry-item.strategy { background: #fef9c3; color: #eab308; }
.entry-item.trade { background: #fee2e2; color: #ef4444; }
.entry-item.earnings { background: #f0f9ff; color: #0ea5e9; }
.entry-item.transaction { background: #fef3c7; color: #d97706; }
.entry-item.user { background: #e0e7ff; color: #6366f1; }
.entry-item:hover {
  box-shadow: 0 6px 18px rgba(0,0,0,0.10);
  transform: translateY(-2px);
}
.market-card {
  padding: 24px 32px 18px 32px;
}
.market-title {
  font-size: 1.18em;
  font-weight: bold;
  margin-bottom: 18px;
}
.market-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
}
.market-item {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  padding: 18px 10px 12px 18px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  box-shadow: 0 2px 6px rgba(0,0,0,0.03);
}
.market-label {
  color: #64748b;
  font-size: 1em;
  margin-bottom: 6px;
}
.market-value {
  font-size: 1.5em;
  font-weight: bold;
  margin-bottom: 2px;
}
.market-date {
  font-size: 0.95em;
  color: #a1a1aa;
  margin-bottom: 2px;
}
.market-change {
  font-size: 1em;
  font-weight: 500;
}
.market-change.up { color: #ef4444; }
.market-change.down { color: #10b981; }
.recent-card {
  padding: 24px 32px 18px 32px;
}
.recent-title {
  font-size: 1.18em;
  font-weight: bold;
  margin-bottom: 18px;
}
.recent-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}
.recent-item {
  background: #f9fafb;
  border-radius: 10px;
  padding: 16px 10px 10px 18px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  font-size: 1.05em;
  box-shadow: 0 2px 6px rgba(0,0,0,0.03);
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
}
.recent-item i {
  font-size: 1.3em;
  margin-bottom: 6px;
  color: #60a5fa;
}
.recent-item:hover {
  box-shadow: 0 6px 18px rgba(0,0,0,0.10);
  transform: translateY(-2px);
}
.recent-tag {
  margin-top: 4px;
  font-size: 0.92em;
  color: #a1a1aa;
  background: #e0e7ef;
  border-radius: 6px;
  padding: 2px 8px;
  display: inline-block;
}
/* 功能入口区标题样式已合并到上方style定义，无需重复 */
@media (max-width: 900px) {
  .market-grid, .recent-grid {
    grid-template-columns: 1fr 1fr;
  }
  .entry-grid {
    grid-template-columns: 1fr 1fr 1fr;
  }
}
@media (max-width: 600px) {
  .home-container {
    padding: 10px 2px;
  }
  .card {
    padding: 14px 6px;
  }
  .market-grid, .recent-grid {
    grid-template-columns: 1fr;
  }
  .entry-grid {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: repeat(3, 1fr);
  }
  .welcome-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>