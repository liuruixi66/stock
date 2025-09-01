from xg_tdx_func.xg_tdx_func import *
class small_fruit_band_trading_hist_trader:
    '''
    小果波段交易高频T0
    '''
    def __init__(self,df):
        '''
        小果波段交易高频T0
        '''
        self.df=df
    def small_fruit_band_trading_hist_trader(self):
        '''
        N1赋值:5
        N2赋值:5
        N3赋值:3
        MA_1赋值:3
        MA_2赋值:5
        BUY_AMOUNT_N赋值:2
        SELL_AMOUNT_N赋值:3
        ABC1赋值:(((最高价 + 最低价)+(收盘价*2)) / 4)
        ABC3赋值:ABC1的N1日指数移动平均
        ABC4赋值:ABC1的N1日估算标准差
        ABC5赋值:((ABC1 - ABC3)*100) / ABC4
        ABC6赋值:ABC5的N2日指数移动平均
        RK7赋值:ABC6的N1日指数移动平均
        UP赋值:(ABC6的10日指数移动平均+(100 / 2)) - 5,画红色
        DOWN赋值:UP的N3日指数移动平均
        ACB1赋值:DOWN的N3日指数移动平均
        ACB2赋值:ACB1的N3日指数移动平均,画绿色
        ACB3赋值:ACB2的N3日指数移动平均
        ACB4赋值:ACB3的N3日指数移动平均
        当满足条件UP<1日前的UP时,在UP和UP的3日简单移动平均位置之间画柱状线,宽度为5,0不为0则画空心柱.,画蓝色
        当满足条件UP>1日前的UP时,在UP和UP的3日指数移动平均位置之间画柱状线,宽度为5,0不为0则画空心柱.,画洋红色
        输出MA1:UP的MA_1日简单移动平均
        输出均线:UP的MA_2日简单移动平均
        BUY_AMOUNT赋值:条件连续成立次数
        SELL_AMOUNT赋值:条件连续成立次数
        当满足条件UP>1日前的UPANDREF(UP,1)<2日前的UPANDSELL_AMOUNT>=SELL_AMOUNT_N时,在UP位置书写文字,画红色
        当满足条件UP<1日前的UPANDREF(UP,1)>2日前的UPANDBUY_AMOUNT>=BUY_AMOUNT_N时,在UP位置书写文字 ,画绿色

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
        N1=5
        N2=9
        N3=7
        MA_1=3
        MA_2=5
        BUY_AMOUNT_N=0
        SELL_AMOUNT_N=0
        ABC1=(((HIGH + LOW)+(CLOSE*2)) / 4)
        ABC3=EMA(ABC1,N1)
        ABC4=STD(ABC1,N1)
        ABC5=((ABC1 - ABC3)*100) / ABC4
        ABC6=EMA(ABC5,N2)
        RK7=EMA(ABC6,N1)
        UP=(EMA(ABC6,10)+(100 / 2)) - 5
        DOWN=EMA(UP,N3)
        ACB1=EMA(DOWN,N3)
        ACB2=EMA(ACB1,N3)
        ACB3=EMA(ACB2,N3)
        ACB4=EMA(ACB3,N3)
        #STICKLINE(UP < REF(UP,1),UP,MA(UP,3),5,0),COLORBLUE;
        #STICKLINE(UP > REF(UP,1),UP,EMA(UP,3),5,0),COLORMAGENTA;
        MA1=MA(UP,MA_1)
        MA2=MA(UP,MA_2)
        df['MA1']=MA1
        df['MA2']=MA2
        BUY_AMOUNT=BARSLASTCOUNT( REF(UP,1) > REF(UP,2))
        SELL_AMOUNT=BARSLASTCOUNT( REF(UP,1) < REF(UP,2))
        #DRAWTEXT(UP > REF(UP,1) AND  REF(UP,1) < REF(UP,2) AND SELL_AMOUNT>=SELL_AMOUNT_N,UP,'买'),COLORRED;
        #DRAWTEXT(UP < REF(UP,1)  AND  REF(UP,1) > REF(UP,2)  AND BUY_AMOUNT>=BUY_AMOUNT_N,UP,'卖') ,COLORGREEN;
        df['柱子']=IF(UP > REF(UP,1),'红色','蓝色')
        df['买']=IF(AND(AND(UP > REF(UP,1),REF(UP,1) < REF(UP,2)),SELL_AMOUNT>=SELL_AMOUNT_N),'买',None)
        df['卖']=IF(AND(AND(UP < REF(UP,1),REF(UP,1) > REF(UP,2)),BUY_AMOUNT>=BUY_AMOUNT_N),'卖',None)
        stats_list=[]
        for buy,sell in zip(df['买'].tolist(),df['卖'].tolist()):
            if buy=='买':
                stats_list.append('买')
            elif sell=='卖':
                stats_list.append('卖')
            else:
                stats_list.append(None)
        
        df['stats']=stats_list
        df['stats']=df['stats'].fillna(method='ffill')
        return df
if __name__=='__main__':
    from trader_tool.unification_data import unification_data
    data=unification_data(trader_tool='ths')
    data=data.get_unification_data()
    df=data.get_hist_data_em(stock='511130',data_type='5')
    modes=small_fruit_band_trading_hist_trader(df=df)
    result=modes.small_fruit_band_trading_hist_trader()
    print(result)
    result.to_excel(r'数据.xlsx')

