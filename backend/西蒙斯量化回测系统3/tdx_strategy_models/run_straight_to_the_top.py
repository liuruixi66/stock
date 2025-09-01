from xg_tdx_func.xg_tdx_func import *
from qmt_trader.unification_data_qmt import unification_data_qmt
class run_straight_to_the_top:
    def __init__(self,df):
        '''
        同花顺逃顶王
        '''
        self.df=df
    def run_straight_to_the_top(self):
        '''
        同花顺逃顶王
        指标买卖口诀：红柱出现时买入并持股，绿柱出现时卖
        VAR2赋值:10日内最低价的最低值
        VAR3赋值:25日内最高价的最高值
        输出阶段卖出: 3.2,COLORC6C600
        3.5,COLOR0088FF
        输出清仓卖出: 3.5,COLORFF75FF
        动力线赋值: (收盘价-VAR2)/(VAR3-VAR2)*4的4日指数移动平均
        当满足条件动力线>1日前的动力线时,在动力线和1日前的动力线位置之间画柱状线,宽度为3,1不为0则画空心柱.,画红色
        当满足条件动力线<=1日前的动力线时,在动力线和1日前的动力线位置之间画柱状线,宽度为3,1不为0则画空心柱.,COLOR00FF00
        输出底部:0.2,COLOR70DB93
        输出关注:0.5,画黄色
        当满足条件动力线上穿关注的20日过滤时,在动力线+0.02位置画1号图标
        当满足条件清仓卖出上穿动力线的20日过滤时,在动力线+0.02位置画2号图标
        当满足条件动力线上穿底部的20日过滤时,在动力线+0.02位置画1号图标
        当满足条件阶段卖出上穿动力线的20日过滤时,在动力线+0.02位置画2号图标
        输出强弱分界线:1.75,POINTDOT,线宽为2,COLOR70DB93
        输出数值:动力线,COLORA8A8A8
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
        VAR2=LLV(LOW,10)
        VAR3=HHV(HIGH,25)
        阶段卖出= 3.2#COLORC6C600;
        df['阶段卖出']=阶段卖出
        #3.5,COLOR0088FF;
        清仓卖出=3.5#,COLORFF75FF;
        df['清仓卖出']=清仓卖出
        动力线= EMA((CLOSE-VAR2)/(VAR3-VAR2)*4,4)
        df['动力线']=动力线
        #STICKLINE(动力线>REF(动力线,1) ,动力线 ,REF(动力线,1),3 ,1),COLORRED;
        #STICKLINE(动力线<=REF(动力线,1) ,动力线 ,REF(动力线,1),3 ,1),COLOR00FF00;
        df['柱子']=IF(动力线>REF(动力线,1),'红色','绿色')
        底部=0.2#,COLOR70DB93;
        df['底部']=底部
        关注=0.5#,COLORYELLOW;
        df['关注']=关注
        #DRAWICON( FILTER(CROSS(动力线,关注),20),动力线+0.02 ,1);
        #DRAWICON( FILTER(CROSS(清仓卖出,动力线),20),动力线+0.02,2);
        df['关注箭头']=IF(CROSS(动力线,关注),'红色','')
        #DRAWICON( FILTER(CROSS(动力线,底部),20),动力线+0.02 ,1);
        #DRAWICON( FILTER(CROSS(阶段卖出,动力线),20),动力线+0.02,2);
        df['底部箭头']=IF(CROSS(动力线,底部),'红色','')
        强弱分界线=1.75
        df['强弱分界线']=强弱分界线
        数值=动力线
        df['动力线']=数值
        df['MA_3']=MA(数值,3)
        return df
if __name__=='__main__':
    data=unification_data_qmt()
    df=data.get_hist_data_em(stock='159934')
    modes=run_straight_to_the_top(df=df)
    result=modes.run_straight_to_the_top()
    print(result)
    result.to_excel(r'数据.xlsx')