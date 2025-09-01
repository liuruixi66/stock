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
import time
class xueqiou_trading_strategy:
    
    def __init__(self,trader_tool='qmt',exe='C:/同花顺软件/同花顺/xiadan.exe',tesseract_cmd='C:/Program Files/Tesseract-OCR/tesseract',
                qq='1029762153@qq.com',open_set='否',qmt_path='D:/国金证券QMT交易端/userdata_mini',
                qmt_account='8882514071',qmt_account_type='STOCK',name='run_xueqiou_trading_strategy'):
        '''
        雪球跟单模型
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
    def set_slippage(self,stock='600031',price=12,trader_type='buy'):
        '''
        设置滑点
        '''
        with open(r'{}\雪球跟单设置.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        slippage_type=text['滑点类型']
        value=text['滑点值']
        if slippage_type=='百分比':
            if trader_type=='buy':
                price=price*(1+value)
            else:
                price=price*(1-value)
        elif slippage_type=='数值':
            if trader_type=='buy':
                price=price+value
            else:
                price=price-value
        else:
            price=price
        stock=str(stock)[:6]
        data_type=self.select_data_type(stock=stock)
        if data_type=='stock':
            price=round(price,2)
        else:
             price=round(price,3)
        return price
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
    def get_del_buy_sell_data(self,name='',assembly_id='ZH3223683'):
        '''
        处理交易数据
        '''
        with open(r'{}\雪球跟单设置.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        cookie=text['雪球cookie']
        models=xueqie_data(cookie=cookie,assembly_id=assembly_id)
        df=pd.read_excel(r'持股数据\持股数据.xlsx',dtype='object')
        df1=df[df['股票余额']>=10]
        df1['证券代码']=df1['证券代码'].astype(str)
        hold_stock_list=df1['证券代码'].tolist()
        df=models.get_hist_move()
        try:
            now_date=str(datetime.now())[:10]
        except Exception as e:
            print(e)
            trader_time=self.stock_data.get_trader_date_list()
            now_date=trader_time[-1]
        if df.shape[0]>0:
            print('不开同步持股')
            df['updated_at']=pd.to_datetime(df['updated_at'],unit='ms')
            df['created_at']=pd.to_datetime(df['created_at'],unit='ms')
            df['updated_at']=df['updated_at'].apply(lambda x:str(x)[:10])
            df1=df[df['updated_at']==now_date]
            if df1.shape[0]>0:
                print('策略{} {}今天有交易数据'.format(name,now_date))
                print(df1)
                df=df1
                df['证券代码']=df['stock_symbol'].apply(lambda x:str(x)[2:])
                df['证券代码']=df['证券代码'].astype(str)
                df['prev_weight']=df['prev_weight'].fillna(0)
                df['adjust']=df['target_weight']-df['prev_weight']
                df=df.sort_values(by='created_at',ascending=True)
                df.to_excel(r'{}\原始数据\原始数据.xlsx'.format(self.path))
            else:
                print('策略{} {}今天没有交易数据'.format(name,now_date))
                df=pd.DataFrame()
                df.to_excel(r'{}\原始数据\原始数据.xlsx'.format(self.path))

        else:
            print('策略{} {}今天没有交易数据'.format(name,now_date))
            df=pd.DataFrame()
            df.to_excel(r'{}\原始数据\原始数据.xlsx'.format(self.path))
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
            print(df)
        else:
            df=pd.DataFrame()
            df.to_excel(r'{}\交易股票池\交易股票池.xlsx'.format(self.path))
    def get_trader_data(self):
        '''
        获取交易数据
        '''
        with open(r'{}\雪球跟单设置.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        adjust_ratio=text['账户跟单比例']
        disk_ptice=text['下单的价格']
        other_stock=text['特殊交易标的']
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
            trader_log['证券代码']=trader_log['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
        except:
            pass
        try:
            del trader_log['Unnamed: 0']
        except:
            pass
        if df.shape[0]>0:
            if trader_log.shape[0]>0:
                trader_id_list=trader_log['id'].tolist()
            else:
                trader_id_list=[]
            df['交易情况']=df['id'].apply(lambda x : '已经下单' if x in trader_id_list else '没有下单')
            df=df[df['交易情况']=='没有下单']
            print('没有下单的交易*****************************')
            print(df)
            if df.shape[0]>0:
                df['证券名称']=df['stock_name']
                df['自动价格']='是'
                df['价格']=df['price']
                df['交易类型']='数量'
                df['交易方向']=df['adjust'].apply(lambda x : 'buy' if x>=0 else 'sell')
                df['交易状态']=df['交易方向'].apply(lambda x :'未买' if x=='buy' else '未卖')
                amount_list=[]
                for stock ,trader,adjust,target_weight, in zip(df['证券代码'],df['交易方向'],df['adjust'],df['target_weight']):
                    try:
                        stock=str(stock)
                        try:
                            price=self.get_disk_port_data(stock=stock,data_type=disk_ptice)
                            if str(stock)[:6] in other_stock:
                                price=price/10
                            else:
                                price=price
                        except Exception as e:
                            print(e,'((((((((((((((获取盘口数据有问题(((())))))))))))))))))')
                            price=self.data.get_spot_data(stock=stock)['最新价']
                            if str(stock)[:6] in other_stock:
                                price=price/10
                            else:
                                price=price
                        #adjust=(adjust*adjust_ratio)/100
                        adjust=(target_weight*adjust_ratio)/100
                        if trader=='buy':
                            price=self.set_slippage(stock=stock,price=price,trader_type=trader)
                            trader_type,trader_amount,price=self.trader.order_target_percent(stock=stock,target_percent=adjust,price=price)
                            print(trader_type,trader_amount,price,'))))))))))))))))))))))))))')
                            if trader_type=='buy' and trader_amount>=10:
                                #trader_type,amount,price=self.trader.order_percent(stock=stock,price=price,percent=adjust,trader_type=trader)
                                amount_list.append(trader_amount)
                            else:
                                amount_list.append(0)
                        elif trader=='sell':
                            price=self.set_slippage(stock=stock,price=price,trader_type=trader)
                            adjust=abs(adjust)
                            trader_type,trader_amount,price=self.trader.order_target_percent(stock=stock,target_percent=adjust,price=price)
                            if trader_type=='sell' and trader_amount>=10:
                                #trader_type,amount,price=self.trader.order_percent(stock=stock,price=price,percent=adjust,trader_type=trader)
                                amount_list.append(trader_amount)
                            else:
                                amount_list.append(0)
                        else:
                            amount_list.append(0)
                    except Exception as e:
                        print(e)
                        amount_list.append(0)
                df['数量']=amount_list
                not_trader=df[df['数量']<=0]
                #数量为0的不进入下单记录
                df=df[df['数量']>=10]
                print('下单股票池））））））））））））））））））））））））')
                print(df)
                print('下单数量为0的标的可能没有持股,可能账户没有资金等待下次成交########################################################')
                print(not_trader)
                df.to_excel(r'{}\下单股票池\下单股票池.xlsx'.format(self.path))
                trader_log=pd.concat([trader_log,df],ignore_index=True)
                trader_log.to_excel(r'{}\跟单记录\跟单记录.xlsx'.format(self.path))
            else:
                print('没有需要下单标度******************')
                df=pd.DataFrame()
                df.to_excel(r'{}\下单股票池\下单股票池.xlsx'.format(self.path))
        else:
            print('没有交易股票池*************')
            df=pd.DataFrame()
            df.to_excel(r'{}\下单股票池\下单股票池.xlsx'.format(self.path))
    def start_trader_on(self):
        '''
        开始下单
        '''
        with open(r'{}\雪球跟单设置.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        disk_ptice=text['下单的价格']
        other_stock=text['特殊交易标的']
        df=pd.read_excel(r'{}\下单股票池\下单股票池.xlsx'.format(self.path))
        try:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
        except:
            pass
        try:
            del df['Unnamed: 0']
        except:
            pass
        #资金模式
        cash_models=text['资金模式']
        #下单模式
        trader_models=text['下单交易模式']
        #自定义资金设置
        data_type=text['交易模式']
        value=text['固定交易资金']
        limit_value=text['持有金额限制']
        amount1=text['固定交易数量']
        limit_amount=text['持股限制']
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].astype(str)
            #print(df['证券代码'])
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            if cash_models=='雪球' and trader_models=='通过综合交易模型':
                buy_df=df[df['交易方向']=='buy']
                if buy_df.shape[0]>0:
                    buy_df=buy_df[['证券代码','证券名称','自动价格','价格','交易类型','数量','交易状态']]
                    buy_df.to_excel(r'自定义买入股票\自定义买入股票.xlsx')
                else:
                    print('{} {} 没有买入股票'.format(cash_models,trader_models))
                sell_df=df[df['交易方向']=='sell']
                if sell_df.shape[0]>0:
                    sell_df=sell_df[['证券代码','证券名称','自动价格','价格','交易类型','数量','交易状态']]
                    sell_df.to_excel(r'自定义卖出股票\自定义卖出股票.xlsx')
                else:
                    print('{} {} 没有卖出股票'.format(cash_models,trader_models))
            elif cash_models=='自定义' and trader_models=='通过综合交易模型':
                buy_df=df[df['交易方向']=='buy']
                if buy_df.shape[0]>0:
                    buy_df=buy_df[['证券代码','证券名称','交易状态']]
                    buy_df.to_excel(r'买入股票\买入股票.xlsx')
                else:
                    print('{} {} 没有买入股票'.format(cash_models,trader_models))
                sell_df=df[df['交易方向']=='sell']
                if sell_df.shape[0]>0:
                    sell_df=sell_df[['证券代码','证券名称','交易状态']]
                    sell_df.to_excel(r'卖出股票\卖出股票.xlsx')
                else:
                    print('{} {} 没有卖出股票'.format(cash_models,trader_models))
            #先卖在买
            elif cash_models=='雪球' and trader_models=='立马下单':
                sell_df=df[df['交易方向']=='sell']
                if sell_df.shape[0]>0:
                    for stock,amount in zip(sell_df['证券代码'],sell_df['数量']):
                        try:
                            price=self.get_disk_port_data(stock=stock,data_type=disk_ptice)
                            if str(stock)[:6] in other_stock:
                                price=price/10
                            else:
                                price=price
                        except Exception as e:
                            print(e,'((((((((((((((获取盘口数据有问题(((())))))))))))))))))')
                            price=self.data.get_spot_data(stock=stock)['最新价']
                            if str(stock)[:6] in other_stock:
                                price=price/10
                            else:
                                price=price
                        try:
                            price=self.set_slippage(stock=stock,price=price,trader_type='sell')
                            self.trader.sell(security=stock,price=price,amount=amount)
                            print('{} {} 卖出 股票{} 数量{} 价格{}'.format(cash_models,trader_models,stock,amount,price))
                        except Exception as e:
                            print(e)
                            print('{} {} 卖出 股票{} 有问题'.format(cash_models,trader_models,stock))
                else:
                    print('{} {} 没有卖出股票'.format(cash_models,trader_models))
                buy_df=df[df['交易方向']=='buy']
                if buy_df.shape[0]>0:
                    for stock,amount in zip(buy_df['证券代码'],buy_df['数量']):
                        try:
                            price=self.get_disk_port_data(stock=stock,data_type=disk_ptice)
                            if str(stock)[:6] in other_stock:
                                price=price/10
                            else:
                                price=price
                        except Exception as e:
                            print(e,'((((((((((((((获取盘口数据有问题(((())))))))))))))))))')
                        try:
                            price=self.data.get_spot_data(stock=stock)['最新价']
                            if str(stock)[:6] in other_stock:
                                price=price/10
                            else:
                                price=price
                            price=self.set_slippage(stock=stock,price=price,trader_type='buy')
                            self.trader.buy(security=stock,price=price,amount=amount)
                            print('{} {} 买入 股票{} 数量{} 价格{}'.format(cash_models,trader_models,stock,amount,price))
                        except Exception as e:
                            print(e)
                            print(print('{} {} 买入 股票{} 有问题'.format(cash_models,trader_models,stock)))
                else:
                    print('{} {} 没有买入股票'.format(cash_models,trader_models))
            #先卖在买
            elif cash_models=='自定义' and trader_models=='立马下单':
                sell_df=df[df['交易方向']=='sell']
                if sell_df.shape[0]>0:
                    for stock in sell_df['证券代码'].tolist():
                        try:
                            price=self.get_disk_port_data(stock=stock,data_type=disk_ptice)
                            if str(stock)[:6] in other_stock:
                                price=price/10
                            else:
                                price=price
                        except Exception as e:
                            print(e,'((((((((((((((获取盘口数据有问题(((())))))))))))))))))')
                            price=self.data.get_spot_data(stock=stock)['最新价']
                            if str(stock)[:6] in other_stock:
                                price=price/10
                            else:
                                price=price
                        try:
                            trader_type,amount,price=self.trader.check_av_target_trader(data_type=data_type,trader_type='sell',
                                        amount=amount1,limit_volume=limit_amount,value=value,limit_value=limit_value,
                                        stock=stock,price=price)
                            if trader_type=='sell':
                                price=self.set_slippage(stock=stock,price=price,trader_type='sell')
                                self.trader.sell(security=stock,price=price,amount=amount)
                                print('{} {} 卖出 股票{} 数量{} 价格{}'.format(cash_models,trader_models,stock,amount,price))
                            else:
                                print('{} {} 卖出 股票{} 数量{} 价格{} 不可以交易'.format(cash_models,trader_models,stock))
                        except Exception as e:
                            print(e)
                            print(print('{} {} 卖出 股票{} 有问题'.format(cash_models,trader_models,stock)))
                else:
                    print('{} {} 没有卖出股票'.format(cash_models,trader_models))
                buy_df=df[df['交易方向']=='buy']
                if buy_df.shape[0]>0:
                    for stock,amount in zip(buy_df['证券代码'],buy_df['数量']):
                        try:
                            price=self.get_disk_port_data(stock=stock,data_type=disk_ptice)
                            if str(stock)[:6] in other_stock:
                                price=price/10
                            else:
                                price=price
                        except Exception as e:
                            print(e,'((((((((((((((获取盘口数据有问题(((())))))))))))))))))')
                            price=self.data.get_spot_data(stock=stock)['最新价']
                            if str(stock)[:6] in other_stock:
                                price=price/10
                            else:
                                price=price
                        try:
                            trader_type,amount,price=self.trader.check_av_target_trader(data_type=data_type,trader_type='buy',
                                    amount=amount1,limit_volume=limit_amount,value=value,limit_value=limit_value,
                                    stock=stock,price=price)
                            if trader_type=='buy':
                                price=self.set_slippage(stock=stock,price=price,trader_type='buy')
                                self.trader.buy(security=stock,price=price,amount=amount)
                                print('{} {} 买入 股票{} 数量{} 价格{}'.format(cash_models,trader_models,stock,amount,price))
                            else:
                                print('{} {} 买入 股票{} 数量{} 价格{} 不可以交易'.format(cash_models,trader_models,stock))
                        except Exception as e:
                            print(e)
                            print(print('{} {} 买入 股票{} 有问题'.format(cash_models,trader_models,stock)))
                else:
                    print('{} {} 没有买入股票'.format(cash_models,trader_models))
            else:
                print('未知的下单模式***********************')
        else:
            print('没有需要下单的数据**************************')
    # def delete_folder_contents_path(self,folder_path):
    #     for item in os.listdir(folder_path):
    #         item_path = os.path.join(folder_path, item)
    #         if os.path.isfile(item_path):
    #             os.remove(item_path)
    #             print('{}删除成功'.format(item))
    #         elif os.path.isdir(item_path):
    #             shutil.rmtree(item_path)
    #             print('{}删除成功'.format(item))
    #         else:
    #             print(item,'文件夹为空')
    # def delete_folder_contents(self):
    #     '''
    #     删除缓存内容
    #     '''
    #     print('删除缓存内容*********************')
    #     import shutil
    #     with open(r'分析配置.json',encoding='utf-8') as f:
    #         com=f.read()
    #     text=json.loads(com)
    #     with open(r'{}\雪球跟单设置.json'.format(self.path),encoding='utf-8') as f:
    #         com=f.read()
    #     text1=json.loads(com)
    #     qmt_path=text['qmt路径']
    #     desktop_path=text1['桌面路径']
    #     try:
    #         os.makedirs(name=r'{}\del_data'.format(desktop_path))
    #     except:
    #         pass
    #     del_com=r'{}\del_data'.format(desktop_path)
    #     del_com=del_com.replace('\\',"/")
    #     all_path=os.listdir(path=qmt_path)
    #     if len(all_path)>0:
    #         for path in all_path:
    #             if path[:5]=='down_':
    #                 del_path=os.path.join(qmt_path, path)
    #                 del_path=del_path.replace('\\',"/")
    #                 try:
    #                     shutil.move(del_path,del_com)
    #                 except Exception as e:
    #                     print(e)
    #             else:
    #                 pass
    #         try:
    #             shutil.rmtree(r'{}'.format(del_com))
    #         except:
    #             pass
    #     else:
    #         print('文件夹下面没有文件')
    def update_all_data(self):
        '''
        更新策略数据
        '''
        if self.base_func.check_is_trader_date_1():
            import time
            with open(r'{}\雪球跟单设置.json'.format(self.path),encoding='utf-8') as f:
                com=f.read()
            text=json.loads(com)
            name_list=text['组合名称']
            zu_list=text['组合id']
            update_time=text['不同策略间隔更新时间']
            for name,zu in zip(name_list,zu_list):
                try:
                    print(self.save_position())
                except Exception as e:
                    print(e)
                try:
                    print(self.save_balance())
                except Exception as e:
                    print(e)
                self.get_del_buy_sell_data(name=name,assembly_id=zu)
                self.get_del_not_trader_stock()
                self.get_trader_data()
                self.start_trader_on()
                # self.delete_folder_contents()
                time.sleep(update_time*60)
        else:
            print('雪球跟单{} 目前不是交易时间***************'.format(datetime.now()))
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
    trader=xueqie_trader(trader_tool=trader_tool,exe=exe,tesseract_cmd=tesseract_cmd,qq=qq,
                           open_set=open_set,qmt_path=qmt_path,qmt_account=qmt_account,
                           qmt_account_type=qmt_account_type)
    schedule.every(0.08).minutes.do(trader.update_all_data)
    while True:
        schedule.run_pending()
        time.sleep(1)