from xg_tdx_func.xg_tdx_func import *
from trader_tool.unification_data import unification_data
A
class dingniu_periodic_resonance_subdiagram:
    def __init__(self,df) :
        '''
        鼎牛共振副图
        '''
        self.df=df
    def dingniu_periodic_resonance_subdiagram(self):
        '''
        ABC51赋值:(最高价+最低价+收盘价*2)/4
        ABC52赋值:ABC51的17日指数移动平均
        ABC53赋值:ABC51的17日估算标准差
        ABC54赋值:((ABC51-ABC52)/ABC53*100+200)/4
        ABC55赋值:(ABC54的5日指数移动平均-25)*1.56
        ABC56赋值:ABC55的2日指数移动平均*1.22
        ABC57赋值:ABC56的2日指数移动平均
        当满足条件ABC56-ABC57>0时,在0.2和0.4位置之间画柱状线,宽度为3,0不为0则画空心柱.,画红色
        当满足条件ABC56-ABC57<0时,在0.2和0.4位置之间画柱状线,宽度为3,0不为0则画空心柱.,画绿色
        当满足条件ABC56-ABC57>0ANDREF(ABC56-ABC57<0,1)时,在0.2和0.4位置之间画柱状线,宽度为3.05,0不为0则画空心柱.,COLOR000099
        当满足条件ABC56-ABC57>0ANDREF(ABC56-ABC57<0,1)时,在0.2和0.4位置之间画柱状线,宽度为2.2,0不为0则画空心柱.,COLOR0000CC
        当满足条件ABC56-ABC57>0ANDREF(ABC56-ABC57<0,1)时,在0.2和0.4位置之间画柱状线,宽度为1.5,0不为0则画空心柱.,画红色
        当满足条件ABC56-ABC57>0ANDREF(ABC56-ABC57<0,1)时,在0.2和0.4位置之间画柱状线,宽度为0.5,0不为0则画空心柱.,画黄色
        当满足条件ABC56-ABC57>0ANDABC56-ABC57<1日前的ABC56-ABC57ANDABC57>110时,在0.2和0.4位置之间画柱状线,宽度为3,0不为0则画空心柱.,画淡红色
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
        VOL=df['volume']
        V=df['volume']
        ABC51=(HIGH+LOW+CLOSE*2)/4
        ABC52=EMA(ABC51,17)
        ABC53=STD(ABC51,17)
        ABC54=((ABC51-ABC52)/ABC53*100+200)/4
        ABC55=(EMA(ABC54,5)-25)*1.56
        ABC56=EMA(ABC55,2)*1.22
        ABC57=EMA(ABC56,2)
        '''
        STICKLINE(ABC56-ABC57>0,0.2,0.4,3,0),COLORRED
        STICKLINE(ABC56-ABC57< 0,0.2,0.4,3,0),COLORGREEN
        '''
        df['柱子']=IF(ABC56-ABC57>0,"红色",'绿色')
        #STICKLINE(ABC56-ABC57>0 AND REF(ABC56-ABC57< 0,1),0.2,0.4,3.05,0),COLOR000099
        #STICKLINE(ABC56-ABC57>0 AND REF(ABC56-ABC57< 0,1),0.2,0.4,2.2,0),COLOR0000CC
        '''
        STICKLINE(ABC56-ABC57>0 AND REF(ABC56-ABC57< 0,1),0.2,0.4,1.5,0),COLORRED
        STICKLINE(ABC56-ABC57>0 AND REF(ABC56-ABC57< 0,1),0.2,0.4,0.5,0),COLORYELLOW
        '''
        df['起点']=AND(ABC56-ABC57>0,REF(ABC56-ABC57< 0,1))
        #STICKLINE(ABC56-ABC57>0 AND ABC56-ABC57< REF(ABC56-ABC57,1) AND ABC57>110,0.2,0.4,3,0),COLORLIRED
        df['淡红色']=AND(ABC56-ABC57>0,AND(ABC56-ABC57< REF(ABC56-ABC57,1),ABC57>110))
        return df
if __name__=='__main__':
    data=unification_data(trader_tool='ths')
    data=data.get_unification_data()
    df=data.get_hist_data_em(stock='159619',start_date='19990101')
    print(df)
    modes=dingniu_periodic_resonance_subdiagram(df=df)
    result=modes.dingniu_periodic_resonance_subdiagram()
    print(result)
    result.to_excel(r'数据.xlsx')
   