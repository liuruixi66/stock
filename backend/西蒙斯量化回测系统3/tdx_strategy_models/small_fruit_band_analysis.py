from xg_tdx_func.xg_tdx_func import *
from trader_tool.unification_data import unification_data
class small_fruit_band_analysis:
    def __init__(self,df) :
        '''
        小果波段分析
        '''
        self.df=df
    def small_fruit_band_analysis(self):
        '''
        {作者:小果}
        {微信：15117320079}
        {公众号:数据分析与运用}
        A1赋值:((开盘价+最高价+最低价+收盘价)/4的3日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的6日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的9日指数移动平均)/3
        A2赋值:((开盘价+最高价+最低价+收盘价)/4的5日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的10日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的20日指数移动平均)/3
        A3赋值:((开盘价+最高价+最低价+收盘价)/4的7日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的14日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的28日指数移动平均)/3
        A4赋值:((开盘价+最高价+最低价+收盘价)/4的9日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的18日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的36日指数移动平均)/3
        A5赋值:((开盘价+最高价+最低价+收盘价)/4的11日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的22日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的44日指数移动平均)/3
        A6赋值:((开盘价+最高价+最低价+收盘价)/4的13日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的26日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的52日指数移动平均)/3
        A7赋值:((开盘价+最高价+最低价+收盘价)/4的21日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的34日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的68日指数移动平均)/3
        VAR1赋值:A1的6日线性回归预测值
        VAR2赋值:A2的6日线性回归预测值
        VAR3赋值:A3的6日线性回归预测值
        VAR4赋值:A4的6日线性回归预测值
        VAR5赋值:A5的6日线性回归预测值
        VAR6赋值:A6的6日线性回归预测值
        VAR7赋值:A7的6日线性回归预测值
        如果VAR1>1日前的VAR1,返回VAR1,否则返回无效数,POINTDOT,COLORFF00FF
        如果VAR1<1日前的VAR1,返回VAR1,否则返回无效数,POINTDOT,COLOR00FF00
        如果VAR2>1日前的VAR2,返回VAR2,否则返回无效数,POINTDOT,COLORFF00FF
        如果VAR2<1日前的VAR2,返回VAR2,否则返回无效数,POINTDOT,COLOR00FF00
        如果VAR3>1日前的VAR3,返回VAR3,否则返回无效数,POINTDOT,COLORFF00FF
        如果VAR3<1日前的VAR3,返回VAR3,否则返回无效数,POINTDOT,COLOR00FF00
        如果VAR4>1日前的VAR4,返回VAR4,否则返回无效数,POINTDOT,COLORFF00FF
        如果VAR4<1日前的VAR4,返回VAR4,否则返回无效数,POINTDOT,COLOR00FF00
        如果VAR5>1日前的VAR5,返回VAR5,否则返回无效数,POINTDOT,COLORFF00FF
        如果VAR5<1日前的VAR5,返回VAR5,否则返回无效数,POINTDOT,COLOR00FF00
        如果VAR6>1日前的VAR6,返回VAR6,否则返回无效数,POINTDOT,COLORFF00FF
        如果VAR6<1日前的VAR6,返回VAR6,否则返回无效数,POINTDOT,COLOR00FF00
        如果VAR7>1日前的VAR7,返回VAR7,否则返回无效数,线宽为2,COLORFF00FF
        如果VAR7<1日前的VAR7,返回VAR7,否则返回无效数,线宽为2,COLOR00FF00
        TOWERC赋值:(3*收盘价+2*开盘价+最高价+最低价)/7的3日指数移动平均的6日线性回归预测值
        DIRECTIONMAX赋值:1日前的TOWERC和1日前的TOWERC的较大值
        DIRECTIONMIN赋值:1日前的TOWERC和1日前的TOWERC的较小值
        当满足条件TOWERC>=1日前的TOWERC时,在TOWERC和DIRECTIONMAX位置之间画柱状线,宽度为4,0不为0则画空心柱.,COLOR0000FF
        当满足条件TOWERC<1日前的TOWERC时,在TOWERC和DIRECTIONMIN位置之间画柱状线,宽度为4,0不为0则画空心柱.,COLOR00FF00
        当满足条件TOWERC>=1日前的TOWERCANDREF(TOWERC,1)<2日前的TOWERC时,在TOWERC位置书写文字,画红色
        当满足条件TOWERC<1日前的TOWERCANDREF(TOWERC,1)>2日前的TOWERC时,在TOWERC位置书写文字,画绿色
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
        A1=(EMA((OPEN+HIGH+LOW+CLOSE)/4,3)+EMA((OPEN+HIGH+LOW+CLOSE)/4,6)+EMA((OPEN+HIGH+LOW+CLOSE)/4,9))/3
        A2=(EMA((OPEN+HIGH+LOW+CLOSE)/4,5)+EMA((OPEN+HIGH+LOW+CLOSE)/4,10)+EMA((OPEN+HIGH+LOW+CLOSE)/4,20))/3
        A3=(EMA((OPEN+HIGH+LOW+CLOSE)/4,7)+EMA((OPEN+HIGH+LOW+CLOSE)/4,14)+EMA((OPEN+HIGH+LOW+CLOSE)/4,28))/3
        A4=(EMA((OPEN+HIGH+LOW+CLOSE)/4,9)+EMA((OPEN+HIGH+LOW+CLOSE)/4,18)+EMA((OPEN+HIGH+LOW+CLOSE)/4,36))/3
        A5=(EMA((OPEN+HIGH+LOW+CLOSE)/4,11)+EMA((OPEN+HIGH+LOW+CLOSE)/4,22)+EMA((OPEN+HIGH+LOW+CLOSE)/4,44))/3
        A6=(EMA((OPEN+HIGH+LOW+CLOSE)/4,13)+EMA((OPEN+HIGH+LOW+CLOSE)/4,26)+EMA((OPEN+HIGH+LOW+CLOSE)/4,52))/3
        A7=(EMA((OPEN+HIGH+LOW+CLOSE)/4,21)+EMA((OPEN+HIGH+LOW+CLOSE)/4,34)+EMA((OPEN+HIGH+LOW+CLOSE)/4,68))/3
        VAR1=FORCAST(A1,6)
        VAR2=FORCAST(A2,6)
        VAR3=FORCAST(A3,6)
        VAR4=FORCAST(A4,6)
        VAR5=FORCAST(A5,6)
        VAR6=FORCAST(A6,6)
        VAR7=FORCAST(A7,6)
        '''
        IF(VAR1>REF(VAR1,1),VAR1,DRAWNULL),POINTDOT,COLORFF00FF;
        IF(VAR1<REF(VAR1,1),VAR1,DRAWNULL),POINTDOT,COLOR00FF00;
        IF(VAR2>REF(VAR2,1),VAR2,DRAWNULL),POINTDOT,COLORFF00FF;
        IF(VAR2<REF(VAR2,1),VAR2,DRAWNULL),POINTDOT,COLOR00FF00;
        IF(VAR3>REF(VAR3,1),VAR3,DRAWNULL),POINTDOT,COLORFF00FF;
        IF(VAR3<REF(VAR3,1),VAR3,DRAWNULL),POINTDOT,COLOR00FF00;
        IF(VAR4>REF(VAR4,1),VAR4,DRAWNULL),POINTDOT,COLORFF00FF;
        IF(VAR4<REF(VAR4,1),VAR4,DRAWNULL),POINTDOT,COLOR00FF00;
        IF(VAR5>REF(VAR5,1),VAR5,DRAWNULL),POINTDOT,COLORFF00FF;
        IF(VAR5<REF(VAR5,1),VAR5,DRAWNULL),POINTDOT,COLOR00FF00;
        IF(VAR6>REF(VAR6,1),VAR6,DRAWNULL),POINTDOT,COLORFF00FF;
        IF(VAR6<REF(VAR6,1),VAR6,DRAWNULL),POINTDOT,COLOR00FF00;
        '''
        #IF(VAR7>REF(VAR7,1),VAR7,DRAWNULL),LINETHICK2,COLORFF00FF;
        #IF(VAR7<REF(VAR7,1),VAR7,DRAWNULL),LINETHICK2,COLOR00FF00;
        df['趋势线']=IF(VAR7>REF(VAR7,1),'紫色','绿色')
        TOWERC=FORCAST(EMA((3*CLOSE+2*OPEN+HIGH+LOW)/7,3),6)
        DIRECTIONMAX=MAX(REF(TOWERC,1),REF(TOWERC,1))
        DIRECTIONMIN=MIN(REF(TOWERC,1),REF(TOWERC,1))
        #STICKLINE(TOWERC>=REF(TOWERC,1),TOWERC,DIRECTIONMAX,4,0),COLOR0000FF;
        #STICKLINE(TOWERC<REF(TOWERC,1),TOWERC,DIRECTIONMIN,4,0),COLOR00FF00;
        df['方块']=IF(TOWERC>=REF(TOWERC,1),'红色','绿色')
        #DRAWTEXT(TOWERC >= REF(TOWERC,1)  AND  REF(TOWERC,1) < REF(TOWERC,2) ,TOWERC,'买'),COLORRED;
        df['买']=IF(AND(TOWERC >= REF(TOWERC,1), REF(TOWERC,1) < REF(TOWERC,2)),"买",None)
        #DRAWTEXT(TOWERC < REF(TOWERC,1)  AND  REF(TOWERC,1) > REF(TOWERC,2) ,TOWERC,'卖'),COLORGREEN
        df['卖']=IF(AND(TOWERC < REF(TOWERC,1),REF(TOWERC,1) > REF(TOWERC,2)),'卖',None)
        stats_list=[]
        for buy,sell in zip(df['买'].tolist(),df['卖'].tolist()):
            if buy=='买':
                stats_list.append(buy)
            elif sell=='卖':
                stats_list.append(sell)
            else:
                stats_list.append(None)
        df['stats']=stats_list
        df['stats']=df['stats'].fillna(method='ffill')
        return df
if __name__=='__main__':
    data=unification_data(trader_tool='ths')
    data=data.get_unification_data()
    df=data.get_hist_data_em(stock='511090')
    print(df)
    modes=small_fruit_band_analysis(df=df)
    result=modes.small_fruit_band_analysis()
    print(result)
    result.to_excel(r'数据.xlsx')
   