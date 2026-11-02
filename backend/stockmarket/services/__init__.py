"""股票业务服务的稳定入口。

HTTP 视图和管理命令应从本包调用账户、订单与研究工作流；底层实现可在
`trading`、`research` 等模块内部调整，而无需让调用方依赖具体算法或适配器。
"""

from .research import (
    default_research_range,
    run_leaky_forecast_research,
    run_portfolio_research,
    run_sma_research,
)
from .trading import (
    account_analytics,
    account_data,
    account_summary,
    cancel_account_order,
    create_trading_account,
    order_data,
    place_account_order,
    sync_trading_account,
    trading_capabilities,
)

__all__ = [
    'account_analytics',
    'account_data',
    'account_summary',
    'cancel_account_order',
    'create_trading_account',
    'default_research_range',
    'order_data',
    'place_account_order',
    'run_leaky_forecast_research',
    'run_portfolio_research',
    'run_sma_research',
    'sync_trading_account',
    'trading_capabilities',
]
