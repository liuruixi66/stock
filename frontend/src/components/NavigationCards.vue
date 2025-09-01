<template>
  <div class="navigation-cards">
    <router-link to="/earnings-overview" class="nav-card" :class="{ active: currentRoute === '/earnings-overview' }">
      <div class="card-icon">
        <i class="fa fa-chart-line"></i>
      </div>
      <div class="card-content">
        <h3>收益概述</h3>
        <p>策略收益分析</p>
      </div>
    </router-link>
    
    <router-link to="/transaction-details" class="nav-card" :class="{ active: currentRoute === '/transaction-details' }">
      <div class="card-icon">
        <i class="fa fa-list-alt"></i>
      </div>
      <div class="card-content">
        <h3>交易详情</h3>
        <p>交易记录查看</p>
      </div>
    </router-link>
    
    <router-link to="/backtest-details" class="nav-card" :class="{ active: currentRoute === '/backtest-details' }">
      <div class="card-icon">
        <i class="fa fa-history"></i>
      </div>
      <div class="card-content">
        <h3>回测详情</h3>
        <p>回测结果分析</p>
      </div>
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const currentRoute = computed(() => route.path)
</script>

<style scoped>
.navigation-cards {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  margin-top: 0;
  flex-wrap: wrap;
}

.nav-card {
  flex: 1;
  min-width: 250px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  text-decoration: none;
  color: inherit;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border: 2px solid transparent;
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  border-color: #1890ff;
}

.nav-card.active {
  border-color: #1890ff;
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
  color: white;
}

.nav-card.active .card-icon {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.card-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: #f0f9ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1890ff;
  font-size: 20px;
  flex-shrink: 0;
}

.card-content h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
}

.card-content p {
  font-size: 12px;
  color: #666;
  margin: 0;
}

.nav-card.active .card-content p {
  color: rgba(255, 255, 255, 0.8);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .navigation-cards {
    flex-direction: column;
    gap: 12px;
  }
  
  .nav-card {
    min-width: auto;
  }
}

@media (max-width: 480px) {
  .navigation-cards {
    margin-bottom: 15px;
  }
  
  .nav-card {
    padding: 15px;
  }
  
  .card-icon {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }
  
  .card-content h3 {
    font-size: 14px;
  }
  
  .card-content p {
    font-size: 11px;
  }
}
</style> 