from trader_tool.index_data import index_data
import os
from trader_tool.rish_indicator import rish_indicator
from datetime import datetime
import empyrical as ep
import pandas as pd
import time
import schedule
from trader_tool.base_func import base_func
class strategy_count:
    def __init__(self):
        self.index_data=index_data()
        self.path=os.path.dirname(os.path.abspath(__file__))
        self.base_func=base_func()
    def get_return_table(self,strategy_id='global_external_commodity_trend_enhancement_strategy',strategy_name='全球外盘商品趋势增强策略'):
        '''
        读取策略数据
        '''
        now_date=''.join(str(datetime.now())[:10].split('-'))
        path=r'{}\trader_models\{}\data\账户数据\账户数据.xlsx'.format(self.path,strategy_id)
        try:
            df=pd.read_excel(r'{}'.format(path))
        except Exception as e:
            print(path,'路径有问题')
            df=pd.DataFrame()
        try:
            del df['Unnamed: 0']
        except:
            pass
        data=pd.DataFrame()
        if df.shape[0]>0:
            data['时间']=[now_date]
            data['策略名称']=[strategy_name]
            data['今日收益%']=[round(df['收益'].tolist()[-1],2)]
            data['策略收益%']=[round(df['收益'].sum(),2)]
            data['年化收益%']=[round(ep.annual_return(df['收益']/100),2)*100]
            data['最大回撤%']=[round(ep.max_drawdown(df['收益']/100),2)*100]
            data['夏普']=[round(ep.sharpe_ratio(df['收益']/100),2)]
            data['波动率']=[round(ep.annual_volatility(df['收益']/100),2)]
            data['在险价值']=[round(ep.tail_ratio(df['收益']/100),2)]
            data['索提诺比率']=[round(ep.sortino_ratio(df['收益']/100),2)]
            data['卡玛比率']=[round(ep.calmar_ratio(df['收益']/100),2)]
            data['欧米茄比率']=[round(ep.omega_ratio(df['收益']/100),2)]
            data['总天数']=[df.shape[0]]
            #获利的天数
            df1=df[df['收益']>=0]
            data['盈利周期']=[df1.shape[0]]
            #亏损天数
            df2=df[df['收益']<0]
            data['亏损周期']=[df2.shape[0]]
            data['胜率']=round((data['盈利周期']/data['总天数'])*100,2)
            data['盈亏比']=round((data['盈利周期']/data['亏损周期'])*100,2)
        else:
            data=data
        return data
    def get_all_strategy_table(self):
        '''
        获取全部策略统计数据
        '''
        if self.base_func.check_is_trader_date_1():
            strategy_id_list=["xg_bond_cov_5_factor_strategy"
                            
       
                            ]
            strategy_name_list=[
                "小果可转债5因子轮动策略"
                
                                ]
            data=pd.DataFrame()
            for strategy_id,strategy_name in zip(strategy_id_list,strategy_name_list):
                df=self.get_return_table(strategy_id=strategy_id,strategy_name=strategy_name)
                print(strategy_name,'统计完成*******')
                data=pd.concat([data,df])
            data.to_excel(r'策略统计\策略统计.xlsx')
            data['统计时间']=datetime.now()
            return data
        else:
            print('目前不是交易时间')

        
if __name__=='__main__':
    models=strategy_count()
    df=models.get_all_strategy_table()
    print(df)
    schedule.every(5).minutes.do(models.get_all_strategy_table)
    while True:
        schedule.run_pending()
        time.sleep(1)
