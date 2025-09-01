import { createRouter, createWebHistory } from 'vue-router'
import MenuLayoutRefactored from '@/views/MenuLayoutRefactored.vue'
import MenuLayout from '@/views/MenuLayout.vue'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import StockSpot from '@/views/tables/StockSpot.vue'
import StockFundFlow from '@/views/tables/StockFundFlow.vue'
import StockBonus from '@/views/tables/StockBonus.vue'
import StockBlocktrade from '@/views/tables/StockBlocktrade.vue'
import IndustryFundFlow from '@/views/tables/IndustryFundFlow.vue'
import ConceptFundFlow from '@/views/tables/ConceptFundFlow.vue'
import EtfSpot from '@/views/tables/EtfSpot.vue'
import StockTop from '@/views/tables/StockTop.vue'
import Index from '@/views/Index.vue'
import TechnicalIndicatorDisplay from '@/views/TechnicalIndicatorDisplay.vue'
import StockRealtime from '@/components/StockRealtime.vue'
import EarningsOverview from '@/views/EarningsOverview.vue'
import TransactionDetails from '@/views/TransactionDetails.vue'
import BacktestDetails from '@/views/BacktestDetails.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            component: DefaultLayout,
            children: [
                {
                    path: '',
                    component: Index
                },
                {
                    path: 'menu-layout',
                    component: MenuLayoutRefactored
                },
                {
                    path: 'menu-layout-old',
                    component: MenuLayout
                },
                {
                    path: 'tables',
                    children: [
                        { path: 'stock-spot', component: StockSpot },
                        { path: 'stock-fund-flow', component: StockFundFlow },
                        { path: 'stock-bonus', component: StockBonus },
                        { path: 'stock-top', component: StockTop },
                        { path: 'stock-blocktrade', component: StockBlocktrade },
                        { path: 'industry-fund-flow', component: IndustryFundFlow },
                        { path: 'concept-fund-flow', component: ConceptFundFlow },
                        { path: 'etf-spot', component: EtfSpot }
                    ]
                },
                {
                    path: '/technical-indicator-display',
                    name: 'TechnicalIndicatorDisplay',
                    component: TechnicalIndicatorDisplay
                },
                {
                    path: '/earnings-overview',
                    name: 'EarningsOverview',
                    component: EarningsOverview
                },
                {
                    path: '/transaction-details',
                    name: 'TransactionDetails',
                    component: TransactionDetails
                },
                {
                    path: '/backtest-details',
                    name: 'BacktestDetails',
                    component: BacktestDetails
                },
                {
                    path: '/stock-realtime',
                    name: 'StockRealtime',
                    component: StockRealtime
                }
            ]
        }
    ]
})

export default router
