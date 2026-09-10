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
                    path: '/research-terminal',
                    name: 'ResearchTerminal',
                    component: () => import('@/views/ResearchTerminal.vue')
                }
            ]
        }
    ]
})

export default router
