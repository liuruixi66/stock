from xg_tdx_func.xg_tdx_func import *
from qmt_trader.unification_data_qmt import unification_data_qmt
class band_supe_buy_sell:
    def __init__(self,df) -> None:
        self.df=df
    def band_supe_buy_sell(self):
        '''
        波段超级买卖
        尊重市场1赋值:收盘价的6.5日[1日权重]移动平均
        尊重市场2赋值:收盘价的13.5日[1日权重]移动平均
        尊重市场11赋值:收盘价的3日[1日权重]移动平均
        尊重市场21赋值:收盘价的8日[1日权重]移动平均
        当满足条件尊重市场1>尊重市场2时,在尊重市场1和尊重市场2位置之间画柱状线,宽度为2.5,0不为0则画空心柱.,画红色,线宽为2
        当满足条件尊重市场2>尊重市场1时,在尊重市场1和尊重市场2位置之间画柱状线,宽度为2.5,0不为0则画空心柱.,画蓝色,线宽为2
        当满足条件尊重市场1上穿尊重市场2时,在最低价*0.98位置画5号图标
        当满足条件尊重市场21上穿尊重市场11时,在最高价*1.02位置书写文字,画黄色
        BBI赋值:(收盘价的3日简单移动平均+收盘价的6日简单移动平均+收盘价的12日简单移动平均+收盘价的24日简单移动平均)/4
        UPR赋值:BBI+3*BBI的13日估算标准差,线宽为2
        DWN赋值:BBI-3*BBI的13日估算标准差
        安全赋值:收盘价的60日简单移动平均,线宽为2
        LC赋值:1日前的收盘价
        RSI赋值:收盘价-LC和0的较大值的6日[1日权重]移动平均/收盘价-LC的绝对值的6日[1日权重]移动平均*100
        A7赋值:(2*收盘价+最高价+最低价)/4
        输出操作线:A7的5日简单移动平均,线宽为1
        操作线1赋值:A7的5日简单移动平均*1.03,线宽为2
        操作线2赋值:A7的5日简单移动平均*0.97,线宽为2
        输出ABC1:21日内A7的最低值
        输出ABC2:21日内A7的最高值
        SK赋值:(A7-ABC1)/(ABC2-ABC1)*100的7日指数移动平均
        SD赋值:0.667*1日前的SK+0.333*SK的5日指数移动平均
        当满足条件如果统计8日中满足收盘价<1日前的收盘价的天数/8>6/10ANDVOL>=1.5*成交量(手)的5日简单移动平均ANDCOUNT(SK>=SD,3)ANDREF(最低价,1)=120日内最低价的最低值,返回1,否则返回0时,在最低价*0.98位置画9号图标
        当满足条件如果统计13日中满足收盘价<1日前的收盘价的天数/13>6/10ANDCOUNT(SK>SD,6)ANDREF(最低价,5)=120日内最低价的最低值ANDREF(收盘价>=开盘价,4)ANDREF(收阳线,3)ANDREF(收阳线,2)ANDREF(开盘价>CLOS,返回?,否则返回?时,在,1)ANDOPEN>1日前的收盘价,1,0)位置书写文字 ,画黄色
        当满足条件如果统计13日中满足收盘价<1日前的收盘价的天数/13>6/10ANDCOUNT(SK>SD,6)ANDREF(最低价,5)=120日内最低价的最低值ANDREF(收盘价>=开盘价,4)ANDREF(收阳线,3)ANDREF(收阳线,2)ANDREF(开盘价>CLOS,返回?,否则返回?时,在,1)ANDOPEN>1日前的收盘价,1,0)位置画最低价*0.98号图标
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
        尊重市场1=SMA(C,6.5,1)
        尊重市场2=SMA(C,13.5,1)
        尊重市场11=SMA(C,3,1)
        尊重市场21=SMA(C,8,1)
        '''
        STICKLINE(尊重市场1>尊重市场2 , 尊重市场1,尊重市场2 ,2.5, 0),COLORRED,LINETHICK2;
        STICKLINE(尊重市场2>尊重市场1,尊重市场1,尊重市场2,2.5,0),COLORBLUE,LINETHICK2;
        '''
        df['柱子']=IF(尊重市场1>尊重市场2,'红色','蓝色')
        #DRAWICON( CROSS(尊重市场1,尊重市场2),L*0.98,5);
        df['笑脸']=CROSS(尊重市场1,尊重市场2)
        #DRAWTEXT(CROSS(尊重市场21,尊重市场11),H*1.02,''),COLORYELLOW;
        df['标记文字']=CROSS(尊重市场21,尊重市场11)
        BBI=(MA(CLOSE,3)+MA(CLOSE,6)+MA(CLOSE,12)+MA(CLOSE,24))/4
        UPR=BBI+3*STD(BBI,13)
        DWN=BBI-3*STD(BBI,13)
        安全=MA(CLOSE,60)
        LC=REF(CLOSE,1)
        RSI=SMA(MAX(CLOSE-LC,0),6,1)/SMA(ABS(CLOSE-LC),6,1)*100
        A7=(2*C+H+L)/4
        操作线=MA(A7,5)
        df['操作线']=操作线
        操作线1=MA(A7,5)*1.03
        df['操作线1']=操作线1
        操作线2=MA(A7,5)*0.97
        df['操作线2']=操作线2
        ABC1=LLV(A7,21)
        ABC2=HHV(A7,21)
        SK=EMA((A7-ABC1)/(ABC2-ABC1)*100,7)
        SD=EMA(0.667*REF(SK,1)+0.333*SK,5)
        '''
        DRAWICON(IF(COUNT(CLOSE<REF(CLOSE,1),8)/8>6/10 AND VOL>=1.5*MA(VOL,5) AND
        COUNT(SK>=SD,3) AND REF(LOW,1)=LLV(LOW,120),1,0),L*0.98,9);
        {DRAWTEXT(IF(COUNT(CLOSE<REF(CLOSE,1),8)/8>6/10 AND VOL>=1.5*MA(VOL,5) AND
        COUNT(SK>=SD,3) AND REF(LOW,1)=LLV(LOW,120),1,0),LOW*0.98,'底买') ,COLOR0099FF;}
        DRAWTEXT(IF(COUNT(CLOSE<REF(CLOSE,1),13)/13>6/10 AND
        COUNT(SK>SD,6) AND REF(LOW,5)=LLV(LOW,120) AND REF(CLOSE>=OPEN,4) AND
        REF(CLOSE>OPEN,3) AND REF(CLOSE>OPEN,2) AND REF(OPEN>CLOSE,1) AND
        OPEN>REF(CLOSE,1),1,0),LOW*0.98,'底买') ,COLORYELLOW;
        DRAWICON(IF(COUNT(CLOSE<REF(CLOSE,1),13)/13>6/10 AND
        COUNT(SK>SD,6) AND REF(LOW,5)=LLV(LOW,120) AND REF(CLOSE>=OPEN,4) AND
        REF(CLOSE>OPEN,3) AND REF(CLOSE>OPEN,2) AND REF(OPEN>CLOSE,1) AND
        OPEN>REF(CLOSE,1),1,0),L*0.98,9);
        '''
        趋势=CLOSE>=操作线
        df['趋势']=CLOSE>=操作线
        df['stats']=IF(AND(趋势,尊重市场1>尊重市场2),"B","S")
        return df
if __name__=='__main__':
    data=unification_data_qmt()
    df=data.get_hist_data_em(stock='513100')
    modes=band_supe_buy_sell(df=df)
    result=modes.band_supe_buy_sell()
    print(result)
    result.to_excel(r'数据.xlsx')