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
import numpy as np
import os
from datetime import datetime
import time
from trader_tool.lude_data_api import lude_data_api
from .user_def_factor import user_def_factor
from trader_tool.unification_data import unification_data
from xg_data.xg_data import xg_data
from jsl_data_xg_api.jsl_data_xg_api import jsl_data_xg_api
from trader_tool.xg_bond_factor_data import xg_bond_factor_data
class xg_bond_cov_3_low_strategy:
    def __init__(self,trader_tool='ths',exe='C:/同花顺软件/同花顺/xiadan.exe',tesseract_cmd='C:/Program Files/Tesseract-OCR/tesseract',
                qq='1029762153@qq.com',open_set='否',qmt_path='D:/国金QMT交易端模拟/userdata_mini',
                qmt_account='55009640',qmt_account_type='STOCK',name='run_xg_bond_cov_3_low_strategy'):
        '''
        小果可转债3低轮动策略        
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
        self.name=name
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        self.url=text['服务器']
        self.port=text['端口']
        self.password=text['授权码']
        self.lude_data=lude_data_api(url=self.url,port=self.port,password=self.password)
        self.unification_data=unification_data()
        self.data=self.unification_data.get_unification_data()
        with open(r'分析配置.json',encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        cash_set=text['多策略资金设置']
        name_list=list(cash_set.keys())
        if  self.name in name_list:
            hold_limit=cash_set[self.name]['持股限制']
        else:
            hold_limit=cash_set['其他策略']['持股限制']
        with open(r'{}\小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        text['持股限制']=hold_limit
        text['持有限制']=hold_limit
        #保存
        with open(r'{}\小果可转债3低轮动策略.json'.format(self.path),'w',encoding='utf-8') as f:
            json.dump(text, f,ensure_ascii=False,indent=2)
        self.trader.connect()
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
        def select_del_stock_list(x):
            if str(x)[:6] in del_stock_list:
                return '是'
            else:
                return '否'
        df=self.trader.position()
        def select_bond_cov(x):
            '''
            选择可转债
            '''
            if x[:3] in ['110','113','123','127','128','111','118'] or x[:2] in ['11','12']:
                return '是'
            else:
                return '不是'
        try:
            if df==False:
                print('获取持股失败')
        except:
            if df.shape[0]>0:
                df['选择']=df['证券代码'].apply(select_bond_cov)
                try:
                    df['持股天数']=df['持股天数'].replace('--',1)
                except:
                    df['持股天数']=1
                df1=df[df['选择']=='是']
                df1=df1[df1['股票余额']>=10]
                df1['黑名单']=df1['证券代码'].apply(select_del_stock_list)
                df1=df1[df1['黑名单']=='否']
                print('剔除黑名单**********')
                df1.to_excel(r'持股数据\持股数据.xlsx')
                return df1
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
        print(df)
    def select_bond_cov(self,x):
        '''
        选择证券代码
        '''
        if x[:3] in ['110','113','123','127','128','111'] or x[:2] in ['11','12']:
            return '是'
        else:
            return '不是'
    def save_balance(self):
        '''
        保持账户数据
        '''
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        df=self.trader.balance()
        df.to_excel(r'账户数据\账户数据.xlsx')
        return df
    def get_all_lude_data(self):
        '''
        获取可转债全部数据
        '''
        print('获取可转债全部数据')
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        data_type=text['数据源']
        jsl_user=text['集思录账户']
        jsl_password=text['集思录密码']
        url=text['服务器']
        port=text['端口']
        url_code=text['服务器编码']
        user_password=text['授权码']
        test=text['是否测试']
        if test=='是':
            print('启动测试数据')
            now_date=text['测试时间']
        else:
            now_date=''.join(str(datetime.now())[:10].split('-'))
        if data_type=='集思录':
            try:
                jsl_data_xg=jsl_data_xg_api(user=jsl_user,password=jsl_password,limit=10000)
                df=jsl_data_xg.get_user_def_func_models()
                try:
                    df['证券代码']=df['可转债代码']
                except:
                    pass
                if df.shape[0]==0:
                    try:
                        print('集思录没有输入账户登录失败,启动小果可转债数据服务器****')
                        api=xg_bond_factor_data(url=url,port=port,url_code=url_code,password=user_password)
                        df=api.xg_bond_factor_data(date_type='合成因子',date=now_date)
                        stats=df['数据状态'].tolist()[-1]
                        if stats==True or stats=='True' or stats=='true':
                            df=df
                        else:
                            print(df)
                            df=pd.DataFrame()
                    except Exception as e:
                        print(e,'{}可能数据没有更新************'.format(now_date))
                        df=pd.DataFrame()
                        print(df)
                else:
                    df=df
            except Exception as e:
                print(e)
                try:
                    api=xg_bond_factor_data(url=url,port=port,url_code=url_code,password=user_password)
                    df=api.xg_bond_factor_data(date_type='合成因子',date=now_date)
                    stats=df['数据状态'].tolist()[-1]
                    if stats==True or stats=='True' or stats=='true':
                        df=df
                    else:
                        print(df)
                        df=pd.DataFrame()
                except Exception as e:
                    print(e,'{}可能数据没有更新************'.format(now_date))
                    df=pd.DataFrame()
                    print(df)
        else:
            try:
                api=xg_bond_factor_data(url=url,port=port,url_code=url_code,password=user_password)
                df=api.xg_bond_factor_data(date_type='合成因子',date=now_date)
                stats=df['数据状态'].tolist()[-1]
                if stats==True or stats=='True' or stats=='true':
                    df=df
                else:
                    print(df)
                    df=pd.DataFrame()
            except Exception as e:
                print(e,'{}可能数据没有更新************'.format(now_date))
                df=pd.DataFrame()
                print(df)
        df.to_excel(r'{}\全部数据\全部数据.xlsx'.format(self.path))
        print(df)
        return df
    def get_cacal_factor_base_table(self):
        '''
        计算默认因子
        '''
        print('计算默认因子***********************')
        with open('{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        is_open=text['是否开启默认因子计算']
        df=pd.read_excel(r'{}\全部数据\全部数据.xlsx'.format(self.path))
        if df.shape[0]>0:
            try:
                del df['Unnamed: 0']
                del df['Unnamed: 0.1']
            except:
                pass
            factor=text['默认因子计算']
            if is_open=='是':
                print('开启计算默认因子***********************')
                factor_name=list(factor.keys())
                if len(factor_name)>0:
                    for name in factor_name:
                        try:
                            print(name,'因子计算完成')
                            func=factor[name]
                            df[name]=eval(func)
                        except Exception as e:
                            print(name,'因子计算有问题')
                else:
                    print('没有默认因子需要计算')
            else:
                print('不开启计算默认因子***********************')
        else:
            print('默认因子计算没有数据可能不是交易日')
            df=pd.DataFrame()
        df.to_excel(r'{}\默认因子计算\默认因子计算.xlsx'.format(self.path))
        return df
    def get_del_qzsh_data(self):
        '''
        剔除强制赎回
        '''
        print('剔除强制赎回')
        with open('{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        del_select=text['是否剔除强制赎回']
        n=text['满足强制赎回天数']
        df=pd.read_excel(r'{}\默认因子计算\默认因子计算.xlsx'.format(self.path))
        if df.shape[0]>0:
            try:
                del df['Unnamed: 0']
                del df['Unnamed: 0.1']
            except:
                pass
            try:
                select_list=['公告要强赎','已公告']
                df['强赎']=df['强赎提示'].apply(lambda x : '是' if '公告要强赎' in x or '已公告' in x else '不是')
                df1=df[df['强赎']=='是']
                df1.to_excel(r'{}\强制赎回\强制赎回.xlsx'.format(self.path))
                df2=df[df['强赎']=='不是']
                df2['强赎天计数']=df2['强赎提示'].apply(lambda x: '0/15 | 30' if str(x)[:4]=='暂不强赎' or '不强赎' in x else x)
                #df2['强赎天数']=df2['强赎提示'].apply(lambda x: int(str(x).split('/')[0]))
                #df2=df2[df2['强赎天数']<=n]
                df2.to_excel(r'{}\非强制赎回\非强制赎回.xlsx'.format(self.path))
            except Exception as e:
                df2=df
                
        else:
            print('非强制赎回没有数据可能不是交易日')
            df2=pd.DataFrame()
        df2.to_excel(r'{}\非强制赎回\非强制赎回.xlsx'.format(self.path))
        return df2
    def days_excluded_from_market(self):
        '''
        排除上市天数
        '''
        print('排除上市天数')
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        df=pd.read_excel(r'{}\非强制赎回\非强制赎回.xlsx'.format(self.path),dtype='object')
        if df.shape[0]>0:
            try:
                try:
                    del df['Unnamed: 0']
                    del df['Unnamed: 0.1']
                except:
                    pass
                n=text['排除上市天数']
                trader_list=self.stock_data.get_trader_date_list()
                start_date=trader_list[-n]
                try:
                    df=df[df['上市日']<=start_date]
                except:

                    df['上市天数']=df['上市天数'].apply(lambda x: float(str(x).split('days')[0]))
                    df=df[df['上市天数']>=n]
            except:
                df=pd.DataFrame()
        else:
            print('排除上市天数没有数据可能不是交易日')
            df=pd.DataFrame()
        df.to_excel(r'{}\排除上市天数\排除上市天数.xlsx'.format(self.path))
        return df
    def st_exclusion(self):
        '''
        排除st
        '''
        print('排除st')
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        is_del=text['是否排除ST']
        df=pd.read_excel(r'{}\排除上市天数\排除上市天数.xlsx'.format(self.path))
        if df.shape[0]>0:
            try:
                try:
                    del df['Unnamed: 0']
                except:
                    pass
                if is_del=='是':
                    def_list=['ST','st','*ST','*st']
                    df['ST']=df['正股名称'].apply(lambda x: '是' if 'st' in x or 'ST' in x or '*st' in x or '*ST' in x else '不是' )
                    df=df[df['ST']=='不是']
                else:
                    df=df
            except:
                df=pd.DataFrame()
        else:
            print('排除上市天数没有数据可能不是交易日')
            df=pd.DataFrame()
        df.to_excel(r'{}\排除ST\排除ST.xlsx'.format(self.path))
        return df
    def exclusion_of_market(self):
        '''
        排除市场
        '''
        print("排除市场")
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        exclusion_market_list = []
        del_stock_list=text['排除市场']
        for exclusion_market in del_stock_list:
            if exclusion_market == '沪市主板':
                exclusion_market_list.append(['110','113'])
            elif exclusion_market == '深市主板':
                exclusion_market_list.append(['127','128'])
            elif exclusion_market == '创业板':
                exclusion_market_list.append('123')
            elif exclusion_market == '科创板':
                exclusion_market_list.append('118')
            else:
                pass
        df=pd.read_excel(r'{}\排除ST\排除ST.xlsx'.format(self.path))
        if df.shape[0]>0:
            try:
                del df['Unnamed: 0']
            except:
                pass
            try:
                print(exclusion_market_list,"__________________________________________")
                df['market'] = df['可转债代码'].apply(lambda x: '排除' if str(x)[:3] in exclusion_market_list  else '不排除')
                df = df[df['market'] == '不排除']
                    
            except:
                df=pd.DataFrame()
        else:
            print('排除市场没有数据可能不是交易日')
            df=pd.DataFrame()
        df.to_excel(r'{}\排除市场\排除市场.xlsx'.format(self.path))
    def excluded_industry(self):
        '''
        排除行业
        '''
        print('排除行业')
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        del_list=text['排除行业']
        df=pd.read_excel(r'{}\排除市场\排除市场.xlsx'.format(self.path))
        if df.shape[0]>0:
            try:
                try:
                    del df['Unnamed: 0']
                except:
                    pass
                industry_list=[]
                data=pd.DataFrame()
                industry_1=df['一级行业'].tolist()
                for i in industry_1:
                    industry_list.append(i)
                industry_2=df['二级行业'].tolist()
                for i in industry_2:
                    industry_list.append(i)
                industry_3=df['三级行业'].tolist()
                for i in industry_3:
                    industry_list.append(i)
                industry_list=list(set(industry_list))
                data['可转债行业']=industry_list
                data.to_excel(r'{}\可转债行业\可转债行业.xlsx'.format(self.path))
                industry_name=['一级行业','二级行业','三级行业']
                for name in industry_name:
                    df['行业排除']=df[name].apply(lambda x: '是' if x in del_list else '不是')
                    df=df[df['行业排除']=='不是']
                df.to_excel(r'{}\排除行业\排除行业.xlsx'.format(self.path))
                return df
            except:
                df.to_excel(r'{}\排除行业\排除行业.xlsx'.format(self.path))
        else:
            print('排除行业没有数据可能不是交易日')
            df=pd.DataFrame()
        df.to_excel(r'{}\排除行业\排除行业.xlsx'.format(self.path))
        return df
    def exclusion_of_enterprise(self):
        '''
        排除企业
        '''
        print('排除企业')
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        df=pd.read_excel(r'{}\排除行业\排除行业.xlsx'.format(self.path))
        if df.shape[0]>0:
            '''
            try:
                del df['Unnamed: 0']
            except:
                pass
            del_list=text['排除企业类型']
            df['排除企业']=df['企业类型'].apply(lambda x:'是' if str(x) in del_list else '不是')
            df=df[df['排除企业']=='不是']
            '''
        else:
            print('排除企业没有数据可能不是交易日')
            df=pd.DataFrame()
        df.to_excel(r'{}\排除企业\排除企业.xlsx'.format(self.path))
        return df
    def exclusion_area(self):
        '''
        排除地域
        '''
        print('排除地域')
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        df=pd.read_excel(r'{}\排除企业\排除企业.xlsx'.format(self.path))
        if df.shape[0]>0:
            try:
                try:
                    del df['Unnamed: 0']
                except:
                    pass
                del_list=text['排除地域']
                df['排除地域']=df['地域'].apply(lambda x:'是' if str(x) in del_list else '不是')
                df=df[df['排除地域']=='不是']
                df.to_excel(r'{}\排除地域\排除地域.xlsx'.format(self.path))
                return df
            except:
                df.to_excel(r'{}\排除地域\排除地域.xlsx'.format(self.path))
        else:
            print('排除企业没有数据可能不是交易日')
            df=pd.DataFrame()
        df.to_excel(r'{}\排除地域\排除地域.xlsx'.format(self.path))
        return df
    def exclusion_of_external_rating(self):
        '''
        排除外部评级
        '''
        print('排除外部评级')
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        df=pd.read_excel(r'{}\排除地域\排除地域.xlsx'.format(self.path))
        if df.shape[0]>0:
            try:
                try:
                    del df['Unnamed: 0']
                except:
                    pass
                del_list=text['排除外部评级']
                df['排除外部评级']=df['主体评级'].apply(lambda x:'是' if str(x) in del_list else '不是')
                df=df[df['排除外部评级']=='不是']
                df.to_excel(r'{}\排除外部评级\排除外部评级.xlsx'.format(self.path))
                return df
            except:
                df.to_excel(r'{}\排除外部评级\排除外部评级.xlsx'.format(self.path))
        else:
            print('排除外部评级没有数据可能不是交易日')
            df=pd.DataFrame()
        df.to_excel(r'{}\排除外部评级\排除外部评级.xlsx'.format(self.path))
        return df
    def tripartite_exclusion(self):
        '''
        排除三方评级
        '''
        print('排除三方评级')
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        df=pd.read_excel(r'{}\排除外部评级\排除外部评级.xlsx'.format(self.path))
        if df.shape[0]>0:
            try:
                try:
                    del df['Unnamed: 0']
                except:
                    pass
                del_list=text['排除三方评级']
                df['排除三方评级']=df['主体评级'].apply(lambda x:'是' if str(x) in del_list else '不是')
                df=df[df['排除三方评级']=='不是']
                df.to_excel(r'{}\排除三方评级\排除三方评级.xlsx'.format(self.path))
            except:
                df.to_excel(r'{}\排除三方评级\排除三方评级.xlsx'.format(self.path))
        else:
            print('排除外部评级没有数据可能不是交易日')
            df=pd.DataFrame()
        df.to_excel(r'{}\排除三方评级\排除三方评级.xlsx'.format(self.path))
        return df
    def cacal_user_def_factor(self):
        '''
        计算自定义因子
        '''
        print('计算自定义因子')
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        df=pd.read_excel(r'{}\排除三方评级\排除三方评级.xlsx'.format(self.path))
        if df.shape[0]>0:
            try:
                del df['Unnamed: 0']
            except:
                pass
            is_open=text['是否开启自定义因子']
            user_def_factor_list=text['自定义因子']
            name_list=list(user_def_factor_list.keys())
            func_list=list(user_def_factor_list.values())
            value_list=[]
            if is_open=='是':
                print('开启自定义因子****************')
                stock_list=df['证券代码'].tolist()
                for i in tqdm(range(len(stock_list))):
                    stock=stock_list[i]
                    hist=self.data.get_hist_data_em(stock=stock)
                    models=user_def_factor(df=hist,index_df='')
                    func_value=[]
                    for func in func_list:
                        name,value=eval('models.{}'.format(func))
                        func_value.append(value)
                    value_list.append(func_value)
                user_df=pd.DataFrame(value_list)
                user_df.columns=name_list
                user_df['证券代码']=stock_list
                data=pd.merge(df,user_df,on='证券代码')
                data.to_excel(r'{}\自定义因子\自定义因子.xlsx'.format(self.path))       
            else:
                print('不开启自定义函数')
                df.to_excel(r'{}\自定义因子\自定义因子.xlsx'.format(self.path))
        else:
            print('自定义因子没有数据可能不是交易日')
            df=pd.DataFrame()
        df.to_excel(r'{}\自定义因子\自定义因子.xlsx'.format(self.path))
        return df
    def cacal_exclusion_factor(self):
        '''
        计算排除因子
        '''
        print('计算排除因子')
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        df=pd.read_excel(r'{}\自定义因子\自定义因子.xlsx'.format(self.path))
        if df.shape[0]>0:
            try:
                del df['Unnamed: 0']
                del df['Unnamed: 0.1']
                del df['Unnamed: 0.2']
            except:
                pass
            factor_list=text['排除因子']
            factor_func_list=text['因子计算符号']
            factor_value_list=text['因子值']
            all_factor_list=df.columns.tolist()
            for factor,func,value in zip(factor_list,factor_func_list,factor_value_list):
                if factor in all_factor_list:
                    try:
                        df[factor]=pd.to_numeric(df[factor])
                        df[factor]=df[factor].astype(float)
                        if func=='大于':
                        
                            df=df[df[factor]<=value]
                            
                        elif func=='小于':
                            
                            df=df[df[factor]>=value]
                        
                        elif func=='大于排名%':
                            df=df.sort_values(by=factor,ascending=True)[value:]
                        elif func=='小于排名%':
                            df=df.sort_values(by=factor,ascending=True)[:value]
                        elif func=='空值':
                            df=df
                        else:
                            print('{}未知的计算方式'.format(func))
                    except Exception as e:
                        print('{} 排除因子计算有问题{} '.format(factor,e))
                else:
                    print('{}排除因子不在全部的因子表里面全部因子表'.format(factor))
        else:
            print('排除因子没有数据可能不是交易日')
            df=pd.DataFrame()
        df.to_excel(r'{}\排除因子\排除因子.xlsx'.format(self.path))
        return df
    def cacal_score_factor(self):
        '''
        计算打分因子
        升序从小到大
        降序从大到小
        '''
        print("计算打分因子")
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        df=pd.read_excel(r'{}\排除因子\排除因子.xlsx'.format(self.path))
        if df.shape[0]>0:
            try:
                del df['Unnamed: 0']
            except:
                pass
            factor_list=text['打分因子']
            factor_cov_list=text['因子相关性']
            factor_weight_list=text['因子权重']
            all_factor_list=df.columns.tolist()
            score_list=[]
            for factor,cov,weight in zip(factor_list,factor_cov_list,factor_weight_list):
                if factor in all_factor_list:
                    try:
                        if cov=='正相关':
                            df[factor]=df[factor]*1
                        elif cov=='负相关':
                            df[factor]=df[factor]*-1
                        else:
                            print('{}未知的相关性'.format(cov))
                        df['{}_得分'.format(factor)]=df[factor].rank(ascending=False)*weight
                        score_list.append('{}_得分'.format(factor))
                    except Exception as e:
                        print('{} 打分因子计算有问题{} '.format(factor,e))
                else:
                    print('{}打分因子不在全部的因子表里面全部因子表{}'.format(factor,all_factor_list))
            df['总分']=df[score_list].sum(axis=1).tolist()
            df['排名']=df['总分'].rank( ascending=True)
            df=df.sort_values(by='总分',ascending=True)
            
        else:
            print('打分因子没有数据可能不是交易日')
            df=pd.DataFrame()
        df.to_excel(r'{}\打分因子\打分因子.xlsx'.format(self.path))
        return df
    def get_del_buy_sell_data(self):
        '''
        处理交易股票池买入股票
        '''
        print('处理交易股票池买入股票')
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        limit=text['持股限制']
        data_type=text['数据源']
        df=pd.read_excel(r'持股数据\持股数据.xlsx')
        df['证券代码']=df['证券代码'].astype(str)
        df1=df[df['股票余额']>=10]
        hold_stock_list=df1['证券代码'].tolist()
        trader_df=pd.read_excel(r'{}\打分因子\打分因子.xlsx'.format(self.path))
        
        if trader_df.shape[0]>0:
            trader_df['证券代码']=trader_df['证券代码'].astype(str)
            def select_data(stock):
                if stock in hold_stock_list:
                    return '持股超过限制'
                else:
                    return '没有持股'
            trader_df['持股检查']=trader_df['证券代码'].apply(select_data)
            trader_df=trader_df[trader_df['持股检查'] =='没有持股']
        else:
            trader_df=pd.DataFrame()
        trader_df.to_excel(r'{}\交易股票池\交易股票池.xlsx'.format(self.path))
        return trader_df                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
    def get_buy_sell_stock(self):
        '''
        获取买卖数据
        '''
        with open('{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        buy_num=text['买入排名前N']
        hold_rank_num=text['持有排名前N']
        sell_rank_num=text['跌出排名卖出N']
        hold_limit=text['持有限制']
        df=pd.read_excel(r'持股数据\持股数据.xlsx',dtype='object')
        df['证券代码']=df['证券代码'].astype(str)
        df1=df[df['股票余额']>=10]
        hold_stock_list=df1['证券代码'].tolist()
        def select_stock(x):
            '''
            选择etf
            '''
            if x in hold_stock_list:
                return '持股'
            else:
                return "持股不足"
        try:
            del df['Unnamed: 0']
        except:
            pass
        trader_df=pd.read_excel(r'{}\交易股票池\交易股票池.xlsx'.format(self.path),dtype='object')
        if trader_df.shape[0]>0:
            trader_df['证券代码']=trader_df['证券代码'].astype(str)
            try:
                del trader_df['Unnamed: 0']
            except:
                pass
            print('交易股票池*******************')
            trader_df['选择']=trader_df['证券代码'].apply(select_stock)
            trader_df=trader_df[trader_df['选择']=='持股不足']
            try:
                del trader_df['Unnamed: 0']
            except:
                pass
        else:
            trader_df=pd.DataFrame()
        if df1.shape[0]>0:
            #卖出列表
            sell_list=[]
            #持股列表
            hold_stock_list=df['证券代码'].tolist()
            #跌出排名卖出N
            rank_df=pd.read_excel(r'{}\打分因子\打分因子.xlsx'.format(self.path))
            if rank_df.shape[0]>0:
                rank_df['证券代码']=rank_df['证券代码'].astype(str)
                sell_rank_stock=rank_df['证券代码'].tolist()[:sell_rank_num]   
                all_rank_stock=rank_df['证券代码'].tolist()
            else:
                sell_rank_stock=[]
                all_rank_stock=[]
            if len(sell_rank_stock)>0:
                for stock in hold_stock_list:
                    if stock in sell_rank_stock:
                        print('{} 在持有排名里面排名{}**************'.format(stock,all_rank_stock.index(stock)))
                    else:
                        print('{} 不在持有排名里面排名******************'.format(stock))
                        sell_list.append(stock)
            else:
                print('没有排名数据((((((((((()))))))))))')
            sell_list=list(set(sell_list))
            sell_df=pd.DataFrame()
            sell_df['证券代码']=sell_list
            sell_df['交易状态']='未卖'
            if sell_df.shape[0]>0:
                print('卖出etf*****************')
                print(sell_df)
                sell_df['策略名称']=self.name
               
                sell_df.to_excel(r'{}\卖出股票\卖出股票.xlsx'.format(self.path))
            else:
                print('没有卖出etf')
                sell_df['证券代码']=None
                sell_df['交易状态']=None
               
                sell_df['策略名称']=self.name
                sell_df.to_excel(r'{}\卖出股票\卖出股票.xlsx'.format(self.path))
            hold_num=df1.shape[0]
            if hold_num>0:
                av_buy_num=hold_limit-hold_num
                av_buy_num=av_buy_num+sell_df.shape[0]
                if av_buy_num>=hold_limit:
                    av_buy_num=hold_limit
                else:
                    av_buy_num=av_buy_num
                buy_df=trader_df[:av_buy_num]
            else:
                buy_df=trader_df[:buy_num]
            buy_df['交易状态']='未买'
            df['证券代码']=df['证券代码']
            buy_df['策略名称']=self.name
            buy_df.to_excel(r'{}\买入股票\买入股票.xlsx'.format(self.path))
            return buy_df
        else:
            print('没有持股（（（（（（（（（（（（（（（（（（（（（（（（（（（（（（（（（（')
            sell_df=pd.DataFrame()
            sell_df.to_excel(r'{}\卖出股票\卖出股票.xlsx'.format(self.path))
            buy_df=trader_df[:buy_num]
            buy_df['交易状态']='未买'
            buy_df['策略名称']=self.name
            buy_df.to_excel(r'{}\买入股票\买入股票.xlsx'.format(self.path))
            return buy_df
    
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
        if buy_df.shape[0]>0:
            buy_df['证券代码']=buy_df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            try:
                del buy_df['Unnamed: 0']
            except:
                pass
            buy_df['黑名单']=buy_df['证券代码'].apply(select_del_stock_list)
            buy_df=buy_df[buy_df['黑名单']=='否']
            #隔离策略
            buy_df['证券代码']=buy_df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            buy_df['品种']=buy_df['证券代码'].apply(lambda x: self.trader.select_data_type(x))
            print('买入股票））））））））））））））））））））')
            buy_df=buy_df[buy_df['品种']=='bond']
            buy_df['策略名称']=self.name
            buy_df.to_excel(r'买入股票\买入股票.xlsx')
            print(buy_df)
        else:
            print("没有买入的股票））））））））））））））")
        #卖出
        sell_df=pd.read_excel(r'{}\卖出股票\卖出股票.xlsx'.format(self.path),dtype='object')
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
            print('卖出股票））））））））））））））））））））')
            sell_df=sell_df[sell_df['品种']=='bond']
            sell_df['策略名称']=self.name
            sell_df.to_excel(r'卖出股票\卖出股票.xlsx')
            print(sell_df)
        else:
            print('没有卖出的股票）））））））））））））））））））')
    def get_time_rotation(self):
        '''
        轮动方式
        '''
        with open('{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
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
    def updata_all_data(self):
        '''
        更新全部数据
        '''
        with open(r'{}/小果可转债3低轮动策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        if self.get_time_rotation()==True:
            print("今天{} 是轮动时间".format(datetime.now()))
            self.save_position()
            self.save_balance()
            self.get_all_lude_data()
            self.get_cacal_factor_base_table()
            self.get_del_qzsh_data()
            self.days_excluded_from_market()
            self.st_exclusion()
            self.exclusion_of_market()
            self.excluded_industry()
            self.exclusion_of_enterprise()
            self.exclusion_area()
            self.exclusion_of_external_rating()
            self.tripartite_exclusion()
            self.cacal_user_def_factor()
            self.cacal_exclusion_factor()
            self.cacal_score_factor()
            self.get_del_buy_sell_data()
            self.get_buy_sell_stock()
            self.get_del_not_trader_stock()
        else:
            print("今天{} 不是是轮动时间".format(datetime.now()))