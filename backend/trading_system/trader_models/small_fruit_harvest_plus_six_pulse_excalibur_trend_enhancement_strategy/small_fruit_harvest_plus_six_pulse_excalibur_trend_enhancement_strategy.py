from trader_tool.stock_data import stock_data
from trader_tool.bond_cov_data import bond_cov_data
from trader_tool.shape_analysis import shape_analysis
from trader_tool.analysis_models import analysis_models
import pandas as pd
from trader_tool.ths_rq import ths_rq
from tqdm import tqdm
import numpy as np
import json
from  trader_tool import jsl_data
from qmt_trader.qmt_trader_ths import qmt_trader_ths
from xgtrader.xgtrader import xgtrader
from trader_tool.ths_rq import ths_rq
from trader_tool.ths_board_concept_data import ths_board_concept_data
from trader_tool.unification_data import unification_data
import os
import pandas as pd
from trader_tool.dfcf_etf_data import dfcf_etf_data
#六脉神剑
from trader_tool.tdx_trader_function import tdx_trader_function
from .user_def_models import user_def_models
#债券模型

from trader_tool.base_func import base_func
class small_fruit_harvest_plus_six_pulse_excalibur_trend_enhancement_strategy:
    def __init__(self,trader_tool='ths',exe='C:/同花顺软件/同花顺/xiadan.exe',tesseract_cmd='C:/Program Files/Tesseract-OCR/tesseract',
                qq='1029762153@qq.com',open_set='否',qmt_path='D:/国金QMT交易端模拟/userdata_mini',
                qmt_account='55009640',qmt_account_type='STOCK',name='run_small_fruit_harvest_plus_six_pulse_excalibur_trend_enhancement_strategy'):
        '''
        小果固收加六脉神剑趋势增强策略
        '''
        self.exe=exe
        self.tesseract_cmd=tesseract_cmd
        self.qq=qq
        self.trader_tool=trader_tool
        self.open_set=open_set
        self.qmt_path=qmt_path
        self.qmt_account=qmt_account
        self.qmt_account_type=qmt_account_type
        if trader_tool=='ths':
            self.trader=xgtrader(exe=self.exe,tesseract_cmd=self.tesseract_cmd,open_set=open_set)
        else:
            self.trader=qmt_trader_ths(path=qmt_path,account=qmt_account,account_type=qmt_account_type)
        self.stock_data=stock_data()
        self.bond_cov_data=bond_cov_data()
        self.ths_rq=ths_rq()
        self.path=os.path.dirname(os.path.abspath(__file__))
        self.ths_board_concept_data=ths_board_concept_data()
        self.name=name
        self.data=unification_data(trader_tool=self.trader_tool)
        self.data=self.data.get_unification_data()
        self.dfcf_etf_data=dfcf_etf_data()
        self.user_def_moels=user_def_models(trader_tool=self.trader_tool,exe=self.exe,
                                        tesseract_cmd=self.tesseract_cmd,qq=self.qq,
                                        open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                        qmt_account_type=self.qmt_account_type,name=self.name)
        self.trader.connect()
        self.tdx_trader_function=tdx_trader_function()
        self.base_func=base_func()
        with open(r'分析配置.json',encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        cash_set=text['多策略资金设置']
        name_list=list(cash_set.keys())
        if  self.name in name_list:
            hold_limit=cash_set[self.name]['持股限制']
        else:
            hold_limit=cash_set['其他策略']['持股限制']
        with open(r'{}\小果固收加六脉神剑趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        text['持股限制']=hold_limit
        text['持有限制']=hold_limit
        #保存
        with open(r'{}\小果固收加六脉神剑趋势增强策略.json'.format(self.path),'w',encoding='utf-8') as f:
            json.dump(text, f,ensure_ascii=False,indent=2) 
    def save_position(self):
        '''
        保存持股数据
        '''
        with open(r'分析配置.json',encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        del_df=pd.read_excel(r'{}\黑名单\黑名单.xlsx'.format(self.path),dtype='object')
        del_trader_stock=text['黑名单']
        if del_df.shape[0]>0:
            del_df['证券代码']=del_df['证券代码'].apply(lambda x : str(x).split('.')[0])
            del_df['证券代码']=del_df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            del_stock_list=del_df['证券代码'].tolist()
        else:
            del_stock_list=[]
        for del_stock in del_trader_stock:
            del_stock_list.append(del_stock)
        trader_type=text['交易品种']
        def select_del_stock_list(x):
            if str(x)[:6] in del_stock_list:
                return '是'
            else:
                return '否'
        df=self.trader.position()
        if df.shape[0]>0:
            if trader_type=='全部':
                df['选择']=trader_type
                df=df
            else:
                df['选择']=df['证券代码'].apply(self.trader.select_data_type)
            df=df[df['选择']==trader_type]
            df=df[df['股票余额']>=10]
            print('剔除黑名单**********')
            print(df)
            df['黑名单']=df['证券代码'].apply(select_del_stock_list)
            df=df[df['黑名单']=='否']
            df.to_excel(r'持股数据\持股数据.xlsx')
            return df
        else:
            df=pd.DataFrame()
            df['账号类型']=None
            df['资金账号']=None
            df['证券代码']=None
            df['股票余额']=None
            df['可用余额']=None
            df['成本价']=None
            df['市值']=None
            df['选择']=None
            df['持股天数']=None
            df['交易状态']=None
            df['明细']=None
            df['证券名称']=None
            df['冻结数量']=None
            df['市价']=None	
            df['盈亏']=None
            df['盈亏比(%)']=None
            df['当日买入']=None	
            df['当日卖出']=None
            df.to_excel(r'持股数据\持股数据.xlsx')
            return df
    def get_solation_strategy(self):
        '''
        隔离策略
        '''
        with open(r'{}\小果固收加六脉神剑趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        hold_stock=pd.read_excel(r'持股数据\持股数据.xlsx')
        is_open=text['是否开启自动隔离策略']
        if is_open=='是':
            print('开启自动隔离策略***************')
            try:
                trader_df=pd.read_excel(r'{}\自定义交易股票池\自定义交易股票池.xlsx'.format(self.path),dtype='object')
            except Exception as e:
                print(e)
                trader_df=hold_stock
            if  trader_df.shape[0]>0:
                trader_df['证券代码']=trader_df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
                trader_df['证券代码']=trader_df['证券代码'].astype(str)
                stock_list=trader_df['证券代码'].tolist()
            else:
                stock_list=[]
            if hold_stock.shape[0]>0:
                hold_stock['证券代码']=hold_stock['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
                hold_stock['证券代码']=hold_stock['证券代码'].astype(str)
                hold_stock['隔离']= hold_stock['证券代码'].apply(lambda x: '是' if x in stock_list else '不是')
                df1=hold_stock[hold_stock['隔离']=='不是']
                hold_stock=hold_stock[hold_stock['隔离']=='是']
                print('交易的股票池**************')
                print(hold_stock)
                print('剔除的交易股票池**************')
                print(df1)
                hold_stock.to_excel(r'持股数据\持股数据.xlsx')
            else:
                hold_stock.to_excel(r'持股数据\持股数据.xlsx')
        else:
            print('不开启自动隔离策略***************')
        print(hold_stock)
    def save_balance(self):
        '''
        保持账户数据
        '''
        df=self.trader.balance()
        df.to_excel(r'账户数据\账户数据.xlsx')
        return df
    def cacal_six_pulse_excalibur(self,df):
        '''
        技术六脉神剑
        '''
        try:
            signal,markers=self.tdx_trader_function.six_pulse_excalibur(df)
            return signal,markers
        except:
            return None,None
        
    def mean_line_models(self,df,x1=3,x2=5,x3=10,x4=15,x5=20):
        '''
        均线模型
        趋势模型
        5，10，20，30，60
        '''
        df=df
        #df=self.bond_cov_data.get_cov_bond_hist_data(stock=stock,start=start_date,end=end_date,limit=1000000000)
        df1=pd.DataFrame()
        df1['date']=df['date']
        df1['x1']=df['close'].rolling(window=x1).mean()
        df1['x2']=df['close'].rolling(window=x2).mean()
        df1['x3']=df['close'].rolling(window=x3).mean()
        df1['x4']=df['close'].rolling(window=x4).mean()
        df1['x5']=df['close'].rolling(window=x5).mean()
        score=0
        #加分的情况
        mean_x1=df1['x1'].tolist()[-1]
        mean_x2=df1['x2'].tolist()[-1]
        mean_x3=df1['x3'].tolist()[-1]
        mean_x4=df1['x4'].tolist()[-1]
        mean_x5=df1['x5'].tolist()[-1]
        #相邻2个均线进行比较
        if mean_x1>=mean_x2:
            score+=25
        if mean_x2>=mean_x3:
            score+=25
        if mean_x3>=mean_x4:
            score+=25
        if mean_x4>=mean_x5:
            score+=25
        return score
    def cacal_mean_analysis_models(self):
        '''
        均线分析
        '''
        with open(r'{}\小果固收加六脉神剑趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        is_open=text['是否开启均线趋势买入']
        n=text['价格站上N日线买入']
        df=pd.read_excel(r'持股数据\持股数据.xlsx',dtype='object')
        df1=df[df['股票余额']>=10]
        print(df1)
        df1['证券代码']=df1['证券代码'].astype(str)
        if df1.shape[0]>0:
            df1['证券代码']=df1['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            hold_stock_list=df1['证券代码'].tolist()
        else:
            hold_stock_list=[]
        trader_df=pd.read_excel(r'{}\自定义交易股票池\自定义交易股票池.xlsx'.format(self.path),dtype='object')
        if is_open=='是':
            print('开启价格站上N日线买入*****************')
            if trader_df.shape[0]>0:
                print('原始自定义交易股票池****************')
                print(trader_df)
                trader_df['证券代码']=trader_df['证券代码'].astype(str)
                def select_data(stock):
                    if str(stock) in hold_stock_list:
                        return '持股超过限制'
                    else:
                        return '没有持股'
                    
                trader_df['持股检查']=trader_df['证券代码'].apply(select_data)
                trader_df=trader_df[trader_df['持股检查'] !='持股超过限制']
                print('处理原始自定义交易股票池****************')
                if trader_df.shape[0]>0:
                    down_list=[]
                    for i in  tqdm(range(len(trader_df['证券代码'].tolist()))):
                        stock=trader_df['证券代码'].tolist()[i]
                        try:
                            hist=self.data.get_hist_data_em(stock=stock)
                            models=shape_analysis(df=hist)
                            down=models.get_down_mean_line_sell(n=n)
                            down_list.append(down)
                        except Exception as e:
                            print(e)
                            down_list.append('是')
                    trader_df['均线分析']=down_list
                    trader_df=trader_df[trader_df['均线分析']=='不是']
                    trader_df.to_excel(r'{}\均线分析\均线分析.xlsx'.format(self.path))
                else:
                    print('均线分析没有买入的标的￥￥￥￥￥￥￥￥￥￥￥￥￥￥￥￥')
                    trader_df=pd.DataFrame()
                    trader_df.to_excel(r'{}\均线分析\均线分析.xlsx'.format(self.path))
            else:
                print('均线分析没有自定义股票池￥￥￥￥￥￥￥￥￥￥￥￥￥￥￥￥')
                trader_df=pd.DataFrame()
                trader_df.to_excel(r'{}\均线分析\均线分析.xlsx'.format(self.path))
        else:
            print('不开启价格站上N日线买入*********8')
            trader_df.to_excel(r'{}\均线分析\均线分析.xlsx'.format(self.path))
    def cacal_score_analysis_models(self):
        '''
        趋势分析模型
        '''
        print('趋势分析模型**************')
        with open(r'{}\小果固收加六脉神剑趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        buy_min_srore=text['买入最低分']
        trader_df=pd.read_excel(r'{}\均线分析\均线分析.xlsx'.format(self.path),dtype='object')
        try:
            del trader_df['Unnamed: 0']
        except:
            pass
        if trader_df.shape[0]>0:
            trader_df['证券代码']=trader_df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            mean_score_list=[]
            for i in  tqdm(range(len(trader_df['证券代码'].tolist()))):
                stock=trader_df['证券代码'].tolist()[i]
                try:
                    hist_df=self.data.get_hist_data_em(stock=stock)
                    score=self.mean_line_models(df=hist_df)
                    mean_score_list.append(score)
                except Exception as e:
                    print(e)
                    mean_score_list.append(0)
            trader_df['趋势得分']=mean_score_list
            trader_df=trader_df[trader_df['趋势得分']>=buy_min_srore]
            trader_df.to_excel(r'{}\趋势得分\趋势得分.xlsx'.format(self.path))
        else:
            trader_df=pd.DataFrame()
            trader_df.to_excel(r'{}\趋势得分\趋势得分.xlsx'.format(self.path))
    def cacal_stock_premium_rate(self):
        '''
        计算溢价率
        '''
        print('计算溢价率**************')
        with open(r'{}\小果固收加六脉神剑趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        max_ratio=text['ETF溢价率上限']
        min_ratio=text['ETF溢价率下限']
        df=pd.read_excel(r'{}\趋势得分\趋势得分.xlsx'.format(self.path))
        try:
            del df['Unnamed: 0']
        except:
            pass
        
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            fund=self.dfcf_etf_data.get_all_etf_data_1()
            yjl_dict=dict(zip(fund['基金代码'].tolist(),fund['溢价率'].tolist()))
            df['溢价率']=df['证券代码'].apply(lambda x :yjl_dict.get(str(x),0))
            df=df[df['溢价率']<=max_ratio]
            df=df[df['溢价率']>=min_ratio]
            df.to_excel(r'{}\溢价率分析\溢价率分析.xlsx'.format(self.path))
        else:
            df=pd.DataFrame()
            df.to_excel(r'{}\溢价率分析\溢价率分析.xlsx'.format(self.path))
    def cacal_price_limit(self):
        '''
        计算涨跌幅限制
        '''
        print('计算涨跌幅限制**************')
        with open(r'{}\小果固收加六脉神剑趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        max_ratio=text['最大涨跌幅']
        min_ratio=text['最小涨跌幅']
        df=pd.read_excel(r'{}\溢价率分析\溢价率分析.xlsx'.format(self.path))
        try:
            del df['Unnamed: 0']
        except:
            pass
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            zdf_list=[]
            for i in  tqdm(range(len(df['证券代码'].tolist()))):
                stock=df['证券代码'].tolist()[i]
                try:
                    zdf=self.data.get_hist_data_em(stock=stock)['涨跌幅'].tolist()[-1]
                    zdf_list.append(zdf)
                except Exception as e:
                    print(e)
                    zdf_list.append(-40)
            df['涨跌幅']=zdf_list
            df=df[df['涨跌幅']<=max_ratio]
            df=df[df['涨跌幅']>=min_ratio]
            df.to_excel(r'{}\涨跌幅分析\涨跌幅分析.xlsx'.format(self.path))
        else:
            df=pd.DataFrame()
            df.to_excel(r'{}\涨跌幅分析\涨跌幅分析.xlsx'.format(self.path))
    def cacal_degree_of_deviation(self):
        '''
        计算偏离度
        '''
        print('计算偏离度**************')
        with open(r'{}\小果固收加六脉神剑趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        max_ratio=text["买入时候的偏离度"]
        n=text['偏离均线']
        df=pd.read_excel(r'{}\涨跌幅分析\涨跌幅分析.xlsx'.format(self.path))
        try:
            del df['Unnamed: 0']
        except:
            pass
        if df.shape[0]>0:
            deviation_list=[]
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            for i in  tqdm(range(len(df['证券代码'].tolist()))):
                stock=df['证券代码'].tolist()[i]
                try:
                    hist=self.data.get_hist_data_em(stock=stock,start_date='19990101',data_type='W')
                    price=hist['close'].tolist()[-1]
                    hist['mean_line']=hist['close'].rolling(window=n).mean()
                    line=hist['mean_line'].tolist()[-1]
                    deviation=((price-line)/line)*100
                    deviation_list.append(deviation)
                except Exception as e:
                    print(e)
                    deviation_list.append(None)
            df['偏离度']=deviation_list
            df=df[df['偏离度']<=max_ratio]
            df.to_excel(r'{}\偏离度分析\偏离度分析.xlsx'.format(self.path))
        else:
            df=pd.DataFrame()
            df.to_excel(r'{}\偏离度分析\偏离度分析.xlsx'.format(self.path))
    def cacal_cycle_analysis(self):
        '''
        计算周周期
        '''
        print('计算周周期**************')
        with open(r'{}\小果固收加六脉神剑趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        min_ratio=text['周周期买入']
        is_open=text['是否开启周周期']
        df=pd.read_excel(r'{}\偏离度分析\偏离度分析.xlsx'.format(self.path))
        try:
            del df['Unnamed: 0']
        except:
            pass
        if is_open=='是':
            print('开启周周期&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
            if df.shape[0]>0:
                cycle_list=[]
                df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
                for i in  tqdm(range(len(df['证券代码'].tolist()))):
                    stock=df['证券代码'].tolist()[i]
                    try:
                        hist=self.data.get_hist_data_em(stock=stock,start_date='19990101',data_type='W')
                        signal,markers=self.cacal_six_pulse_excalibur(df=hist)
                        cycle_list.append(signal)
                    except Exception as e:
                        print(e)
                        cycle_list.append(None)
                df['周周期']=cycle_list
                print(df)
                df=df[df['周周期']>=min_ratio]
                df.to_excel(r'{}\周周期分析\周周期分析.xlsx'.format(self.path))
            else:
                df=pd.DataFrame()
                df.to_excel(r'{}\周周期分析\周周期分析.xlsx'.format(self.path))
        else:
            df.to_excel(r'{}\周周期分析\周周期分析.xlsx'.format(self.path))
    def cacal_diurnal_cycle(self):
        '''
        计算日周期
        '''
        print('计算日周期**************')
        with open(r'{}\小果固收加六脉神剑趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        min_ratio=text['日周期买入']
        is_open='是'
        df=pd.read_excel(r'{}\周周期分析\周周期分析.xlsx'.format(self.path))
        try:
            del df['Unnamed: 0']
        except:
            pass
        if is_open=='是':
            print('开启日周期&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
            if df.shape[0]>0:
                cycle_list=[]
                df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
                for i in  tqdm(range(len(df['证券代码'].tolist()))):
                    stock=df['证券代码'].tolist()[i]
                    try:
                        hist=self.data.get_hist_data_em(stock=stock,start_date='19990101',data_type='D')
                        signal,markers=self.cacal_six_pulse_excalibur(df=hist)
                        cycle_list.append(signal)
                    except Exception as e:
                        print(e)
                        cycle_list.append(None)
                
                df['日周期']=cycle_list
                print('日周期************')
                print(df)
                df=df[df['日周期']>=min_ratio]
                df.to_excel(r'{}\日周期分析\日周期分析.xlsx'.format(self.path))
            else:
                df=pd.DataFrame()
                df.to_excel(r'{}\日周期分析\日周期分析.xlsx'.format(self.path))
        else:
            df.to_excel(r'{}\日周期分析\日周期分析.xlsx'.format(self.path))
    def run_user_def_buy_models(self):
        '''
        运行自定义买入模型
        '''
        with open(r'{}\小果固收加六脉神剑趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        is_open=text['是否开启自定义买入模型']
        select_models=text['自定义买入模型']
        df=pd.read_excel(r'{}\日周期分析\日周期分析.xlsx'.format(self.path))
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
        try:
            del df['Unnamed: 0']
        except:
            pass
        if is_open=='是':
            print('开启选股自定义模型')
            if df.shape[0]>0:
                name_list=list(select_models.keys())
                if len(name_list)>0:
                    df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
                    for name in name_list:
                        func=select_models[name]
                        value_list=[]
                        for stock in df['证券代码'].tolist():
                            try:
                                run_func='self.user_def_moels.{}'.format(func)
                                value=eval(run_func)
                                value_list.append(value)
                            except:
                                value_list.append(False)
                        df[name]=value_list
                    print('**************')
                    print(df)                     
                    for column in name_list:
                        df=df[df[column]==True]
                    df.to_excel(r'{}\自定义选股模型\自定义选股模型.xlsx'.format(self.path))
                else:
                    print('没有自定义选股模型')
                    df.to_excel(r'{}\自定义选股模型\自定义选股模型.xlsx'.format(self.path))
            else:
                print('没有买入的标的')
                df.to_excel(r'{}\自定义选股模型\自定义选股模型.xlsx'.format(self.path))
        else:
            print('不开启自定义选股模型')
            df.to_excel(r'{}\自定义选股模型\自定义选股模型.xlsx'.format(self.path))
    def get_sell_stock_data(self):
        '''
        获取卖出股票数据
        '''
        with open(r'{}\小果固收加六脉神剑趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        is_open_down_mean_line=text['是否自定义交易品种跌破N日均线卖出']
        men_line_n=text['自定义交易品种跌破N日均线卖出']
        is_open_yjl=text['是否开启溢价率平仓']
        sell_yjl=text['平仓溢价率']
        is_open_week_n_sell=text['是否开启周周期']
        week_n_sell=text['周周期清仓']
        daily_n_sell=text['日周期清仓']
        n=text['偏离均线']
        deviation_sell=text['向上偏离N点卖出']
        zdf_sell=text['大涨']
        is_open_zdf_not_sell=text['是否开启大跌不卖']
        zdf_not_sell=text['大跌']
        is_open_max_zdf_sell=text['是否开启大涨卖出']
        hold_score=text['自定义交易品种持有分数']
        df=pd.read_excel(r'持股数据\持股数据.xlsx')
        try:
            del df['Unnamed: 0']
        except:
            pass
        df=df[df['股票余额']>=10]
        if df.shape[0]>0:
            fund=self.dfcf_etf_data.get_all_etf_data_1()
            yjl_dict=dict(zip(fund['基金代码'].tolist(),fund['溢价率'].tolist()))
            if is_open_yjl=='是':
                df['溢价率']=df['证券代码'].apply(lambda x :yjl_dict.get(str(x),0))
            else:
                df['溢价率']=-100
            deviation_list=[]
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            for i in  tqdm(range(len(df['证券代码'].tolist()))):
                stock=df['证券代码'].tolist()[i]
                try:
                    hist=self.data.get_hist_data_em(stock=stock,start_date='19990101',data_type='W')
                    price=hist['close'].tolist()[-1]
                    hist['mean_line']=hist['close'].rolling(window=n).mean()
                    line=hist['mean_line'].tolist()[-1]
                    deviation=((price-line)/line)*100
                    deviation_list.append(deviation)
                except Exception as e:
                    print(e)
                    deviation_list.append(None)

            df['偏离度']=deviation_list
            week_cycle_list=[]
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            for i in  tqdm(range(len(df['证券代码'].tolist()))):
                stock=df['证券代码'].tolist()[i]
                try:
                    hist=self.data.get_hist_data_em(stock=stock,start_date='19990101',data_type='W')
                    signal,markers=self.cacal_six_pulse_excalibur(df=hist)
                    week_cycle_list.append(signal)
                except Exception as e:
                    print(e)
                    week_cycle_list.append(None)
            
            df['周周期']=week_cycle_list
            daily_cycle_list=[]
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            for i in  tqdm(range(len(df['证券代码'].tolist()))):
                stock=df['证券代码'].tolist()[i]
                try:
                    hist=self.data.get_hist_data_em(stock=stock,start_date='19990101',data_type='D')
                    signal,markers=self.cacal_six_pulse_excalibur(df=hist)
                    daily_cycle_list.append(signal)
                except Exception as e:
                    print(e)
                    daily_cycle_list.append(None)
            df['日周期']=daily_cycle_list
            if is_open_down_mean_line=='是':
                    down_list=[]
                    for i in  tqdm(range(len(df['证券代码'].tolist()))):
                        stock=df['证券代码'].tolist()[i]
                        try:
                            hist=self.data.get_hist_data_em(stock=stock)
                            models=shape_analysis(df=hist)
                            down=models.get_down_mean_line_sell(n=men_line_n)
                            down_list.append(down)
                        except Exception as e:
                            print(e)
                            down_list.append('是')
                    df['均线分析']=down_list
            else:
                df['均线分析']='不是'
            if is_open_max_zdf_sell=='是':
                zdf_list=[]
                for i in  tqdm(range(len(df['证券代码'].tolist()))):
                    stock=df['证券代码'].tolist()[i]
                    try:
                        zdf=self.data.get_hist_data_em(stock=stock)['涨跌幅'].tolist()[-1]
                        zdf_list.append(zdf)
                    except Exception as e:
                        print(e)
                        zdf_list.append(-40)
                df['涨跌幅']=zdf_list
            else:
                df['涨跌幅']=-40
            mean_score_list=[]
            for i in  tqdm(range(len(df['证券代码'].tolist()))):
                stock=df['证券代码'].tolist()[i]
                try:
                    hist_df=self.data.get_hist_data_em(stock=stock)
                    score=self.mean_line_models(df=hist_df)
                    mean_score_list.append(score)
                except Exception as e:
                    print(e)
                    mean_score_list.append(0)
            df['趋势得分']=mean_score_list
            sell_stock_list=[]
            print(df)
            for stock,yjl,deviation,week_cycle,daily_cycle,score,down,zdf in zip(df['证券代码'],df['溢价率'],df['偏离度'],
                                            df['周周期'],df['日周期'],df['趋势得分'],df['均线分析'],df['涨跌幅']):
                if yjl>=sell_yjl:
                    print('{} 溢价率{} 大于平仓{} 平仓'.format(stock,yjl,sell_yjl))
                    sell_stock_list.append(stock)
                elif deviation>=deviation_sell:
                    print('{} 偏离度{} 大于平仓偏离度{} 平仓'.format(stock,deviation,deviation_sell))
                    sell_stock_list.append(stock)
                elif is_open_week_n_sell=='是' and week_cycle<=week_n_sell:
                        print('{} 周周期{} 小于平仓周周期{} 平仓'.format(stock,week_cycle,week_cycle))
                        sell_stock_list.append(stock)
                elif daily_cycle<=daily_n_sell:
                    print('{} 日周期{} 小于平仓日周期{} 平仓'.format(stock,daily_cycle,daily_n_sell))
                    sell_stock_list.append(stock)
                elif score<hold_score:
                    print('{} 分数{} 小于持有分数{} 平仓'.format(stock,score,hold_score))
                    sell_stock_list.append(stock)
                elif down=='是':
                    print('{} 跌破均线{} 平仓'.format(stock,men_line_n))
                    sell_stock_list.append(stock)
                elif zdf>=zdf_sell:
                    print('{} 涨跌幅{} 大于平仓涨跌幅{} 平仓'.format(stock,zdf,zdf_sell))
                    sell_stock_list.append(stock)
                else:
                    print('{} 不符合卖出模型继续持有'.format(stock))
            sell_stock_list=list(set(sell_stock_list))
            for stock,zdf in zip(df['证券代码'],df['涨跌幅']):
                if zdf<=zdf_not_sell:
                    if is_open_zdf_not_sell=='是':
                        try:
                            sell_stock_list.remove(stock)
                            print('{}开启大跌不卖 涨跌幅{} 小于大跌涨跌幅'.format(stock,zdf,zdf_not_sell))
                        except:
                            pass
                    else:
                        pass
                else:
                    pass
            sell_df=pd.DataFrame()
            sell_df['证券代码']=sell_stock_list
            sell_df.to_excel(r'{}\持股分析\持股分析.xlsx'.format(self.path))
        else:
            sell_df=pd.DataFrame()
            sell_df.to_excel(r'{}\持股分析\持股分析.xlsx'.format(self.path))
    def run_user_def_sell_models(self):
        '''
        运行自定义卖出模型
        '''
        with open(r'{}\小果固收加六脉神剑趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        is_open=text['是否开启自定义卖出模型']
        select_models=text['自定义卖出模型']
        df=pd.read_excel(r'{}\持股分析\持股分析.xlsx'.format(self.path))
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
        try:
            del df['Unnamed: 0']
        except:
            pass
        if is_open=='是':
            print('开启自定义卖出模型')
            if df.shape[0]>0:
                name_list=list(select_models.keys())
                if len(name_list)>0:
                    df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
                    for name in name_list:
                        func=select_models[name]
                        value_list=[]
                        for stock in df['证券代码'].tolist():
                            try:
                                run_func='self.user_def_moels.{}'.format(func)
                                value=eval(run_func)
                                value_list.append(value)
                            except:
                                value_list.append(False)
                        df[name]=value_list
                    print('**************')
                    print(df)                     
                    for column in name_list:
                        df=df[df[column]==True]
                    df.to_excel(r'{}\自定义卖出模型\自定义卖出模型.xlsx'.format(self.path))
                else:
                    print('没有自定义选股模型')
                    df.to_excel(r'{}\自定义卖出模型\自定义卖出模型.xlsx'.format(self.path))
            else:
                print('没有买入的标的')
                df.to_excel(r'{}\自定义卖出模型\自定义卖出模型.xlsx'.format(self.path))
        else:
            print('不开启自定义卖出模型')
            print(df)
            df.to_excel(r'{}\自定义卖出模型\自定义卖出模型.xlsx'.format(self.path))
    def get_buy_sell_stock_data(self):
        '''
        获取买卖数据
        '''
        with open(r'{}\小果固收加六脉神剑趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        hold_limit=text['持股限制']
        hold_stock=pd.read_excel(r'持股数据\持股数据.xlsx')
        try:
            del hold_stock['Unnamed: 0']
        except:
            pass
        if hold_stock.shape[0]>0:
            hold_stock['证券代码']=hold_stock['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            hold_stock_list=hold_stock['证券代码'].tolist()
            hold_amount=hold_stock.shape[0]
        else:
            hold_stock_list=[]
            hold_amount=0
        buy_df=pd.read_excel(r'{}\自定义选股模型\自定义选股模型.xlsx'.format(self.path))
        buy_df['交易状态']='未买'
        
        try:
            del buy_df['Unnamed: 0']
        except:
            pass
        if buy_df.shape[0]>0:
            buy_df['证券代码']=buy_df['证券代码'].apply(lambda x:'0'*(6-len(str(x)))+str(x))
            def select_data(stock):
                if str(stock) in hold_stock_list:
                    return '持股超过限制'
                else:
                    return '没有持股'
            buy_df['持股检查']=buy_df['证券代码'].apply(select_data)
            buy_df=buy_df[buy_df['持股检查']=='没有持股']
        sell_df=pd.read_excel(r'{}\自定义卖出模型\自定义卖出模型.xlsx'.format(self.path))
        sell_df['交易状态']='未卖'
        try:
            del sell_df['Unnamed: 0']
        except:
            pass
        if sell_df.shape[0]>0:
            sell_df['证券代码']=sell_df['证券代码'].apply(lambda x:'0'*(6-len(str(x)))+str(x))
            sell_stock_list=sell_df['证券代码'].tolist()
            sell_amount=len(sell_stock_list)
        else:
            sell_amount=0
        print('卖出股票**********************')
        print(sell_df)
        sell_df.to_excel(r'{}\卖出股票\卖出股票.xlsx'.format(self.path))
        av_buy=(hold_limit-hold_amount)+sell_amount
        if av_buy>=hold_limit:
            av_buy=hold_limit
        else:
            av_buy=av_buy
        buy_df=buy_df[:av_buy]
        print('买入的标的***************************')
        print(buy_df)
        buy_df.to_excel(r'{}\买入股票\买入股票.xlsx'.format(self.path))   
    def select_data_type(self,stock='600031'):
        '''
        选择数据类型
        '''
        stock=str(stock)[:6]
        if stock[:3] in ['110','113','128','127','123','117'] or stock[:2] in ['11','12']:
            return 'bond'
        elif stock[:3] in ['502','501'] or stock[:2] in ['16','15','51','50','56','58'] or stock[:1] in ['5']:
            return 'fund'
        else:
            return 'stock'
    def get_del_sell_stock(self):
        '''
        隔离卖出标5的
        '''
        sell_df=pd.read_excel(r'{}\卖出股票\卖出股票.xlsx'.format(self.path))
        if sell_df.shape[0]>0:
            sell_df['交易品种']=sell_df['证券代码'].apply(lambda x: self.select_data_type(x))
            sell_df=sell_df[sell_df['交易品种']=='fund']
            sell_df.to_excel(r'{}\卖出股票\卖出股票.xlsx'.format(self.path))
            print('隔离符合交易的卖出股票池****************')
            print(sell_df)
        else:
            print('隔离卖出股票池没有标的')
            sell_df=pd.DataFrame()
            sell_df.to_excel(r'{}\卖出股票\卖出股票.xlsx'.format(self.path))
    def get_del_not_trader_stock(self):
        '''
        剔除黑名单
        '''
        print('剔除黑名单______________*************************_______________________')
        with open(r'分析配置.json',encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        del_df=pd.read_excel(r'{}\黑名单\黑名单.xlsx'.format(self.path),dtype='object')
        del_trader_stock=text['黑名单']
        if del_df.shape[0]>0:
            del_df['证券代码']=del_df['证券代码'].apply(lambda x : str(x).split('.')[0])
            del_df['证券代码']=del_df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            del_stock_list=del_df['证券代码'].tolist()
        else:
            del_stock_list=[]
        for del_stock in del_trader_stock:
            del_stock_list.append(del_stock)
        def select_del_stock_list(x):
            if str(x)[:6] in del_stock_list:
                return '是'
            else:
                return '否'
        buy_df=pd.read_excel(r'{}\买入股票\买入股票.xlsx'.format(self.path),dtype='object')
        buy_df['交易状态']='未买'
        if buy_df.shape[0]>0:
            buy_df['证券代码']=buy_df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            try:
                del buy_df['Unnamed: 0']
            except:
                pass
            #buy_df['黑名单']=buy_df['证券代码'].apply(select_del_stock_list)
            #buy_df=buy_df[buy_df['黑名单']=='否']
            #隔离策略
            buy_df['证券代码']=buy_df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            buy_df['品种']=buy_df['证券代码'].apply(lambda x: self.trader.select_data_type(x))
            buy_df['策略名称']=self.name
            buy_df.to_excel(r'买入股票\买入股票.xlsx')
            print(buy_df)
        else:
            buy_df=pd.DataFrame()
            buy_df['策略名称']=self.name
            buy_df.to_excel(r'买入股票\买入股票.xlsx')
        #卖出
        sell_df=pd.read_excel(r'{}\卖出股票\卖出股票.xlsx'.format(self.path),dtype='object')
        sell_df['交易状态']='未卖'
        if sell_df.shape[0]>0:
            sell_df['证券代码']=sell_df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            try:
                del sell_df['Unnamed: 0']
            except:
                pass
            sell_df['黑名单']=sell_df['证券代码'].apply(select_del_stock_list)
            sell_df=sell_df[sell_df['黑名单']=='否']
            #隔离策略
            sell_df['证券代码']=sell_df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            sell_df['品种']=sell_df['证券代码'].apply(lambda x: self.trader.select_data_type(x))
            sell_df['策略名称']=self.name
            sell_df.to_excel(r'卖出股票\卖出股票.xlsx')
            print(sell_df)
        else:
            sell_df=pd.DataFrame()
            sell_df['策略名称']=self.name
            sell_df.to_excel(r'卖出股票\卖出股票.xlsx')
        return buy_df,sell_df
     
    def update_all_data(self):
        '''
        更新策略数据
        '''
        if self.base_func.check_is_trader_date_1():
            print(self.save_position())
            self.get_solation_strategy()
            print(self.save_balance())
            self.cacal_mean_analysis_models()
            self.cacal_score_analysis_models()
            self.cacal_stock_premium_rate()
            self.cacal_price_limit()
            self.cacal_degree_of_deviation()
            self.cacal_cycle_analysis()
            self.cacal_diurnal_cycle()
            self.run_user_def_buy_models()
            self.get_sell_stock_data()
            self.run_user_def_sell_models()
            self.get_buy_sell_stock_data()
            self.get_del_sell_stock()
            self.get_del_not_trader_stock()
        else:
            print('没有不是交易时间,修改hi哦啊有时间在更新************')

        