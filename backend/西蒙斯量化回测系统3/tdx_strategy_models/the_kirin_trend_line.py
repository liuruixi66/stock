from xg_tdx_func.xg_tdx_func import *
from trader_tool.unification_data import unification_data
class the_kirin_trend_line:
    def __init__(self,df) :
        '''
        麒麟趋势线
        '''
        self.df=df
    def the_kirin_trend_line(self):
        '''
        输出SWL:(收盘价的10日指数移动平均*7+收盘价的20日指数移动平均*3)/10
        输出SWS:以1和100*(成交量(手)的5日累和/(3*当前流通股本(手)))的较大值为权重收盘价的20日指数移动平均的动态移动平均,画白色,DOTLINE
        输出MA5:收盘价的5日简单移动平均DOTLINE 画白色
        画带状线
        当满足条件收阳线时,在收盘价和开盘价位置之间画柱状线,宽度为2.8,0不为0则画空心柱.,画红色
        K线
        JRH赋值:2日内收盘价的最高值
        JRL赋值:2日内收盘价的最低值
        MA3赋值:收盘价的3日简单移动平均
        YTSL赋值:(3*收盘价+最低价+开盘价+最高价)/6
        ABC1赋值:(收盘价>1日前的收盘价 AND 收盘价>2日前的收盘价)
        ABC2赋值:(1日前的ABC1 AND 收盘价<=1日前的收盘价 AND 收盘价>=2日前的收盘价)
        ABC3赋值:(1日前的ABC2 AND 收盘价>=1日前的收盘价 AND 收盘价<=2日前的收盘价)
        ABC4赋值:(1日前的ABC3 AND 收盘价<=1日前的收盘价 AND 收盘价>=2日前的收盘价)
        ABC5赋值:(1日前的ABC4 AND 收盘价>=1日前的收盘价 AND 收盘价<=2日前的收盘价)
        ABC6赋值:(1日前的ABC5 AND 收盘价<=1日前的收盘价 AND 收盘价>=2日前的收盘价)
        ABC7赋值:(1日前的ABC6 AND 收盘价>=1日前的收盘价 AND 收盘价<=2日前的收盘价)
        ABC8赋值:(1日前的ABC7 AND 收盘价<=1日前的收盘价 AND 收盘价>=2日前的收盘价)
        ABC9赋值:(1日前的ABC8 AND 收盘价>=1日前的收盘价 AND 收盘价<=2日前的收盘价)
        ABCA赋值:(1日前的ABC9 AND 收盘价<=1日前的收盘价 AND 收盘价>=2日前的收盘价)
        ABCB赋值:(1日前的ABCA AND 收盘价>=1日前的收盘价 AND 收盘价<=2日前的收盘价)
        ABCC赋值:(1日前的ABCB AND 收盘价<=1日前的收盘价 AND 收盘价>=2日前的收盘价)
        ABCD赋值:(收盘价<1日前的收盘价 AND 收盘价<2日前的收盘价)
        ABCE赋值:(1日前的ABCD AND 收盘价>=1日前的收盘价 AND 收盘价<=2日前的收盘价)
        ABCF赋值:(1日前的ABCE AND 收盘价<=1日前的收盘价 AND 收盘价>=2日前的收盘价)
        ABC10赋值:(1日前的ABCF AND 收盘价>=1日前的收盘价 AND 收盘价<=2日前的收盘价)
        ABC11赋值:(1日前的ABC10 AND 收盘价<=1日前的收盘价 AND 收盘价>=2日前的收盘价)
        ABC12赋值:(1日前的ABC11 AND 收盘价>=1日前的收盘价 AND 收盘价<=2日前的收盘价)
        ABC13赋值:(1日前的ABC12 AND 收盘价<=1日前的收盘价 AND 收盘价>=2日前的收盘价)
        ABC14赋值:(1日前的ABC13 AND 收盘价>=1日前的收盘价 AND 收盘价<=2日前的收盘价)
        ABC15赋值:(1日前的ABC14 AND 收盘价<=1日前的收盘价 AND 收盘价>=2日前的收盘价)
        ABC16赋值:(1日前的ABC15 AND 收盘价>=1日前的收盘价 AND 收盘价<=2日前的收盘价)
        ABC17赋值:(1日前的ABC16 AND 收盘价<=1日前的收盘价 AND 收盘价>=2日前的收盘价)
        ABC18赋值:(1日前的ABC17 AND 收盘价>=1日前的收盘价 AND 收盘价<=2日前的收盘价)
        ABC19赋值:((1日前的ABCDORABCEORABCFORABC10ORABC11ORABC12ORABC13ORABC14ORABC15ORABC16ORABC17ORABC18) AND ABC1)
        ABC1A赋值:((1日前的ABC1ORABC2ORABC3ORABC4ORABC5ORABC6ORABC7ORABC8ORABC9ORABCAORABCBORABCC) AND ABCD)
        输出红色持股:ABC1 OR ABC2 OR ABC3 OR ABC4 OR ABC5 OR ABC6 OR ABC7 OR ABC8 OR ABC9 OR ABCA OR ABCB OR ABCC,COLOR0000FF,NODRAW
        离场赋值:如果红色持股,返回JRL,否则返回无效数
        明离场价赋值:离场,COLORFF99FF,NODRAW
        输出今离场价:1日前的离场COLOR0000FF,NODRAW
        输出青色观望:ABCD OR ABCE OR ABCF OR ABC10 OR ABC11 OR ABC12 OR ABC13 OR ABC14 OR ABC15 OR ABC16 OR ABC17 OR ABC18,COLORFFFF00,NODRAW
        进赋值:如果青色观望,返回JRH,否则返回无效数
        明进场价赋值:进,COLOR33AACC,NODRAW
        输出今进场价:1日前的明进场价,COLORFF0000,NODRAW
        输出短买:ABC19,COLOR33AACC,NODRAW
        输出白色离场:ABC1A,COLORFF99FF,NODRAW
        输出急速超跌:(收盘价-收盘价的34日简单移动平均)/收盘价的34日简单移动平均*100<-14,COLORFFFFFF,NODRAW
        输出上市日期年:收盘价的有效数据周期数-1日前的年份,NODRAW,COLOR0000FF
        输出月:收盘价的有效数据周期数-1日前的月份,NODRAW,COLORFF00FF
        输出日:收盘价的有效数据周期数-1日前的日,NODRAW,COLOR00FFFF
        辰星线赋值:(20*YTSL+19*1日前的YTSL+18*2日前的YTSL+17*3日前的YTSL+16*4日前的YTSL+15*5日前的YTSL+14*6日前的YTSL+13*7日前的YTSL+12*8日前的YTSL+11*9日前的YTSL+10*10日前的YTSL+9*11日前的YTSL+8*12日前的YTSL+7*13日前的YTSL+6*14日前的YTSL+5*15日前的YTSL+4*16日前的YTSL+3*17日前的YTSL+2*18日前的YTSL+20日前的YTSL)/211,COLOR0000FF
        牵牛线赋值:收盘价的26日简单移动平均,COLORFF00FF
        等待赋值:如果MA3>辰星线,返回辰星线,否则返回MA3
        当满足条件ISLASTBARAND(红色持股ORREF(红色持股,1)=1)时,在今离场价和今离场价位置之间画柱状线,宽度为2.8,1不为0则画空心柱.,画红色
        当满足条件收盘价>=开盘价时,在最低价和最高价位置之间画柱状线,宽度为0,0不为0则画空心柱.,画红色
        当满足条件收阴线时,在最低价和最高价位置之间画柱状线,宽度为0,0不为0则画空心柱.,COLOR00BD00
        当满足条件收盘价>=开盘价时,在收盘价和开盘价位置之间画柱状线,宽度为2.8,0不为0则画空心柱.,画红色
        当满足条件红色持股时,在收盘价和开盘价位置之间画柱状线,宽度为2.8,0不为0则画空心柱.,画红色
        当满足条件青色观望时,在收盘价和开盘价位置之间画柱状线,宽度为2.8,0不为0则画空心柱.,画蓝色
        CO赋值:(收盘价-开盘价)
        当满足条件急速超跌时,在开盘价和收盘价-CO/2位置之间画柱状线,宽度为2.8,0不为0则画空心柱.,COLORC0C0C0
        当满足条件短买时,在开盘价和收盘价位置之间画柱状线,宽度为2.8,0不为0则画空心柱.,COLOR00FFFF
        当满足条件白色离场时,在开盘价和收盘价位置之间画柱状线,宽度为2.8,0不为0则画空心柱.,画蓝色
        当满足条件短买时,在最低价-0.04位置画5号图标
        当满足条件白色离场时,在最高价*1.005位置画6号图标
        E赋值:(最高价+最低价+开盘价+2*收盘价)/5
        明日阻力赋值:2*E-最低价
        明日支撑赋值:2*E-最高价
        明日突破赋值:E+(最高价-最低价)
        明日反转赋值:E-(最高价-最低价)
        今日阻力赋值:1日前的明日阻力
        今日支撑赋值:1日前的明日支撑
        当满足条件收盘价不等于0时,在横轴0.90纵轴0.88位置书写文字,画红色
        当满足条件收盘价不等于0时,在横轴0.90纵轴0.96位置书写文字,画黄色
        X1赋值:如果收盘价的5日简单移动平均>收盘价的10日简单移动平均,返回20,否则返回0
        X2赋值:如果收盘价的20日简单移动平均>收盘价的60日简单移动平均,返回10,否则返回0
        X3赋值:如果KDJ的J>KDJ的K,返回10,否则返回0
        X4赋值:如果平滑异同平均线的DIF>平滑异同平均线的DEA,返回10,否则返回0
        X5赋值:如果平滑异同平均线的MACD>0,返回10,否则返回0
        X6赋值:如果成交量(手)>成交量(手)的60日简单移动平均,返回10,否则返回0
        X7赋值:如果以收盘价计算的获利盘比例>0.5,返回10,否则返回0
        X8赋值:如果收盘价/1日前的收盘价>1.03,返回10,否则返回0
        XX赋值:X1+X2+X3+X4+X5+X6+X7+X8
        当满足条件成交量(手)>开盘价时,在横轴0.90纵轴0.80位置书写文字,COLORFFFFFF
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
        CAPITAL=(df['volume']/(df['换手率']))*100
        SWL=(EMA(CLOSE,10)*7+EMA(CLOSE,20)*3)/10
        SWS=DMA(EMA(CLOSE,20),1)#COLORWHITE,DOTLINE;
        MA5=MA(CLOSE,5)#DOTLINE COLORWHITE;
        #DRAWBAND(SWL,RGB(255,50,50),SWS,RGB(64,204,208))
        #STICKLINE(C>O,C,O,2.8,0),COLORRED;
        #DRAWKLINE(HIGH,OPEN,LOW,CLOSE);
        JRH=HHV(C,2)
        JRL=LLV(C,2)
        MA3=MA(CLOSE,3)
        YTSL=(3*CLOSE+LOW+OPEN+HIGH)/6
        ABC1=AND(CLOSE>REF(CLOSE,1),CLOSE>REF(CLOSE,2))
        ABC2=AND(REF(ABC1,1),AND(CLOSE<=REF(CLOSE,1),CLOSE>=REF(CLOSE,2)))
        ABC3=AND(REF(ABC2,1),AND(CLOSE>=REF(CLOSE,1),CLOSE<=REF(CLOSE,2)))
        ABC4=AND(REF(ABC3,1),AND(CLOSE<=REF(CLOSE,1),CLOSE>=REF(CLOSE,2)))
        ABC5=AND(REF(ABC4,1),AND(CLOSE>=REF(CLOSE,1),CLOSE<=REF(CLOSE,2)))
        ABC6=AND(REF(ABC5,1),AND(CLOSE<=REF(CLOSE,1),CLOSE>=REF(CLOSE,2)))
        ABC7=AND(REF(ABC6,1),AND(CLOSE>=REF(CLOSE,1),CLOSE<=REF(CLOSE,2)))
        ABC8=AND(REF(ABC7,1) , AND(CLOSE<=REF(CLOSE,1),CLOSE>=REF(CLOSE,2)))
        ABC9=AND(REF(ABC8,1),AND(CLOSE>=REF(CLOSE,1),CLOSE<=REF(CLOSE,2)))
        ABCA=AND(REF(ABC9,1) , AND(CLOSE<=REF(CLOSE,1),CLOSE>=REF(CLOSE,2)))
        ABCB=AND(REF(ABCA,1),AND(CLOSE>=REF(CLOSE,1),CLOSE<=REF(CLOSE,2)))
        ABCC=AND(REF(ABCB,1),AND(CLOSE<=REF(CLOSE,1),CLOSE>=REF(CLOSE,2)))
        ABCD=AND(CLOSE<REF(CLOSE,1),CLOSE<REF(CLOSE,2))
        ABCE=AND(REF(ABCD,1),AND(CLOSE>=REF(CLOSE,1),CLOSE<=REF(CLOSE,2)))
        ABCF=AND(REF(ABCE,1),AND(CLOSE<=REF(CLOSE,1),CLOSE>=REF(CLOSE,2)))
        ABC10=AND(REF(ABCF,1),AND(CLOSE>=REF(CLOSE,1),CLOSE<=REF(CLOSE,2)))
        ABC11=AND(REF(ABC10,1),AND(CLOSE<=REF(CLOSE,1),CLOSE>=REF(CLOSE,2)))
        ABC12=AND(REF(ABC11,1),AND(CLOSE>=REF(CLOSE,1),CLOSE<=REF(CLOSE,2)))
        ABC13=AND(REF(ABC12,1),AND(CLOSE<=REF(CLOSE,1),CLOSE>=REF(CLOSE,2)))
        ABC14=AND(REF(ABC13,1),AND(CLOSE>=REF(CLOSE,1),CLOSE<=REF(CLOSE,2)))
        ABC15=AND(REF(ABC14,1),AND(CLOSE<=REF(CLOSE,1),CLOSE>=REF(CLOSE,2)))
        ABC16=AND(REF(ABC15,1),AND(CLOSE>=REF(CLOSE,1),CLOSE<=REF(CLOSE,2)))
        ABC17=AND(REF(ABC16,1),AND(CLOSE<=REF(CLOSE,1),CLOSE>=REF(CLOSE,2)))
        ABC18=AND(REF(ABC17,1),AND(CLOSE>=REF(CLOSE,1),CLOSE<=REF(CLOSE,2)))
        ABC19=AND(REF(OR(ABCD,OR(ABCE,OR(ABCF,OR(ABC10,OR(ABC11,OR(ABC12,OR(ABC13,OR(ABC14,OR(ABC15,OR(ABC16,OR(ABC17,ABC18))))))))))),1),ABC1)
        ABC1A=AND(REF(OR(ABC1,OR(ABC2,OR(ABC3,OR(ABC4,OR(ABC5,OR(ABC6,OR(ABC7,OR(ABC8,OR(ABC9,OR(ABCA,OR(ABCB,ABCC))))))))))),1),ABCD)
        红色持股=OR(ABC1,OR(ABC2,OR(ABC3,OR(ABC4,OR(ABC5,OR(ABC6,OR(ABC7,OR(ABC8,OR(ABC9,OR(ABCA,OR(ABCB,ABCC)))))))))))
        df['红色持股']=红色持股
        离场=IF(红色持股,JRL,None)
        df['离场']=离场
        明离场价=离场
        今离场价=REF(离场,1)
        青色观望=OR(ABCD,OR(ABCE,OR(ABCF,OR(ABC10,OR(ABC11,OR(ABC12,OR(ABC13,OR(ABC14,OR(ABC15,OR(ABC16,OR(ABC17,ABC18)))))))))))
        df['青色观望']=青色观望
        进=IF(青色观望,JRH,None)
        df['进']=进
        明进场价=进
        df['明进场价']=明进场价
        今进场价=REF(明进场价,1)
        df['今进场价']=今进场价
        短买=ABC19
        df['短买']=短买
        白色离场=ABC1A
        df['白色离场']=白色离场
        急速超跌=(CLOSE-MA(CLOSE,34))/MA(CLOSE,34)*100<-14
        df['急速超跌']=急速超跌
        辰星线=(20*YTSL+19*REF(YTSL,1)+18*REF(YTSL,2)+17*REF(YTSL,3)+16*REF(YTSL,4)+15*REF(YTSL,5)+14*REF(YTSL,6)+13*REF(YTSL,7)+12*REF(YTSL,8)+11*REF(YTSL,9)+10*REF(YTSL,10)+9*REF(YTSL,11)+8*REF(YTSL,12)+7*REF(YTSL,13)+6*REF(YTSL,14)+5*REF(YTSL,15)+4*REF(YTSL,16)+3*REF(YTSL,17)+2*REF(YTSL,18)+REF(YTSL,20))/211
        df['辰星线']=辰星线
        牵牛线=MA(CLOSE,26)
        df['牵牛线']=牵牛线
        等待=IF(MA3>辰星线,辰星线,MA3)
        df['等待']=等待
        '''
        STICKLINE(ISLASTBAR AND (红色持股 OR REF(红色持股,1)=1),今离场价,今离场价,2.8,1),COLORRED;
        STICKLINE(C>=O,L,H,0,0),COLORRED;
        STICKLINE(C<O, L,H,0,0),COLOR00BD00;
        STICKLINE(C>=O,C,O,2.8,0),COLORRED;
        STICKLINE(红色持股,C,O,2.8,0),COLORRED;
        STICKLINE(青色观望,C,O,2.8,0),COLORBLUE;
        '''
        CO=(C-O)
        '''
        STICKLINE(急速超跌,O,C-CO/2,2.8,0),COLORC0C0C0;
        STICKLINE(短买,O,C,2.8,0),COLOR00FFFF;
        STICKLINE(白色离场,O,C,2.8,0),COLORBLUE;
        DRAWICON(短买,L-0.04,5);
        DRAWICON(白色离场,H*1.005,6);
        '''
        E=(HIGH+LOW+OPEN+2*CLOSE)/5
        明日阻力=2*E-LOW
        明日支撑=2*E-HIGH
        明日突破=E+(HIGH-LOW)
        明日反转=E-(HIGH-LOW)
        今日阻力=REF(明日阻力 , 1)
        今日支撑=REF(明日支撑 , 1)
        df['明日支撑']=明日支撑
        df['明日突破']=明日突破
        df['明日反转']=明日反转
        df['今日阻力']=今日阻力
        df['今日支撑']=今日支撑
        '''
        DRAWTEXT_FIX(C!=0,0.90,0.88,0,STRCAT('支撑:',STRCAT(CON2STR(明日支撑,2),' 元'))),COLORRED;
        DRAWTEXT_FIX(C!=0,0.90,0.96,0,STRCAT('反转:',STRCAT(CON2STR(明日反转,2),' 元'))),COLORYELLOW;
        '''
        X1=IF(MA(C,5)>MA(C,10),20,0)
        X2=IF(MA(C,20)>MA(C,60),10,0)
        KDJ_J=KDJ(CLOSE=CLOSE,HIGH=HIGH,LOW=LOW)[-1]
        KDJ_K=KDJ(CLOSE=CLOSE,HIGH=HIGH,LOW=LOW)[0]
        X3=IF(KDJ_J>KDJ_K,10,0)
        MACD_DIF=MACD(CLOSE=CLOSE)[0]
        MACD_DEA=MACD(CLOSE=CLOSE)[1]
        MACD_MACD=MACD(CLOSE=CLOSE)[-1]
        X4=IF(MACD_DIF>MACD_DEA,10,0)
        X5=IF(MACD_MACD>0,10,0)
        X6=IF(V>MA(V,60),10,0)
        #X7=IF(xg_tdx_func_dll.WINNER(C)>0.5,10,0)
        X8=IF(C/REF(C,1)>1.03,10,0)
        XX=X1+X2+X3+X4+X5+X6+X8
        xx=(100/90)*XX
        df['量化评分']=xx
        buy_list=[]
        for 红色持股,短买 in zip(df['红色持股'].tolist(),df['短买'].tolist()):
            if 红色持股==True :
                buy_list.append('买')
            else:
                buy_list.append(None)
        sell_list=[]
        for 青色观望 in df['青色观望'].tolist():
            if 青色观望==True:
                sell_list.append('卖')
            else:
                sell_list.append(None)
        df['买']=buy_list
        df['卖']=sell_list
        stats_list=[]
        for buy,sell in zip(buy_list,sell_list):
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
    modes=the_kirin_trend_line(df=df)
    result=modes.the_kirin_trend_line()
    print(result)
    result.to_excel(r'数据.xlsx')
   