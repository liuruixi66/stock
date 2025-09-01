from xg_tdx_func.xg_tdx_func import *
from trader_tool.unification_data import unification_data
class small_fruit_band_gold_mining:
    def __init__(self,df):
        '''
        小果波段掘金
        '''
        self.df=df
    def small_fruit_band_gold_mining(self):
        '''
        输出MA3:收盘价的3日简单移动平均
        输出MA5:收盘价的5日简单移动平均,画黄色
        输出MA10:收盘价的10日简单移动平均
        输出MA15:收盘价的15日简单移动平均,画白色
        输出MA20:收盘价的20日简单移动平均,画绿色,POINTDOT
        输出MA30:收盘价的30日简单移动平均,画红色,POINTDOT
        A1赋值:如果收盘价>=MA3,返回1,否则返回-1
        A2赋值:如果收盘价>=MA5,返回1,否则返回-1
        A3赋值:如果收盘价>=MA10,返回1,否则返回-1
        A4赋值:如果MA3>=1日前的MA3,返回1,否则返回-1
        A5赋值:如果MA5>=1日前的MA5,返回1,否则返回-1
        A6赋值:如果MA10>=1日前的MA10,返回1,否则返回-1
        QUSHIX赋值:(A1+A2+A3+A4+A5+A6)/6*100,画青色,线宽为3
        X1赋值:(收盘价+最低价+最高价)/3
        X2赋值:X1的3日指数移动平均
        X3赋值:X2的5日指数移动平均
        当满足条件X2上穿X3时,在最低价*0.98位置书写文字
        当满足条件X3上穿X2时,在最高价*1.02位置书写文字
        当满足条件X2>=X3时,在最低价和最高价位置之间画柱状线,宽度为0,0不为0则画空心柱.,画红色
        当满足条件X2<X3时,在最低价和最高价位置之间画柱状线,宽度为0,0不为0则画空心柱.,画绿色
        当满足条件X2上穿X3时,在开盘价和收盘价位置之间画柱状线,宽度为3,0不为0则画空心柱.,画黄色
        当满足条件X3上穿X2时,在开盘价和收盘价位置之间画柱状线,宽度为3,0不为0则画空心柱.,画蓝色
        当满足条件QUSHIX>=100ANDMA3>1日前的MA3AND(收盘价-开盘价)/开盘价*100>5ANDCLOSE>MA3时,在最低价*0.99位置书写文字,画洋红色
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
        MA3=MA(C,3)
        MA5=MA(C,5)
        MA10=MA(C,10)
        MA15=MA(C,15)
        MA20=MA(C,20)
        MA30=MA(C,30)
        A1=IF(C>=MA3,1,-1)
        A2=IF(C>=MA5,1,-1)
        A3=IF(C>=MA10,1,-1)
        A4=IF(MA3>=REF(MA3,1),1,-1)
        A5=IF(MA5>=REF(MA5,1),1,-1)
        A6=IF(MA10>=REF(MA10,1),1,-1)
        QUSHIX=(A1+A2+A3+A4+A5+A6)/6*100
        X1=(C+L+H)/3
        X2=EMA(X1,3)
        X3=EMA(X2,5)
        #DRAWTEXT(CROSS(X2,X3),L*0.98,'B');
        df['B']=CROSS(X2,X3)
        #DRAWTEXT(CROSS(X3,X2),H*1.02,'S');
        df['S']=CROSS(X3,X2)
        #STICKLINE(X2>=X3,LOW,HIGH,0,0),COLORRED;
        #STICKLINE(X2>=X3,CLOSE,OPEN,3,1),COLORRED;
        df['红色']=X2>=X3
        #STICKLINE(X2<X3,LOW,HIGH,0,0),COLORGREEN;
        #STICKLINE(X2<X3,CLOSE,OPEN,3,1),COLORGREEN;
        df['绿色']=X2<X3
        #STICKLINE(CROSS(X2,X3),OPEN,CLOSE,3,0),COLORYELLOW;
        df['黄色']=CROSS(X2,X3)
        #STICKLINE(CROSS(X3,X2),OPEN,CLOSE,3,0),COLORBLUE;
        df['蓝色']=CROSS(X3,X2)
        #DRAWTEXT(QUSHIX>=100 AND MA3>REF(MA3,1) AND (CLOSE-OPEN)/OPEN*100>5 AND CLOSE>MA3,L*0.99,'★'),COLORMAGENTA
        df['星']=AND(AND(AND(QUSHIX>=100,MA3>REF(MA3,1)),(CLOSE-OPEN)/OPEN*100>5),CLOSE>MA3)
        return df
if __name__=='__main__':
    data=unification_data(trader_tool='ths')
    data=data.get_unification_data()
    df=data.get_hist_data_em(stock='513100')
    modes=small_fruit_band_gold_mining(df=df)
    result=modes.small_fruit_band_gold_mining()
    print(result)
    result.to_excel(r'数据.xlsx')