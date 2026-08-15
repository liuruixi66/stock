from django.urls import path
from . import trading_views
import cache_views

urlpatterns = [
    path('api/market/quotes/', trading_views.market_quotes, name='market_quotes'),
    path('api/paper/accounts/', trading_views.accounts, name='paper_accounts'),
    path('api/paper/orders/', trading_views.orders, name='paper_orders'),
    path('api/paper/accounts/<int:account_id>/summary/', trading_views.account_summary, name='paper_account_summary'),
    path('api/paper/accounts/<int:account_id>/analytics/', trading_views.account_analytics, name='paper_account_analytics'),
    path('api/research/backtest/', trading_views.research_backtest, name='research_backtest'),
    path('api/research/runs/', trading_views.research_runs, name='research_runs'),
    path('api/research/runs/<int:run_id>/', trading_views.research_run_detail, name='research_run_detail'),
    path('api/watchlist/', trading_views.watchlist, name='watchlist'),
    path('api/watchlist/<int:item_id>/', trading_views.watchlist_item, name='watchlist_item'),
    path('api/cache/backtest-details/', cache_views.get_backtest_details_cache, name='cache_backtest_details'),
    path('api/cache/status/', cache_views.get_cache_status, name='cache_status'),
]
