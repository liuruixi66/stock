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
from tdx_strategy_models.small_fruit_band_trading import small_fruit_band_trading
#债券模型
from trader_tool.base_func import base_func
class commodity_trend_strategy:
    def __init__(self,trader_tool='ths',exe='C:/同花顺软件/同花顺/xiadan.exe',tesseract_cmd='C:/Program Files/Tesseract-OCR/tesseract',
                qq='1029762153@qq.com',open_set='否',qmt_path='D:/国金QMT交易端模拟/userdata_mini',
                qmt_account='55009640',qmt_account_type='STOCK',name='run_commodity_trend_strategy'):
        '''
        商品趋势策略
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
        with open(r'{}\商品趋势策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        text['持股限制']=hold_limit
        text['持有限制']=hold_limit
        #保存
        with open(r'{}\商品趋势策略.json'.format(self.path),'w',encoding='utf-8') as f:
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
        with open(r'{}\商品趋势策略.json'.format(self.path),encoding='utf-8') as f:
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
        df=pd.read_excel(r'{}\自定义交易股票池\自定义交易股票池.xlsx'.format(self.path))
    def get_buy_stock_analysis(self):
        '''
        买入股票分析波段分析
        '''
        with open(r'{}\商品趋势策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        n=text['买入统计天数']
        m=text['买入符合天数']
        print('买入股票分析****************')
        df=pd.read_excel(r'持股数据\持股数据.xlsx',dtype='object')
        df1=df[df['股票余额']>=10]
        df1['证券代码']=df1['证券代码'].astype(str)
        if df1.shape[0]>0:
            df1['证券代码']=df1['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            hold_stock_list=df1['证券代码'].tolist()
        else:
            hold_stock_list=[]
        trader_df=pd.read_excel(r'{}\自定义交易股票池\自定义交易股票池.xlsx'.format(self.path),dtype='object')
        if trader_df.shape[0]>0:
            trader_df['证券代码']=trader_df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            trader_df['证券代码']=trader_df['证券代码'].astype(str)
            def select_data(stock):
                if str(stock) in hold_stock_list:
                    return '持股超过限制'
                else:
                    return '没有持股'
            trader_df['持股检查']=trader_df['证券代码'].apply(select_data)
            trader_df=trader_df[trader_df['持股检查'] !='持股超过限制']
            if trader_df.shape[0]>0:
                stock_list=trader_df['证券代码'].tolist()
                buy_list_stats=[]
                buy_amount_list=[]
                for i in tqdm(range(len(stock_list))):
                    stock=stock_list[i]
                    try:
                        hist=self.data.get_hist_data_em(stock=stock)
                        models=small_fruit_band_trading(df=hist)
                        models=models.small_fruit_band_trading()
                        models['stats']=models['stats'].fillna(method='ffill')
                        buy_list=models['stats'].tolist()[-n:]
                        buy=models['stats'].tolist()[-1]
                        buy_amount=buy_list.count('买')
                        buy_list_stats.append(buy)
                        buy_amount_list.append(buy_amount)
                    except Exception as e:
                        print(e,'{}买入波段分析有问题'.format(stock))
                        buy_list_stats.append(None)
                        buy_amount_list.append(None)
                df=trader_df
                df['买']=buy_list_stats
                df['买的数量']=buy_amount_list
                df.to_excel(r'{}\买入股票分析\买入股票分析.xlsx'.format(self.path))
                df=df[df['买']=='买']
                df=df[df['买的数量']>=m]
                df.to_excel(r'{}\买入股票\买入股票.xlsx'.format(self.path))
            else:
                print('没有需要买入的数据买入分析')
                df=pd.DataFrame()
                df.to_excel(r'{}\买入股票\买入股票.xlsx'.format(self.path))
                df.to_excel(r'{}\买入股票分析\买入股票分析.xlsx'.format(self.path))
        else:
            print('没有自定义股票池数据买入分析')
            df=pd.DataFrame()
            df.to_excel(r'{}\买入股票\买入股票.xlsx'.format(self.path))
            df.to_excel(r'{}\买入股票分析\买入股票分析.xlsx'.format(self.path))
    def get_sell_stock_analysis(self):
        '''
        卖出股票分析波段分析
        '''
        with open(r'{}\商品趋势策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        n=text['卖出统计天数']
        m=text['卖出符合天数']
        print('卖出股票分析****************')
        df=pd.read_excel(r'持股数据\持股数据.xlsx',dtype='object')
        df1=df[df['股票余额']>=10]
        df1['证券代码']=df1['证券代码'].astype(str)
        if df1.shape[0]>0:
            stock_list=df1['证券代码'].tolist()
            sell_list_stats=[]
            sell_amount_list=[]
            for i  in tqdm(range(len(stock_list))):
                stock=stock_list[i]
                try:
                    hist=self.data.get_hist_data_em(stock=stock)
                    models=small_fruit_band_trading(df=hist)
                    models=models.small_fruit_band_trading()
                    models['stats']=models['stats'].fillna(method='ffill')
                    sell_list=models['stats'].tolist()[-n:]
                    sell=sell_list[-1]
                    sell_amount=sell_list.count('卖')
                    sell_list_stats.append(sell)
                    sell_amount_list.append(sell_amount)
                except Exception as e:
                    print(e,'{}卖出波段分析有问题'.format(stock))
                    sell_list_stats.append(None)
                    sell_amount_list.append(None)
            df1['卖']=sell_list_stats
            df1['卖的数量']=sell_amount_list
           
            df1=df1[df1['卖']=='卖']
           
            df1=df1[df1['卖的数量']>=m]
            print(df1)
            df1.to_excel(r'{}\卖出股票\卖出股票.xlsx'.format(self.path))
            df1.to_excel(r'{}\卖出股票分析\卖出股票分析.xlsx'.format(self.path))
        else:
            print('没有卖出股票*********************')
            df1=pd.DataFrame()
            df1.to_excel(r'{}\卖出股票\卖出股票.xlsx'.format(self.path))
            df1.to_excel(r'{}\卖出股票分析\卖出股票分析.xlsx'.format(self.path))
    def get_buy_sell_stock_data(self):
        '''
        获取买卖数据
        '''
        with open(r'{}\商品趋势策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        hold_limit=text['持股限制']
        hold_stock=pd.read_excel(r'持股数据\持股数据.xlsx')
        try:
            del hold_stock['Unnamed: 0']
        except:
            pass
        if hold_stock.shape[0]>0:
            hold_stock=hold_stock[hold_stock['股票余额']>=10]
            if hold_stock.shape[0]>0:
                hold_stock['证券代码']=hold_stock['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
                hold_stock_list=hold_stock['证券代码'].tolist()
                hold_amount=hold_stock.shape[0]
            else:
                hold_stock_list=[]
                hold_amount=0
        else:
            hold_stock_list=[]
            hold_amount=0
        buy_df=pd.read_excel(r'{}\买入股票\买入股票.xlsx'.format(self.path))
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
        sell_df=pd.read_excel(r'{}\卖出股票\卖出股票.xlsx'.format(self.path))
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
            self.get_buy_stock_analysis()
            self.get_sell_stock_analysis()
            self.get_buy_sell_stock_data()
            self.get_del_sell_stock()
            self.get_del_not_trader_stock()
           
        else:
            print('没有不是交易时间,修改hi哦啊有时间在更新************')

        