import pandas as pd
from trader_tool.shape_analysis import shape_analysis
from trader_tool.analysis_models import analysis_models
from tdx_strategy_models.six_pulse_excalibur_hist import six_pulse_excalibur_hist
from tdx_strategy_models.small_fruit_band_trading import small_fruit_band_trading
import os
class user_def_models_sell:
    def __init__(self,df):
        '''
        分析模型
        自定义交易算法卖出
        '''
        self.df=df
        self.path=os.path.dirname(os.path.abspath(__file__))
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
        if price<line:
            return 1
        else:
            return 0
    def cacal_price_limit(self):
        '''
        计算涨跌幅
        '''
        df=self.df
        zdf=df['涨跌幅'].tolist()[-1]
        return zdf
    def cacal_return_N(self,n=5):
        '''
        N日收益
        '''
        df=self.df
        zdf=df['涨跌幅'].tolist()[-n:]
        return sum(zdf)
    def cacal_diurnal_cycle(self):
        '''
        计算日周期
        '''
        df=self.df
        models=six_pulse_excalibur_hist(df=df)
        df=models.six_pulse_excalibur_hist()
        signal=df['signal'].tolist()[-1]
        return signal
    def cacal_diurnal_cycle_amount(self,n=10):
        '''
        计算日周期数据
        '''
        df=self.df
        models=six_pulse_excalibur_hist(df=df)
        df=models.six_pulse_excalibur_hist()
        signal=df['signal'].tolist()[-n:]
        return sum(signal)
    def cacal_small_fruit_band_trading(self):
        '''
        波段交易
        '''
        df=self.df
        models=small_fruit_band_trading(df=df)
        result=models.small_fruit_band_trading()
        stats=result['stats'].tolist()[-1]
        if stats=='卖':
            return 1
        else:
            return 0
    def cacal_small_fruit_band_trading_aount(self,n=10):
        '''
        波段交易数量
        '''
        df=self.df
        models=small_fruit_band_trading(df=df)
        result=models.small_fruit_band_trading()
        stats=result['stats'].tolist()[-n:]
        return stats.count('卖')   
    
    
    
    


        
    


            


    