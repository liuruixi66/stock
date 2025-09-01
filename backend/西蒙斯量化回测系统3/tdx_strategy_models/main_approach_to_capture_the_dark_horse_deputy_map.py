from xg_tdx_func.xg_tdx_func import *
from trader_tool.unification_data import unification_data
class main_approach_to_capture_the_dark_horse_deputy_map:
    def __init__(self,df=''):
        '''
        主力进场擒黑马副图
        '''
        self.df=df
    def main_approach_to_capture_the_dark_horse_deputy_map(self):
        """
        N赋值:30
        M赋值:13
        LC赋值:1日前的收盘价
        RSI1赋值:收盘价-LC和0的较大值的13日[1日权重]移动平均/收盘价-LC的绝对值的13日[1日权重]移动平均*100
        RSIF赋值:90-RSI1,COLOR33DD33
        A4赋值:((收盘价-33日内最低价的最低值)/(33日内最高价的最高值-33日内最低价的最低值))*67
        ABC1赋值:(9日内最高价的最高值-收盘价)/(9日内最高价的最高值-9日内最低价的最低值)*100-70
        ABC2赋值:ABC1的9日[1日权重]移动平均+100
        ABC3赋值:(收盘价-9日内最低价的最低值)/(9日内最高价的最高值-9日内最低价的最低值)*100
        ABC4赋值:ABC3的3日[1日权重]移动平均
        ABC5赋值:ABC4的3日[1日权重]移动平均+100
        ABC6赋值:ABC5-ABC2
        输出趋势:如果ABC6>45,返回ABC6-45,否则返回0
        当满足条件1日前的趋势<趋势时,在趋势和1日前的趋势位置之间画柱状线,宽度为2,0不为0则画空心柱.,画洋红色
        当满足条件1日前的趋势>趋势时,在趋势和1日前的趋势位置之间画柱状线,宽度为2,0不为0则画空心柱.,画绿色
        强弱分界赋值:50,COLORFFFFCC
        底部赋值:0,COLOR00FFFF
        安全赋值:20,COLORFFFF66,线宽为1
        预警赋值:80,COLORFFFF66,线宽为1
        顶部赋值:100,COLORFFFF33
        V1赋值:10日内最低价的最低值
        V2赋值:25日内最高价的最高值
        价位线赋值:(收盘价-V1)/(V2-V1)*4的4日指数移动平均
        当满足条件价位线上穿0.3时,在20+4位置书写文字,画红色
        当满足条件3.5上穿价位线时,在趋势位置书写文字,画白色
        ABC2Q赋值:1日前的最低价
        ABC3Q赋值:最低价-ABC2Q的绝对值的3日[1日权重]移动平均/最低价-ABC2Q和0的较大值的3日[1日权重]移动平均*100
        ABC4Q赋值:如果收盘价*1.3,返回ABC3Q*10,否则返回ABC3Q/10的3日指数移动平均
        ABC5Q赋值:30日内最低价的最低值
        ABC6Q赋值:30日内ABC4Q的最高值
        ABC7Q赋值:如果收盘价的58日简单移动平均,返回1,否则返回0
        ABC8Q赋值:如果最低价<=ABC5Q,返回(ABC4Q+ABC6Q*2)/2,否则返回0的3日指数移动平均/618*ABC7Q
        ABC9Q赋值:如果ABC8Q>100,返回100,否则返回ABC8Q
        ACB3赋值:(21日内最高价的最高值-收盘价)/(21日内最高价的最高值-21日内最低价的最低值)*100-10
        ACB4赋值:(收盘价-21日内最低价的最低值)/(21日内最高价的最高值-21日内最低价的最低值)*100
        ACB5赋值:ACB4的13日[8日权重]移动平均
        走势赋值:ACB5的13日[8日权重]移动平均的向上舍入
        ACB6赋值:ACB3的21日[8日权重]移动平均
        卖临界赋值:当满足条件走势-ACB6>85时,在103和100位置之间画柱状线,宽度为15,1不为0则画空心柱.,画红色,线宽为2
        主力线赋值:3*(收盘价-27日内最低价的最低值)/(27日内最高价的最高值-27日内最低价的最低值)*100的5日[1日权重]移动平均-2*(收盘价-27日内最低价的最低值)/(27日内最高价的最高值-27日内最低价的最低值)*100的5日[1日权重]移动平均的3日[1日权重]移动平均,线宽为2,画蓝色
        超短线赋值:(((主力线-21日内主力线的最低值)/(21日内主力线的最高值-21日内主力线的最低值))*(4))*(25),线宽为2,画蓝色
        ABC11赋值:1日前的(最低价+开盘价+收盘价+最高价)/4
        ABC21赋值:最低价-ABC11的绝对值的13日[1日权重]移动平均/最低价-ABC11和0的较大值的10日[1日权重]移动平均
        ABC31赋值:ABC21的10日指数移动平均
        ABC41赋值:33日内最低价的最低值
        ABC51赋值:如果最低价<=ABC41,返回ABC31,否则返回0的3日指数移动平均
        输出主力吸筹:如果ABC51>1日前的ABC51,返回ABC51,否则返回0,画红色,NODRAW
        当满足条件ABC51>1日前的ABC51时,在0和ABC51位置之间画柱状线,宽度为3,0不为0则画空心柱.,COLOR000055
        当满足条件ABC51>1日前的ABC51时,在0和ABC51位置之间画柱状线,宽度为2.6,0不为0则画空心柱.,COLOR000077
        当满足条件ABC51>1日前的ABC51时,在0和ABC51位置之间画柱状线,宽度为2.1,0不为0则画空心柱.,COLOR000099
        当满足条件ABC51>1日前的ABC51时,在0和ABC51位置之间画柱状线,宽度为1.5,0不为0则画空心柱.,COLOR0000BB
        当满足条件ABC51>1日前的ABC51时,在0和ABC51位置之间画柱状线,宽度为0.9,0不为0则画空心柱.,COLOR0000DD
        当满足条件ABC51>1日前的ABC51时,在0和ABC51位置之间画柱状线,宽度为0.3,0不为0则画空心柱.,COLOR0000FF
        ABC12赋值:3
        ABC28赋值:(3)*(((收盘价-27日内最低价的最低值)/(27日内最高价的最高值-27日内最低价的最低值))*(100)的5日[1日权重]移动平均) - (2)*(((收盘价-27日内最低价的最低值)/(27日内最高价的最高值-27日内最低价的最低值))*(100)的5日[1日权重]移动平均的3日[1日权重]移动平均)
        动态底部赋值:如果最低价<=30日内最低价的最低值,返回最低价-1日前的最低价的绝对值的30日[1日权重]移动平均/最低价-1日前的最低价和0的较大值的99日[1日权重]移动平均,否则返回0*5的3日指数移动平均
        准备买入赋值:收盘价上穿(收盘价,N,1)*1.02
        输出低点:如果动态底部AND准备买入,返回50,否则返回0,画白色,线宽为3
        RSV11赋值:(收盘价-19日内最低价的最低值)/(19日内最高价的最高值-19日内最低价的最低值)*100
        K赋值:RSV11的3日[1日权重]移动平均
        D赋值:K的3日[1日权重]移动平均
        J赋值:3*K-2*D
        短线赋值:J的6日指数移动平均,画红色
        浮筹赋值:短线的28日简单移动平均*1,线宽为2,画绿色
        空方赋值:100*(35日内最高价的最高值-收盘价)/(35日内最高价的最高值-35日内最低价的最低值)的3日简单移动平均,画黄色
        当满足条件短线上穿浮筹AND短线<36时,在20+4位置画9号图标,画蓝色, 线宽为1
        当满足条件浮筹上穿空方时,在浮筹位置书写文字,画白色
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
        N=30
        M=13
        LC=REF(CLOSE,1)
        RSI1=SMA(MAX(CLOSE-LC,0),13,1)/SMA(ABS(CLOSE-LC),13,1)*100
        RSIF=90-RSI1#,COLOR33DD33;
        A4=((C-LLV(L,33))/(HHV(H,33)-LLV(L,33)))*67
        ABC1=(HHV(HIGH,9)-CLOSE)/(HHV(HIGH,9)-LLV(LOW,9))*100-70
        ABC2=SMA(ABC1,9,1)+100
        ABC3=(CLOSE-LLV(LOW,9))/(HHV(HIGH,9)-LLV(LOW,9))*100
        ABC4=SMA(ABC3,3,1)
        ABC5=SMA(ABC4,3,1)+100
        ABC6=ABC5-ABC2
        趋势=IF(ABC6>45,ABC6-45,0)
        '''
        STICKLINE(REF(趋势,1)< 趋势, 趋势,REF(趋势,1),2,0),COLORMAGENTA;

        STICKLINE(REF(趋势,1)> 趋势, 趋势,REF(趋势,1),2,0),COLORGREEN;
        '''
        df['趋势']=IF(REF(趋势,1),"洋红色","绿色")
        强弱分界=50,#COLORFFFFCC;
        底部=0,#COLOR00FFFF;
        安全=20#COLORFFFF66,LINETHICK1;
        预警=80#COLORFFFF66,LINETHICK1;
        顶部=100#,COLORFFFF33;
        V1=LLV(LOW,10)
        V2=HHV(H,25)
        价位线=EMA((C-V1)/(V2-V1)*4,4)
        #DRAWTEXT(CROSS(价位线,0.3),20+4,'●买'),COLORRED;
        df['买']=IF(CROSS(价位线,0.3),"买",None)
        #DRAWTEXT(CROSS(3.5,价位线),趋势,'●卖'),COLORWHITE;
        df['卖']=IF(CROSS(3.5,价位线),"卖",None)
        ABC2Q=REF(LOW,1)
        ABC3Q=SMA(ABS(LOW-ABC2Q),3,1)/SMA(MAX(LOW-ABC2Q,0),3,1)*100
        ABC4Q=EMA(IF(CLOSE*1.3,ABC3Q*10,ABC3Q/10),3)
        ABC5Q=LLV(LOW,30)
        ABC6Q=HHV(ABC4Q,30)
        ABC7Q=IF(MA(CLOSE,58),1,0)
        ABC8Q=EMA(IF(LOW<=ABC5Q,(ABC4Q+ABC6Q*2)/2,0),3)/618*ABC7Q
        ABC9Q=IF(ABC8Q>100,100,ABC8Q)
        ACB3=(HHV(HIGH,21)-CLOSE)/(HHV(HIGH,21)-LLV(LOW,21))*100-10
        ACB4=(CLOSE-LLV(LOW,21))/(HHV(HIGH,21)-LLV(LOW,21))*100
        ACB5=SMA(ACB4,13,8)
        走势=SMA(ACB5,13,8)
        ACB6=SMA(ACB3,21,8)
        df['卖临界']=IF(走势-ACB6>85,'红色柱状',None)
        主力线=3*SMA((CLOSE-LLV(LOW,27))/(HHV(HIGH,27)-LLV(LOW,27))*100,5,1)-2*SMA(SMA((CLOSE-LLV(LOW,27))/(HHV(HIGH,27)-LLV(LOW,27))*100,5,1),3,1)
        超短线=(((主力线-LLV(主力线,21))/(HHV(主力线,21)-LLV(主力线,21)))*(4))*(25)
        ABC11=REF((LOW+OPEN+CLOSE+HIGH)/4,1)
        ABC21=SMA(ABS(LOW-ABC11),13,1)/SMA(MAX(LOW-ABC11,0),10,1)
        ABC31=EMA(ABC21,10)
        ABC41=LLV(LOW,33)
        ABC51=EMA(IF(LOW<=ABC41,ABC31,0),3)
        df['主力吸筹']=IF(ABC51>REF(ABC51,1),ABC51,0)
        '''
        STICKLINE(ABC51>REF(ABC51,1),0,ABC51,3,0 ),COLOR000055;

        STICKLINE(ABC51>REF(ABC51,1),0,ABC51,2.6,0 ),COLOR000077;

        STICKLINE(ABC51>REF(ABC51,1),0,ABC51,2.1,0 ),COLOR000099;

        STICKLINE(ABC51>REF(ABC51,1),0,ABC51,1.5,0 ),COLOR0000BB;

        STICKLINE(ABC51>REF(ABC51,1),0,ABC51,0.9,0 ),COLOR0000DD;

        STICKLINE(ABC51>REF(ABC51,1),0,ABC51,0.3,0 ),COLOR0000FF;
        '''
        ABC12=3
        ABC28=(3)*(SMA(((CLOSE - LLV(LOW,27))/(HHV(HIGH,27) - LLV(LOW,27)))*(100),5,1)) - (2)*(SMA(SMA(((CLOSE - LLV(LOW,27))/(HHV(HIGH,27) - LLV(LOW,27)))*(100),5,1),3,1))
        动态底部=EMA(IF(L<= LLV(L,30),SMA(ABS(L-REF(L,1)),30,1)/SMA(MAX(L-REF(L,1),0),99,1),0)*5,3)
        准备买入=CROSS(C,CLOSE*1.02)
        df['低点']=IF(AND(动态底部, 准备买入[1:]),50,0)
        RSV11=(CLOSE-LLV(LOW,19))/(HHV(HIGH,19)-LLV(LOW,19))*100
        K=SMA(RSV11,3,1)
        D=SMA(K,3,1)
        J=3*K-2*D
        短线=EMA(J,6)
        浮筹=MA(短线,28)*1
        空方=MA(100*(HHV(HIGH,35)-CLOSE)/(HHV(HIGH,35)-LLV(LOW,35)),3)
        #DRAWICON(CROSS(短线,浮筹) AND 短线<36,20+4,9),COLORBLUE, LINETHICK1;
        #DRAWTEXT(CROSS(浮筹,空方),浮筹,' 追')
        df['追']=IF(CROSS(浮筹,空方),"追",None)
        return df
if __name__=='__main__':
    data=unification_data(trader_tool='ths')
    data=data.get_unification_data()
    df=data.get_hist_data_em(stock='513100')
    modes=main_approach_to_capture_the_dark_horse_deputy_map(df=df)
    result=modes.main_approach_to_capture_the_dark_horse_deputy_map()
    print(result)
    result.to_excel(r'数据.xlsx')