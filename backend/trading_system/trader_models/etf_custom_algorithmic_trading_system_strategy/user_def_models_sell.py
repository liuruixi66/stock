import pandas as pd
from trader_tool.shape_analysis import shape_analysis
from trader_tool.analysis_models import analysis_models
from tdx_strategy_models.six_pulse_excalibur_hist import six_pulse_excalibur_hist
import os
class user_def_models_sell:
    def __init__(self,df):
        '''
        分析模型
        自定义交易算法卖出
        '''
        self.df=df
        self.path=os.path.dirname(os.path.abspath(__file__))
    def mean_line_models_sell(self,x1=3,x2=5,x3=10,x4=15,x5=20):
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
    def down_average_line(self,n=5):
        '''
        跌破均线
        '''
        df=self.df
        df['n']=df['close'].rolling(n).mean()
        line=df['n'].tolist()[-1]
        price=df['close'].tolist()[-1]
        if price<line:
            return 1
        else:
            return 0
    def cacal_stock_premium_rate(self,stock='513100'):
        '''
        计算溢价率
        '''
        df=pd.read_excel(r'{}\全部ETF\全部ETF.xlsx'.format(self.path))
        yjl_dict=dict(zip(df['证券代码'],df['溢价率']))
        yjl=yjl_dict.get(stock,0)
        return yjl
    def cacal_price_limit(self):
        '''
        计算涨跌幅
        '''
        df=self.df
        zdf=df['涨跌幅'].tolist()[-1]
        return zdf
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
    def cacal_diurnal_cycle(self):
        '''
        计算日周期
        '''
        df=self.df
        models=six_pulse_excalibur_hist(df=df)
        df=models.six_pulse_excalibur_hist()
        signal=df['signal'].tolist()[-1]
        return signal
    def cacal_diurnal_cycle_amount(self,n=2):
        '''
        计算日周期数量
        '''
        df=self.df
        models=six_pulse_excalibur_hist(df=df)
        df=models.six_pulse_excalibur_hist()
        signal=df['signal'].tolist()[-n:]
        return sum(signal)
    def cacal_return_N(self,n=3):
        '''
        N日收益
        '''
        df=self.df
        zdf=df['涨跌幅'].tolist()[-n:]
        return sum(zdf)
    
    


        
    


            


    