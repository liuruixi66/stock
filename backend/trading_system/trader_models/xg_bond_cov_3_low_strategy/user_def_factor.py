import empyrical
from finta import TA
from trader_tool.stock_index_library import stock_index_library
from trader_tool.unification_data import unification_data
class user_def_factor:
    def __init__(self,df='',index_df='',all=False):
        '''
        自定义因子
        '''
        self.df=df
        self.index_df=index_df
        self.all=all
        self.stock_index_library=stock_index_library(df=self.df,index_df=self.index_df,all=self.all)
    def return_5(self):
        '''
        5日收益
        '''
        name='5日收益'
        try:
            return_5=self.df['close'].pct_change()[-5:].sum()
            return name,return_5
        except:
            return name,None
    def ma_gold_fork(self):
        '''
        均线金叉
        '''
        name='均线金叉'
        try:
            name1,result=self.stock_index_library.ema_gold_fork()
            if result==True:
                return name,1
            else:
                return name,0
        except:
            return name,None
    def macd_gold_fork(self):
        '''
        macd金叉
        '''
        name='macd金叉'
        try:
            name1,result=self.stock_index_library.macd_gold_fork()
            if result==True:
                return name,1
            else:
                return name,0
        except:
            return name,None
    

            
    

        


