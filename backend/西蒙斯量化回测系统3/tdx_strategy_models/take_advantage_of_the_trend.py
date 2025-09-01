from xg_tdx_func.xg_tdx_func import *
import pandas as pd
class take_advantage_of_the_trend:
    def __init__(self,df) :
        self.df=df
    def take_advantage_of_the_trend(self):
        '''
        【顺势黑马】套装指标简介：
        这是一个依托EXPMA基础上添加五线通道，并实时显示五线通道的价格，来判断K线所在位置的参考。
        1、“黄金金叉“显示阳线为黄，红色做多线持有；
        2、“死叉阴线”为蓝；绿线做空线休息；
        3、出信号放量突破时，均线多头排列可取，空排不取。
        ABC7:=EMA(C,7),COLORYELLOW,LINETHICK2;
        ABC14:=EMA(C,14),COLOR7FF00F,LINETHICK1 DOTLINE;
        ABC25:=EMA(C,25),COLORFF7F00,LINETHICK1 DOTLINE;
        ABCMA45:=EMA(C,45),COLORF00FFF,LINETHICK1 DOTLINE;
        MA5:=MA(C,5);{微信公众号:尊重市场}
        MA10:=MA(C,10);
        MA20:=MA(C,20);
        ABC:=ABC7>ABC14;
        STICKLINE(C/REF(C,1)>1.095,C,O,2,0),COLORYELLOW;
        DRAWTEXT(C/REF(C,1)>1.095,L*0.96,' ★强'),COLORLIRED;
        STICKLINE(HIGH<REF(LOW,0),HIGH,REF(LOW,0),10,0);
        STICKLINE(LOW>REF(HIGH,0) ,LOW,REF(HIGH,0),10,0);
        STICKLINE(C=O,H,L,0,0);
        STICKLINE((C=O)AND(C>REF(C,0)),C,O,8,0);
        STICKLINE((C=O)AND(C<REF(C,0)),C,O,8,0);
        STICKLINE(CROSS(ABC7,ABC14) AND ABC,CLOSE,OPEN,2,0),COLORMAGENTA;
        DRAWICON(CROSS(ABC7,ABC14) AND ABC,L*1.002,9);
        DRAWTEXT(CROSS(ABC7,ABC14) AND{微信公众号:尊重市场}ABC,L*0.98,' ★买'),COLORMAGENTA;
        STICKLINE(CROSS(ABC25,ABC7),CLOSE,OPEN,2,0),COLORBLUE;
        CC:=ABS((2*CLOSE+HIGH+LOW)/4-MA(CLOSE,20))/MA(CLOSE,20);
        DD:=DMA(CLOSE,CC);
        上轨:(1+7/100)*DD,DOTLINE,COLORGREEN;
        下轨:(1-7/100)*DD,DOTLINE,COLORGREEN;
        中轨:(上轨+下轨)/2,DOTLINE,COLORGREEN;
        FK:(1+14/100)*DD,DOTLINE,COLORGRAY;
        CD:(1-14/100)*DD,DOTLINE,COLORGRAY;
        DRAWNUMBER(ISLASTBAR,上轨,上轨),COLOR00FFFF;
        DRAWNUMBER(ISLASTBAR,下轨,下轨),COLORFFFF00;
        DRAWNUMBER(ISLASTBAR,中轨,中轨),COLOR00FF00;
        DRAWNUMBER(ISLASTBAR,FK,FK){微信公众号:尊重市场},COLOR0000FF;
        DRAWNUMBER(ISLASTBAR,CD,CD),COLORWHITE;
        上轨绿:IF(上轨>=REF(上轨,1),上轨,DRAWNULL),DOTLINE,COLORGREEN,LINETHICK1;
        上轨红:IF(上轨>=REF(上轨,1),上轨,DRAWNULL),DOTLINE COLORRED,LINETHICK1;
        中轨绿:IF(中轨>=REF(中轨,1), 中轨,DRAWNULL),DOTLINE,COLORGREEN,LINETHICK1;
        中轨红:IF(中轨>=REF(中轨,1), 中轨,DRAWNULL),DOTLINE COLORRED, LINETHICK1;
        下轨绿:IF(下轨>=REF(下轨,1), 下轨,DRAWNULL),DOTLINE,COLORGREEN,LINETHICK1;
        下轨红:IF(下轨>=REF(下轨,1), 下轨,DRAWNULL),DOTLINE COLORRED,LINETHICK1;
        IF(ABC7>REF(ABC7,1),ABC7,DRAWNULL),COLORRED,LINETHICK2;
        IF(ABC7<REF(ABC7,1),ABC7,DRAWNULL),COLORGREEN,LINETHICK2;
        翻译

        '''
        df=self.df
        data=pd.DataFrame()
        data['date']=df['date']
        C=df['close']
        #ABC7赋值:收盘价的7日指数移动平均,画黄色,线宽为2
        ABC7=EMA(C,7)#,COLORYELLOW,LINETHICK2;
        #ABC14赋值:收盘价的14日指数移动平均,COLOR7FF00F,线宽为1 DOTLINE
        ABC14=EMA(C,14)#COLOR7FF00F,LINETHICK1 DOTLINE;
        #ABC25赋值:收盘价的25日指数移动平均,COLORFF7F00,线宽为1 DOTLINE
        ABC25=EMA(C,25)#,COLORFF7F00,LINETHICK1 DOTLINE;
        #ABCMA45赋值:收盘价的45日指数移动平均,COLORF00FFF,线宽为1 DOTLINE
        ABCMA45=EMA(C,45)#,COLORF00FFF,LINETHICK1 DOTLINE;
        MA5=MA(C,5)
        MA10=MA(C,10)
        MA20=MA(C,20)
        ABC=ABC7>ABC14
        #当满足条件收盘价/1日前的收盘价>1.095时,在收盘价和开盘价位置之间画柱状线,宽度为2,0不为0则画空心柱.,画黄色
        #STICKLINE(C/REF(C,1)>1.095,C,O,2,0),COLORYELLOW;
        #当满足条件收盘价/1日前的收盘价>1.095时,在最低价*0.96位置书写文字,画淡红色
        data['强']=C/REF(C,1)>1.09
        #DRAWTEXT(C/REF(C,1)>1.095,L*0.96,' ★强'),COLORLIRED;

        #当满足条件最高价<0日前的最低价时,在最高价和0日前的最低价位置之间画柱状线,宽度为10,0不为0则画空心柱.
        #STICKLINE(HIGH<REF(LOW,0),HIGH,REF(LOW,0),10,0);
        #STICKLINE(LOW>REF(HIGH,0) ,LOW,REF(HIGH,0),10,0);
        ''''
        STICKLINE(C=O,H,L,0,0);
        STICKLINE((C=O)AND(C>REF(C,0)),C,O,8,0);
        STICKLINE((C=O)AND(C<REF(C,0)),C,O,8,0);
        STICKLINE(CROSS(ABC7,ABC14) AND ABC,CLOSE,OPEN,2,0),COLORMAGENTA;
        DRAWICON(CROSS(ABC7,ABC14) AND ABC,L*1.002,9);
        '''
        data['买']=CROSS(ABC7,ABC14)
        #DRAWTEXT(CROSS(ABC7,ABC14) AND{微信公众号:尊重市场}ABC,L*0.98,' ★买'),COLORMAGENTA;
        '''
        STICKLINE(CROSS(ABC25,ABC7),CLOSE,OPEN,2,0),COLORBLUE;
        CC:=ABS((2*CLOSE+HIGH+LOW)/4-MA(CLOSE,20))/MA(CLOSE,20);
        DD:=DMA(CLOSE,CC);
        上轨:(1+7/100)*DD,DOTLINE,COLORGREEN;
        下轨:(1-7/100)*DD,DOTLINE,COLORGREEN;
        中轨:(上轨+下轨)/2,DOTLINE,COLORGREEN;
        FK:(1+14/100)*DD,DOTLINE,COLORGRAY;
        CD:(1-14/100)*DD,DOTLINE,COLORGRAY;
        DRAWNUMBER(ISLASTBAR,上轨,上轨),COLOR00FFFF;
        DRAWNUMBER(ISLASTBAR,下轨,下轨),COLORFFFF00;
        DRAWNUMBER(ISLASTBAR,中轨,中轨),COLOR00FF00;
        DRAWNUMBER(ISLASTBAR,FK,FK){微信公众号:尊重市场},COLOR0000FF;
        DRAWNUMBER(ISLASTBAR,CD,CD),COLORWHITE;
        上轨绿:IF(上轨>=REF(上轨,1),上轨,DRAWNULL),DOTLINE,COLORGREEN,LINETHICK1;
        上轨红:IF(上轨>=REF(上轨,1),上轨,DRAWNULL),DOTLINE COLORRED,LINETHICK1;
        中轨绿:IF(中轨>=REF(中轨,1), 中轨,DRAWNULL),DOTLINE,COLORGREEN,LINETHICK1;
        中轨红:IF(中轨>=REF(中轨,1), 中轨,DRAWNULL),DOTLINE COLORRED, LINETHICK1;
        下轨绿:IF(下轨>=REF(下轨,1), 下轨,DRAWNULL),DOTLINE,COLORGREEN,LINETHICK1;
        下轨红:IF(下轨>=REF(下轨,1), 下轨,DRAWNULL),DOTLINE COLORRED,LINETHICK1;
        '''
        data['红色']=IF(ABC7>REF(ABC7,1),ABC7,None)
        data['绿色']=IF(ABC7<REF(ABC7,1),ABC7,None)
        data['buy']= data['买']
        data['hold']=data['红色']
        data['sell']=data['绿色']
        data['hold']= data['hold'].apply(lambda x : True if x!=None else False)
        data['sell']= data['sell'].apply(lambda x : True if x!=None else False)
        return data