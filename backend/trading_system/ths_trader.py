from .trader_frame import Trader

class THSTrader(Trader):
    def __init__(self, config):
        # Initialize THS connection here
        print("THS Trader Initialized")

    def buy(self, stock_id, amount):
        print(f"THS: Buying {amount} of {stock_id}")
        # THS specific API call

    def sell(self, stock_id, amount):
        print(f"THS: Selling {amount} of {stock_id}")
        # THS specific API call
