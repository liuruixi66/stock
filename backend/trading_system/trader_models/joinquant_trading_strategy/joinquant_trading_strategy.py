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
from trader_tool.xueqie_data import xueqie_data
from datetime import datetime
from trader_tool.base_func import base_func
from qmt_trader.qmt_data import qmt_data
import shutil
import schedule
from trader_tool.xg_jq_data import xg_jq_data
import time
class joinquant_trading_strategy:
    def __init__(self,trader_tool='qmt',exe='C:/同花顺软件/同花顺/xiadan.exe',tesseract_cmd='C:/Program Files/Tesseract-OCR/tesseract',
                qq='1029762153@qq.com',open_set='否',qmt_path='D:/国金证券QMT交易端/userdata_mini',
                qmt_account='8882514071',qmt_account_type='STOCK',name='run_joinquant_trading_strategy'):
        '''
       聚宽跟单模型
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
        self.data=unification_data(trader_tool='ths')
        self.data=self.data.get_unification_data()
        self.dfcf_etf_data=dfcf_etf_data()
        #滑点
        self.trader.slippage=0.01
        self.base_func=base_func()
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
        trader_type=text['交易品种']
        def select_del_stock_list(x):
            if str(x)[:6] in del_stock_list:
                return '是'
            else:
                return '否'
        df=self.trader.position()
        try:
            if df==False:
                print('获取持股失败')
        except:
            if df.shape[0]>0:
                if trader_type=='全部':
                    df=df
                else:
                    df['选择']=df['证券代码'].apply(self.trader.select_data_type)
                    df=df[df['选择']==trader_type]
                print(df)
                df=df[df['可用余额']>=10]
                df['黑名单']=df['证券代码'].apply(select_del_stock_list)
                df=df[df['黑名单']=='否']
                print('剔除黑名单**********')
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
    def get_disk_port_data(self,stock='600031.SH',data_type='卖一'):
        price=self.data.get_spot_data(stock=stock)['最新价']
        return price
    def get_del_buy_sell_data(self,name='测试1',password='123456'):
        '''
        处理交易数据
        '''
        with open(r'{}\聚宽跟单设置.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        test=text['是否开启测试']
        url=text['服务器']
        port=text['端口']
        now_date=str(datetime.now())[:10]
        xg_data=xg_jq_data(url=url,port=port,password=password)
        info=xg_data.get_user_data(data_type='用户信息')
        df=xg_data.get_user_data(data_type='实时数据')
        print('用户信息')
        print(info)
        if  df.shape[0]>0:
            stats=df['数据状态'].tolist()[-1]
            if stats==True:
                df['证券代码']=df['股票代码'].apply(lambda x: str(x).split('.XSHE')[0])
                df['数据长度']=df['证券代码'].apply(lambda x: len(str(x)))
                df['订单添加时间']=df['订单添加时间'].apply(lambda x :str(x)[:10])
                df=df[df['数据长度']>=6]
                df['交易类型']=df['买卖'].apply(lambda x: 'buy' if x==True else 'sell')
                df=df.drop_duplicates(subset=['股票代码','下单数量','买卖','多空'],keep='last')
                df['组合名称']=name
                df['组合授权码']=password
                df['证券代码']=df['证券代码'].apply(lambda x: str(x)[:6])
                if test=='是':
                    print('开启测试模式,实盘记得关闭')
                    df=df
                else:
                    df=df[df['订单添加时间']==now_date]
            else:
                df=pd.DataFrame()
        else:
            df=pd.DataFrame()
        if df.shape[0]>0:
            print('组合 {} 策略授权码 {} {}今天跟单数据*********************'.format(name,password,now_date))
            print(df)
        else:
            print('组合 {} 策略授权码 {} {}今天没有跟单数据*********************'.format(name,password,now_date))
        df.to_excel(r'{}\原始数据\原始数据.xlsx'.format(self.path))
        return df
    def get_del_not_trader_stock(self,name='测试1',password='123456'):
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
        df=pd.read_excel(r'{}\原始数据\原始数据.xlsx'.format(self.path),dtype='object')
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            try:
                del df['Unnamed: 0']
            except:
                pass
            df['黑名单']=df['证券代码'].apply(select_del_stock_list)
            df=df[df['黑名单']=='否']
            #隔离策略
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            df['品种']=df['证券代码'].apply(lambda x: self.trader.select_data_type(x))
            df.to_excel(r'{}\交易股票池\交易股票池.xlsx'.format(self.path))
        else:
            df=pd.DataFrame()
            df.to_excel(r'{}\交易股票池\交易股票池.xlsx'.format(self.path))
    def get_trader_data(self,name='测试1',password='123456',zh_ratio=0.1):
        '''
        获取交易数据
        组合的跟单比例
        '''
        with open(r'{}\聚宽跟单设置.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        test=text['是否开启测试']
        adjust_ratio=text['账户跟单比例']
        df=pd.read_excel(r'{}\交易股票池\交易股票池.xlsx'.format(self.path))
        try:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
        except:
            pass
        try:
            del df['Unnamed: 0']
        except:
            pass
        trader_log=pd.read_excel(r'{}\跟单记录\跟单记录.xlsx'.format(self.path))
        try:
            del trader_log['Unnamed: 0']
        except:
            pass
        now_date=str(datetime.now())[:10]
        if trader_log.shape[0]>0:
            trader_log['证券代码']=trader_log['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            trader_log['交易日']=trader_log['交易日'].astype(str)
            #trader_log['订单ID']=trader_log['订单ID'].str(str)
            if test=='是':
                trader_log=trader_log
            else:
                trader_log=trader_log[trader_log['交易日']==now_date]
            trader_log['组合授权码']=trader_log['组合授权码'].astype(str)
            trader_log_1=trader_log[trader_log['组合授权码']==password]
            if trader_log_1.shape[0]>0:
                trader_id_list=trader_log_1['订单ID'].tolist()
            else:
                trader_id_list=[]
        else:
            trader_id_list=[]
        
        if df.shape[0]>0:
            df['组合授权码']=df['组合授权码'].astype(str)
            #df['订单ID ']=df['订单ID'].astype(str)
            df=df[df['组合授权码']==password]
            if df.shape[0]>0:
                df['账户跟单比例']=adjust_ratio
                df['组合跟单比例']=zh_ratio
                df['交易检查']=df['订单ID'].apply(lambda x: '已经交易' if x in trader_id_list else '没有交易')
                df=df[df['交易检查']=='没有交易']
                amount_list=[]
                if df.shape[0]>0:
                    for stock,amount,trader_type in zip(df['证券代码'].tolist(),df['下单数量'].tolist(),df['交易类型'].tolist()):
                        price=self.data.get_spot_data(stock=stock)['最新价']
                        test=text['是否开启测试']
                        test_amount=text['测试数量']
                        down_type=text['下单模式']
                        down_value=text['下单值']
                        if test=='是':
                            value=test_amount*price
                        else:
                            if down_type=='默认':
                                value=price*amount*adjust_ratio*zh_ratio
                            elif down_type=='数量':
                                value=price*down_value*adjust_ratio*zh_ratio
                            elif down_type=='金额':
                                value=down_value
                            else:
                                value=price*amount*adjust_ratio*zh_ratio
                        if trader_type=='buy':
                            try:
                                trader_type,amount,price=self.trader.order_value(stock=stock,value=value,price=price,trader_type='buy')
                                print(trader_type,amount,price)
                                if trader_type=='buy' and amount>=10:
                                    amount=self.trader.adjust_amount(stock=stock,amount=amount)
                                    amount_list.append(amount)
                                else:
                                    amount_list.append(0)
                            except Exception as e:
                                
                                print('组合{} 组合授权码{} {}买入有问题可能没有资金'.format(name,password,stock))
                                amount_list.append(0)
                        elif trader_type=='sell':
                            try:
                                trader_type,amount,price=self.trader.order_value(stock=stock,value=value,price=price,trader_type='sell')
                                if trader_type=='sell' and amount>=10:
                                    amount=self.trader.adjust_amount(stock=stock,amount=amount)
                                    amount_list.append(amount)
                                else:
                                    amount_list.append(0)
                            except Exception as e:
                               
                                print('组合{} 组合授权码{} {}卖出有问题可能没有持股'.format(name,password,stock))
                                amount_list.append(0)
                        else:
                            print('组合{} 组合授权码{} {}未知的交易类型'.format(name,password,stock))
                    df['数量']=amount_list
                    not_trader=df[df['数量']<=0]
                    #数量为0的不进入下单记录
                    df=df[df['数量']>=10]
                    print('下单股票池））））））））））））））））））））））））')
                    print(df)
                    print('下单数量为0的标的可能没有持股,可能账户没有资金等待下次成交########################################################')
                    print(not_trader)
                    df.to_excel(r'{}\下单股票池\下单股票池.xlsx'.format(self.path))
                    df.to_excel(r'数据.xlsx')
                    trader_log=pd.concat([trader_log,df],ignore_index=True)
                    trader_log=trader_log.drop_duplicates(subset=['订单添加时间','订单ID','组合授权码','组合名称'],keep='last')
                    trader_log.to_excel(r'{}\跟单记录\跟单记录.xlsx'.format(self.path))
                else:
                    print('{}组合没有需要下单标度******************'.format(name))
                    df=pd.DataFrame()
                    df.to_excel(r'{}\下单股票池\下单股票池.xlsx'.format(self.path))
            else:
                print('{}没有这个组合*************'.format(name))
                df=pd.DataFrame()
                df.to_excel(r'{}\下单股票池\下单股票池.xlsx'.format(self.path))
        else:
            print('{}交易股票池没有数据*************'.format(name))
            df=pd.DataFrame()
            df.to_excel(r'{}\下单股票池\下单股票池.xlsx'.format(self.path))
    def start_trader_on(self,name='测试1',password='123456'):
        '''
        开始下单
        '''
        with open(r'{}\聚宽跟单设置.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        df=pd.read_excel(r'{}\下单股票池\下单股票池.xlsx'.format(self.path))
       
        try:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
        except:
            pass
        try:
            del df['Unnamed: 0 ']
        except:
            pass
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].astype(str)
            #print(df['证券代码'])
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            #先卖在买
            sell_df=df[df['交易类型']=='sell']
            if sell_df.shape[0]>0:
                for stock,amount, in zip(sell_df['证券代码'].tolist(),sell_df['数量'].tolist()):
                    try:
                        price=self.data.get_spot_data(stock=stock)['最新价']
                        self.trader.sell(security=stock,amount=amount,price=price)
                    except Exception as e:
                        print(e)
                        print('组合{} {}卖出有问题'.format(name,stock))
            else:
                print('{}组合没有符合调参的卖出数据'.format(name))
            buy_df=df[df['交易类型']=='buy']
            if buy_df.shape[0]>0:
                for stock,amount, in zip(buy_df['证券代码'].tolist(),buy_df['数量'].tolist()):
                    try:
                        price=self.data.get_spot_data(stock=stock)['最新价']
                        self.trader.buy(security=stock,amount=amount,price=price)
                    except Exception as e:
                        print(e)
                        print('组合{} {}买入有问题'.format(name,stock))
            else:
                print('{}组合没有符合调参的买入数据'.format(name))
        else:
            print('{}组合没有符合调参数据'.format(name))
    def update_all_data(self):
        '''
        更新策略数据
        '''
        if self.base_func.check_is_trader_date_1():
            import time
            with open(r'{}\聚宽跟单设置.json'.format(self.path),encoding='utf-8') as f:
                com=f.read()
            text=json.loads(com)
            name_list=text['组合名称']
            password_list=text['组合授权码']
            ratio_list=text['组合跟单比例']
            update_time=text['不同策略间隔更新时间']
            for name,password,ratio in zip(name_list,password_list,ratio_list):
                try:
                    print(self.save_position())
                except Exception as e:
                    print(e)
                try:
                    print(self.save_balance())
                except Exception as e:
                    print(e)
                self.get_del_buy_sell_data(name=name,password=password)
                self.get_del_not_trader_stock(name=name,password=password)
                self.get_trader_data(name=name,password=password,zh_ratio=ratio)
                self.start_trader_on(name=name,password=password)
                time.sleep(update_time*60)
        else:
            print('跟单{} 目前不是交易时间***************'.format(datetime.now()))
if __name__=='__main__':
    '''
    跟单
    '''
    with open('分析配置.json','r+',encoding='utf-8') as f:
        com=f.read()
    text=json.loads(com)
    trader_tool=text['交易系统']
    exe=text['同花顺下单路径']
    tesseract_cmd=text['识别软件安装位置']
    qq=text['发送qq']                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
    open_set=text['是否开启特殊证券公司交易设置']
    qmt_path=text['qmt路径']
    qmt_account=text['qmt账户']
    qmt_account_type=text['qmt账户类型']
    trader=joinquant_trading_strategy(trader_tool=trader_tool,exe=exe,tesseract_cmd=tesseract_cmd,qq=qq,
                           open_set=open_set,qmt_path=qmt_path,qmt_account=qmt_account,
                           qmt_account_type=qmt_account_type)
    
    schedule.every(0.08).minutes.do(trader.update_all_data)
    while True:
        schedule.run_pending()
        time.sleep(1)
    
    
    