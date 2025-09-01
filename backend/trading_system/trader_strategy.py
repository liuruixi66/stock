import os
import importlib
import schedule
import time
import json
from trading_system.trader_frame import get_trader

class TradingSystem:
    def __init__(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.trader = get_trader(self.config)
        self.strategies = self.load_strategies()

    def load_strategies(self):
        strategies = []
        # 从配置中获取启用的策略
        enabled_strategies = self.config.get("模型策略", {})
        for strategy_name, strategy_desc in enabled_strategies.items():
            try:
                # 假设策略文件名与run_function同名
                module_name = f"trading_system.strategies.{strategy_name}"
                strategy_module = importlib.import_module(module_name)
                # 传递trader和策略特定配置
                strategy_config = self.config.get("多策略资金设置", {}).get(strategy_name, {})
                strategies.append(strategy_module.Strategy(self.trader, strategy_config))
                print(f"Loaded strategy: {strategy_desc}")
            except ImportError:
                print(f"Warning: Could not find or load strategy module for '{strategy_name}'")
        return strategies


    def run_custom_trading_modules(self):
        print("Running custom trading modules...")
        for strategy in self.strategies:
            strategy.run()

    def start(self):
        print("Starting trading system...")
        schedule.every(10).seconds.do(self.run_custom_trading_modules)
        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    system = TradingSystem('trading_system/trader_config.json')
    system.start()
