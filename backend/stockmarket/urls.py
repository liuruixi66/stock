from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views
from . import trading_views
# 导入缓存视图
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import cache_views

urlpatterns = [
    path('api/market/quotes/', trading_views.market_quotes, name='market_quotes'),
    path('api/paper/accounts/', trading_views.accounts, name='paper_accounts'),
    path('api/paper/orders/', trading_views.orders, name='paper_orders'),
    path('api/paper/accounts/<int:account_id>/summary/', trading_views.account_summary, name='paper_account_summary'),
    path('api/stocks/', csrf_exempt(views.stock_list), name='stock_list'),
    path('api/stock-data/', csrf_exempt(views.stock_data), name='stock_data'),
    path('api/indicators/', csrf_exempt(views.indicators), name='indicators'),
    path('api/backtest/', csrf_exempt(views.backtest), name='backtest'),
    path('api/backtest/run/', csrf_exempt(views.backtest_run), name='backtest_run'),
    path('api/backtest-results/', csrf_exempt(views.backtest_results), name='backtest_results'),
    path('api/compare/', csrf_exempt(views.compare), name='compare'),
    
    # 缓存API路由 - 用于前端页面数据读取
    path('api/cache/backtest-details/', cache_views.get_backtest_details_cache, name='cache_backtest_details'),
    path('api/cache/earnings-overview/', cache_views.get_earnings_overview_cache, name='cache_earnings_overview'),
    path('api/cache/transaction-details/', cache_views.get_transaction_details_cache, name='cache_transaction_details'),
    path('api/cache/status/', cache_views.get_cache_status, name='cache_status'),
]
