<template>
  <!-- 左侧菜单 -->
  <aside class="sidebar" :class="{ 'collapsed': isSidebarCollapsed }">
    <div class="sidebar-header">
      <img src="/src/assets/img/favicon.ico" alt="Logo" class="logo" />
      <h1 class="app-title">InStock</h1>
    </div>
    
    <nav class="sidebar-nav">
      <div class="nav-section" v-for="(section, index) in menuSections" :key="index">
        <!-- 一级菜单标题 -->
        <div class="nav-section-title" 
             :class="{ active: currentSection === section.title }" 
             @click="toggleSection(index)">
          <div class="nav-section-content">
            <i :class="section.icon"></i>
            <span>{{ section.title }}</span>
          </div>
          <div v-if="section.items && section.items.length" class="arrow-wrapper">
            <i class="fa fa-angle-right arrow" :class="{ rotated: openSections[index] }"></i>
          </div>
        </div>
        
        <!-- 二级菜单 -->
        <transition name="slide">
          <ul v-if="section.items && section.items.length" 
              class="nav-items" 
              v-show="openSections[index]">
            <li v-for="(item, itemIndex) in section.items" :key="item.path">
              <!-- 带子菜单的项目 -->
              <template v-if="item.children">
                <div class="sub-menu-title" 
                     :class="{ active: item.isOpen }"
                     @click="toggleSubMenu(section, itemIndex)">
                  <span>{{ item.name }}</span>
                  <i class="fa fa-angle-right arrow" :class="{ rotated: item.isOpen }"></i>
                </div>
                <!-- 三级菜单 -->
                <transition name="slide">
                  <ul v-if="item.isOpen" class="sub-nav-items">
                    <li v-for="child in item.children" :key="child.path">
                      <router-link :to="child.path" 
                                  :class="{ active: currentPath === child.path }">
                        {{ child.name }}
                      </router-link>
                    </li>
                  </ul>
                </transition>
              </template>
              <!-- 无子菜单的项目 -->
              <router-link v-else 
                           :to="item.path" 
                           :class="{ active: currentPath === item.path }">
                {{ item.name }}
              </router-link>
            </li>
          </ul>
        </transition>
      </div>
    </nav>

    <div class="sidebar-footer" @click="toggleSidebar">
      <i class="fa" :class="isSidebarCollapsed ? 'fa-angle-right' : 'fa-angle-left'"></i>
    </div>
  </aside>

  <!-- 主内容区域 -->
  <div class="app-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <div class="content-wrapper">
      <router-view></router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const isSidebarCollapsed = ref(false)
const openSections = ref<boolean[]>([true, true, true, true, true])

interface MenuItem {
  name: string;
  path: string;
  isOpen?: boolean;
  children?: {
    name: string;
    path: string;
  }[];
}

interface MenuSection {
  title: string;
  icon: string;
  items: MenuItem[];
}

const menuSections = ref<MenuSection[]>([
  {
    title: '首页',
    icon: 'fa fa-home',
    items: [
    ]
  },
  {
    title: '数据管理',
    icon: 'fa fa-database',
    items: [
      { 
        name: '历史数据', 
        path: '/tables',
        isOpen: false,
        children: [
          { name: '每日股票数据', path: '/tables/stock-spot' },
          { name: '股票资金流向', path: '/tables/stock-fund-flow' },
          { name: '股票分红配送', path: '/tables/stock-bonus' },
          { name: '股票龙虎榜', path: '/tables/stock-top' },
          { name: '股票大宗交易', path: '/tables/stock-blocktrade' },
          { name: '行业资金流向', path: '/tables/industry-fund-flow' },
          { name: '概念资金流向', path: '/tables/concept-fund-flow' },
          { name: '每日ETF数据', path: '/tables/etf-spot' }
        ]
      },
      { 
        name: '实时数据', 
        path: '/realtime',
        isOpen: false,
        children: [
          { name: '股票的实时数据', path: '/realtime/quote' }
        ]
      }
    ]
  },

  {
    title: '策略管理',
    icon: 'fa fa-area-chart',
    items: [
      { 
        name: '策略选股', 
        path: '/menu-layout',
        isOpen: false,
      },
      { 
        name: '策略库', 
        path: '/stock/realtime-data',
        isOpen: false,
      },

      { 
        name: '回测详情', 
        path: '/backtest-details',
        isOpen: false,
      },

      { 
        name: '策略排行', 
        path: '/stock/realtime-data',
        isOpen: false,
      },
      { 
        name: '策略实时收益展示', 
        path: '/stock/realtime-data',
        isOpen: false,
      }
    ]
  },
  {
    title: '交易管理',
    icon: 'fa fa-puzzle-piece',
    items: [
       { 
        name: '策略实盘', 
        path: '/stock/realtime-data',
        isOpen: false,
      },
      { 
        name: '交易详情', 
        path: '/stock/realtime-data',
        isOpen: false,
        children: [
          { name: '每日交易情况', path: '/stock/realtime/quote' }
        ]
      },
      { 
        name: '消息通知', 
        path: '/stock/realtime-data',
        isOpen: false,
        children: [
          { name: '微信', path: '/stock/realtime/quote' }
        ]
      }
    ]
  },
  {
    title: '用户管理',
    icon: 'fa fa-puzzle-piece',
    items: [
      { 
        name: '注册账号', 
        path: '/stock/realtime-data',
        isOpen: false,
        children: [
          { name: '手机号注册', path: '/stock/realtime/quote' },
          { name: '微信号注册', path: '/stock/realtime/quote' },
          { name: '密码找回', path: '/stock/realtime/quote' },
          { name: '验证码登录', path: '/stock/realtime/quote' }
        ]
      },
      { 
        name: '用户信息管理', 
        path: '/stock/realtime-data',
        isOpen: false,
        children: [
          { name: '头像', path: '/stock/realtime/quote' },
          { name: '手机号', path: '/stock/realtime/quote' }
        ]
      },
      { 
        name: '用户权限管理', 
        path: '/stock/realtime-data',
        isOpen: false,
        children: [
          { name: '角色划分', path: '/stock/realtime/quote' },
          { name: '权限划分', path: '/stock/realtime/quote' }
        ]
      }
    ]
  }
])

const currentPath = computed(() => route.path)

// 获取当前路由对应的菜单项
const findCurrentMenuItem = () => {
  for (const section of menuSections.value) {
    if (section.items) {
      for (const item of section.items) {
        if (item.path === route.path) {
          return { section, item, child: null }
        }
        if (item.children) {
          const child = item.children.find((child: MenuItem) => child.path === route.path)
          if (child) {
            return { section, item, child }
          }
        }
      }
    }
  }
  return null
}

// 更新面包屑导航
const currentSection = computed(() => {
  const current = findCurrentMenuItem()
  return current?.section.title || '首页'
})

const currentPage = computed(() => {
  const current = findCurrentMenuItem()
  if (!current) return '首页'
  return current.child ? current.child.name : current.item.name
})

// 判断菜单项是否激活
const isMenuItemActive = (item: MenuItem) => {
  if (item.path === route.path) return true
  if (item.children) {
    return item.children.some(child => child.path === route.path)
  }
  return false
}

const toggleSection = (index: number) => {
  // 如果是选股中心(index为2)，则直接导航到对应页面
  if (index === 2) {
    router.push('/menu-layout')
  } else {
    openSections.value[index] = !openSections.value[index]
  }
}

const toggleSubMenu = (section: any, itemIndex: number) => {
  console.log('toggleSubMenu called', section, itemIndex) // 添加调试日志
  if (section.items && section.items[itemIndex]) {
    section.items[itemIndex].isOpen = !section.items[itemIndex].isOpen
  }
}

const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

const refreshData = () => {
  // 实现数据刷新逻辑
  window.location.reload()
}
</script>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
  background: #f4f6f9;
}

.nav-section {
  width: 100%;
  margin: 0;
}

/* 一级菜单样式 */
.nav-section-title {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.3s;
  color: #000000;
  font-size: 14px;
  background: #ffffff;
}

.nav-section-title:hover {
  background: #ffffff;
}

.nav-section-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-section-content span {
  flex: 1;
  background: #ffffff;
  color: #000000;
}

.nav-section-content i {
  font-size: 14px;
  width: 14px;
  text-align: center;
}

/* 二级菜单样式 */
.nav-items {
  background: #ffffff;
  color: #000000;
  padding: 4px 0;
}

.nav-items a,
.sub-menu-title {
  padding: 10px 16px 10px 40px;
  display: flex;
  align-items: center;
  color: #000000;
  text-decoration: none;
  transition: all 0.3s;
  font-size: 14px;
  position: relative;
}

.nav-items a:hover,
.nav-items a.active,
.sub-menu-title:hover,
.sub-menu-title.active {
  background: #ffffff;
  color: #000000;
}

/* 三级菜单样式 */
.sub-nav-items {
  background: #ffffff;
  color: #000000;
  padding: 4px 0;
  margin-left: 0; /* 移除额外的左边距 */
}

.sub-nav-items a {
  padding: 8px 16px 8px 40px; /* 调整为与二级菜单相同的左内边距 */
  font-size: 14px;
  color: #000000;
}

/* 子菜单样式 */
.sub-menu-title {
  padding: 10px 16px 10px 40px;
  display: flex;
  align-items: center;
  color: #000000;
  text-decoration: none;
  transition: all 0.3s;
  font-size: 14px;
  position: relative;
  background: #ffffff;
}

.submenu {
  background: #ffffff;
  overflow: hidden;
  transition: all 0.3s ease;
  border-left: none; /* 移除左边框 */
  margin-left: 0; /* 移除左边距 */
}

.submenu-item {
  padding: 10px 16px 10px 40px; /* 统一缩进 */
  color: #000000;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #ffffff;
  font-size: 14px;
}

/* 移除小圆点 */
.sub-nav-items li a::before {
  display: none;
}

.sub-section-title::before {
  display: none;
}

/* 侧边栏样式 */
.sidebar {
  width: 200px;
  background: #ffffff;
  color: #000000;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 1000;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

/* Logo区域样式 */
.sidebar-header {
  height: 60px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: #ffffff;
  color: #000000;
  border-bottom: 1px solid #e8e8e8;
}

.logo {
  width: 24px;
  height: 24px;
}

.app-title {
  font-size: 18px;
  font-weight: 500;
  color: #000000;
  margin: 0;
  white-space: nowrap;
}

/* 主内容区域 */
.main-content {
  flex: 1;
  padding-left: 200px;
  background: #ffffff;
  transition: padding-left 0.3s ease;
}

.content-wrapper {
  padding: 20px;
  width: 100%;
  max-width: 1600px;
  margin: 0 0 0 200px;
  box-sizing: border-box;
  height: 100vh;
  overflow-y: auto;
}

/* 折叠状态样式 */
.sidebar.collapsed {
  width: 60px;
}

.app-container.sidebar-collapsed .main-content {
  padding-left: 60px;
}

.app-container.sidebar-collapsed .content-wrapper {
  margin-left: 60px;
}

/* 箭头样式 */
.arrow-wrapper {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.arrow {
  font-size: 12px;
  color: #000000;
  transition: transform 0.3s;
}

.arrow.rotated {
  transform: rotate(90deg);
}

/* 滚动条样式 */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-nav::-webkit-scrollbar {
  width: 4px;
}

.sidebar-nav::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.sidebar-nav::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.sidebar-nav::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 底部样式 */
.sidebar-footer {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  cursor: pointer;
  color: #000000;
  transition: all 0.3s;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.sidebar-footer:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.05);
}

/* 动画效果优化 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 子菜单动画 */
.sub-nav-items {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sub-nav-items li {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: top;
}

/* 箭头动画 */
.arrow {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.arrow.rotated {
  transform: rotate(90deg);
}

/* 菜单项hover效果 */
.nav-section-title:hover,
.sub-section-title:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateX(5px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 收起按钮动画 */
.sidebar-footer {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-footer:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateX(5px);
}

/* 优化折叠状态动画 */
.sidebar {
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.main-content {
  transition: padding-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 菜单项激活状态动画 */
.nav-items a.active,
.sub-nav-items a.active {
  position: relative;
  overflow: hidden;
}

.nav-items a.active::after,
.sub-nav-items a.active::after {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 3px;
  background: #4a90e2;
  transform: scaleY(0);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: bottom;
}

.nav-items a.active::after,
.sub-nav-items a.active::after {
  transform: scaleY(1);
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}


.content-wrapper::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.content-wrapper::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.content-wrapper::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 添加子菜单样式 */
.sub-section-title {
  padding: 10px 20px 10px 50px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #000000;
  transition: all 0.3s;
  font-size:14px;
  position: relative;
  background: transparent;
}

.sub-section-title::before {
  content: '';
  position: absolute;
  left: 40px;
  top: 50%;
  width: 4px;
  height: 4px;
  background: #b8c7ce;
  border-radius: 50%;
  transform: translateY(-50%);
  opacity: 0.7;
}

.sub-section-title:hover {
  background: #ffffff;
  color: #000000;
}

.sub-section-title:hover::before {
  background: #fff;
}

.sub-section-title i {
  width: 20px;
  margin-right: 10px;
  font-size: 12px;
}

.sub-section-title .arrow {
  margin-left: auto;
  transition: transform 0.3s;
  opacity: 0.7;
  font-size: 0.8em;
}

.sub-section-title .arrow.rotated {
  transform: rotate(-180deg);
}

.sub-nav-items {
  list-style: none;
  padding: 0;
  margin: 0;
  background: #ffffff;
  border-left: 2px solid rgba(255, 255, 255, 0.1);
  margin-left: 50px;
  overflow: hidden; /* 确保动画正常工作 */
}

.sub-nav-items li {
  opacity: 1;
  transform: translateX(0);
  transition: all 0.3s ease;
}

/* 优化展开/收起动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
  max-height: 500px; /* 设置一个合适的最大高度 */
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}

.slide-enter-from .sub-nav-items li,
.slide-leave-to .sub-nav-items li {
  opacity: 0;
  transform: translateX(-20px);
}

.sub-nav-items li a {
  padding: 8px 20px 8px 30px;
  font-size: 0.9em;
  position: relative;
}

.sub-nav-items li a::before {
  content: '';
  position: absolute;
  left: 15px;
  top: 50%;
  width: 3px;
  height: 3px;
  background: #ffffff;
  border-radius: 50%;
  transform: translateY(-50%);
  opacity: 0.5;
}

.sub-nav-items li a:hover::before,
.sub-nav-items li.active a::before {
  background: #fff;
  opacity: 1;
}

/* 收起状态优化 */
.sidebar.collapsed .nav-section-title span,
.sidebar.collapsed .nav-items span,
.sidebar.collapsed .app-title {
  display: none;
  background: #ffffff;
  color: #000000;
}

.sidebar.collapsed .nav-items a,
.sidebar.collapsed .sub-nav-items a {
  padding: 10px 0;
  justify-content: center;
}

.sidebar.collapsed .nav-section-content {
  justify-content: center;
  width: 100%;
}

.sidebar.collapsed .nav-section-content i {
  margin: 0;
}

/* 箭头容器样式 */
.arrow-wrapper {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 二级菜单标题样式 */
.sub-menu-title {
  padding: 10px 16px 10px 40px;
  display: flex;
  align-items: center;
  color: #000000;
  text-decoration: none;
  transition: all 0.3s;
  font-size: 14px;
  position: relative;
  background: #ffffff;
}

.sub-menu-title:hover,
.sub-menu-title.active {
  background: #ffffff;
  color: #000000;
}

/* 箭头动画 */
.arrow {
  transition: transform 0.3s;
  font-size: 12px;
  color: #000000;
}

.arrow.rotated {
  transform: rotate(90deg);
}

/* 展开/收起动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

/* 优化hover效果 */
.nav-section-title:hover,
.sub-section-title:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* 优化折叠状态 */
.sidebar.collapsed .arrow-wrapper {
  margin-left: 0;
}

.sidebar.collapsed .nav-section-title,
.sidebar.collapsed .sub-section-title {
  padding: 12px 8px;
  justify-content: center;
}

/* 添加新的样式 */
.router-view-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
  padding: 20px;
  margin-top: 20px;
}

/* 表格容器样式 */
:deep(.table-container) {
  width: 100%;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin: 0 auto;
}

:deep(.table-header) {
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.table-content) {
  padding: 0 24px;
  width: 100%;
}

:deep(.table-footer) {
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
}

/* 响应式布局 */
@media screen and (max-width: 1440px) {
  .content-wrapper {
    max-width: 1200px;
  }
}

@media screen and (max-width: 1200px) {
  .content-wrapper {
    max-width: 1000px;
    padding: 16px;
    margin-left: 200px;
  }
}

@media screen and (max-width: 992px) {
  .content-wrapper {
    max-width: 800px;
    padding: 12px;
    margin-left: 200px;
  }
}

@media screen and (max-width: 768px) {
  .main-content {
    padding-left: 0;
  }
  
  .content-wrapper {
    max-width: 100%;
    padding: 10px;
    margin-left: 0;
  }
  
  .sidebar {
    transform: translateX(-100%);
  }
  
  .sidebar.collapsed {
    transform: translateX(0);
  }
}

.menu-container {
  width: 200px;
  height: 100vh;
  background: linear-gradient(180deg, #1e88e5 0%, #1565c0 100%);
  color: white;
  padding: 0;
  overflow-y: auto;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
}

.menu-item {
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #000000;
  position: relative;
}

.menu-item:hover {
  background: #ffffff;
  color: #000000;
}

.menu-item.active {
  background: #ffffff;
  color: #000000;
}

.menu-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: white;
}

.submenu {
  background: #ffffff;
  overflow: hidden;
  transition: all 0.3s ease;
}

.submenu-item {
  padding: 10px 20px 10px 40px;
  color: #000000;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #ffffff;
}

.submenu-item:hover,
.submenu-item.active {
  background: #ffffff;
  color: #000000;
}

.menu-header {
  padding: 20px;
  font-size: 24px;
  font-weight: bold;
  color: white;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 滚动条样式 */
.menu-container::-webkit-scrollbar {
  width: 6px;
}

.menu-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

.menu-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

.menu-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

/* 图标样式 */
.menu-item i {
  font-size: 18px;
  width: 24px;
  text-align: center;
}

/* 展开/收起箭头 */
.arrow {
  margin-left: auto;
  transition: transform 0.3s ease;
}

.arrow.expanded {
  transform: rotate(90deg);
}

/* Logo样式 */
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.1);
}

.logo img {
  width: 32px;
  height: 32px;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  color: white;
}

/* 统一所有菜单项的字体大小 */
.nav-section-title,
.nav-items a,
.sub-menu-title,
.sub-nav-items a,
.submenu-item,
.sub-section-title,
.nav-section-content span,
.sub-nav-items li a,
.submenu .sub-menu-title,
.submenu-item a {
  font-size: 14px !important;
}

/* 移除可能影响字体大小的其他样式 */
.sub-nav-items {
  background: #ffffff;
  color: #000000;
  padding: 4px 0;
  margin-left: 0;
}

.sub-nav-items li {
  font-size: 14px !important;
}

.sub-nav-items li a {
  padding: 8px 16px 8px 40px;
  color: #000000;
  font-size: 14px !important;
}

.submenu-item {
  padding: 10px 16px 10px 40px;
  color: #000000;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #ffffff;
  font-size: 14px !important;
}

/* 确保子菜单标题也是相同大小 */
.sub-menu-title span,
.submenu-item span {
  font-size: 14px !important;
}

/* 移除任何可能的缩放 */
* {
  text-size-adjust: none;
  -webkit-text-size-adjust: none;
  -moz-text-size-adjust: none;
  -ms-text-size-adjust: none;
}
</style> 