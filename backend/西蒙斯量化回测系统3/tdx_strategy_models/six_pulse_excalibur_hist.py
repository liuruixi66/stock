from xg_tdx_func.xg_tdx_func import *
from trader_tool.unification_data import unification_data
class six_pulse_excalibur_hist:
    def __init__(self,df):
        '''
        六脉神剑
        '''
        self.df=df
    def six_pulse_excalibur_hist(self):
        '''
        六脉神剑
        DIFF赋值:收盘价的8日指数移动平均-收盘价的13日指数移动平均
        DEA赋值:DIFF的5日指数移动平均
        当满足条件DIFF>DEA时,在1位置画1号图标
        当满足条件DIFF<DEA时,在1位置画2号图标
        当满足条件是否最后一个周期=1时,在1位置书写文字,COLORFFFFFF
        ABC1赋值:DIFF>DEA
        尊重市场1赋值:(收盘价-8日内最低价的最低值)/(8日内最高价的最高值-8日内最低价的最低值)*100
        K赋值:尊重市场1的3日[1日权重]移动平均
        D赋值:K的3日[1日权重]移动平均
        当满足条件K>D时,在2位置画1号图标
        当满足条件K<D时,在2位置画2号图标
        当满足条件是否最后一个周期=1时,在2位置书写文字,COLORFFFFFF
        ABC2赋值:K>D
        指标营地赋值:1日前的收盘价
        RSI1赋值:(收盘价-指标营地和0的较大值的5日[1日权重]移动平均)/(收盘价-指标营地的绝对值的5日[1日权重]移动平均)*100
        RSI2赋值:(收盘价-指标营地和0的较大值的13日[1日权重]移动平均)/(收盘价-指标营地的绝对值的13日[1日权重]移动平均)*100
        当满足条件RSI1>RSI2时,在3位置画1号图标
        当满足条件RSI1<RSI2时,在3位置画2号图标
        当满足条件是否最后一个周期=1时,在3位置书写文字,COLORFFFFFF
        ABC3赋值:RSI1>RSI2
        尊重市场赋值:-(13日内最高价的最高值-收盘价)/(13日内最高价的最高值-13日内最低价的最低值)*100
        LWR1赋值:尊重市场的3日[1日权重]移动平均
        LWR2赋值:LWR1的3日[1日权重]移动平均
        当满足条件LWR1>LWR2时,在4位置画1号图标
        当满足条件LWR1<LWR2时,在4位置画2号图标
        当满足条件是否最后一个周期=1时,在4位置书写文字,COLORFFFFFF
        ABC4赋值:LWR1>LWR2
        BBI赋值:(收盘价的3日简单移动平均+收盘价的5日简单移动平均+收盘价的8日简单移动平均+收盘价的13日简单移动平均)/4
        当满足条件收盘价>BBI时,在5位置画1号图标
        当满足条件收盘价<BBI时,在5位置画2号图标
        当满足条件是否最后一个周期=1时,在5位置书写文字,COLORFFFFFF
        ABC10赋值:7
        ABC5赋值:收盘价>BBI
        MTM赋值:收盘价-1日前的收盘价
        MMS赋值:100*MTM的5日指数移动平均的3日指数移动平均/MTM的绝对值的5日指数移动平均的3日指数移动平均
        MMM赋值:100*MTM的13日指数移动平均的8日指数移动平均/MTM的绝对值的13日指数移动平均的8日指数移动平均
        当满足条件MMS>MMM时,在6位置画1号图标
        当满足条件MMS<MMM时,在6位置画2号图标
        当满足条件是否最后一个周期=1时,在6位置书写文字,COLORFFFFFF
        ABC6赋值:MMS>MMM
        输出买入:如果ABC1ANDABC2ANDABC3ANDABC4ANDABC5ANDABC6=1ANDREF(ABC1ANDABC2ANDABC3ANDABC4ANDABC5ANDABC6,1)=0,返回6,否则返回0,画黄色,线宽为2
        输出持有:如果ABC1ANDABC2ANDABC3ANDABC4ANDABC5ANDABC6,返回6,否则返回0,画洋红色,线宽为2
        共振赋值:ABC1 AND ABC2 AND ABC3 AND ABC4 AND ABC5 AND ABC6 
        当满足条件共振时,在0和6位置之间画柱状线,宽度为0.6,1不为0则画空心柱.,画洋红色
        当满足条件买入时,在0和6位置之间画柱状线,宽度为0.6,0不为0则画空心柱.,画黄色
        当满足条件DIFF>DEA时,在1位置画1号图标
        当满足条件DIFF<DEA时,在1位置画2号图标
        当满足条件K>D时,在2位置画1号图标
        当满足条件K<D时,在2位置画2号图标
        当满足条件RSI1>RSI2时,在3位置画1号图标
        当满足条件RSI1<RSI2时,在3位置画2号图标
        当满足条件LWR1>LWR2时,在4位置画1号图标
        当满足条件LWR1<LWR2时,在4位置画2号图标
        当满足条件收盘价>BBI时,在5位置画1号图标
        当满足条件收盘价<BBI时,在5位置画2号图标
        当满足条件MMS>MMM时,在6位置画1号图标
        当满足条件MMS<MMM时,在6位置画2号图标
        当满足条件买入时,在6.6位置画9号图标
        '''
        df=self.df
        markers=0
        signal=0
        #df=self.data.get_hist_data_em(stock=stock)
        CLOSE=df['close']
        LOW=df['low']
        HIGH=df['high']
        DIFF=EMA(CLOSE,8)-EMA(CLOSE,13)
        DEA=EMA(DIFF,5)
        #如果满足DIFF>DEA 在1的位置标记1的图标
        #DRAWICON(DIFF>DEA,1,1);
        markers+=IF(DIFF>DEA,1,0)
        #如果满足DIFF<DEA 在1的位置标记2的图标
        #DRAWICON(DIFF<DEA,1,2);
        markers+=IF(DIFF<DEA,1,0)
        #DRAWTEXT(ISLASTBAR=1,1,'. MACD'),COLORFFFFFF;{微信公众号:尊重市场}
        ABC1=DIFF>DEA
        signal+=IF(ABC1,1,0)
        尊重市场1=(CLOSE-LLV(LOW,8))/(HHV(HIGH,8)-LLV(LOW,8))*100
        K=SMA(尊重市场1,3,1)
        D=SMA(K,3,1)
        #如果满足k>d 在2的位置标记1的图标
        markers+=IF(K>D,1,0)
        #DRAWICON(K>D,2,1);
        markers+=IF(K<D,1,0)
        #DRAWICON(K<D,2,2);
        #DRAWTEXT(ISLASTBAR=1,2,'. KDJ'),COLORFFFFFF;
        ABC2=K>D
        signal+=IF(ABC2,1,0)
        指标营地=REF(CLOSE,1)
        RSI1=(SMA(MAX(CLOSE-指标营地,0),5,1))/(SMA(ABS(CLOSE-指标营地),5,1))*100
        RSI2=(SMA(MAX(CLOSE-指标营地,0),13,1))/(SMA(ABS(CLOSE-指标营地),13,1))*100
        markers+=IF(RSI1>RSI2,1,0)
        #DRAWICON(RSI1>RSI2,3,1);
        markers+=IF(RSI1<RSI2,1,0)
        #DRAWICON(RSI1<RSI2,3,2);
        #DRAWTEXT(ISLASTBAR=1,3,'. RSI'),COLORFFFFFF;
        ABC3=RSI1>RSI2
        signal+=IF(ABC3,1,0)
        尊重市场=-(HHV(HIGH,13)-CLOSE)/(HHV(HIGH,13)-LLV(LOW,13))*100
        LWR1=SMA(尊重市场,3,1)
        LWR2=SMA(LWR1,3,1)
        #DRAWICON(LWR1>LWR2,4,1);
        markers+=IF(LWR1>LWR2,1,0)
        #DRAWICON(LWR1<LWR2,4,2);
        markers+=IF(LWR1<LWR2,1,0)
        #DRAWTEXT(ISLASTBAR=1,4,'. LWR'),COLORFFFFFF;
        ABC4=LWR1>LWR2
        signal+=IF(ABC4,1,0)
        BBI=(MA(CLOSE,3)+MA(CLOSE,5)+MA(CLOSE,8)+MA(CLOSE,13))/4
        #DRAWICON(CLOSE>BBI,5,1);
        markers+=IF(CLOSE>BBI,1,0)
        #DRAWICON(CLOSE<BBI,5,2);
        markers+=IF(CLOSE<BBI,1,0)
        #DRAWTEXT(ISLASTBAR=1,5,'. BBI'),COLORFFFFFF;
        ABC10=7
        ABC5=CLOSE>BBI
        signal+=IF(ABC5,1,0)
        MTM=CLOSE-REF(CLOSE,1)
        MMS=100*EMA(EMA(MTM,5),3)/EMA(EMA(ABS(MTM),5),3)
        MMM=100*EMA(EMA(MTM,13),8)/EMA(EMA(ABS(MTM),13),8)
        markers+=IF(MMS>MMM,1,0)
        #DRAWICON(MMS>MMM,6,1);
        markers+=IF(MMS<MMM,1,0)
        #DRAWICON(MMS<MMM,6,2);
        #DRAWTEXT(ISLASTBAR=1,6,'. ZLMM'),COLORFFFFFF;
        ABC6=MMS>MMM
        signal+=IF(ABC6,1,0)
        '''
        买入:IF(ABC1 AND ABC2 AND ABC3 AND ABC4 AND ABC5 AND ABC6=1  
        AND REF(ABC1 AND ABC2 AND ABC3 AND ABC4 AND ABC5 AND ABC6,1)=0,6,0),COLORYELLOW,LINETHICK2;
        持有:IF(ABC1 AND ABC2 AND ABC3 AND ABC4 AND ABC5 AND ABC6,6,0),COLORMAGENTA,LINETHICK2;
        共振:=ABC1 AND ABC2 AND ABC3 AND ABC4 AND ABC5 AND ABC6 ;
        STICKLINE(共振,0,6,0.6,1),COLORMAGENTA;
        STICKLINE(买入,0,6,0.6,0),COLORYELLOW;
        DRAWICON(DIFF>DEA,1,1);
        DRAWICON(DIFF<DEA,1,2);
        DRAWICON(K>D,2,1);
        DRAWICON(K<D,2,2);
        DRAWICON(RSI1>RSI2,3,1);
        DRAWICON(RSI1<RSI2,3,2);
        DRAWICON(LWR1>LWR2,4,1);
        DRAWICON(LWR1<LWR2,4,2);
        DRAWICON(CLOSE>BBI,5,1);
        DRAWICON(CLOSE<BBI,5,2);
        DRAWICON(MMS>MMM,6,1);{微信公众号:尊重市场}
        DRAWICON(MMS<MMM,6,2);
        DRAWICON(买入,6.6,9);
        '''
        df['signal']=signal
        df['markers']=markers
        return df
if __name__=='__main__':
    data=unification_data(trader_tool='ths')
    data=data.get_unification_data()
    df=data.get_hist_data_em(stock='513100')
    modes=six_pulse_excalibur_hist(df=df)
    result=modes.six_pulse_excalibur_hist()
    print(result)
    