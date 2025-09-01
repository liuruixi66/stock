import pandas as pd
from tqdm import tqdm
import numpy as np
import json
from qmt_trader.qmt_trader_ths import qmt_trader_ths
from xgtrader.xgtrader import xgtrader
from trader_tool.unification_data import unification_data
import os
import pandas as pd
from trader_tool.base_func import base_func
from trader_tool.small_fruit_data import small_fruit_data
from datetime import datetime
class small_fruit_server_copy_strategy:
    def __init__(self,trader_tool='qmt',exe='C:/同花顺软件/同花顺/xiadan.exe',tesseract_cmd='C:/Program Files/Tesseract-OCR/tesseract',
                qq='1029762153@qq.com',open_set='否',qmt_path='D:/国金QMT交易端模拟/userdata_mini',
                qmt_account='55009640',qmt_account_type='STOCK',name='run_small_fruit_band_trading_strategy'):
        '''
        小果服务器跟单策略
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
    
        self.data=unification_data(trader_tool=self.trader_tool)
        self.data=self.data.get_unification_data()
        self.trader.connect()
        self.base_func=base_func()
        self.path=os.path.dirname(os.path.abspath(__file__))
        with open(r'{}\小果服务器跟单策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        url=text['服务器']
        port=text['端口']
        password=text['服务器授权码']
        url_id=text['服务器id']
        self.xg_data=small_fruit_data(url=url,port=port,password=password,url_id=url_id)
    def save_position(self):
        '''
        保存持股数据
        '''
        df=self.trader.position()
        if df.shape[0]>0:
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
    def get_servre_data(self):
        '''
        获取服务器数据
        '''
        with open(r'{}\小果服务器跟单策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        trader_models=text['跟单模式']
        if trader_models=='委托':
            print('跟单委托模式。读取委托数据***************')
            df=self.xg_data.get_trader_data(data_type='今日委托')
            if df.shape[0]>0:
                df=df[['资金账号','证券代码','委托类型','委托数量','柜台合同编号','委托状态']]
                df.columns=['资金账号','证券代码','类型','数量','柜台合同编号','状态']
                df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
                df['类型']=df['类型'].apply(lambda x: '买' if x in [23,33] else '卖')
            else:
                df=pd.DataFrame()
        else:
            print('跟单委托模式。读取成交数据***************')
            df=self.xg_data.get_trader_data(data_type='今日成交')
            if df.shape[0]>0:
                df=df[['资金账号','证券代码','委托类型','成交数量',"柜台合同编号"]]
                df.columns=['资金账号','证券代码','类型','数量',"柜台合同编号"]
                df['状态']=56
                df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
                df['类型']=df['类型'].apply(lambda x: '买' if x in [23,33] else '卖')
            else:
                df=pd.DataFrame()
        df.to_excel(r'{}\原始数据\原始数据.xlsx'.format(self.path))
        print(df)
        return df
    def get_servre_data_analysis(self):
        '''
        服务器数据分析
        '''
        with open(r'{}\小果服务器跟单策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        trader_models=text['跟单模式']
        df=pd.read_excel(r'{}\原始数据\原始数据.xlsx'.format(self.path))
        try:
            del df['Unnamed: 0']
        except:
            pass
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            #交易状态
            trader_list=[48,49,50,51,52,55,56]
            #撤单状态
            cacal_list=[54,55]
            #废单
            trader_not_list=[57,255]
            df['交易']=df['状态'].apply(lambda x: '是' if x in trader_list else '不是')
            df['撤单']=df['状态'].apply(lambda x: '是' if x in cacal_list else '不是')
            df['废单']=df['状态'].apply(lambda x: '是' if x in trader_not_list else '不是')
            trader_df=df[df['交易']=='是']
            cacal_df=df[df['撤单']=='是']
            trader_not_df=df[df['废单']=='是']
            trader_df.to_excel(r'{}\交易股票池\交易股票池.xlsx'.format(self.path))
            cacal_df.to_excel(r'{}\撤单股票池\撤单股票池.xlsx'.format(self.path))
            trader_not_df.to_excel(r'{}\废单股票池\废单股票池.xlsx'.format(self.path))
        else:
            trader_df=pd.DataFrame()
            cacal_df=pd.DataFrame()
            trader_not_df=pd.DataFrame()
            trader_df.to_excel(r'{}\交易股票池\交易股票池.xlsx'.format(self.path))
            cacal_df.to_excel(r'{}\撤单股票池\撤单股票池.xlsx'.format(self.path))
            trader_not_df.to_excel(r'{}\废单股票池\废单股票池.xlsx'.format(self.path))
        print('可以交易的数据*********')
        print(trader_df)
        print('撤单交易的数据*********')
        print(cacal_df)
        print('废单的数据*********')
        print(trader_not_df)

    def get_trader_data(self):
        '''

        获取交易数据
        下单默认说明":"默认/金额/数量",
        "下单模式":"金额",
        "下单值":1000
        '''
        with open(r'{}\小果服务器跟单策略.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        down_models=text['下单模式']
        value=text['下单值']
        account_ratio=text['账户跟单比例']
        zh_ratio=text['委托比例']
        df=pd.read_excel(r'{}\交易股票池\交易股票池.xlsx'.format(self.path))
        try:
            del df['Unnamed: 0']
        except:
            pass
        try:
            log=pd.read_excel(r'{}\跟单记录\跟单记录.xlsx'.format(self.path))
        except:
            log=pd.DataFrame()
        try:
            del log['Unnamed: 0']
        except:
            pass
        if log.shape[0]>0:
            log['柜台合同编号']=log['柜台合同编号'].astype(str)
            log_list=log['柜台合同编号'].tolist()
        else:
            log_list=[]
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            df['柜台合同编号']=df['柜台合同编号'].astype(str)
            df['已经委托']=df['柜台合同编号'].apply(lambda x: '是' if x in log_list else '不是')
            df=df[df['已经委托']=='不是']
            if df.shape[0]>0:

                amount_list=[]
                for stock,trader_type,amount in zip(df['证券代码'].tolist(),df['类型'].tolist(),df['数量'].tolist()):
                    try:
                        price=self.data.get_spot_data(stock=stock)['最新价']
                        if down_models=='默认':
                            amount=amount*zh_ratio*account_ratio
                        elif down_models=='金额':
                            amount=value/price
                        elif down_models=='数量':
                            amount=value
                        else:
                            amount=amount
                        amount=self.trader.adjust_amount(stock=str(stock),amount=amount)
                        if trader_type=='买':
                            #检查是否可以买入
                            stats=self.trader.check_stock_is_av_buy(stock=stock,price=price,amount=amount)
                            if stats==True:
                                amount_list.append(amount)
                            else:
                                amount_list.append(0)
                        elif trader_type=="卖":
                            stats=self.trader.check_stock_is_av_sell(stock=stock,amount=amount)
                            if stats==True:
                                amount_list.append(amount)
                            else:
                                amount_list.append(0)
                        else:
                            print('{} 未知的交易类型'.format(trader_type))
                            amount_list.append(0)
                    except Exception as e:
                        print(e,'{}交易分析有问题'.format(stock))
                        amount_list.append(0)
                df['下单模式']=down_models
                df['账户跟单比例']=account_ratio
                df['组合跟单比例']=zh_ratio
                df['下单值']=value
                df['可以下单数量']=amount_list
                trader_df=df[df['可以下单数量']>=10]
                trader_not_df=df[df['可以下单数量']<10]
                print('可以下单的数据*********************')
                print(trader_df)
                print('下单数量为0的标的等待下次成交**************')
                print(trader_not_df)
                log=pd.concat([log,trader_df],ignore_index=True)
                log.to_excel(r'{}\跟单记录\跟单记录.xlsx'.format(self.path))

            else:
                print('没有可以交易的数据***************')
                trader_df=pd.DataFrame()
                trader_not_df=pd.DataFrame()
        else:
            print('没有交易股票池数据****************')
            trader_df=pd.DataFrame()
            trader_not_df=pd.DataFrame()
        trader_df.to_excel(r'{}\可以下单的标的\可以下单的标的.xlsx'.format(self.path))
        trader_not_df.to_excel(r'{}\不可以下单的标的\不可以下单的标的.xlsx'.format(self.path))
    def get_start_trader_on(self):
        '''
        开始下单
        '''
        df=pd.read_excel(r'{}\可以下单的标的\可以下单的标的.xlsx'.format(self.path))
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            for stock,trader_type,amount in zip(df['证券代码'].tolist(),df['类型'].tolist(),df['可以下单数量'].tolist()):
                try:
                    price=self.data.get_spot_data(stock=stock)['最新价']
                    if trader_type=='买':
                        self.trader.buy(security=stock,amount=amount,price=price)
                        print('{} 买入{} 数量{} 价格{}'.format(datetime.now(),stock,amount,price))
                    elif trader_type=='卖':
                        self.trader.sell(security=stock,amount=amount,price=price)
                        print('{} 卖出{} 数量{} 价格{}'.format(datetime.now(),stock,amount,price))
                    else:
                        print('{} 不知道交易类型{} 数量{} 价格{}'.format(datetime.now(),stock,amount,price))
                except Exception as e:
                    print('{} 交易有问题{} 数量{} 价格{}'.format(datetime.now(),stock,amount,price))
        else:
            print('{} 没有下单的数据*********'.format(datetime.now()))      
    def updata_all_data(self):
        '''
        更新全部数据
        '''
        if self.base_func.check_is_trader_date_1():
            self.save_position()
            self.save_balance()
            self.get_servre_data()
            self.get_servre_data_analysis()
            self.get_trader_data()
            self.get_start_trader_on()
        else:
            print('{} 目前不是交易时间'.format(datetime.now()))




        
        





    






            

    
            


    
