import pandas as pd
class position:
    def __init__(self,):
        '''
        持股数据
        '''
        self.position=pd.DataFrame()
        self.position['证券代码']=None
        self.position['名称']=None
        self.position['股票余额']=None
        self.position['可用余额']=None
        self.position['参考成本价']=None
        self.position['卖出价']=None
        self.position['市价']=None
        self.position['参考盈亏']=None
        self.position['参考盈亏比']=None
        self.position['当日盈亏']=None
        self.position['当日盈亏比']=None
        self.position['市值']=None
        self.position['参考卖出盈亏']=None
        self.position['当日卖出盈亏']=None
        self.position['持股天数']=None
        self.position['交易状态']=None
        self.position['买入时间']=None
        self.position['卖出时间']=None
        self.position['时间']=None
    def get_position_data(self):
        '''
        获取持股数据
        '''
        return self.position
    def get_stock_position(self,stock='513100'):
        '''
        获取个股的持股情况
        '''
        df=self.position()
        df=df[df['证券代码']==stock]
        return df
    def re_position_data(self):
        '''
        清空持股数据
        '''
        self.position=pd.DataFrame()
        self.position['证券代码']=None
        self.position['名称']=None
        self.position['股票余额']=None
        self.position['可用余额']=None
        self.position['参考成本价']=None
        self.position['卖出价']=None
        self.position['市价']=None
        self.position['参考盈亏']=None
        self.position['参考盈亏比']=None
        self.position['当日盈亏']=None
        self.position['当日盈亏比']=None
        self.position['市值']=None
        self.position['参考卖出盈亏']=None
        self.position['当日卖出盈亏']=None
        self.position['持股天数']=None
        self.position['交易状态']=None
        self.position['买入时间']=None
        self.position['卖出时间']=None
        self.position['更新日期']=None
        return self.position()
    def get_stock_cost_price(self,stock='513100'):
        '''
        获取股票的成本价
        '''
        if self.position.shape[0]>0:
            stock_list=self.position['证券代码'].tolist()
            if stock in stock_list:
                df=self.position[self.position['证券代码']==stock]
                cost_price=df['参考成本价'].tolist()[-1]
            else:
                cost_price=0
        else:
            cost_price=0
        return cost_price
    def get_stock_maker_price(self,stock='513100'):
        '''
        获取持股的市价
        '''
        if self.position.shape[0]>0:
            stock_list=self.position['证券代码'].tolist()
            if stock in stock_list:
                df=self.position[self.position['证券代码']==stock]
                maker_price=df['市价'].tolist()[-1]
            else:
                maker_price=0
        else:
            maker_price=0
        return maker_price

    

    

        
   
   
   
           
           