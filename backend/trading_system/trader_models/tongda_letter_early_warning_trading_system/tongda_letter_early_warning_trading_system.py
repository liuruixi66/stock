import pandas as pd
from tqdm import tqdm
import numpy as np
import json
from qmt_trader.qmt_trader_ths import qmt_trader_ths
from xgtrader.xgtrader import xgtrader
from trader_tool.unification_data import unification_data
import os
import pandas as pd
from datetime import datetime
from trader_tool.base_func import base_func
import shutil
import schedule
import time
class tongda_letter_early_warning_trading_system:
    def __init__(self,trader_tool='qmt',exe='C:/同花顺软件/同花顺/xiadan.exe',tesseract_cmd='C:/Program Files/Tesseract-OCR/tesseract',
                qq='1029762153@qq.com',open_set='否',qmt_path='D:/国金证券QMT交易端/userdata_mini',
                qmt_account='',qmt_account_type='STOCK',name='customize_trading_strategies'):
        '''
        小果通达信预警交易系统
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
        
        self.path=os.path.dirname(os.path.abspath(__file__))
        self.name=name
        self.data=unification_data(trader_tool='ths')
        self.data=self.data.get_unification_data()
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
        with open(r'{}\小果通达信预警设置.json'.format(self.path),encoding='utf-8') as f:
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
    def get_disk_port_data(self,stock='600031.SH'):
        price=self.data.get_spot_data(stock=stock)['最新价']
        return price
    def del_text_data(self):
        '''
        清空通达信数据接收最新的数据
        '''
        with open(r'{}\小果通达信预警设置.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        path=text['通达信警告保存路径']
        with open(r'{}'.format(path),'r+',encoding='utf-8') as f:
            com=f.truncate(0)
        f.close()
    def params_tdx_text(self):
        '''
        分析通达信内容
        '''
        with open(r'{}\小果通达信预警设置.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        path=text['通达信警告保存路径']
        columns=text['通达信警告列名称']
        try:
            with open(r'{}'.format(path),'r+',encoding='utf-8') as f:
                com=f.readlines()
        except:
            with open(r'{}'.format(path),'r+',encoding='gbk') as f:
                com=f.readlines()
        result_list=[]
        if len(com)<0:
            df=pd.DataFrame()
            df.to_excel(r'{}\原始数据\原始数据.xlsx'.format(self.path))
            print('没有警告内容****')
        else:
            for i in com:
                result_list.append(str(i).strip().split('\t'))
            df=pd.DataFrame(result_list)
            if df.shape[0]>0:
                df.columns=columns
                now_date=str(datetime.now())[:10]
                try:
                    df['时间']=df['预警时间'].apply(lambda x:str(x)[:10])
                    df=df[df['时间']==now_date]
                    df['预警id']=df['证券代码']+df['买卖条件']
                    df=df.drop_duplicates(subset=['预警id'],keep='last')
                    df.to_excel(r'{}\原始数据\原始数据.xlsx'.format(self.path))
                except Exception as e:
                    print(e)
                    df['预警id']=df['证券代码']+df['买卖条件']
                    df=df.drop_duplicates(subset=['预警id'],keep='last')
                    df.to_excel(r'{}\原始数据\原始数据.xlsx'.format(self.path))
                    
            else:
                df=pd.DataFrame()
                df.to_excel(r'{}\原始数据\原始数据.xlsx'.format(self.path))
        return df
    def get_analysis_buy_sell_data(self):
        '''
        分析买卖数据
        '''
        with open(r'{}\小果通达信预警设置.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        buy_condi=text['买入警告条件']
        sell_condi=text['卖出警告条件']
        df=pd.read_excel(r'{}\原始数据\原始数据.xlsx'.format(self.path))
        try:
            del df['Unnamed: 0']
        except:
            pass
        if df.shape[0]>0:
            df['买入']=df['买卖条件'].apply(lambda x: '是' if x in buy_condi else '不是')
            df['卖出']=df['买卖条件'].apply(lambda x: '是' if x in sell_condi else '不是')
        else:
            df=pd.DataFrame()
        df.to_excel(r'{}\买卖分析\买卖分析.xlsx'.format(self.path))
        return df
    def get_trader_stock_analysis(self):
        '''
        交易股票池分析
        '''
        with open(r'{}\小果通达信预警设置.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        test=text['是否测试']
        now_date=str(datetime.now())[:10]
        df=pd.read_excel(r'{}\买卖分析\买卖分析.xlsx'.format(self.path))
        try:
            del df['Unnamed: 0']
        except:
            pass
        log=pd.read_excel(r'{}\预警记录\预警记录.xlsx'.format(self.path))
        try:
            del log['Unnamed: 0']
        except:
            pass
        if test=='是':
            print('开启测试模型实盘记得关闭***********************')
            trader_id=[]
        else:
            if log.shape[0]>0:
                log=log[log['时间']==now_date]
                if log.shape[0]>0:
                    trader_id=log['预警id'].tolist()
                else:
                    trader_id=[]
            else:
                trader_id=[]
        if df.shape[0]>0:
            df['未交易']=df['预警id'].apply(lambda x: '是' if x in trader_id else '不是')
            df=df[df['未交易']=='不是']
            log=pd.concat([log,df],ignore_index=True)
        else:
            df=pd.DataFrame()
        log.to_excel(r'{}\预警记录\预警记录.xlsx'.format(self.path))
        df.to_excel(r'{}\交易股票池\交易股票池.xlsx'.format(self.path))
        return df
    def get_trader_stock(self):
        '''
        获取交易股票池
        '''
        with open(r'{}\小果通达信预警设置.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com) 
        test=text['是否测试']
        hold_limit=text['持股限制']
        df=pd.read_excel(r'{}\交易股票池\交易股票池.xlsx'.format(self.path))
        try:
            del df['Unnamed: 0']
        except:
            pass
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            buy_df=df[df['买入']=='是']
            buy_stock_list=buy_df['证券代码'].tolist()
        else:
            buy_stock_list=[]
        hold_stock=pd.read_excel(r'{}\持股数据\持股数据.xlsx'.format(self.path))
        if hold_stock.shape[0]>0:
            hold_stock['证券代码']=hold_stock['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            hold_stock=hold_stock[hold_stock['股票余额']>=10]
            if hold_stock.shape[0]>0:
                hold_stock_list=hold_stock['证券代码'].tolist()
                hold_amount=hold_stock.shape[0]
            else:
                hold_stock_list=[]
                hold_amount=0
        else:
            hold_stock_list=[]
            hold_amount=0
        today_entrusts=self.trader.today_entrusts()
        if today_entrusts.shape[0]>0:
            #53
            today_entrusts=today_entrusts[today_entrusts['委托状态']<=53]
            today_entrusts['买入委托']=today_entrusts['证券代码'].apply(lambda x: '是' if x in buy_stock_list else '不是')
            today_entrusts=today_entrusts[today_entrusts['买入委托']=='是']
            print(today_entrusts)
            if today_entrusts.shape[0]>0:

                today_entrusts_list=today_entrusts['证券代码'].tolist()
                today_entrusts_amount=today_entrusts.shape[0]
            else:
                today_entrusts_list=[]
                today_entrusts_amount=0
        else:
            today_entrusts_list=[]
            today_entrusts_amount=0
        if len(today_entrusts_list)>0:
            for stock in today_entrusts_list:
                hold_stock_list.append(stock)
                hold_amount+=today_entrusts_amount
        else:
            hold_stock_list=hold_stock_list
            hold_amount=hold_amount
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            buy_df=df[df['买入']=='是']
            buy_df['持股检查']=buy_df['证券代码'].apply(lambda x: '是' if x in hold_stock_list else '不是')
            buy_df=buy_df[buy_df['持股检查']=='不是']
            buy_amount=buy_df.shape[0]
            sell_df=df[df['卖出']=='是']
            sell_df['卖出检查']=sell_df['证券代码'].apply(lambda x: '是' if x in hold_stock_list else '不是')
            if test=='是':
                print('开启测试模型实盘记得关闭***********************')
                sell_df=sell_df
            else:
                sell_df=sell_df[sell_df['卖出检查']=='是']
            sell_amount=sell_df.shape[0]
            av_amount=(hold_limit-hold_amount)+sell_amount
            if av_amount<0:
                print(av_amount,'达到持股限制不买入**************')
                av_amount=0
            else:
                av_amount=av_amount
            buy_df=buy_df[:av_amount]
        else:
            buy_df=pd.DataFrame()
            sell_df=pd.DataFrame()
        buy_df.to_excel(r'{}\买入股票池\买入股票池.xlsx'.format(self.path))
        sell_df.to_excel(r'{}\卖出股票池\卖出股票池.xlsx'.format(self.path))
        print('买入股票池*********************************')
        print(buy_df)
        print('卖出股票池***********************************')
        print(sell_df)
    def check_av_target_tarder(self,stock='600031',price=2.475,trader_type='buy'):
        '''
        检查目标交易
        '''
        with open('小果通达信预警设置.json','r+',encoding='utf-8') as f:
            com=f.read()
        text1=json.loads(com)
        stock=str(stock)
        down_type=text1['交易模式']
        value=text1['固定交易资金']
        sell_value=text1['卖出资金']
        value_limit=text1['持有金额限制']
        amount=text1['固定交易数量']
        sell_value=text1['卖出资金']
        amount_limit=text1['持有数量限制']
        ratio=text1['交易百分比']
        sell_ratio=text1['卖出百分比']
        ratio_limt=text1['持有百分比']
        if trader_type=='sell':
            #检查是否可以卖出
            if down_type=='数量':
                stats=self.trader.check_stock_is_av_sell(stock=stock,amount=amount)
                if stats==True:
                    trader_type='sell'
                    amount=amount
                    price=price
                else:
                    trader_type=''
                    amount=amount
                    price=price
            elif down_type=='金额':
                trader_type,amount,price=self.trader.order_value(stock=stock,value=sell_value,price=price,trader_type=trader_type)
            elif down_type=='百分比':
                trader_type,amount,price=self.trader.order_percent(stock=stock,percent=sell_ratio,price=price,trader_type=trader_type)
            else:
                print('未知的交易类型{} 交易类型{} 下单类型{} 数量{}  价格{}'.format(stock,trader_type,down_type,amount,price))
                trader_type=''
                amount=amount
                price=price
        elif trader_type=='buy':
            #检查是否委托
            if down_type=='数量':
                trader_type,amount_1,price=self.trader.order_target_volume(stock=stock,amount=amount_limit,price=price)
                if trader_type=='buy':
                    av_buy=self.trader.check_stock_is_av_buy(stock=stock,amount=amount,price=price)
                    if av_buy==True:
                        trader_type='buy'
                        amount=amount
                        price=price
                    else:
                        trader_type=''
                        amount=amount
                        price=price
            elif down_type=='金额':
                trader_type,amount_1,price=self.trader.order_target_value(stock=stock,value=value_limit,price=price)
                if trader_type=='buy' and amount_1>=10:
                    trader_type,amount,price=self.trader.order_value(stock=stock,value=value,price=price,trader_type=trader_type)
                else:
                    trader_type=''
                    amount=amount
                    price=price
            elif down_type=='百分比':
                trader_type,amount_1,price=self.trader.order_target_percent(stock=stock,target_percent=ratio_limt,price=price)
                if trader_type=='buy' and amount_1>=10:
                    trader_type,amount,price=self.trader.order_percent(stock=stock,percent=ratio,price=price,trader_type=trader_type)
                else:
                    trader_type=''
                    amount=amount
                    price=price
            else:
                print('未知的交易类型{} 交易类型{} 下单类型{} 数量{} 价格{}'.format(stock,trader_type,down_type,amount,price))
                trader_type=''
                amount=amount
                price=price
        else:
            print('未知道下单类型{} 交易类型{} 下单类型{} 数量{} 价格{}'.format(stock,trader_type,down_type,amount,price))
            trader_type=''
            amount=amount
            price=price
            amount=int(amount)
        if trader_type=='sell' and abs(amount)>=10:
            amount=abs(amount)
        else:
            pass
        print('时间{} 交易类型{} 交易数量{} 交易价格'.format(datetime.now(),trader_type,amount,price))
        return trader_type,amount,price
    def start_trader_on(self):
        '''
        开始下单
        '''
        with open(r'{}\小果通达信预警设置.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        buy_df=pd.read_excel(r'{}\买入股票池\买入股票池.xlsx'.format(self.path))
        sell_df=pd.read_excel(r'{}\卖出股票池\卖出股票池.xlsx'.format(self.path))
        
        #先卖出
        if sell_df.shape[0]>0:
            sell_df['证券代码']=sell_df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            for stock,trader_id in zip(sell_df['证券代码'].tolist(),sell_df['预警id'].tolist()):
                try:
                    price=self.get_disk_port_data(stock=stock)
                    price=self.set_slippage(stock=stock,price=price)
                    trader_type,amount,price=self.check_av_target_tarder(stock=stock,price=price,trader_type='sell')
                    if trader_type=='sell' and amount>=10:
                        if self.trader_tool=='ths':
                            self.trader.sell(security=stock,price=price,amount=amount)
                        else:
                            self.trader.sell(security=stock,price=price,amount=amount,strategy_name=trader_id,order_remark=trader_id)
                        print('时间{} 股票{} 卖出 数量{} 价格 {} 预警id{}'.format(datetime.now(),stock,amount,price,trader_id))
                    else:
                        print('时间{} 股票{} 卖出失败可能数量不足 数量{} 价格 {} 预警id{}'.format(datetime.now(),stock,amount,price,trader_id))
                except Exception as e:
                    print(e,'{} 卖出有问题***********'.format(stock))
        else:
            print('{}没有卖出数据********************************'.format(datetime.now()))
        #买入
        if buy_df.shape[0]>0:
            buy_df['证券代码']=buy_df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            for stock,trader_id in zip(buy_df['证券代码'].tolist(),buy_df['预警id'].tolist()):
                try:
                    price=self.get_disk_port_data(stock=stock)
                    price=self.set_slippage(stock=stock,price=price)
                    trader_type,amount,price=self.check_av_target_tarder(stock=stock,price=price,trader_type='buy')
                    if trader_type=='buy' and amount>=10:
                        if self.trader_tool=='ths':
                            self.trader.buy(security=stock,price=price,amount=amount)
                        else:
                            self.trader.buy(security=stock,price=price,amount=amount,strategy_name=trader_id,order_remark=trader_id)
                        print('时间{} 股票{} 买入 数量{} 价格 {} 预警id{}'.format(datetime.now(),stock,amount,price,trader_id))
                    else:
                        print('时间{} 股票{} 买入失败可能资金不足 数量{} 价格 {} 预警id{}'.format(datetime.now(),stock,amount,price,trader_id))
                except Exception as e:
                    print(e,'{} 买入有问题***********'.format(stock))
        else:
            print('{}没有买入数据********************************'.format(datetime.now()))
    def update_all_data(self):
        '''
        更新策略数据
        '''
        if self.base_func.check_is_trader_date_1():
            try:
                self.save_balance()
                self.save_position()
                self.params_tdx_text()
                self.get_analysis_buy_sell_data()
                self.get_trader_stock_analysis()
                self.get_trader_stock()
                self.start_trader_on()
            except Exception as e:
                print(e,'模型分析有问题*************')
            
        else:
            print('{} 目前不是交易时间可以修改参数'.format(datetime.now()))
if __name__=='__main__':
    '''
    小果通达信预警系统
    '''
    with open('分析配置.json','r+',encoding='utf-8') as f:
        com=f.read()
    text=json.loads(com)
    with open(r'小果通达信预警设置.json',encoding='utf-8') as f:
        com=f.read()
    text1=json.loads(com)
    trader_tool=text['交易系统']
    exe=text['同花顺下单路径']
    tesseract_cmd=text['识别软件安装位置']
    qq=text['发送qq']                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
    open_set=text['是否开启特殊证券公司交易设置']
    qmt_path=text['qmt路径']
    qmt_account=text['qmt账户']
    qmt_account_type=text['qmt账户类型']
    trader=tongda_letter_early_warning_trading_system(trader_tool=trader_tool,exe=exe,tesseract_cmd=tesseract_cmd,qq=qq,
                           open_set=open_set,qmt_path=qmt_path,qmt_account=qmt_account,
                           qmt_account_type=qmt_account_type)
    print(trader.save_balance())
    print(trader.save_position())
    test=text1['是否测试']
    if test=='是':
        pass
    else:
        trader.del_text_data()
    #schedule.every().day.at('09:45').do(trader.update_all_data)
    schedule.every(0.05).minutes.do(trader.update_all_data)
    while True:
        schedule.run_pending()
        time.sleep(1)