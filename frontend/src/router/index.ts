import { createRouter, createWebHistory } from 'vue-router'
import DefaultLayout from '@/layouts/DefaultLayout.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            component: DefaultLayout,
            children: [
                {
                    path: '',
                    component: () => import('@/views/Index.vue')
                },
                {
                    path: 'menu-layout',
                    component: () => import('@/views/MenuLayoutRefactored.vue')
                },
                {
                    path: 'tables',
                    children: [
                        { path: 'stock-spot', component: () => import('@/views/tables/StockSpot.vue') },
                        { path: 'stock-fund-flow', component: () => import('@/views/tables/StockFundFlow.vue') },
                        { path: 'stock-bonus', component: () => import('@/views/tables/StockBonus.vue') },
                        { path: 'stock-top', component: () => import('@/views/tables/StockTop.vue') },
                        { path: 'stock-blocktrade', component: () => import('@/views/tables/StockBlocktrade.vue') },
                        { path: 'industry-fund-flow', component: () => import('@/views/tables/IndustryFundFlow.vue') },
                        { path: 'concept-fund-flow', component: () => import('@/views/tables/ConceptFundFlow.vue') },
                        { path: 'etf-spot', component: () => import('@/views/tables/EtfSpot.vue') }
                    ]
                },
                {
                    path: '/technical-indicator-display',
                    name: 'TechnicalIndicatorDisplay',
                    component: () => import('@/views/TechnicalIndicatorDisplay.vue')
                },
                {
                    path: '/earnings-overview',
                    name: 'EarningsOverview',
                    component: () => import('@/views/EarningsOverview.vue')
                },
                {
                    path: '/transaction-details',
                    name: 'TransactionDetails',
                    component: () => import('@/views/TransactionDetails.vue')
                },
                {
                    path: '/backtest-details',
                    name: 'BacktestDetails',
                    component: () => import('@/views/BacktestDetails.vue')
                },
                {
                    path: '/stock-realtime',
                    name: 'StockRealtime',
                    component: () => import('@/components/StockRealtime.vue')
                },
                {
                    path: '/research-terminal',
                    name: 'ResearchTerminal',
                    component: () => import('@/views/ResearchTerminal.vue')
                }
            ]
        }
    ]
})

export default router
