from xg_tdx_func.xg_tdx_func import *
from trader_tool.unification_data import unification_data
class main_approach_to_capture_dark_horse_main_figure:
    def __init__(self,df):
        
        self.df=df
    def main_approach_to_capture_dark_horse_main_figure(self):
        '''
        一、主图：
        1、灰色K线，底部保持关注；
        2、黄色K线，底部酌情买入；
        3、红色K线，强势持仓阶段；
        4、粉红K线，阶段开始减仓；
        5、青色K线，准备清仓卖出；
        6、绿色K线，要大跌，卖出；
        7、“红色圆球”黑马启动信号；
        8、白虚线上持有，线下休息。
        二、副图：
        1、红柱子，主力吸筹；
        2、紫色柱，主力入场；
        3、绿色柱，主力离场；
        4、先吸筹，后入场买；
        5、保留了“买、卖、追涨”等信号参考；
        输出MA5:收盘价的5日简单移动平均DOTLINE 画白色
        N赋值:30
        M赋值:13
        赋值: 1日前的收盘价
        RSI1赋值:收盘价-LC和0的较大值的13日[1日权重]移动平均/收盘价-LC的绝对值的13日[1日权重]移动平均*100
        RSIF赋值:90-RSI1,COLOR33DD33
        A4赋值:((收盘价-33日内最低价的最低值)/(33日内最高价的最高值-33日内最低价的最低值))*67
        AAC22赋值:10日内最低价的最低值
        AAC33赋值:25日内最高价的最高值
        动力线赋值:(收盘价-AAC22)/(AAC33-AAC22)*4的4日指数移动平均
        RSV赋值:(收盘价-9日内最低价的最低值)/(9日内最高价的最高值-9日内最低价的最低值)*100
        ABB1赋值:RSV的3日[1日权重]移动平均
        ABB2赋值:ABB1的3日[1日权重]移动平均
        ABB3赋值:3*ABB1-2*ABB2
        ABC1赋值:(最低价+最高价+收盘价*2)/4
        ABC2赋值: ABC1的4日简单移动平均
        ABC3赋值:10日内ABC2的最高值
        ABC4赋值:ABC3的3日简单移动平均
        ABC5赋值:1.25*ABC4-0.25*ABC3
        XKKJ赋值:如果ABC5>ABC3,返回ABC3,否则返回ABC5
        ACB1赋值:10日内ABC2的最低值
        ACB2赋值:ACB1的3日简单移动平均
        ACB3赋值:1.25*ACB2-0.25*ACB1
        DKKJ赋值:如果ACB3<ACB1,返回ACB1,否则返回ACB3
        MA13赋值:收盘价的13日简单移动平均
        ZDHM赋值:收盘价上穿DKKJ AND 收盘价上穿MA13 AND 收盘价上穿XKKJ
        ZHM赋值:收盘价上穿MA13 AND 收盘价上穿XKKJ
        当满足条件(ZDHMORZHM)时,在最低价位置画13号图标
        当满足条件(ZDHMORZHM)时,在收盘价和开盘价位置之间画柱状线,宽度为2,0不为0则画空心柱.,画洋红色
        当满足条件(ZDHMORZHM)时,在最低价位置书写文字,画黄色

        当满足条件动力线>0AND((ABB3>ABB1ANDABB3<1日前的ABB3)ORABB3>ABB1)时,在收盘价和开盘价位置之间画柱状线,宽度为1,0不为0则画空心柱.,画深灰色
        当满足条件动力线>=0.2AND动力线<0.5AND((ABB3>ABB1ANDABB3<1日前的ABB3)ORABB3>ABB1)时,在收盘价和开盘价位置之间画柱状线,宽度为1,0不为0则画空心柱.,画深灰色
        当满足条件动力线>=0.5AND动力线<1.75AND((ABB3>ABB1ANDABB3<1日前的ABB3)ORABB3>ABB1)时,在收盘价和开盘价位置之间画柱状线,宽度为1,0不为0则画空心柱.,画黄色
        当满足条件动力线>=1.75AND动力线<3.2AND((ABB3>ABB1ANDABB3<1日前的ABB3)ORABB3>ABB1)时,在收盘价和开盘价位置之间画柱状线,宽度为1,0不为0则画空心柱.,画红色
        当满足条件动力线>=3.2AND动力线<3.45AND((ABB3>ABB1ANDABB3<1日前的ABB3)ORABB3>ABB1)时,在收盘价和开盘价位置之间画柱状线,宽度为1,0不为0则画空心柱.,画淡红色
        当满足条件动力线>=3.45时,在收盘价和开盘价位置之间画柱状线,宽度为1,0不为0则画空心柱. AND ABB3<ABB1,画青色
        当满足条件ABB3<ABB1时,在收盘价和开盘价位置之间画柱状线,宽度为1,0不为0则画空心柱.,画绿色
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
        MA5=MA(CLOSE,5)#DOTLINE COLORWHITE;
        N=30
        M=13
        LC = REF(CLOSE,1)
        RSI1=SMA(MAX(CLOSE-LC,0),13,1)/SMA(ABS(CLOSE-LC),13,1)*100
        RSIF=90-RSI1#COLOR33DD33;
        A4=((C-LLV(L,33))/(HHV(H,33)-LLV(L,33)))*67
        AAC22=LLV(LOW,10)
        AAC33=HHV(HIGH,25)
        动力线=EMA((CLOSE-AAC22)/(AAC33-AAC22)*4,4)
        RSV=(C-LLV(L,9))/(HHV(H,9)-LLV(L,9))*100
        ABB1=SMA(RSV,3,1)
        ABB2=SMA(ABB1,3,1)
        ABB3=3*ABB1-2*ABB2
        ABC1=(LOW+HIGH+CLOSE*2)/4
        ABC2= MA(ABC1,4)
        ABC3=HHV(ABC2,10)
        ABC4=MA(ABC3,3)
        ABC5=1.25*ABC4-0.25*ABC3
        XKKJ=IF(ABC5>ABC3,ABC3,ABC5)
        ACB1=LLV(ABC2,10)
        ACB2=MA(ACB1,3)
        ACB3=1.25*ACB2-0.25*ACB1
        DKKJ=IF(ACB3<ACB1,ACB1,ACB3)
        MA13=MA(C,13)
        ZDHM=AND(AND(CROSS(C,DKKJ),CROSS(C,MA13)) ,CROSS(C,XKKJ))
        ZHM=AND(CROSS(C,MA13),CROSS(C,XKKJ))
        #DRAWICON((ZDHM OR ZHM),L,13);
        #STICKLINE((ZDHM OR ZHM),C,O,2,0),COLORMAGENTA;
        #DRAWTEXT((ZDHM OR ZHM),L,' ★黑马'),COLORYELLOW;
        df['黑马']=IF(OR(ZDHM,ZHM),True,False)[1:]
        #当满足条件动力线>0AND((ABB3>ABB1ANDABB3<1日前的ABB3)ORABB3>ABB1)时,在收盘价和开盘价位置之间画柱状线,宽度为1,0不为0则画空心柱.,画深灰色
        #STICKLINE(动力线>0 AND ((ABB3>ABB1 AND ABB3<REF(ABB3,1)) OR ABB3>ABB1),C,O,1,0),COLORGRAY;
        df['深灰色']=OR(AND(动力线>0,AND(ABB3>ABB1,ABB3<REF(ABB3,1))),ABB3>ABB1)
        #当满足条件动力线>=0.2AND动力线<0.5AND((ABB3>ABB1ANDABB3<1日前的ABB3)ORABB3>ABB1)时,在收盘价和开盘价位置之间画柱状线,宽度为1,0不为0则画空心柱.,画深灰色
        #STICKLINE(动力线>=0.2 AND 动力线<0.5 AND ((ABB3>ABB1 AND ABB3<REF(ABB3,1)) OR ABB3>ABB1),C,O,1,0),COLORGRAY;
        df['深灰色']=OR(AND(AND(动力线>=0.2,动力线<0.5),AND(ABB3>ABB1 , ABB3<REF(ABB3,1))),ABB3>ABB1)
        #当满足条件动力线>=0.5AND动力线<1.75AND((ABB3>ABB1ANDABB3<1日前的ABB3)ORABB3>ABB1)时,在收盘价和开盘价位置之间画柱状线,宽度为1,0不为0则画空心柱.,画黄色
        #STICKLINE(动力线>=0.5 AND 动力线<1.75 AND ((ABB3>ABB1 AND ABB3<REF(ABB3,1)) OR ABB3>ABB1),C,O,1,0),COLORYELLOW;
        df['黄色']=OR(AND(AND(动力线>=0.5,动力线<1.75),AND(ABB3>ABB1,ABB3<REF(ABB3,1))),ABB3>ABB1)
        #当满足条件动力线>=1.75AND动力线<3.2AND((ABB3>ABB1ANDABB3<1日前的ABB3)ORABB3>ABB1)时,在收盘价和开盘价位置之间画柱状线,宽度为1,0不为0则画空心柱.,画红色
        #STICKLINE(动力线>=1.75 AND 动力线<3.2 AND ((ABB3>ABB1 AND ABB3<REF(ABB3,1)) OR ABB3>ABB1),C,O,1,0),COLORRED;
        df['红色']=OR(AND(AND(动力线>=1.75 ,动力线<3.2) ,AND(ABB3>ABB1,ABB3<REF(ABB3,1))), ABB3>ABB1)
        #当满足条件动力线>=3.2AND动力线<3.45AND((ABB3>ABB1ANDABB3<1日前的ABB3)ORABB3>ABB1)时,在收盘价和开盘价位置之间画柱状线,宽度为1,0不为0则画空心柱.,画淡红色
        #STICKLINE(动力线>=3.2 AND 动力线<3.45 AND ((ABB3>ABB1 AND ABB3<REF(ABB3,1)) OR ABB3>ABB1),C,O,1,0),COLORLIRED;
        df['淡红色']=OR(AND(AND(动力线>=3.2,动力线<3.45),AND(ABB3>ABB1,ABB3<REF(ABB3,1))) , ABB3>ABB1)
        #当满足条件动力线>=3.45时,在收盘价和开盘价位置之间画柱状线,宽度为1,0不为0则画空心柱. AND ABB3<ABB1,画青色
        #STICKLINE(动力线>=3.45,C,O,1,0) AND ABB3<ABB1,COLORCYAN;
        df['青色']=AND(动力线>=3.45,ABB3<ABB1)
        #当满足条件ABB3<ABB1时,在收盘价和开盘价位置之间画柱状线,宽度为1,0不为0则画空心柱.,画绿色
        #STICKLINE(ABB3<ABB1,C,O,1,0),COLORGREEN;
        df['绿色']=ABB3<ABB1
        return df 
if __name__=='__main__':
    data=unification_data(trader_tool='ths')
    data=data.get_unification_data()
    df=data.get_hist_data_em(stock='513100')
    modes=main_approach_to_capture_dark_horse_main_figure(df=df)
    result=modes.main_approach_to_capture_dark_horse_main_figure()
    print(result)
    result.to_excel(r'数据.xlsx')
