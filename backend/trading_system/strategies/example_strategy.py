import random

class Strategy:
    def __init__(self, trader):
        self.trader = trader

    def run(self):
        # This is a simple example strategy.
        # In a real system, you would analyze market data here.
        if random.choice([True, False]):
            self.trader.buy("000001", 100)
        else:
            self.trader.sell("000001", 100)
