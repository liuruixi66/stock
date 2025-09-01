from xg_tdx_func.xg_tdx_func import *
class small_fruit_high_frequency_measurement_line:
    '''
    小果高频量线
    '''
    def __init__(self,df):
        '''
        小果高频量线
        '''
        self.df=df
    def small_fruit_high_frequency_measurement_line(self):
        '''
        超准赋值:收盘价的20日指数移动平均
        输出股:如果收盘价的1日简单移动平均>=超准,返回超准,否则返回无效数,画红色,线宽为4
        输出币:如果收盘价的2日简单移动平均<超准,返回超准,否则返回无效数,画绿色,线宽为2
        输出均:收盘价*成交量(手)的240日累和/成交量(手)的240日累和,画黄色,DOTLINE,线宽为1

        '''
        df=self.df
        CLOSE=df['close']
        C=df['close']
        LOW=df['low']
        L=df['low']
        HIGH=df['high']
        H=df['high']
        OPEN=df['open']
        O=df['open']
        volume=df['volume']
        V=df['volume']
        超准=EMA(C,20)
        df['超准']=超准
        股=IF(MA(C,1)>=超准,超准,0)
        df['股']=股
        币=IF(MA(C,2)<超准,超准,0)
        df['币']=币
        均=SUM(C*V,240)/SUM(V,240)
        df['均']=均
       
        df['买']=IF(AND(REF(股,1)==0,股>0),'买',None)
        df['卖']=IF(AND(REF(股,1)>0,股==0),'卖',None)
        stats_list=[]
        for buy,sell in zip(df['买'].tolist(),df['卖'].tolist()):
            if buy=='买':
                stats_list.append('买')
            elif sell=='卖':
                stats_list.append('卖')
            else:
                stats_list.append(None)
        df['stats']=stats_list
        
        df['连续交易']=df['stats'].fillna(method='ffill')
        return df
if __name__=='__main__':
    from trader_tool.unification_data import unification_data
    data=unification_data(trader_tool='ths')
    data=data.get_unification_data()
    df=data.get_hist_data_em(stock='511090',data_type='1')
    modes=small_fruit_high_frequency_measurement_line(df=df)
    result=modes.small_fruit_high_frequency_measurement_line()
    print(result)
    result.to_excel(r'数据.xlsx')

