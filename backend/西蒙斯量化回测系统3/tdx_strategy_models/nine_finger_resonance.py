from xg_tdx_func.xg_tdx_func import *
from trader_tool.unification_data import unification_data
class nine_finger_resonance:
    def __init__(self,df) :
        '''
        九指共振
        '''
        self.df=df
    def nine_finger_resonance(self):
        '''
        输出DD11:0.95,COLORFF33FF
        输出DD22:2,画绿色
        日K赋值:"KDJ的K"(9,3,3)
        日D赋值:"KDJ的D"(9,3,3)
        当满足条件日K>日D时,在1位置画1号图标
        当满足条件日K<日D时,在1位置画2号图标
        当满足条件是否最后一个周期=1时,在1位置书写文字,COLORFFFFFF
        日DIF赋值:"平滑异同平均线的DIF"(12,26,9)
        日DEA赋值:"平滑异同平均线的DEA"(12,26,9)
        当满足条件日DIF>日DEA时,在1.1位置画1号图标
        当满足条件日DIF<日DEA时,在1.1位置画2号图标
        当满足条件是否最后一个周期=1时,在1.1位置书写文字,COLORFFFFFF
        日RSI赋值:"RSI的RSI1"(9)
        当满足条件日RSI>50时,在1.2位置画1号图标
        当满足条件日RSI<50时,在1.2位置画2号图标
        当满足条件是否最后一个周期=1时,在1.2位置书写文字,COLORFFFFFF
        周K赋值:"KDJ的K"(9,3,3)
        周D赋值:"KDJ的D"(9,3,3)
        当满足条件周K>周D时,在1.3位置画1号图标
        当满足条件周K<周D时,在1.3位置画2号图标
        当满足条件是否最后一个周期=1时,在1.3位置书写文字,COLORFFFFFF
        周DIF赋值:"平滑异同平均线的DIF"(12,26,9)
        周DEA赋值:"平滑异同平均线的DEA"(12,26,9)
        当满足条件周DIF>周DEA时,在1.4位置画1号图标
        当满足条件周DIF<周DEA时,在1.4位置画2号图标
        当满足条件是否最后一个周期=1时,在1.4位置书写文字,COLORFFFFFF
        周RSI赋值:"RSI的RSI1"(9)
        当满足条件周RSI>50时,在1.5位置画1号图标
        当满足条件周RSI<50时,在1.5位置画2号图标
        当满足条件是否最后一个周期=1时,在1.5位置书写文字,COLORFFFFFF
        月K赋值:"KDJ的K"(9,3,3)
        月D赋值:"KDJ的D"(9,3,3)
        当满足条件月K>月D时,在1.6位置画1号图标
        当满足条件月K<月D时,在1.6位置画2号图标
        当满足条件是否最后一个周期=1时,在1.6位置书写文字,COLORFFFFFF
        月DIF赋值:"平滑异同平均线的DIF"(12,26,9)
        月DEA赋值:"平滑异同平均线的DEA"(12,26,9)
        当满足条件月DIF>月DEA时,在1.7位置画1号图标
        当满足条件月DIF<月DEA时,在1.7位置画2号图标
        当满足条件是否最后一个周期=1时,在1.7位置书写文字,COLORFFFFFF
        月RSI赋值:"RSI的RSI1"(9)
        当满足条件月RSI>50时,在1.8位置画1号图标
        当满足条件月RSI<50时,在1.8位置画2号图标
        当满足条件是否最后一个周期=1时,在1.8位置书写文字,COLORFFFFFF
        ABC1赋值:日K>日D
        ABC2赋值:日DIF>日DEA
        ABC3赋值:日RSI>50
        ABC4赋值:周K>周D
        ABC5赋值:周DIF>周DEA
        ABC6赋值:周RSI>50
        ABC7赋值:月K>月D
        ABC8赋值:月DIF>月DEA
        ABC9赋值:月RSI>50
        尊重市场赋值:ABC1 AND ABC2 AND ABC3 AND ABC4 AND ABC5 AND ABC6 AND ABC7 AND ABC8 AND ABC9
        共振赋值:条件连续成立次数=1
        当满足条件共振时,在0.95和1.85位置之间画柱状线,宽度为2,0不为0则画空心柱.,画洋红色
        当满足条件共振时,在1.9位置画9号图标
        当满足条件共振时,在1.90位置书写文字,画红色
        '''
        df=self.df
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        weekly_data = df.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        })
        weekly_data.dropna(inplace=True)
        monthly_data=df.resample('M').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        })
        amount=0
        DD11=0.95
        DD22=2
        日K = KDJ(CLOSE=df['close'],HIGH=df['high'],LOW=df['low'])[0].tolist()[-1] #"KDJ.K"(9,3,3)
        日D= KDJ(CLOSE=df['close'],HIGH=df['high'],LOW=df['low'])[1].tolist()[-1]#"KDJ.D"(9,3,3);
        ''''
        DRAWICON(日K>日D,1,1);
        DRAWICON(日K<日D,1,2);
        '''
        #DRAWTEXT(ISLASTBAR=1,1,'日K'),COLORFFFFFF;
        日DIF=MACD(CLOSE=df['close'])[0].tolist()[-1] #"MACD.DIF"(12,26,9);
        日DEA=MACD(CLOSE=df['close'])[1].tolist()[-1] #"MACD.DEA"(12,26,9);
        '''
        DRAWICON(日DIF>日DEA,1.1,1);
        DRAWICON(日DIF<日DEA,1.1,2);
        DRAWTEXT(ISLASTBAR=1,1.1,'日M'),COLORFFFFFF;
        '''
        日RSI = RSI(CLOSE=df['close'],N1=9)[0].tolist()[-1]#"RSI.RSI1"(9)
        '''
        DRAWICON(日RSI>50,1.2,1);
        DRAWICON(日RSI<50,1.2,2);
        DRAWTEXT(ISLASTBAR=1,1.2,'日R'),COLORFFFFFF;
        '''
        周K = KDJ(CLOSE=weekly_data['close'],HIGH=weekly_data['high'],LOW=weekly_data['low'])[0].tolist()[-1]#"KDJ.K"(9,3,3);
        周D= KDJ(CLOSE=weekly_data['close'],HIGH=weekly_data['high'],LOW=weekly_data['low'])[1].tolist()[-1]#"KDJ.D"(9,3,3);
        '''
        DRAWICON(周K>周D,1.3,1);
        DRAWICON(周K<周D,1.3,2);
        DRAWTEXT(ISLASTBAR=1,1.3,'周K'),COLORFFFFFF;
        '''
        周DIF=MACD(CLOSE=weekly_data['close'])[0].tolist()[-1] #"MACD.DIF"(12,26,9);
        周DEA=MACD(CLOSE=weekly_data['close'])[1].tolist()[-1]#"MACD.DEA"(12,26,9);
        '''
        DRAWICON(周DIF>周DEA,1.4,1);
        DRAWICON(周DIF<周DEA,1.4,2);
        DRAWTEXT(ISLASTBAR=1,1.4,'周M'),COLORFFFFFF;
        '''
        
        周RSI=RSI(CLOSE=weekly_data['close'])[0].tolist()[-1]#"RSI.RSI1"(9);
        '''
        DRAWICON(周RSI>50,1.5,1);
        DRAWICON(周RSI<50,1.5,2);
        DRAWTEXT(ISLASTBAR=1,1.5,'周R'),COLORFFFFFF;
        '''

        月K=KDJ(CLOSE=monthly_data['close'],HIGH=monthly_data['high'],LOW=monthly_data['low'])[0].tolist()[-1]#"KDJ.K"(9,3,3);
        月D= KDJ(CLOSE=monthly_data['close'],HIGH=monthly_data['high'],LOW=monthly_data['low'])[1].tolist()[-1]# "KDJ.D"(9,3,3);
        '''
        DRAWICON(月K>月D,1.6,1);
        DRAWICON(月K<月D,1.6,2);
        DRAWTEXT(ISLASTBAR=1,1.6,'月K'),COLORFFFFFF;
        '''
        月DIF=MACD(CLOSE=monthly_data['close'])[0].tolist()[-1]#"MACD.DIF"(12,26,9);
        月DEA=MACD(CLOSE=monthly_data['close'])[1].tolist()[-1]#"MACD.DEA"(12,26,9);
        '''
        DRAWICON(月DIF>月DEA,1.7,1);
        DRAWICON(月DIF<月DEA,1.7,2);
        DRAWTEXT(ISLASTBAR=1,1.7,'月M'),COLORFFFFFF;
        '''
        月RSI=RSI(CLOSE=monthly_data['close'])[0].tolist()[-1] #"RSI.RSI1"(9);
        '''
        DRAWICON(月RSI>50,1.8,1);
        DRAWICON(月RSI<50,1.8,2);
        DRAWTEXT(ISLASTBAR=1,1.8,'月R'),COLORFFFFFF;
        '''
        ABC1=日K>日D
        amount+=IF(ABC1,1,0)
        ABC2=日DIF>日DEA
        amount+=IF(ABC2,1,0)
        ABC3=日RSI>50
        amount+=IF(ABC3,1,0)
        ABC4=周K>周D
        amount+=IF(ABC4,1,0)
        ABC5=周DIF>周DEA
        amount+=IF(ABC5,1,0)
        ABC6=周RSI>50
        amount+=IF(ABC6,1,0)
        ABC7=月K>月D
        amount+=IF(ABC7,1,0)
        ABC8=月DIF>月DEA
        amount+=IF(ABC8,1,0)
        ABC9=月RSI>50
        amount+=IF(ABC9,1,0)
        尊重市场=AND(AND(AND(AND(AND(AND(AND(AND(ABC1,ABC2),ABC3) ,ABC4),ABC5) ,ABC6),ABC7) ,ABC8) ,ABC9)
        '''
        STICKLINE(共振,0.95,1.85,2,0),COLORMAGENTA;
        DRAWICON(共振,1.9,9);
        DRAWTEXT(共振,1.90,'★共振'),COLORRED;
        '''
        return amount
if __name__=='__main__':
    data=unification_data(trader_tool='ths')
    data=data.get_unification_data()
    df=data.get_hist_data_em(stock='159920')
    print(df)
    modes=nine_finger_resonance(df=df)
    result=modes.nine_finger_resonance()
    print(result)
   