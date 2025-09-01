import pandas as pd
class order:
    def __init__(self):
        '''
        交易记录函数
        '''
        self.order=pd.DataFrame()
        self.order['时间']=None
        self.order['证券代码']=None
        self.order['名称']=None
        self.order['交易数量']=None
        self.order['买入价']=None
        self.order['卖出价']=None
        self.order['交易时间']=None
        self.order['交易状态']=None
        self.order['交易备注']=None
    def get_order_data(self):
        '''
        获取交易记录数据
        '''
        return self.order
    def write_to_trader_log(self,log=pd.DataFrame()):
        '''
        写入交易记录
        now_date=''.join(str(datetime.now())[:10].split('-'))
        log=pd.DataFrame()
        log['时间']=[now_date]
        log['证券代码']=[stock]
        log['名称']=[stock]
        log['交易数量']=[amount]
        log['买入价']=[buy_price_dict.get(stock,None)]
        log['卖出价']=[price]
        log['交易时间']=[str(datetime.now())]
        log['交易状态']=['sell']
        log['交易备注']=['卖出失败:可用数量不足']
        '''
        trader_log=self.order
        trader_log=pd.concat([trader_log,log],ignore_index=True)
        trader_log=trader_log.drop_duplicates(subset=['时间','证券代码',
                '交易状态','交易时间','交易数量','买入价'],keep='last')
        self.order=trader_log
        return self.order
    def write_strategy_tarder_log(
            self,date='',
            trader_date='',
            stock='',
            maker='策略备注'):
        '''
        策略自定义日志
        '''
        log=pd.DataFrame()
        log['时间']=[date]
        log['证券代码']=[stock]
        log['名称']=[None]
        log['交易数量']=[None]
        log['买入价']=[None]
        log['卖出价']=[None]
        log['交易时间']=[str(trader_date)]
        log['交易状态']=[None]
        log['交易备注']=[maker]
        trader_log=self.order
        trader_log=pd.concat([trader_log,log],ignore_index=True)
        trader_log=trader_log.drop_duplicates(subset=['时间','证券代码',
                '交易状态','交易时间','交易数量','买入价'],keep='last')
        self.order=trader_log
        return self.order
    def re_order_data(self):
        '''
        重新设置委托记录
        '''
        self.order=pd.DataFrame()
        self.order['时间']=None
        self.order['证券代码']=None
        self.order['名称']=None
        self.order['交易数量']=None
        self.order['买入价']=None
        self.order['卖出价']=None
        self.order['交易时间']=None
        self.order['交易状态']=None
        self.order['交易备注']=None
        return self.order