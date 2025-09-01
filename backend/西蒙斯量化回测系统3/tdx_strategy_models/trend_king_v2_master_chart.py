from xg_tdx_func.xg_tdx_func import *
from trader_tool.unification_data import unification_data
class trend_king_v2_master_chart:
    def __init__(self,df):
        '''
        趋势王V02主图
        '''
        self.df=df
    def trend_king_v2_master_chart(self):
        """
        趋势王V02主图
        输出MA1:收盘价的5日简单移动平均画白色 DOTLINE
        A1赋值:((开盘价+最高价+最低价+收盘价)/4的3日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的6日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的9日指数移动平均)/3
        A2赋值:((开盘价+最高价+最低价+收盘价)/4的5日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的10日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的20日指数移动平均)/3
        A3赋值:((开盘价+最高价+最低价+收盘价)/4的7日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的14日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的28日指数移动平均)/3
        A4赋值:((开盘价+最高价+最低价+收盘价)/4的9日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的18日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的36日指数移动平均)/3
        A5赋值:((开盘价+最高价+最低价+收盘价)/4的11日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的22日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的44日指数移动平均)/3
        A6赋值:((开盘价+最高价+最低价+收盘价)/4的13日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的26日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的52日指数移动平均)/3
        A7赋值:((开盘价+最高价+最低价+收盘价)/4的21日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的34日指数移动平均+(开盘价+最高价+最低价+收盘价)/4的68日指数移动平均)/3
        ABC1赋值:A1的6日线性回归预测值
        ABC2赋值:A2的6日线性回归预测值
        ABC3赋值:A3的6日线性回归预测值
        ABC4赋值:A4的6日线性回归预测值
        ABC5赋值:A5的6日线性回归预测值
        ABC6赋值:A6的6日线性回归预测值
        ABC7赋值:A7的6日线性回归预测值
        输出做多线:如果ABC7>1日前的ABC7,返回ABC7,否则返回无效数,线宽为2,COLORFF00FF
        输出做空线:如果ABC7<1日前的ABC7,返回ABC7,否则返回无效数,线宽为2,COLOR00FF00
        TOWERC赋值:(3*收盘价+2*开盘价+最高价+最低价)/7的3日指数移动平均的6日线性回归预测值
        DIRECTIONMAX赋值:1日前的TOWERC和1日前的TOWERC的较大值
        DIRECTIONMIN赋值:1日前的TOWERC和1日前的TOWERC的较小值
        共振赋值:条件连续成立次数=1
        当满足条件共振时,在最低价位置画9号图标,画黄色
        建仓赋值:条件连续成立次数=1
        当满足条件建仓时,在最低价位置画1号图标

        """
        df=self.df
        CLOSE=df['close']
        C=df['close']
        LOW=df['low']
        L=df['low']
        low=df['low']
        HIGH=df['high']
        H=df['high']
        OPEN=df['open']
        O=df['open']
        volume=df['volume']
        V=df['volume']
        MA1=MA(CLOSE,5)
        A1=(EMA((OPEN+HIGH+LOW+CLOSE)/4,3)+EMA((OPEN+HIGH+LOW+CLOSE)/4,6)+EMA((OPEN+HIGH+LOW+CLOSE)/4,9))/3
        A2=(EMA((OPEN+HIGH+LOW+CLOSE)/4,5)+EMA((OPEN+HIGH+LOW+CLOSE)/4,10)+EMA((OPEN+HIGH+LOW+CLOSE)/4,20))/3
        A3=(EMA((OPEN+HIGH+LOW+CLOSE)/4,7)+EMA((OPEN+HIGH+LOW+CLOSE)/4,14)+EMA((OPEN+HIGH+LOW+CLOSE)/4,28))/3
        A4=(EMA((OPEN+HIGH+LOW+CLOSE)/4,9)+EMA((OPEN+HIGH+LOW+CLOSE)/4,18)+EMA((OPEN+HIGH+LOW+CLOSE)/4,36))/3
        A5=(EMA((OPEN+HIGH+LOW+CLOSE)/4,11)+EMA((OPEN+HIGH+LOW+CLOSE)/4,22)+EMA((OPEN+HIGH+LOW+CLOSE)/4,44))/3
        A6=(EMA((OPEN+HIGH+LOW+CLOSE)/4,13)+EMA((OPEN+HIGH+LOW+CLOSE)/4,26)+EMA((OPEN+HIGH+LOW+CLOSE)/4,52))/3
        A7=(EMA((OPEN+HIGH+LOW+CLOSE)/4,21)+EMA((OPEN+HIGH+LOW+CLOSE)/4,34)+EMA((OPEN+HIGH+LOW+CLOSE)/4,68))/3
        ABC1=FORCAST(A1,6)
        ABC2=FORCAST(A2,6)
        ABC3=FORCAST(A3,6)
        ABC4=FORCAST(A4,6)
        ABC5=FORCAST(A5,6)
        ABC6=FORCAST(A6,6)
        ABC7=FORCAST(A7,6)
        做多线=IF(ABC7>REF(ABC7,1),ABC7,None)#,LINETHICK2,COLORFF00FF;
        做空线=IF(ABC7<REF(ABC7,1),ABC7,None)#,LINETHICK2,COLOR00FF00;
        df['趋势']=IF(ABC7>REF(ABC7,1),'紫色','绿色')
        TOWERC=FORCAST(EMA((3*CLOSE+2*OPEN+HIGH+LOW)/7,3),6)
        DIRECTIONMAX=MAX(REF(TOWERC,1),REF(TOWERC,1))
        DIRECTIONMIN=MIN(REF(TOWERC,1),REF(TOWERC,1))
        共振=BARSLASTCOUNT(AND(做多线,TOWERC>=REF(TOWERC,1)))==1
        df['共振']=共振
        #DRAWICON(共振,LOW,9),COLORYELLOW;{微信公众号:尊重市场}
        建仓=BARSLASTCOUNT(TOWERC>=REF(TOWERC,1))==1
        df['建仓']=建仓
        #DRAWICON(建仓,LOW,1);
        return df
if __name__=='__main__':
    data=unification_data(trader_tool='ths')
    data=data.get_unification_data()
    df=data.get_hist_data_em(stock='159920')
    modes=trend_king_v2_master_chart(df=df)
    result=modes.trend_king_v2_master_chart()
    print(result)
    result.to_excel(r'数据.xlsx')
