import pandas as pd
from tdx_strategy_models.small_fruit_band_trading import small_fruit_band_trading
class user_def_factor:
    def __init__(self,df):
        '''
        自定义因子交易
        '''
        self.df=df
    def mean_line_models_buy(self,x1=3,x2=5,x3=10,x4=15,x5=20):
        '''
        均线模型
        趋势模型
        '''
        df=self.df
        df1=pd.DataFrame()
        df1['date']=df['date']
        df1['x1']=df['close'].rolling(window=x1).mean()
        df1['x2']=df['close'].rolling(window=x2).mean()
        df1['x3']=df['close'].rolling(window=x3).mean()
        df1['x4']=df['close'].rolling(window=x4).mean()
        df1['x5']=df['close'].rolling(window=x5).mean()
        score=0
        #加分的情况
        mean_x1=df1['x1'].tolist()[-1]
        mean_x2=df1['x2'].tolist()[-1]
        mean_x3=df1['x3'].tolist()[-1]
        mean_x4=df1['x4'].tolist()[-1]
        mean_x5=df1['x5'].tolist()[-1]
        #相邻2个均线进行比较
        if mean_x1>=mean_x2:
            score+=25
        if mean_x2>=mean_x3:
            score+=25
        if mean_x3>=mean_x4:
            score+=25
        if mean_x4>=mean_x5:
            score+=25
        return score
    def standing_average_line(self,n=5):
        '''
        站上均线分析
        '''
        df=self.df
        df['n']=df['close'].rolling(n).mean()
        line=df['n'].tolist()[-1]
        price=df['close'].tolist()[-1]
        if price>=line:
            return 1
        else:
            return 0
    def cacal_degree_of_deviation(self,n=5):
        '''
        计算偏离度
        '''
        hist=self.df
        price=hist['close'].tolist()[-1]
        hist['mean_line']=hist['close'].rolling(window=n).mean()
        line=hist['mean_line'].tolist()[-1]
        deviation=((price-line)/line)*100
        return deviation
    def small_fruit_band_trading_buy(self):
        '''
        波段买
        '''
        models=small_fruit_band_trading(df=self.df)
        models=models.small_fruit_band_trading()
        models['stats']=models['stats'].fillna(method='ffill')
        buy=models['stats'].tolist()[-1]
        if buy=='买':
            return 1
        else:
            return 0
    def small_fruit_band_trading_sell(self):
        '''
        波段买
        '''
        models=small_fruit_band_trading(df=self.df)
        models=models.small_fruit_band_trading()
        models['stats']=models['stats'].fillna(method='ffill')
        buy=models['stats'].tolist()[-1]
        if buy=='卖':
            return 1
        else:
            return 0
    def down_average_line(self,n=5):
        '''
        跌破均线分析
        '''
        df=self.df
        df['n']=df['close'].rolling(n).mean()
        line=df['n'].tolist()[-1]
        price=df['close'].tolist()[-1]
        if price<line:
            return 1
        else:
            return 0
    
    
