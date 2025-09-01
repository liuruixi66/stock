from .qmt_trader import QMTTrader
from .ths_trader import THSTrader

class Trader:
    def buy(self, stock_id, amount):
        raise NotImplementedError

    def sell(self, stock_id, amount):
        raise NotImplementedError

def get_trader(config):
    trader_tool = config.get("交易系统")
    if trader_tool == "qmt":
        return QMTTrader(config)
    elif trader_tool == "ths":
        return THSTrader(config)
    else:
        raise ValueError(f"Unknown trader tool: {trader_tool}")
