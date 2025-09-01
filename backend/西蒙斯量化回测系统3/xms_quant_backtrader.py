import pandas as pd
from account.account import account
from position.position import position
from position_log.position_log import position_log
from order.order import order
from data.data import data
import math
import os
from trader_tool.index_data import index_data
import quantstats as qs
import mplfinance as mpf
import matplotlib.pyplot as plt
import numpy as np
import empyrical as ep
import pandas as pd
from pyecharts.components import Table
from pyecharts.charts import Page, Line, Bar
from pyecharts import options as opts
from pyecharts.globals import ThemeType
class xms_quant_backtrader:
    '''
    西蒙斯量化回测系统3.0
    作者:西蒙斯量化
    微信:xg_quant
    '''
    def __init__(
        self,
        trader_tool='ths',
        data_api='dfcf',
        data_type='D',
        stock_list=[],
        start_date='20200101',
        end_date='20500101',
        total_cash=10000,
        st_name='西蒙斯量化回测策略'):
        '''
        数据源支持股票/可转债/etf
        data_dict = {'1': '1', '5': '5', '15': '15', '30': '30', '60': '60', 'D': '101', 'W': '102', 'M': '103'}
        数据格式
          date   open  close   high    low   volume           成交额    振幅   涨跌幅   涨跌额   换手率    证券代码
        0    2021-01-04  34.04  33.59  34.80  33.19  1027586  3.603294e+09  4.77 -0.53 -0.18  1.21  600031
        1    2021-01-05  33.30  35.34  35.59  33.09  1072169  3.824581e+09  7.44  5.21  1.75  1.26  600031
        2    2021-01-06  35.37  35.75  36.25  34.79  1097482  4.029568e+09  4.13  1.16  0.41  1.29  600031
        3    2021-01-07  36.29  39.18  39.45  36.07  1401786  5.461736e+09  9.45  9.59  3.43  1.65  600031
        4    2021-01-08  39.18  39.16  40.17  37.80  1459535  5.862015e+09  6.05 -0.05 -0.02  1.72  600031
        '''
        self.trader_tool=trader_tool
        self.data_api=data_api
        self.data_type=data_type
        self.stock_list=stock_list
        self.start_date=start_date
        self.end_date=end_date
        self.total_cash=total_cash
        self.account=account(
            start_date=self.start_date,
            total_cash=self.total_cash)
        self.position=position()
        self.order=order()
        self.data=data(trader_tool=self.trader_tool,
            data_api=self.data_api,
            start_date=self.start_date,
            end_date=self.end_date,
            data_type=self.data_type)
        self.position_log=position_log()
        self.index_data=index_data()
        self.hist=pd.DataFrame()
        self.price_dict={}
        self.zdf_dict={}
        self.path=os.path.dirname(os.path.abspath(__file__))
        self.st_name=st_name
    def select_data_type(self,stock='600031'):
        '''
        选择数据类型
        '''
        stock=str(stock)
        if stock[:2] in ['11','12'] or stock[:3] in ['123','110','113','123','127','128','118','132','120']:
            return 'bond'
        elif stock[:2] in ['51','15','50','16','18','52']:
            return 'fund'
        else:
            return 'stock'
    def adjust_stock(self,stock='600031.SH'):
        '''
        调整代码
        '''
        if stock[-2:]=='SH' or stock[-2:]=='SZ' or stock[-2:]=='sh' or stock[-2:]=='sz':
            stock=stock.upper()
        else:
            if stock[:3] in ['600','601','603','605','688','689',
                             ] or stock[:2] in ['11','51','58']:
                stock=stock+'.SH'
            else:
                stock=stock+'.SZ'
        return stock
    def adjust_amount(self,stock='',amount=''):
        '''
        调整数量
        '''           
        try:
            amount_num = float(amount) if isinstance(amount, str) else amount
            if stock[:3] in ['110','113','123','127','128','111'] or stock[:2] in ['11','12']:
                amount_num=math.floor(amount_num/10.0)*10
            else:
                amount_num=math.floor(amount_num/100.0)*100
            return int(amount_num)
        except (ValueError, TypeError):
            return 0
        return amount
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
            df['名称']=df['证券代码']
        except Exception as e:
            print(e,'通达信路径有问题可能不存在',path)
            maker='{},通达信路径有问题可能不存在,{}'.format(e,path)
            df=pd.DataFrame()
        return df 
    def re_trader_stock(self,stock_list=[]):
        '''
        重新定义交易股票池
        '''
        self.stock_list=stock_list
        return self.stock_list
    def get_trader_stock(self):
        '''
        获取交易股票池
        '''
        return self.stock_list
    def get_remove_trader_stock(self,stock='600031'):
        ''''
        移除交易股票池
        '''
        try:
            self.stock_list.remove(stock)
            print(stock,'移除成功')
        except Exception as e:
            print(e,'移除失败')
            
    def get_trader_date_list(self):
        '''
        获取全部交易时间
        '''
        if self.hist.shape[0]>0:
            date_list=sorted(list(set(self.hist['date'].tolist())))
        else:
            date_list=[]
        return date_list
    def get_hist_data_thread(self):
        '''
        获取全部的历史数据
        多线程
        '''
        self.data.get_thread_add_data(stock_list=self.stock_list)
        self.hist=self.data.hist
        self.hist['date']=self.hist['date'].astype(str)
        self.hist['date']=self.hist['date'].apply(lambda x:''.join(str(x)[:10].split('-')))
        self.hist['stock']=self.hist['stock'].astype(str)
        for stock in self.stock_list:
            hist=self.hist[self.hist['stock']==stock]
           
            if hist.shape[0]>0:
                price_dict=dict(zip(hist['date'],hist['close']))
                zdf_dict=dict(zip(hist['date'],hist['涨跌幅']))
                self.price_dict[stock]=price_dict
                self.zdf_dict[stock]=zdf_dict
            else:
                self.price_dict[stock]={}
                self.zdf_dict[stock]={}
        else:
            self.price_dict[stock]={}
            self.zdf_dict[stock]={}
        return self.hist
    def get_hist_data(self):
        '''
        获取全部的历史数据
        单线程
        '''
        self.data.get_connect_hist(stock_list=self.stock_list)
        self.hist=self.data.hist
        self.hist['date']=self.hist['date'].astype(str)
        self.hist['date']=self.hist['date'].apply(lambda x:''.join(str(x)[:10].split('-')))
        self.hist['stock']=self.hist['stock'].astype(str)
        for stock in self.stock_list:
            hist=self.hist[self.hist['stock']==stock]
           
            if hist.shape[0]>0:
                price_dict=dict(zip(hist['date'],hist['close']))
                zdf_dict=dict(zip(hist['date'],hist['涨跌幅']))
                self.price_dict[stock]=price_dict
                self.zdf_dict[stock]=zdf_dict
            else:
                self.price_dict[stock]={}
                self.zdf_dict[stock]={}
        self.data.hist=self.hist
        return self.hist
    def get_stock_hist_data(self,stock='600031',start_date='20200101',end_date='20250101'):
        '''
        获取股票历史数据
        '''
        if self.hist.shape[0]>0:
            df=self.hist[self.hist['stock']==stock]
            if df.shape[0]>0:
                df['date']=pd.to_datetime(df['date'])
                df=df[df['date']>=self.start_date]
                df=df[df['date']<=self.end_date]
                df['date']=df['date'].apply(lambda x:''.join(str(x)[:10].split('-')))
            else:
                df=pd.DataFrame()
        else:
            df=pd.DataFrame()
        return df
    def get_user_hist_data(self,df=''):
        '''
        获取自定义历史数据
        '''
        try:
            del df['Unnamed: 0']
        except :
            pass
        self.hist=df
       
        self.hist['date']=self.hist['date'].astype(str)
        self.hist['date']=self.hist['date'].apply(lambda x:''.join(str(x)[:10].split('-')))
        self.hist['stock']=self.hist['stock'].astype(str)
        self.hist['stock']=self.hist['stock'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
        for stock in self.stock_list:
            hist=self.hist[self.hist['stock']==stock]
            if hist.shape[0]>0:
                price_dict=dict(zip(hist['date'],hist['close']))
                zdf_dict=dict(zip(hist['date'],hist['涨跌幅']))
                self.price_dict[stock]=price_dict
                self.zdf_dict[stock]=zdf_dict
            else:
                self.price_dict[stock]={}
                self.zdf_dict[stock]={}
        self.data.hist=self.hist
        return self.hist
    def get_zdf(self,date='20250103',stock='513100'):
        '''
        获取涨跌幅数据
        '''
        df=self.hist[self.hist['date']==date]
        df=df[df['stock']==stock]
        if df.shape[0]>0:
            zdf=df['涨跌幅'].tolist()[-1]
        else:
            zdf=0
        return zdf 
    def get_zdf_1(self,date='20250103',stock='513100'):
        '''
        获取涨跌幅1
        '''
        if len(self.zdf_dict):
            if stock in list(self.zdf_dict.keys()):
                zdf=self.zdf_dict[stock]
                if len(zdf)>0:
                    zdf=zdf.get(date,0)
                else:
                    zdf=0
            else:
                zdf=0
        else:
            zdf=0
        return 0
    def get_price(self,date='20250103',stock='513100'):
        '''
        获取价格
        '''
        df=self.hist[self.hist['date']==date]
        df=df[df['stock']==stock]
        if df.shape[0]>0:
            price=df['close'].tolist()[-1]
        else:
            price=self.position.get_stock_maker_price(stock=stock)
        return price
    def get_price_1(self,date='20250103',stock='513100'):
        '''
        获取价格函数1
        '''
        if len(self.price_dict):
            if stock in list(self.price_dict.keys()):
                price=self.price_dict[stock]
                if len(price)>0:
                    maker_price=self.position.get_stock_maker_price(stock=stock)
                    price=price.get(date,maker_price)
                else:
                    price=self.position.get_stock_maker_price(stock=stock)
            else:
                price=self.position.get_stock_maker_price(stock=stock)
        else:
            price=self.position.get_stock_maker_price(stock=stock)
        return price
    def check_is_T_stock(self,stock='600031'):
        '''
        检查是否T0
        '''
        df=pd.read_excel(r'T0股票池\T0股票池.xlsx')
        if df.shape[0]>0:
            df=df[['证券代码','名称']]
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            stock_list=df['证券代码'].tolist()
        else:
            stock_list=[]
        if stock in stock_list:
            return True
        else:
            return False
    def check_is_av_sell(self,stock='600031',amount=100):
        '''
        检查是否可以卖出
        '''
        position=self.position.position
        if position.shape[0]>0:
            position=position[position['证券代码']==stock]
            if position.shape[0]>0:
                hold_amount=position['股票余额'].tolist()[-1]
                av_amount=position['可用余额'].tolist()[-1]
                if av_amount>=amount and av_amount>=10:
                    print(stock,'允许卖出:持有数量{} 可用数量{}大于卖出数量{}'.format(hold_amount,av_amount,amount))
                    return True
                elif av_amount<amount and av_amount>=10:
                    print(stock,'允许卖出:持有数量{} 可用数量{}小于卖出数量{} 但是大于10'.format(hold_amount,av_amount,amount))
                    return True
                else:
                    print(stock,'不允许卖出:持有数量{} 可用数量{}小于卖出数量{}'.format(hold_amount,av_amount,amount))
                    return False
            else:
                print(stock,'不允许卖出没有持股')
                return False
        else:
            print(stock,'不允许卖出没有持股')
            return False
    def check_is_av_buy(self,stock='600031',amount=100,price=10):
        '''
        检查是否可以买入
        '''
        account=self.account.account
        if account.shape[0]>0:
            av_cash=account['可用金额'].tolist()[-1]
            value=amount*price
            if av_cash>=value and value>=100:
                print(stock,'允许买入:可用资金大于{} 买入价值{} 数量{} 价格{}'.format(av_cash,value,amount,price))
                return True
            else:
                print(stock,'不允许买入:可用资金小于{} 买入价值{} 数量{} 价格{}'.format(av_cash,value,amount,price))
                return False
        else:
            print(stock,'不允许买入没有账户数据')
            return False
    def buy(self,
            date='20250101',
            stock='513100',
            amount=100,
            price=1,
            maker='买入成功'):
        '''
        买入函数
        '''
        #持股
        position=self.position.position
        account=self.account.account
        trader_log=self.order.order
        if position.shape[0]>0:
            stock_list=position['证券代码'].tolist()
        else:
            stock_list=[]
        T_0=self.check_is_T_stock(stock=stock)
        if T_0:
            av_amount=amount
        else:
            av_amount=0
        value=amount*price
        if self.check_is_av_buy(stock=stock,amount=amount,price=price):
            #try:
            if True:
                if stock not in stock_list:
                    buy_df=pd.DataFrame()
                    buy_df['证券代码']=[stock]
                    buy_df['名称']=[stock]
                    buy_df['股票余额']=[amount]
                    buy_df['可用余额']=[av_amount]
                    buy_df['参考成本价']=[price]
                    buy_df['卖出价']=[None]
                    buy_df['市价']=[price]
                    buy_df['参考盈亏']=[0]
                    buy_df['参考盈亏比']=[0]
                    buy_df['当日盈亏']=[0]
                    buy_df['当日盈亏比']=[0]
                    buy_df['市值']=[value]
                    buy_df['参考卖出盈亏']=[0]
                    buy_df['当日卖出盈亏']=[0]
                    buy_df['持股天数']=[1]
                    buy_df['交易状态']=['buy']
                    buy_df['买入时间']=[date]
                    buy_df['卖出时间']=[None]
                    buy_df['时间']=[date]
                    position=pd.concat([position,buy_df],ignore_index=True)
                    self.position.position=position
                else:
                    test_postion=position[position['证券代码'] !=stock]
                    buy_hold=position[position['证券代码']==stock]
                    hold_amount=buy_hold['股票余额'].tolist()[-1]
                    #总数量
                    total_amount=hold_amount+amount
                    clost_price=buy_hold['参考成本价'].tolist()[-1]
                    #加权的成本价
                    clost_price=clost_price*(hold_amount/total_amount)+price*(amount/total_amount)
                    #print(clost_price,'1111111111')
                    #可用数量
                    hold_av_amount=buy_hold['可用余额'].tolist()[-1]
                    hold_av_amount+=av_amount
                    #市值
                    maker_value=total_amount*price
                    buy_hold.iloc[-1, buy_hold.columns.get_loc('股票余额')] = total_amount
                    buy_hold.iloc[-1, buy_hold.columns.get_loc('可用余额')] = hold_av_amount
                    buy_hold.iloc[-1, buy_hold.columns.get_loc('参考成本价')] = clost_price
                    buy_hold.iloc[-1, buy_hold.columns.get_loc('市值')] = maker_value
                    buy_hold.iloc[-1, buy_hold.columns.get_loc('市价')] = price
                    '''
                    #卖出赚钱
                    sell_value_return=buy_hold['参考卖出盈亏'].tolist()[-1]
                    #今天交易的
                    daily_sell_value_return=buy_hold['当日卖出盈亏'].tolist()[-1]
                    #参考盈亏
                    stock_return=total_amount*((price-clost_price)/clost_price)*price+sell_value_return
                    buy_hold.iloc[-1, buy_hold.columns.get_loc('参考盈亏')] = stock_return
                    #参考盈亏比
                    stock_return_ratio=((price-clost_price)/clost_price)*100
                    buy_hold.iloc[-1, buy_hold.columns.get_loc('参考盈亏比')] = stock_return_ratio
                    #当日盈亏比我直接利用涨跌幅替代，准确的需要分可以数量，和买入数量计算
                    daily_zdf=self.get_zdf(date=date,stock=stock)
                    buy_hold.iloc[-1, buy_hold.columns.get_loc('当日盈亏比')] = daily_zdf
                    #当日盈亏
                    daily_zdf_vaule=(total_amount*price*daily_zdf)/100+daily_sell_value_return
                    buy_hold.iloc[-1, buy_hold.columns.get_loc('当日盈亏')] = daily_zdf_vaule
                    '''
                    buy_hold['时间']=date
                    buy_hold['交易时间']=date
                    position=pd.concat([test_postion,buy_hold],ignore_index=True)
                
                self.position.position=position
                
                #"时间","总资产","股票市值","可用金额","当日盈亏","当日盈亏比","持仓盈亏","收益"
                last_date=str(account['时间'].tolist()[-1])
                total_value=account['总资产'].tolist()[-1]
                stock_value=account['股票市值'].tolist()[-1]
                av_value=account['可用金额'].tolist()[-1]
                daily_return=account['当日盈亏'].tolist()[-1]
                daily_return_ratio=account['当日盈亏比'].tolist()[-1]
                hold_return=account['持仓盈亏'].tolist()[-1]
                return_ratio=account['收益'].tolist()[-1]
                if last_date !=str(date):
                    stock_value+=value
                    av_value-=value
                    buy_account=pd.DataFrame()
                    buy_account['时间']=[date]
                    buy_account['总资产']=[av_value+stock_value]
                    buy_account['股票市值']=[stock_value]
                    buy_account['可用金额']=[av_value]
                    buy_account['当日盈亏']=[daily_return]
                    buy_account['当日盈亏比']=[daily_return_ratio]
                    buy_account['持仓盈亏']=[hold_return]
                    buy_account['收益']=[return_ratio]
                    buy_account['更新时间']=[date]
                    account=pd.concat([account,buy_account],ignore_index=True)
                    self.account.account=account
                else:
                    stock_value+=value
                    av_value-=value
                    account.iloc[-1, account.columns.get_loc('股票市值')] = stock_value
                    account.iloc[-1, account.columns.get_loc('可用金额')] = av_value
                    account.iloc[-1, account.columns.get_loc('更新时间')] = date
                    account.iloc[-1, account.columns.get_loc('时间')] = date
                    
                self.account.account=account
                log=pd.DataFrame()
                log['时间']=[date]
                log['证券代码']=[stock]
                log['名称']=[stock]
                log['交易数量']=[amount]
                log['买入价']=[price]
                log['卖出价']=[None]
                log['交易时间']=[str(date)]
                log['交易状态']=['buy']
                log['交易备注']=[maker]
                trader_log=pd.concat([trader_log,log],ignore_index=True)
                trader_log=trader_log.drop_duplicates(subset=['时间','证券代码',
                                '交易状态','交易时间','交易数量','买入价'],keep='last')
                self.order.order=trader_log
            '''
            except Exception as e:
                maker='{},买入有问题'.format(e)
                now_date=date
                log=pd.DataFrame()
                log['时间']=[now_date]
                log['证券代码']=[stock]
                log['名称']=[stock]
                log['交易数量']=[amount]
                log['买入价']=[price]
                log['卖出价']=[price]
                log['交易时间']=[str(date)]
                log['交易状态']=['buy']
                log['交易备注']=[maker]
                self.order.write_to_trader_log(log=log)
            '''
        else:
            #print(stock,amount,price,'不能买入')
            now_date=date
            log=pd.DataFrame()
            log['时间']=[now_date]
            log['证券代码']=[stock]
            log['名称']=[stock]
            log['交易数量']=[amount]
            log['买入价']=[price]
            log['卖出价']=[price]
            log['交易时间']=[str(date)]
            log['交易状态']=['sell']
            log['交易备注']=['买入失败:账户金额不足']
            self.order.write_to_trader_log(log=log)

        #self.settlement_data(date=date)
        return self.position.position,self.account.account,self.order.order
    def sell(self,
        date='20250101',
        stock='513100',
        amount=100,
        price=1,
        maker='卖出成功'):
        '''
        卖出函数
        '''
        position=self.position.position
        account=self.account.account
        trader_log=self.order.order
        now_date=date
        #try:
        if True:
            if position.shape[0]>0:
                buy_price_dict=dict(zip(position['证券代码'].tolist(),position['参考成本价'].tolist()))
            else:
                buy_price_dict={}
            value=amount*price
            if self.check_is_av_sell(stock=stock,amount=amount):
                log=pd.DataFrame()
                log['时间']=[date]
                log['证券代码']=[stock]
                log['名称']=[stock]
                log['交易数量']=[amount]
                log['买入价']=[buy_price_dict.get(stock,None)]
                log['卖出价']=[price]
                log['交易时间']=[str(date)]
                log['交易状态']=['sell']
                log['交易备注']=[maker]
                trader_log=pd.concat([trader_log,log],ignore_index=True)
                trader_log=trader_log.drop_duplicates(subset=['时间','证券代码',
                        '交易状态','交易时间','交易数量','买入价'],keep='last')
                self.order.order=trader_log
                test_postion=position[position['证券代码'] !=stock]
                sell_hold=position[position['证券代码']==stock]
                hold_amount=sell_hold['股票余额'].tolist()[-1]
                daily_zdf=self.get_zdf(date=date,stock=stock)
                #总数量
                total_amount=hold_amount
                total_amount_1=total_amount
                total_amount=hold_amount-amount
        
                clost_price=sell_hold['参考成本价'].tolist()[-1]

                #加权的成本价
                clost_price=clost_price

                #可用数量
                hold_av_amount=sell_hold['可用余额'].tolist()[-1]
                hold_av_amount-=amount

                #市值
                maker_value=sell_hold['市值'].tolist()[-1]
                maker_value-=value

                sell_hold.iloc[-1, sell_hold.columns.get_loc('股票余额')] = total_amount
                sell_hold.iloc[-1, sell_hold.columns.get_loc('可用余额')] = hold_av_amount
                sell_hold.iloc[-1, sell_hold.columns.get_loc('参考成本价')] = clost_price
                sell_hold.iloc[-1, sell_hold.columns.get_loc('市值')] =total_amount*price
                sell_hold.iloc[-1, sell_hold.columns.get_loc('市价')] = price
                sell_hold.iloc[-1, sell_hold.columns.get_loc('卖出时间')] = date
                
                #参考卖出盈亏
                last_sell_value=sell_hold['参考卖出盈亏'].tolist()[-1]
                sell_value_return=last_sell_value+amount*((price-clost_price)/clost_price)*price
               
                sell_value_return=sell_value_return
                #参考卖出盈亏
                sell_hold.iloc[-1, sell_hold.columns.get_loc('参考卖出盈亏')] = sell_value_return

                #当日卖出盈亏
                daily_sell_value=sell_hold['当日卖出盈亏'].tolist()[-1]
                daily_sell_value=(amount*price*daily_zdf)/100+daily_sell_value
        
                sell_hold.iloc[-1, sell_hold.columns.get_loc('当日卖出盈亏')] = daily_sell_value
                
                #参考盈亏比
                stock_return_ratio=((price-clost_price)/clost_price)*100
                sell_hold.iloc[-1, sell_hold.columns.get_loc('参考盈亏比')] = stock_return_ratio
                #参考盈亏
                stock_return=total_amount*((price-clost_price)/clost_price)*price+sell_value_return
                sell_hold.iloc[-1, sell_hold.columns.get_loc('参考盈亏')] = stock_return
                
               
                #当日盈亏比我直接利用涨跌幅替代，准确的需要分可以数量，和买入数量计算
                sell_hold.iloc[-1, sell_hold.columns.get_loc('当日盈亏比')] = daily_zdf
                #当日盈亏
                daily_zdf_vaule=(total_amount*price*daily_zdf)/100+daily_sell_value
                sell_hold.iloc[-1, sell_hold.columns.get_loc('当日盈亏')] = daily_zdf_vaule
                
                position=pd.concat([test_postion,sell_hold],ignore_index=True)
                self.position.position=position

                #print(position)
                #"时间","总资产","股票市值","可用金额","当日盈亏","当日盈亏比","持仓盈亏","收益"
                last_date=str(account['时间'].tolist()[-1])
                total_value=account['总资产'].tolist()[-1]
                stock_value=account['股票市值'].tolist()[-1]
                av_value=account['可用金额'].tolist()[-1]
                daily_return=account['当日盈亏'].tolist()[-1]
                daily_return_ratio=account['当日盈亏比'].tolist()[-1]
                hold_return=account['持仓盈亏'].tolist()[-1]
                return_ratio=account['收益'].tolist()[-1]
                if last_date !=str(now_date):
                    stock_value-=value
                    av_value+=value
                    sell_account=pd.DataFrame()
                    sell_account['时间']=[now_date]
                    sell_account['总资产']=[total_value+hold_return]
                    sell_account['股票市值']=[stock_value]
                    sell_account['可用金额']=[av_value]
                    sell_account['当日盈亏']=[daily_return]
                    sell_account['当日盈亏比']=[daily_return_ratio]
                    sell_account['持仓盈亏']=[hold_return]
                    sell_account['收益']=[return_ratio]
                    account=pd.concat([account,sell_account],ignore_index=True)
                else:
                    stock_value-=value
                    av_value+=value
                    account.iloc[-1, account.columns.get_loc('股票市值')] = stock_value
                    account.iloc[-1, account.columns.get_loc('可用金额')] = av_value
                self.account.account=account
            else:
                print(stock,amount,price,'不能卖出')
                now_date=date
                log=pd.DataFrame()
                log['时间']=[now_date]
                log['证券代码']=[stock]
                log['名称']=[stock]
                log['交易数量']=[amount]
                log['买入价']=[buy_price_dict.get(stock,None)]
                log['卖出价']=[price]
                log['交易时间']=[str(date)]
                log['交易状态']=['sell']
                log['交易备注']=['卖出失败:可用数量不足']
                trader_log=pd.concat([trader_log,log],ignore_index=True)
                trader_log=trader_log.drop_duplicates(subset=['时间','证券代码',
                        '交易状态','交易时间','交易数量','买入价'],keep='last')
                self.order.order=trader_log
        '''
        except Exception as e:
            print(e,'卖出函数有问题*************')
            maker='{},卖出有问题'.format(e)
            now_date=date
            log=pd.DataFrame()
            log['时间']=[now_date]
            log['证券代码']=[stock]
            log['名称']=[stock]
            log['交易数量']=[amount]
            log['买入价']=[price]
            log['卖出价']=[price]
            log['交易时间']=[str(date)]
            log['交易状态']=['sell']
            log['交易备注']=[maker]
            self.order.write_to_trader_log(log=log)
        
        #self.settlement_data(date=date)
        '''
        return self.position.position,self.account.account,self.order.order
    def get_name_data(self):
        '''
        读取全部股票数据
        '''
        try:
            df=pd.read_excel(r'{}\股票名称\股票名称.xlsx'.format(self.path))
            if df.shape[0]>0:
                df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
                df=df[['证券代码','名称']]
            else:
                df=pd.DataFrame()
        except Exception as e:
            print(e,'读取成交数据有问题')
            df=pd.DataFrame()
        return df
    def settlement_data(self,date='20250101'):
        '''
        持股结算数据
        '''
        #结算持股
        position=self.position.position
        account=self.account.account
        now_date=date
        name_df=self.get_name_data()
        if name_df.shape[0]>0:
            name_dict=dict(zip(name_df['证券代码'].tolist(),name_df['名称'].tolist()))
        else:
            name_dict={}
        if position.shape[0]>0:
            position['名称']=position['证券代码'].apply(lambda x: name_dict.get(x,x))
            last_data=str(position['时间'].tolist()[-1])
            position['市价'] = position.apply(lambda row: self.get_price(date=row['时间'], stock=row['证券代码']), axis=1)
           
            position['当日盈亏比'] = position.apply(lambda row: self.get_zdf(date=row['时间'], stock=row['证券代码']), axis=1)

            
            position['当日盈亏']=(position['股票余额']*position['当日盈亏比']*position['市价'])/100+position['当日卖出盈亏']
            position['市值']=position['股票余额']*position['市价']
            position['参考盈亏比']=((position['市价']-position['参考成本价'])/position['参考成本价'])*100
            position['参考盈亏']=position['股票余额']*((position['市价']-position['参考成本价'])/position['参考成本价'])*position['市价']+position['参考卖出盈亏']
            #调整当天数据,当天买入，当日盈亏等于持仓盈，次日有持股直接安涨跌幅计算收益
            position.loc[position['持股天数'] <= 1, '当日盈亏'] = position['参考盈亏']
            position.loc[position['持股天数'] <= 1, '当日盈亏比'] = position['参考卖出盈亏']
        else:
            print('没有持股数据不结算')
        #时间	总资产	股票市值	可用金额	当日盈亏	当日盈亏比	持仓盈亏	收益
        if account.shape[0]>0:
            last_data=str(account['时间'].tolist()[-1])
            if position.shape[0]>0:
                #股票市值
                stock_value=position['市值'].sum()
                #当日盈亏
                dayly_return_value=position['当日盈亏'].sum()
                #持仓盈亏
                hold_return_value=position['参考盈亏'].sum()
            else:
                stock_value=0
                dayly_return_value=0
                hold_return_value=0

            if last_data==now_date:
                account.iloc[-1, account.columns.get_loc('股票市值')] = stock_value
                account.iloc[-1, account.columns.get_loc('当日盈亏')] = dayly_return_value
                account.iloc[-1, account.columns.get_loc('持仓盈亏')] = hold_return_value
                account['总资产']=account['股票市值']+account['可用金额']
                account['当日盈亏比']=(account['当日盈亏']/(account['总资产']-account['当日盈亏']))*100
                #收益
                account['收益']=(account['持仓盈亏']/(account['总资产']-account['当日盈亏']))*100
                account['持仓盈亏']=account['当日盈亏'].cumsum()
                account['收益']=account['当日盈亏比'].cumsum()
            else:
                av_cash=self.account.account['可用金额'].tolist()[-1]
                set_account=pd.DataFrame()
                '''
                set_account['总资产']=[total_value]
                set_account['股票市值']=[stock_value]
                set_account['可用金额']=[av_value]
                set_account['当日盈亏']=[dayly_return_value]
                set_account['当日盈亏比']=[daily_return_ratio]
                set_account['持仓盈亏']=[hold_return]
                set_account['收益']=[return_ratio]
                '''
                set_account['时间']=[now_date]
                set_account['股票市值']=[stock_value]
                set_account['当日盈亏']=[dayly_return_value]
                set_account['持仓盈亏']=[hold_return_value]
                set_account['可用金额']=[av_cash]
                set_account['总资产']=set_account['股票市值']+set_account['可用金额']
                set_account['当日盈亏比']=(set_account['当日盈亏']/(set_account['总资产']-set_account['当日盈亏']))*100
                #收益
                set_account['收益']=(set_account['持仓盈亏']/(set_account['总资产']-set_account['当日盈亏']))*100
                account=pd.concat([account,set_account],ignore_index=True)
                account['持仓盈亏']=account['当日盈亏'].cumsum()
                account['收益']=account['当日盈亏比'].cumsum()
        else:
            print('没有账户数据')
        self.position_log.add_position_log_data(log=position)
        if last_data !=now_date:
            position['时间']=date
            position=position[position['股票余额']>=10]
            position['当日卖出盈亏']=0
            position['持股天数']=position['持股天数']+1
            position['时间']=now_date
            position['可用余额']=position['股票余额']
        else:
            position['时间']=date
            position=position[position['股票余额']>=10]
            position['当日卖出盈亏']=0
            position['持股天数']=position['持股天数']+1
            position['时间']=now_date
            position['可用余额']=position['股票余额']
        self.position.position=position
        account['更新时间']=str(date)
        #account['总资产']=account['总资产']+account['持仓盈亏']
        self.account.account=account
        
        print(date,'持股数据结算完成')
        return self.position.position,self.account.account,self.order.order
    


    def order_value(self,date='20250101',stock='501018',value=1000,price=1.33,trader_type='buy'):
        '''
        按金额下单
        stock: 证券代码
        value下单金额
        value大于0买入，小0卖出
        prive交易的的价格
        '''
        hold_stock=self.position.position
        account=self.account.get_last_account_data()
        cash=account['可用金额'].tolist()[-1]
        amount=value/price
        amount=self.adjust_amount(stock=stock,amount=amount)
        if trader_type=='buy':
            #这里按道理需要考虑手续费，看隔日资金
            if cash>=value:
                if amount>=10:
                    print('{} 按金额下单{} 交易类型{} 可用资金{}大于 下单金额{}  下单数量{}'.format(date,stock,trader_type,cash,value,amount))
                    return 'buy',amount,price
                else:
                    print('{}按金额下单{} 交易类型{} 可用资金{}大于 下单金额{}  下单数量{}小于最小下单单位不交易'.format(date,stock,trader_type,cash,value,amount))
                    return '',0,price
            else:
                print('{}按金额下单{} 交易类型{} 可用资金{}小于 下单金额{}  下单数量{} 不交易'.format(date,stock,trader_type,cash,value,amount))
                return '',0,price
        elif trader_type=='sell':
            df1=hold_stock[hold_stock['证券代码']==stock]
            if df1.shape[0]>0:
                #可以使用的数量兼容t0
                av_num=df1['可用余额'].tolist()[-1]
                #持有数量
                hold_num=df1['股票余额'].tolist()[-1]
                #可用余额大于下单数量
                if av_num>=amount:
                    print('{}按金额下单{} 交易类型{} 持有数量{} 可用数量{}大于 下单数量{}  下单数量{}'.format(date,stock,trader_type,hold_num,av_num,amount,amount))
                    return 'sell',amount,price
                else:
                    if av_num>=10:
                        print('{}按金额下单{} 交易类型{} 持有数量{} 可用数量{}小于 下单数量{}  直接卖出全部下单数量{}'.format(date,stock,trader_type,hold_num,av_num,amount,av_num))
                        return 'sell',av_num,price
                    else:
                        print('{}按金额下单{} 交易类型{} 持有数量{} 可用数量{}小于 下单数量{}  下单数量{}小于最小单位不交易'.format(date,stock,trader_type,hold_num,av_num,amount,av_num))
                        return '',0,price
            else:
                return '',0,price
        else:
            print('{}按金额下单{} 交易类型{}未知道 不交易'.format(date,stock,trader_type))
            return '',0,price
    def order_target_value(self,date='20250101',stock='501018',value=1000,price=1.33):
        '''
        目标价值下单
        stock: 股票名字
        value: 股票价值，value = 最新价 * 手数 * 保证金率（股票为1） * 乘数（股票为100）
        prive交易的的价格
        '''
        hold_stock=self.position.position
        account=self.account.get_last_account_data()
        cash=account['可用金额'].tolist()[-1]
        amount=math.floor(value/price)
        if hold_stock.shape[0]>0:
            stock=str(stock)
            df1=hold_stock[hold_stock['证券代码']==stock]
            if df1.shape[0]>0:
                #可以使用的数量兼容t0
                av_num=df1['可用余额'].tolist()[-1]
                #持有数量
                hold_num=df1['股票余额'].tolist()[-1]
                #持有的价值
                hold_value=df1['市值'].tolist()[-1]
            else:
                av_num=0
                hold_num=0
                hold_value=0
        else:
            av_num=0
            hold_num=0
            hold_value=0
        #买卖价值差转成数量
        #可转债最新10
        amount=self.adjust_amount(stock=stock,amount=amount)
        #买卖的差额
        buy_sell_num=math.floor(amount-float(hold_num))
        buy_sell_num=self.adjust_amount(stock=stock,amount=buy_sell_num)
        buy_sell_value=buy_sell_num*price
        #存在买入差额,买入的大于持有的
        if buy_sell_num>0:
            if buy_sell_num>=10:
                #可用现金大于买卖的差额
                if cash>=buy_sell_value:
                    print('{} 目标价值下单{} 目标价值{} 可用资金{}大于买卖资金{} 目标数量{} 持有数量{} 可用数量{} 买入差额{}'.format(date,stock,value,cash,buy_sell_value,amount,hold_num,av_num,buy_sell_num))
                    return 'buy',buy_sell_num,price
                else:
                    print('{} 目标价值下单{} 目标价值{} 可用资金{}小于买卖资金{} 目标数量{} 持有数量{} 可用数量{} 买入差额{}不下单'.format(date,stock,value,cash,buy_sell_value,amount,hold_num,av_num,buy_sell_num))
                    return '',0,price
            else:
                print('{} 目标价值下单{} 目标价值{} 可用资金{} 买卖资金{} 目标数量{} 持有数量{} 可用数量{} 买入差额{}不下单小于最小单位去10'.format(date,value,cash,buy_sell_value,amount,hold_num,av_num,buy_sell_num))
                return '',0,price
        #存在卖出空间,目标数量小于持有数量卖出：
        elif buy_sell_num <0:
            #可以卖出的数量多
            if av_num>=buy_sell_num:
                buy_sell_num=abs(buy_sell_num)
                buy_sell_num=self.adjust_amount(stock=stock,amount=buy_sell_num)
                print('{} 目标价值下单{} 目标价值{} 目标数量{} 持有数量{} 可用数量{} 卖出差额{}'.format(date,stock,value,amount,hold_num,av_num,buy_sell_num))
                return 'sell',buy_sell_num,price
            else:
                #可以卖出的不足卖出全部可以卖出的
                print('{} 目标价值下单{} 目标价值{} 目标数量{} 持有数量{} 可用数量{}小于卖出数量 卖出差额{}'.format(date,stock,value,amount,hold_num,av_num,buy_sell_num))
                return 'sell',av_num,price
        else:
            print('{} 目标价值下单{} 目标价值{} 目标数量{} 等于持有数量{} 可用数量{} 卖出差额{}不下单'.format(date,stock,value,amount,hold_num,av_num,buy_sell_num))
            return '',0,price
    def order_percent(self,date='20250101',stock='501018',percent=0.1,price=1.33,trader_type='buy'):
        '''
        百分比交易
        percent下单百分比
        '''
        hold_stock=self.position.position
        account=self.account.get_last_account_data()
        cash=account['可用金额'].tolist()[-1]
        total_asset=account['总资产'].tolist()[-1]
        entrusts_amount,entrusts_df=0,pd.DataFrame()
        #目标金额=目标百分比-委托金额
        target_value=total_asset*percent-entrusts_amount
        #数量
        amount=target_value/price
        amount=self.adjust_amount(stock=stock,amount=amount)
        if trader_type=='buy':
            #这里按道理要考虑手续费看个资金
            if cash>=target_value:
                if amount>=10:
                    print('{} 百分比交易{} 下单类型{} 百分比{} 下单数量{} 可以资金{}大于目标资金{} 买入数量{}'.format(date,stock,trader_type,percent,amount,cash,target_value,amount))
                    return 'buy',amount,price
                else:
                    print('{} 百分比交易{} 下单类型{} 百分比{} 下单数量{} 可以资金{}大于目标资金{} 买入数量{}小于10不下单'.format(date,stock,trader_type,percent,amount,cash,target_value,amount))
                    return '',0,price
            else:
                print('{} 百分比交易{} 下单类型{} 百分比{} 下单数量{} 可以资金{}小于目标资金{} 买入数量{}'.format(date,stock,trader_type,percent,amount,cash,target_value,amount))
                return '',0,price
        elif trader_type=='sell':
            if hold_stock.shape[0]>0:
                stock=str(stock)
                df1=hold_stock[hold_stock['证券代码']==stock]
                if df1.shape[0]>0:
                    #可以使用的数量兼容t0
                    av_num=df1['可用余额'].tolist()[-1]
                    #持有数量
                    hold_num=df1['股票余额'].tolist()[-1]
                    #持有的价值
                    hold_value=df1['市值'].tolist()[-1]
                    #可用数量大于卖出数量
                    if av_num>=amount:
                        print('{} 百分比交易{} 下单类型{} 百分比{} 持有数量{} 可以数量{} 大于等于下单数量{} 下单{}'.format(date,stock,trader_type,percent,hold_num,cash,amount,amount))
                        return 'sell',amount,price
                    else:
                        print('{} 百分比交易{} 下单类型{} 百分比{} 持有数量{} 可以数量{} 小于下单数量{} 下单{}'.format(date,stock,trader_type,percent,hold_num,cash,amount,av_num))
                        return 'sell',av_num,price
                else:
                    print('{} {}账户没有持股不支持交易类型{}'.format(date,stock,trader_type))
                    return '',0,price
            else:
                print('{} 账户没有持股不支持交易类型{}'.format(date,trader_type))
                return '',0,price
        else:
            print('{} 未知的交易类型{}'.format(date,trader_type))
            return '',0,price
    def order_target_percent(self,date='20250101',stock='501018',target_percent=0.1,price=1.33):
        '''
        目标百分比下单
        '''
        hold_stock=self.position.position
        account=self.account.get_last_account_data()
        cash=account['可用金额'].tolist()[-1]
        total_asset=account['总资产'].tolist()[-1]
        #entrusts_amount,entrusts_df=self.get_check_not_trader_today_entrusts(stock=stock,trader_type='buy',data_type='金额')
        #目标金额
        target_value=total_asset*target_percent
        #目标数量
        target_amount=target_value/price
        amount=self.adjust_amount(stock=stock,amount=target_amount)
        if hold_stock.shape[0]>0:
            stock=str(stock)
            df1=hold_stock[hold_stock['证券代码']==stock]
            if df1.shape[0]>0:
                #可以使用的数量兼容t0
                av_num=df1['可用余额'].tolist()[-1]
                #持有数量
                hold_num=df1['股票余额'].tolist()[-1]
                #持有的价值
                hold_value=df1['市值'].tolist()[-1]
            else:
                av_num=0
                hold_num=0
                hold_value=0
        else:
            av_num=0
            hold_num=0
            hold_value=0
        #没有买入数量,目标数量-持有数量
        buy_sell_amount=amount-hold_num
        #大于0 存在买入的差额
        if buy_sell_amount>=10:
            #可以现金大于目标金额 这里要考虑手续看个人资金
            if cash>=target_value:
                print('{} 目标百分比下单{} 目标百分比{} 目标数量{} 可以资金{}大于目标资金{} 持有数量{} 可用数量{} 买入差额{}'.format(date,stock,target_percent,target_amount,cash,target_value,hold_num,av_num,buy_sell_amount))
                return 'buy',buy_sell_amount,price
            else:
                print('{} 目标百分比下单{} 目标百分比{} 目标数量{} 可以资金{}小于目标资金{} 持有数量{} 可用数量{} 买入差额{}不下单'.format(date,stock,target_percent,target_amount,cash,target_value,hold_num,av_num,buy_sell_amount))
                return '',0,price
        elif buy_sell_amount<=10 and buy_sell_amount>=0:
            print('{} 目标百分比下单{} 目标百分比{} 目标数量{} 可以资金{}目标资金{} 持有数量{} 可用数量{} 买入差额{}小于10不下单'.format(date,stock,target_percent,target_amount,cash,target_value,hold_num,av_num,buy_sell_amount))
            return '',0,price
        else:
            #可用买入的差额小于0 卖出
            buy_sell_amount=abs(buy_sell_amount)
            #可用数量大于差额
            if av_num>=buy_sell_amount:
                print('{} 目标百分比下单{} 目标百分比{} 目标数量{} 持有数量{} 可用数量{} 大于差额{} 卖出差额{}'.format(date,stock,target_percent,target_amount,hold_num,av_num,buy_sell_amount,buy_sell_amount))
                return 'sell',buy_sell_amount,price
            else:
                print('{} 目标百分比下单{} 目标百分比{} 目标数量{} 持有数量{} 可用数量{} 小于差额{} 卖出全部{}'.format(date,stock,target_percent,target_amount,hold_num,av_num,buy_sell_amount,av_num))
                return 'sell',av_num,price
    def one_click_clearance(self):
        '''
        一键清仓
        '''
        hold_stock=self.position.position
        account=self.account.get_last_account_data()
        if hold_stock.shape[0]>0:
            for stock,hold_num,av_num in zip(hold_stock["证券代码"].tolist(),
                hold_stock['可用余额'].tolist(),hold_stock['股票余额'].tolist()):
                try:
                   
                    price=self.get_price(stock=stock)
                    if av_num>=10:
                        print('一键清仓{} 持有数量{} 可用数量{} 卖出数量{}'.format(stock,hold_num,av_num,av_num))
                        self.sell(stock=stock,amount=av_num,price=price)
                    else:
                        print('一键清仓{} 持有数量{} 可用数量{}小于0 卖出数量{} 不交易'.format(stock,hold_num,av_num,av_num))
                except Exception as e:
                    print(e)
        else:
            print("一键清仓 账户没有持股，清仓不了")
    def get_trader_report(self):
        '''
        生成交易报告
        复利计算的
        '''
        #生成交易报告
        account=self.account.get_account_data()
        account=account[['时间','当日盈亏','当日盈亏比','持仓盈亏','收益']]
        account_len=account.shape[0]
        index_data=self.index_data.get_index_hist_data(start_date=self.start_date,end_date=self.end_date)
        index_data_len=index_data.shape[0]
        n=min(account_len,index_data_len)
        account=account[-n:]
        index_data=index_data[-n:]
        account['index_zdf']=index_data['close'].pct_change().tolist()
        try:
            account['时间']=account['时间'].astype(str)
            account.index=pd.to_datetime(account['时间'])
            account['当日盈亏比']=account['当日盈亏比'].astype(float)
            qs.reports.html(
                returns= account['当日盈亏比']/100,  # 每日变化,
                output=r'{}\历史回测\历史回测.html'.format(self.path),
                
                benchmark=account['index_zdf'])
            print('历史回测报告生成完成*****************')
        except Exception as e:
            print(e,'历史数据不足交易报告*****************')
    def get_trader_return_table(self):
        '''
        获取交易报告表
        '''
        df=self.account.get_account_data()
        data=pd.DataFrame()
        if df.shape[0]>0:
            data['时间']=[self.end_date]
            data['策略名称']=[self.st_name]
            data['今日收益%']=[round(df['当日盈亏比'].tolist()[-1],2)]
            data['策略收益%']=[round(df['当日盈亏比'].sum(),2)]
            data['3日收益%']=[round(df['当日盈亏比'][-3:].sum(),2)]
            data['周收益%']=[round(df['当日盈亏比'][-5:].sum(),2)]
            data['月收益%']=[round(df['当日盈亏比'][-20:].sum(),2)]
            data['3月收益%']=[round(df['当日盈亏比'][-60:].sum(),2)]
            data['6月收益%']=[round(df['当日盈亏比'][-120:].sum(),2)]
            data['年月收益%']=[round(df['当日盈亏比'][-265:].sum(),2)]
            data['年化收益%']=[round(ep.annual_return(df['当日盈亏比']/100),2)*100]
            data['最大回撤%']=[round(ep.max_drawdown(df['当日盈亏比']/100),2)*100]
            data['夏普']=[round(ep.sharpe_ratio(df['当日盈亏比']/100),2)]
            data['波动率']=[round(ep.annual_volatility(df['当日盈亏比']/100),2)]
            data['在险价值']=[round(ep.tail_ratio(df['当日盈亏比']/100),2)]
            data['索提诺比率']=[round(ep.sortino_ratio(df['当日盈亏比']/100),2)]
            data['卡玛比率']=[round(ep.calmar_ratio(df['当日盈亏比']/100),2)]
            data['欧米茄比率']=[round(ep.omega_ratio(df['当日盈亏比']/100),2)]
            data['总天数']=[df.shape[0]]
            #获利的天数
            df1=df[df['当日盈亏比']>=0]
            data['盈利周期']=[df1.shape[0]]
            #亏损天数
            df2=df[df['当日盈亏比']<0]
            data['亏损周期']=[df2.shape[0]]
            data['胜率%']=round((data['盈利周期']/data['总天数'])*100,2)
            data['盈亏比%']=round((data['盈利周期']/data['亏损周期'])*100,2)
        else:
            data=data
        return data

    def calculate_monthly_profit(self):
        """
        计算并返回月度收益统计
        
        参数:
        file_path (str): Excel文件路径
        
        返回:
        pd.DataFrame: 包含月度收益统计的DataFrame
        """
        try:
            # 读取Excel文件
            df = self.account.get_account_data()
            if df.shape[0]>0:
                # 将时间列转换为datetime格式
                df['时间'] = pd.to_datetime(df['时间'], format='%Y%m%d')
                
                # 提取年月信息
                df['年月'] = df['时间'].dt.to_period('M')
                
                # 按年月分组计算统计指标
                monthly_stats = df.groupby('年月').agg({
                    '当日盈亏': ['sum', 'mean', 'max', 'min', 'count'],
                    '当日盈亏比': ['sum', 'mean'],
                    '收益': 'last'  # 取当月最后一天的累计收益
                }).reset_index()
                
                # 扁平化多级列索引
                monthly_stats.columns = [
                    '年月', 
                    '月总盈亏', '日均盈亏', '月最大单日盈亏', '月最小单日盈亏', '交易天数',
                    '月总盈亏比', '日均盈亏比',
                    '月末累计收益'
                ]
                
                # 计算月收益率 (月末累计收益 - 月初累计收益)
                monthly_stats['月收益率'] = monthly_stats['月末累计收益'] - monthly_stats['月末累计收益'].shift(1)
                monthly_stats.loc[monthly_stats.index[0], '月收益率'] = monthly_stats.loc[monthly_stats.index[0], '月末累计收益']
                
                
            else:
                monthly_stats=pd.DataFrame()
        
        except Exception as e:
            print(f"处理文件时出错: {e}")
            monthly_stats=pd.DataFrame()
        return monthly_stats
    def calculate_yearly_profit(self):
        """
        计算并返回年度收益统计
        
        返回:
        pd.DataFrame: 包含年度收益统计的DataFrame
        """
        try:
            # 读取Excel文件
            df = self.account.get_account_data()
            if df.shape[0] > 0:
                # 将时间列转换为datetime格式
                df['时间'] = pd.to_datetime(df['时间'], format='%Y%m%d')
                
                # 提取年月信息
                df['年份'] = df['时间'].dt.to_period('Y')
                
                # 按年份分组计算统计指标
                yearly_stats = df.groupby('年份').agg({
                    '当日盈亏': ['sum', 'mean', 'max', 'min', 'count'],
                    '当日盈亏比': ['sum', 'mean'],
                    '收益': 'last'  # 取当年最后一天的累计收益
                }).reset_index()
                
                # 扁平化多级列索引
                yearly_stats.columns = [
                    '年份', 
                    '年总盈亏', '日均盈亏', '年最大单日盈亏', '年最小单日盈亏', '交易天数',
                    '年总盈亏比', '日均盈亏比',
                    '年末累计收益'
                ]
                
                # 计算年收益率 (年末累计收益 - 年初累计收益)
                yearly_stats['年收益率'] = yearly_stats['年末累计收益'] - yearly_stats['年末累计收益'].shift(1)
                yearly_stats.loc[yearly_stats.index[0], '年收益率'] = yearly_stats.loc[yearly_stats.index[0], '年末累计收益']
                
                # 计算年化收益率（假设一年250个交易日）
                yearly_stats['年化收益率'] = yearly_stats['日均盈亏比'] * 250
                
            else:
                yearly_stats = pd.DataFrame()
        
        except Exception as e:
            print(f"计算年收益时出错: {e}")
            yearly_stats = pd.DataFrame()
        return yearly_stats

    def get_sign_buy_sell_dot(self,stock='600031'):
        '''
        标记个股的买卖点
        '''
        hist=self.hist
        stock_list=hist['stock'].tolist()
        if stock in stock_list:
            hist=hist[hist['stock']==stock]
            order=self.order.get_order_data()
            if order.shape[0]>0:
                order=order[order['证券代码']==stock]
                order['成功']=order['交易备注'].apply(lambda x: '是' if '买入成功' in x or '卖出成功' in x else '不是')
                order=order[order['成功']=='是']
                buy_dict={}
                sell_dict={}
                for date,stats,buy_price,sell_price in zip(order['时间'],
                                order['交易状态'],order['买入价'],order['卖出价']):
                    if stats=='buy':
                        buy_dict[date]=buy_price*0.99
                    elif stats=='sell':
                        sell_dict[date]=sell_price*1.01
                    else:
                        pass
                hist['buy']=hist['date'].apply(lambda x: buy_dict.get(x,None))
                hist['sell']=hist['date'].apply(lambda x: sell_dict.get(x,None))
                df1=hist
                df1['buy'] = df1['buy'].replace([None], np.nan)
                df1['sell'] = df1['sell'].replace([None], np.nan)
                df1['buy_fill']=df1['buy'].fillna(value=0)
                df1['sell_fill']=df1['sell'].fillna(value=0)
                df1.rename(columns={'date': 'Date', 'open': 'Open', 'close': 'Close', 'high': 'High', 'low': 'Low',
                                    'volume': 'Volume'}, inplace=True)
                # 时间格式转换
                plt.rcParams['font.family'] = 'SimHei'
                plt.rcParams['axes.unicode_minus'] = False
                df1['Date'] = pd.to_datetime(df1['Date'])
                # 出现设置索引
                df1.set_index(['Date'], inplace=True)
                # 设置股票颜
                mc = mpf.make_marketcolors(up='r', down='g', edge='i',volume='i')
                # 设置系统
                s = mpf.make_mpf_style(marketcolors=mc)
                add_plot = []
                if  df1['buy_fill'].sum(axis=0)>0:
                    add_plot.append( mpf.make_addplot(df1['buy'],panel=0,color='r',type='scatter',marker='^',markersize=60))
                if df1['sell_fill'].sum(axis=0)>0:
                    add_plot.append( mpf.make_addplot(df1['sell'],panel=0,color='g',type='scatter',marker='v',markersize=60))
                   
                   
                
                # 绘制股票图，5，10，20日均线
                mpf.plot(df1, type='candle', mav=(5, 10, 20),style=s,figratio=(800, 650),
                        addplot=add_plot,volume=True,
                        title='xg_backtrader sub_position_stock:{} start_date:{} end_date:{}'.format(stock,self.start_date,self.end_date))#,
                plt.show()
            else:
                print(stock,'标记个股的买卖点没有委托数据')
        else:
            print(stock,'标记个股的买卖点没有历史数据')
    def get_stock_trader_report(self,stock='600031'):
        '''
        获取个股的交易报告
        '''
        hist=self.hist
        stock_list=hist['stock'].tolist()
        if stock in stock_list:
            hist=hist[hist['stock']==stock] 
            if hist.shape[0]>0:
                position_log=self.position_log.get_position_log_data()
                if position_log.shape[0]>0:
                    position_log=position_log[position_log['证券代码']==stock]
                    daily_return_dict=dict(zip(position_log['时间'],position_log['当日盈亏比']))
                    hist['当日盈亏比']=hist['date'].apply(lambda x: daily_return_dict.get(x,0))
                    index_data=self.index_data.get_index_hist_data(start_date=self.start_date,end_date=self.end_date)
                    index_data_len=index_data.shape[0]
                    n=min(hist.shape[0],index_data_len)
                    hist=hist[-n:]
                    index_data=index_data[-n:]
                    hist['index_zdf']=index_data['close'].pct_change().tolist()
                    try:
                    
                        hist['date']=hist['date'].astype(str)
                        hist.index=pd.to_datetime(hist['date'])
                        hist['当日盈亏比']=hist['当日盈亏比'].astype(float)
                        qs.reports.html(
                            returns=hist['当日盈亏比']/100,
                            output=r'{}\个股交易报告\{}个股交易报告.html'.format(self.path,stock),
                            
                            benchmark=hist['index_zdf'])
                        print('{}回测报告生成完成*****************'.format(stock))
                    except:
                        print('{}数据不足交易报告*****************'.format(stock))
                else:
                    print(stock,'回测报告生成完成没有记录数据')
            else:
                print(stock,'回测报告生成完成没有历史数据')   
        else:
            print(stock,'回测报告生成完成没有历史数据') 
    def get_all_stock_trader_report(self):
        '''
        获取全部股票的历史交易报告
        '''
        for stock in self.stock_list:
            try:
                self.get_stock_trader_report(stock=stock)
            except Exception as e:
                print(stock,e,'回测报告有问题')

    def get_all_trader_data(self):
        '''
        获取全部股票的交易数据
        '''
        account=self.account.get_account_data()
        account=account[['时间','当日盈亏','当日盈亏比','持仓盈亏','收益']]
        account.to_excel(r'{}\全部交易数据\账户数据.xlsx'.format(self.path))
        position=self.position.get_position_data()
        position.to_excel(r'{}\全部交易数据\持股数据.xlsx'.format(self.path))
        order=self.order.get_order_data()
        order.to_excel(r'{}\全部交易数据\委托数据.xlsx'.format(self.path))
        position_log=self.position_log.get_position_log_data()
        position_log.to_excel(r'{}\全部交易数据\持股记录数据.xlsx'.format(self.path))
        table=self.get_trader_return_table()
        table.to_excel(r'{}\策略评价数据\策略评价数据.xlsx'.format(self.path))
        df=self.calculate_monthly_profit()
        df.to_excel(r'{}\月度收益统计\月度收益统计.xlsx'.format(self.path))
        df=self.calculate_yearly_profit()
        df.to_excel(r'{}\年度收益统计\年度收益统计.xlsx'.format(self.path))
        print('获取全部股票的交易数据成功')
    
    def generate_strategy_report(self,
        
    ):
        """
        生成完整的策略回测报告
        
        参数:
            strategy_data_path: 策略评价数据文件路径
            account_data_path: 账户数据文件路径
            yearly_data_path: 年度收益统计数据文件路径
            output_file: 输出HTML文件路径
            
        返回:
            无，直接生成HTML报告文件
        """
        strategy_data_path=self.get_trader_return_table()
        account_data_path=self.account.get_account_data()
        yearly_data_path=self.calculate_yearly_profit()
        output_file=r"{}\历史回测\历史回测.html".format(self.path)
        # 创建页面
        page = self.create_report_page()
        
        # 添加标题
        page.add(self.create_title_component())
        
        # 添加策略评价数据表格（表1和表2）
        for table in self.create_split_tables(strategy_data_path):
            page.add(table)
        
        # 添加收益曲线图（图3）
        page.add(self.create_profit_chart(account_data_path))
        
        # 添加年收益率分布条形图（图4）
        page.add(self.create_yearly_return_chart(yearly_data_path))
        
        # 添加年度收益统计表（表4）
        page.add(self.create_yearly_stats_table(yearly_data_path))
        
        # 渲染页面
        page.render(output_file)
        print(f"HTML报告已生成: {output_file}")

    def create_report_page(self):
        """创建报告页面基础配置"""
        return Page(
            layout=Page.SimplePageLayout,
            page_title="西蒙斯量化3.0回测报告"
        )

    def create_title_component(self):
        """创建标题组件（简化版）"""
        title_table = Table()
        title_table.add(
            headers=["西蒙斯量化3.0回测系统-{}回测,作者:西蒙斯量化,微信:xg_quant".format(self.st_name)],
            rows=[],
        )
        title_table.set_global_opts(
            title_opts=opts.TitleOpts(
                title="西蒙斯量化3.0回测系统",
                subtitle="回测结果报告",
                title_textstyle_opts=opts.TextStyleOpts(
                    font_size=20,
                    color="#333",
                    font_weight="bold"
                ),
                subtitle_textstyle_opts=opts.TextStyleOpts(
                    font_size=16,
                    color="#666"
                ),
                pos_left="center",
                padding=[10, 0]
            )
        )
        return title_table

    def create_split_tables(self,data_path):
        """切分策略评价数据为多个子表格"""
        df_strategy = data_path
        try:
            del df_strategy['Unnamed: 0']
        except:
            pass
        
        # 格式化数据，保留两位小数
        def format_value(x):
            if isinstance(x, (int, float)):
                return f"{float(x):.2f}"
            return x
        
        df_strategy = df_strategy.applymap(format_value)
        
        cols = df_strategy.columns.tolist()
        data = df_strategy.values.tolist()
        
        # 将列分成2组
        col_groups = [
            cols[:12],   # 前12列
            cols[12:],   # 剩余列
        ]
        
        tables = []
        for i, group in enumerate(col_groups):
            # 获取当前组的列索引
            col_indices = [cols.index(c) for c in group]
            
            # 提取对应的数据
            table_data = [[row[j] for j in col_indices] for row in data]
            
            # 创建子表格
            table = Table()
            table.add(group, table_data)
            table.set_global_opts(
                title_opts=opts.TitleOpts(
                    title=f"表{i+1}：策略评价数据(Part {i+1})",
                    subtitle="数据保留两位小数",
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(
                        font_size=16,
                        color="#333",
                        font_weight="bold"
                    )
                )
            )
            tables.append(table)
        return tables

    def create_profit_chart(self,data_path):
        """创建账户收益曲线图"""
        df_account =data_path
        df_account['时间'] = pd.to_datetime(df_account['时间'], format='%Y%m%d')
        df_account['收益'] = df_account['收益'].apply(lambda x: round(x, 2))
        
        line = Line(init_opts=opts.InitOpts(
            theme=ThemeType.LIGHT,
            width="100%",
            height="600px",
            chart_id="profit_chart"
        ))
        line.add_xaxis(df_account['时间'].dt.strftime('%Y-%m-%d').tolist())
        line.add_yaxis(
            series_name="累计收益(%)",
            y_axis=df_account['收益'].tolist(),
            is_smooth=True,
            label_opts=opts.LabelOpts(is_show=False),
            linestyle_opts=opts.LineStyleOpts(width=3, color="#5470C6"),
            symbol_size=8,
            itemstyle_opts=opts.ItemStyleOpts(color="#5470C6"),
            markpoint_opts=opts.MarkPointOpts(
                data=[
                    opts.MarkPointItem(type_="max", name="最大值"),
                    opts.MarkPointItem(type_="min", name="最小值")
                ],
                label_opts=opts.LabelOpts(formatter="{c}%")
            ),
            markline_opts=opts.MarkLineOpts(
                data=[opts.MarkLineItem(type_="average", name="平均值")],
                label_opts=opts.LabelOpts(formatter="{c}%")
            )
        )
        
        line.set_global_opts(
            title_opts=opts.TitleOpts(
                title="策略收益曲线",
                pos_left="center",
                title_textstyle_opts=opts.TextStyleOpts(
                    font_size=16,
                    color="#333",
                    font_weight="bold"
                )
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="axis",
                formatter="{b}<br/>{a0}: {c0}%",
                axis_pointer_type="cross"
            ),
            legend_opts=opts.LegendOpts(pos_top="8%"),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(rotate=45),
                axispointer_opts=opts.AxisPointerOpts(is_show=True)
            ),
            yaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(formatter="{value}%"),
                splitline_opts=opts.SplitLineOpts(is_show=True)
            ),
            datazoom_opts=[
                opts.DataZoomOpts(
                    range_start=0,
                    range_end=100,
                    pos_bottom="5%"
                ),
                opts.DataZoomOpts(type_="inside")
            ],
            toolbox_opts=opts.ToolboxOpts(
                is_show=True,
                feature={
                    "dataZoom": {"yAxisIndex": "none"},
                    "restore": {},
                    "saveAsImage": {}
                }
            )
        )
        return line

    def create_yearly_return_chart(self,data_path):
        """创建年收益率分布条形图"""
        df_yearly = data_path
        df_yearly['年收益率'] = df_yearly['年收益率'].apply(lambda x: round(x, 2))
        
        bar = Bar(init_opts=opts.InitOpts(
            theme=ThemeType.LIGHT,
            width="100%",
            height="500px",
            chart_id="yearly_chart"
        ))
        bar.add_xaxis(df_yearly['年份'].astype(str).tolist())
        bar.add_yaxis(
            series_name="年收益率(%)",
            y_axis=df_yearly['年收益率'].tolist(),
            label_opts=opts.LabelOpts(
                formatter="{c}%",
                position="top",
                color="#333",
                font_size=12
            ),
            itemstyle_opts=opts.ItemStyleOpts(
                color="#91CC75",
                border_color="#333",
                border_width=0.5
            ),
            markpoint_opts=opts.MarkPointOpts(
                data=[
                    opts.MarkPointItem(type_="max", name="最大值"),
                    opts.MarkPointItem(type_="min", name="最小值")
                ],
                label_opts=opts.LabelOpts(formatter="{c}%")
            ),
            markline_opts=opts.MarkLineOpts(
                data=[opts.MarkLineItem(type_="average", name="平均值")],
                label_opts=opts.LabelOpts(formatter="{c}%")
            )
        )
        
        bar.set_global_opts(
            title_opts=opts.TitleOpts(
                title="年收益率分布",
                pos_left="center",
                title_textstyle_opts=opts.TextStyleOpts(
                    font_size=16,
                    color="#333",
                    font_weight="bold"
                )
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="axis",
                formatter="{b}<br/>{a}: {c}%",
                axis_pointer_type="shadow"
            ),
            xaxis_opts=opts.AxisOpts(
                name="年份",
                axislabel_opts=opts.LabelOpts(rotate=0),
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(width=2)
                )
            ),
            yaxis_opts=opts.AxisOpts(
                name="收益率(%)",
                axislabel_opts=opts.LabelOpts(formatter="{value}%"),
                splitline_opts=opts.SplitLineOpts(is_show=True)
            ),
            toolbox_opts=opts.ToolboxOpts(
                is_show=True,
                feature={
                    "saveAsImage": {},
                    "dataView": {}
                }
            )
        )
        return bar

    def create_yearly_stats_table(self,data_path):
        """创建年度收益统计表"""
        df_yearly = data_path
        
        # 格式化数据，保留两位小数
        formatted_data = []
        for _, row in df_yearly.iterrows():
            formatted_row = [
                str(row['年份']),
                f"{float(row['年总盈亏']):.2f}",
                f"{float(row['日均盈亏']):.2f}",
                f"{float(row['年最大单日盈亏']):.2f}",
                f"{float(row['年最小单日盈亏']):.2f}",
                str(int(row['交易天数'])),
                f"{float(row['年总盈亏比']):.2f}%",
                f"{float(row['日均盈亏比']):.2f}%",
                f"{float(row['年末累计收益']):.2f}%",
                f"{float(row['年收益率']):.2f}%",
                f"{float(row['年化收益率']):.2f}%"
            ]
            formatted_data.append(formatted_row)
        
        headers = [
            "年份", "年总盈亏", "日均盈亏", "年最大单日盈亏", "年最小单日盈亏",
            "交易天数", "年总盈亏比", "日均盈亏比", "年末累计收益", "年收益率", "年化收益率"
        ]
        
        table = Table()
        table.add(headers, formatted_data)
        table.set_global_opts(
            title_opts=opts.TitleOpts(
                title="表4：年度收益统计",
                subtitle="所有数据保留两位小数",
                pos_left="center",
                title_textstyle_opts=opts.TextStyleOpts(
                    font_size=16,
                    color="#333",
                    font_weight="bold"
                )
            )
        )
        return table
if __name__=='__main__':
    trader=xms_quant_backtrader()
    trader.generate_strategy_report()
    trader.buy()







    




    

        
    
        
        
       
      




    





        

