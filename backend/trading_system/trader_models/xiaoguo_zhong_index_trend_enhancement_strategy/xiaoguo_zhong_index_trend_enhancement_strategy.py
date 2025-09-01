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
from .user_def_models import user_def_models
from trader_tool.base_func import base_func
from trader_tool.jsl_xg import jsl_xg
from trader_tool.xg_bond_data_down import xg_bond_data_down
from datetime import datetime
from xg_data.xg_data import xg_data
from wencai_threading_data.wencai_threading_data import wencai_threading_data
from trader_tool.xg_index_data import xg_index_data
import time
class xiaoguo_zhong_index_trend_enhancement_strategy:
    def __init__(self,trader_tool='ths',exe='C:/同花顺软件/同花顺/xiadan.exe',tesseract_cmd='C:/Program Files/Tesseract-OCR/tesseract',
                qq='1029762153@qq.com',open_set='否',qmt_path='D:/国金QMT交易端模拟/userdata_mini',
                qmt_account='55009640',qmt_account_type='STOCK',name='run_etf_custom_algorithmic_trading_system_strategy'):
        '''
        小果指数趋势增强策略
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
        self.xg_index_data=xg_index_data()
        self.data=self.data.get_unification_data()
        self.dfcf_etf_data=dfcf_etf_data()
        self.trader.connect()
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
        with open(r'{}\小果指数趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        text['持股限制']=hold_limit
        text['持有限制']=hold_limit
        #保存
        with open(r'{}\小果指数趋势增强策略.json'.format(self.path),'w',encoding='utf-8') as f:
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
            df['黑名单']=df['证券代码'].apply(select_del_stock_list)
            df=df[df['黑名单']=='否']
            df['交易品种']=df['证券代码'].apply(lambda x: self.select_data_type(x))
            df=df[df['交易品种']=='stock']
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
    def save_balance(self):
        '''
        保持账户数据
        '''
        df=self.trader.balance()
        df.to_excel(r'账户数据\账户数据.xlsx')
        return df
    def get_read_tdx_data(self,path):
        '''
        读取通达信数据
        '''
        try:
            stock_list=[]
            with open(r'{}'.format(path)) as p:
                com=p.readlines()
                for stock in com:
                    if len(stock)>=6:
                        stock=stock.replace("\n", "")
                        stock_list.append(stock)
            df=pd.DataFrame()
            df['证券代码']=stock_list
            def select_stock(x):
                '''
                选择股票
                '''
                stock=str(x)
                if stock[0]=='0':
                    stock=stock[1:]
                elif stock[0]=='1':
                    stock=stock[1:]
                else:
                    stock=stock[1:]
                return stock
            df['证券代码']=df['证券代码'].apply(lambda x: select_stock(x))
        except Exception as e:
            print(e,'通达信路径有问题可能不存在',path)
            df=pd.DataFrame()
        return df 
    def get_trader_stock_data(self):
        '''
        获取交易股票池
        '''
        with open(r'{}\小果指数趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        data_type=text['自定义股票池']
        index_list=text['指数列表']
        path=text['通达信板块路径']
        del_list=text['剔除的代码开头']
        if data_type=='自定义指数':
            df=pd.DataFrame()
            for index in index_list:
                data=self.xg_index_data.index_stock_cons(symbol=index)
                df=pd.concat([data,df],ignore_index=True)
            df.columns=['证券代码','名称','纳入时间']
        elif data_type=='通达信板块':
            df=self.get_read_tdx_data(path)
            df['名称']=df['证券代码']
        else:
            print('股票池为自定义股票池在策略下面的自定义股票池输入证券代码，名称就可以')
        df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
        df['剔除']=df['证券代码'].apply(lambda x: '是' if str(x)[:3] in del_list else '不是')
        df=df[df['剔除']=='不是']
        df.to_excel(r'{}\自定义交易股票池\自定义交易股票池.xlsx'.format(self.path))
        return df
    def get_solation_strategy(self):
        '''
        隔离策略
        '''
        with open(r'{}\小果指数趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
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
    def get_user_def_func_models(self):
        '''
        自定义函数分析模型
        '''
        with open(r'{}\小果指数趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        is_open=text['是否开启自定义选股函数']
        user_factor=text['自定义选股函数']
        factor_name=list(user_factor.keys())
        df=pd.read_excel(r'{}\自定义交易股票池\自定义交易股票池.xlsx'.format(self.path))
        hold_stock=pd.read_excel(r'持股数据\持股数据.xlsx')
        if hold_stock.shape[0]>0:
            hold_stock['证券代码']=hold_stock['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            hold_stock_list=hold_stock['证券代码'].tolist()
        else:
            hold_stock_list=[]
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            df['持股检查']=df['证券代码'].apply(lambda x: '是' if x in hold_stock_list else '不是')
            df=df[df['持股检查']=='不是']
        else:
            df=df
        try:
            del df['Unnamed: 0']
        except:
            pass
        if is_open=='是':
            print('开启自定义分析算法')
            if df.shape[0]>0:
                user_factor_list=[]
                stock_list=df['证券代码'].tolist()
                for i in tqdm(range(len(stock_list))):
                    stock=stock_list[i]  
                    result_list=[]
                    try: 
                   
                        hist=self.data.get_hist_data_em(stock=stock)     
                        models=user_def_models(df=hist) 
                        for name in  factor_name:
                            try:
                            
                                func=user_factor[name] 
                                func='models.{}'.format(func)
                                result=eval(func)
                                result_list.append(result)
                            
                            except Exception as e:
                                print(e,'函数计算错误')
                                result_list.append(None)
                            
                    
                    except Exception as e:
                        print(e,'数据获取错误')
                    
                        

                    user_factor_list.append(result_list)
                if len(user_factor_list[0])<len(factor_name):
                    df1=pd.DataFrame()
                else:
                    df1=pd.DataFrame(user_factor_list)
                    df1.columns=factor_name
                    df1['证券代码']=stock_list
                    df=pd.merge(df,df1,on=['证券代码'])
                df.to_excel(r'{}\定义选股算法\定义选股算法.xlsx'.format(self.path))
            else:
                print('自定义算法没有数据')
                df.to_excel(r'{}\定义选股算法\定义选股算法.xlsx'.format(self.path))
        else:
            df.to_excel(r'{}\定义选股算法\定义选股算法.xlsx'.format(self.path))
        return df 
    def get_user_analysis_factor(self):
        '''
        定义分析算法选股
        '''
        print('定义分析算法选股********************')
        with open(r'{}\小果指数趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        df=pd.read_excel(r'{}\定义选股算法\定义选股算法.xlsx'.format(self.path))
        df1=df
        try:
            del df['Unnamed: 0']
        except:
            pass
        user_factor=text['自定义因子选择']
        factor_name=list(user_factor.keys())
        or_df=pd.DataFrame()
        select_select=[]
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            all_columns=df.columns.tolist()
            if len(factor_name)>0:
                for name in factor_name:
                    if name  in all_columns:
                        select=user_factor[name]['选择类型']
                        select_select.append(select)
                        try:
                            df[name]=pd.to_numeric(df[name])
                        except:
                            pass
                        try:
                            if select=='and':
                                min_value=user_factor[name]['区间'][0]
                                max_value=user_factor[name]['区间'][-1]
                                df=df[df[name]>=min_value]
                                df=df[df[name]<=max_value]
                            elif select=='or':
                                    min_value=user_factor[name]['区间'][0]
                                    max_value=user_factor[name]['区间'][-1]
                                    df2=df1[df1[name]>=min_value]
                                    df2=df2[df2[name]<=max_value]
                                    or_df=pd.concat([or_df,df2],ignore_index=True)

                            else:
                                print('未知的选择类型1')
                        except Exception as e:
                            print(e)
                            try:
                                if select=='and':
                                    factor_list=user_factor[name]['区间']
                                    df['select']=df[name].apply(lambda x: '是' if x in factor_list else '不是')
                                    df=df[df['select']=='是']
                                elif select=='or':
                                    factor_list=user_factor[name]['区间']
                                    df['select']=df[name].apply(lambda x: '是' if x in factor_list else '不是')
                                    df2=df[df['select']=='是']
                                    or_df=pd.concat([or_df,df2],ignore_index=True)
                                else:
                                    print('未知的选择类型2')
                            except Exception as e:
                                print(e)
                                if select=='and':
                                    factor=user_factor[name]['区间']
                                    df=df[df[name]==factor]
                                elif select=='or':
                                    factor=user_factor[name]['区间']
                                    df2=df1[df1[name]==factor]
                                    or_df=pd.concat([or_df,df2],ignore_index=True)
                        print('{}因子分析完成'.format(name))
                    else:
                        print('{}因子不在因子表里面'.format(name))
                if 'and' in select_select:
                    print(df)
                    print(or_df)
                    df=pd.concat([df,or_df],ignore_index=True)
                else:
                    df=or_df
                    print(df)
                df.to_excel(r'{}\自定义因子数据选择\自定义因子数据选择.xlsx'.format(self.path))
            else:
                print('没有设置自定义因子默认全部因子')
                df.to_excel(r'{}\自定义因子数据选择\自定义因子数据选择.xlsx'.format(self.path))
        else:
            print('没有因子数据************')
            df.to_excel(r'{}\自定义因子数据选择\自定义因子数据选择.xlsx'.format(self.path))
        return df
    def get_deal_etf(self):
        '''
        剔除一样的etf
        '''

        df=pd.read_excel(r'{}\自定义因子数据选择\自定义因子数据选择.xlsx'.format(self.path))
        df=df.drop_duplicates(subset=['证券代码'])
        df.to_excel(r'{}\剔除一样ETF\剔除一样ETF.xlsx'.format(self.path))
        return df
    def get_user_def_rank(self):
        '''
        自定义因子排序
        '''
        print('定义分析算法选股********************')
        with open(r'{}\小果指数趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        factor_rank=text['选股因子排序']
        rank_type=factor_rank['排序方式']
        rank_list=factor_rank['排序因子']
        df=pd.read_excel(r'{}\剔除一样ETF\剔除一样ETF.xlsx'.format(self.path))
        try:
            del df['Unnamed: 0']
        except:
            pass
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            columns_list=df.columns.tolist()
            for factor in rank_list:
                if factor not in columns_list:
                    rank_list.remove(factor)
                else:
                    pass
            if rank_list=='升序':
                rank_type=True
            else:
                rank_type=False
            df.sort_values(by=rank_list,ascending=rank_type,inplace=True)
            df.to_excel(r'{}\自定义因子排序\自定义因子排序.xlsx'.format(self.path))
        else:
            df=pd.DataFrame()
            df.to_excel(r'{}\自定义因子排序\自定义因子排序.xlsx'.format(self.path))
        return df
    def get_user_def_func_models_sell(self):
        '''
        自定义函数卖出分析模型
        '''
        with open(r'{}\小果指数趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        is_open=text['是否开启自定义卖出函数']
        user_factor=text['自定义卖出函数']
        factor_name=list(user_factor.keys())
        df=pd.read_excel(r'持股数据\持股数据.xlsx')
        try:
            del df['Unnamed: 0']
        except:
            pass
        if is_open=='是':
            print('开启自定义分析算法')
            if df.shape[0]>0:
                user_factor_list=[]
                stock_list=df['证券代码'].tolist()
                for i in tqdm(range(len(stock_list))):
                    stock=stock_list[i]  
                    result_list=[]
                    try: 
                        hist=self.data.get_hist_data_em(stock=stock)     
                        models=user_def_models(df=hist) 
                        for name in  factor_name:
                            try:
                                func=user_factor[name] 
                                func='models.{}'.format(func)
                                result=eval(func)
                                result_list.append(result)
                            except Exception as e:
                                print(e,'函数计算错误')
                                result_list.append(None)
                    except Exception as e:
                        print(e,'数据获取错误')
                        
                    user_factor_list.append(result_list)
                if len(user_factor_list[0])<len(factor_name):
                    df1=pd.DataFrame()
                else:
                    df1=pd.DataFrame(user_factor_list)
                    df1.columns=factor_name
                    df1['证券代码']=stock_list
                    df=pd.merge(df,df1,on=['证券代码'])
                df.to_excel(r'{}\自定义卖出因子\自定义卖出因子.xlsx'.format(self.path))
            else:
                print('自定义算法没有数据')
                df.to_excel(r'{}\自定义卖出因子\自定义卖出因子.xlsx'.format(self.path))
        else:
            df.to_excel(r'{}\自定义卖出因子\自定义卖出因子.xlsx'.format(self.path))
        return df
    def get_user_analysis_factor_sell(self):
        '''
        定义分析算法卖出
        '''
        print('定义分析卖出********************')
        with open(r'{}\小果指数趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        df=pd.read_excel(r'{}\自定义卖出因子\自定义卖出因子.xlsx'.format(self.path))
        df1=df
        try:
            del df['Unnamed: 0']
        except:
            pass
        user_factor=text['自定义卖出因子选择']
        factor_name=list(user_factor.keys())
        or_df=pd.DataFrame()
        select_select=[]
        if df.shape[0]>0:
            all_columns=df.columns.tolist()
            if len(factor_name)>0:
                for name in factor_name:
                    if name  in all_columns:
                        select=user_factor[name]['选择类型']
                        select_select.append(select)
                        try:
                            df[name]=pd.to_numeric(df[name])
                        except:
                            pass
                        try:
                            if select=='and':
                                min_value=user_factor[name]['区间'][0]
                                max_value=user_factor[name]['区间'][-1]
                                df=df[df[name]>=min_value]
                                df=df[df[name]<=max_value]
                            elif select=='or':
                                min_value=user_factor[name]['区间'][0]
                                max_value=user_factor[name]['区间'][-1]
                                df2=df1[df1[name]>=min_value]
                                df2=df2[df2[name]<=max_value]
                                or_df=pd.concat([or_df,df2],ignore_index=True)
                            else:
                                print('未知的选择类型1')
                        except Exception as e:
                            print(e,1,name)
                            try:
                                if select=='and':
                                    factor_list=user_factor[name]['区间']
                                    df['select']=df[name].apply(lambda x: '是' if x in factor_list else '不是')
                                    df=df[df['select']=='是']
                            
                                elif select=='or':
                                    df=df1
                                    factor_list=user_factor[name]['区间']
                                    df['select']=df[name].apply(lambda x: '是' if x in factor_list else '不是')
                                    df2=df[df['select']=='是']
                                    or_df=pd.concat([or_df,df2],ignore_index=True)
                                else:
                                    print('未知的选择类型2')
                            except Exception as e:
                                print(e,2,name)
                                if select=='and':
                                    factor=user_factor[name]['区间']
                                    df=df[df[name]==factor]
                                elif select=='or':
                                    factor=user_factor[name]['区间']
                                    df2=df1[df1[name]==factor]
                                    or_df=pd.concat([or_df,df2],ignore_index=True)
                            
                        print('{}因子分析完成'.format(name))
                    else:
                        print('{}因子不在因子表里面'.format(name))
                if 'and' in select_select:
                    print(df)
                    print(or_df)
                    df=pd.concat([df,or_df],ignore_index=True)
                    df=df.drop_duplicates(keep='last')
                else:
                    df=or_df
                    df=df.drop_duplicates(keep='last')
                    print(df)
                df.to_excel(r'{}\自定义卖出因子选择\自定义卖出因子选择.xlsx'.format(self.path))
            else:
                print('没有设置自定义因子默认全部因子')
                df.to_excel(r'{}\自定义卖出因子选择\自定义卖出因子选择.xlsx'.format(self.path))
        else:
            print('没有因子数据************')
            df=pd.DataFrame()
            df.to_excel(r'{}\自定义卖出因子选择\自定义卖出因子选择.xlsx'.format(self.path))
    def get_buy_sell_stock_data(self):
        '''
        获取买卖数据
        '''
        with open(r'{}\小果指数趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
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
        buy_df=pd.read_excel(r'{}\自定义因子排序\自定义因子排序.xlsx'.format(self.path))
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
        sell_df=pd.read_excel(r'{}\自定义卖出因子选择\自定义卖出因子选择.xlsx'.format(self.path))
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
            sell_df=sell_df[sell_df['交易品种']=='stock']
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
            buy_df=buy_df.drop_duplicates(subset=['证券代码'])
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
    def get_time_rotation(self):
        '''
        轮动方式
        '''
        with open('{}/小果指数趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        now_date=''.join(str(datetime.now())[:10].split('-'))
        now_time=time.localtime()                               
        trader_type=text['轮动方式']                               
        trader_wday=text['每周轮动时间']                               
        moth_trader_time=text['每月轮动时间']
        specific_time=text['特定时间']
        year=now_time.tm_year
        moth=now_time.tm_mon
        wday=now_time.tm_wday
        daily=now_time.tm_mday
        if trader_type=='每天':
            print('轮动方式每天')
            return True
        elif trader_type=='每周':
            if trader_wday==wday:
                return True
            elif trader_wday<wday:
                print('安周轮动 目前星期{} 轮动时间星期{} 目前时间大于轮动时间不轮动'.format(wday+1,trader_wday+1))
                return False
            else:
                print('安周轮动 目前星期{} 轮动时间星期{} 目前时间小于轮动时间不轮动'.format(wday+1,trader_wday+1))
                return False
        elif trader_type=='每月轮动时间':
            stats=''
            for date in moth_trader_time:
                data=''.join(data.split('-'))
                if int(moth_trader_time)==int(date):
                    print('安月轮动 目前{} 轮动时间{} 目前时间等于轮动时间轮动'.format(now_date,date))
                    stats=True
                    break
                elif int(moth_trader_time)<int(date):
                    print('安月轮动 目前{} 轮动时间{} 目前时间小于轮动时间轮动'.format(now_date,date))
                    stats=False
                else:
                    print('安月轮动 目前{} 轮动时间{} 目前时间大于轮动时间轮动'.format(now_date,date))
                    stats=False
            return stats
        else:
            #特别时间
            stats=''
            for date in specific_time:
                data=''.join(data.split('-'))
                if int(specific_time)==int(date):
                    print('安月轮动 目前{} 轮动时间{} 目前时间等于轮动时间轮动'.format(now_date,date))
                    stats=True
                    break
                elif int(specific_time)<int(date):
                    print('安月轮动 目前{} 轮动时间{} 目前时间小于轮动时间轮动'.format(now_date,date))
                    stats=False
                else:
                    print('安月轮动 目前{} 轮动时间{} 目前时间大于轮动时间轮动'.format(now_date,date))
                    stats=False
            return stats                    
    def update_all_data(self):
        '''
        更新策略数据
        '''
        with open(r'{}\小果指数趋势增强策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        if self.get_time_rotation()==True:
            
            self.save_position()
            self.get_trader_stock_data()
            self.get_solation_strategy()
            self.get_user_def_func_models()
            self.get_user_analysis_factor()
            self.get_deal_etf()
            self.get_user_def_rank()
            self.get_user_def_func_models_sell()
            self.get_user_analysis_factor_sell()
            self.get_buy_sell_stock_data()
            self.get_del_sell_stock()
            self.get_del_not_trader_stock()
            
        else:
            print("今天{} 不是是轮动时间".format(datetime.now()))

        