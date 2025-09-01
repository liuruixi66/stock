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
#债券模型
from trader_tool.base_func import base_func
from .xg_strategy_info import xg_strategy_info
from datetime import datetime
import schedule
import time
class small_fruit_strategy_trading_system:
    def __init__(self,trader_tool='ths',exe='C:/同花顺软件/同花顺/xiadan.exe',tesseract_cmd='C:/Program Files/Tesseract-OCR/tesseract',
                qq='1029762153@qq.com',open_set='否',qmt_path='D:/国金QMT交易端模拟/userdata_mini',
                qmt_account='55009640',qmt_account_type='STOCK',name='run_small_fruit_strategy_trading_system'):
        '''
        小果策略商城交易系统
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
        with open(r'{}\小果策略交易系统.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        text['持股限制']=hold_limit
        text['持有限制']=hold_limit
        #保存
        with open(r'{}\小果策略交易系统.json'.format(self.path),'w',encoding='utf-8') as f:
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
    def save_balance(self):
        '''
        保持账户数据
        '''
        df=self.trader.balance()
        df.to_excel(r'账户数据\账户数据.xlsx')
        return df
    def get_trader_data(self,strategy_id='24',name='小果六脉神剑30年债券趋势增强策略'):
        '''
        读取交易数据
        '''
        with open(r'{}\小果策略交易系统.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        url=text['服务器']
        port=text['端口']
        password=text['授权码']
        test=text['是否测试']
        try:
            xg_data=xg_strategy_info(url=url,port=port,password=password,strategy_id=strategy_id)
            df=xg_data.get_strategy_trader_info(data_type='交易记录')
            if df.shape[0]>0:
                stats=df['数据状态'].tolist()[-1]
                if stats=='True' or stats=='true' or stats==True:
                    print('{}策略id获取数据持股'.format(strategy_id))
                    now_data=''.join(str(datetime.now())[:10].split('-'))
                    df['时间']=df['时间'].astype(str)
                    if test=='是':
                        print('开启测试模式实盘记得关闭')
                        df=df
                    else:
                        df=df[df['时间']==now_data]
                    df['时间']=df['时间'].astype(str)
                    df['证券代码']=df['证券代码'].astype(str)
                    df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
                    df['买入价格']=df['买入价格'].astype(str)
                    df['策略id']=df['时间']+','+df['证券代码']+','+df['买入价格']
                    df['策略编码']=strategy_id
                    df['策略名称']=name
                else:
                    print(df)
                    df=pd.DataFrame()
            else:
                print(df)
                df=pd.DataFrame()
        except Exception as e:
            print(e,strategy_id,'有问题******')
            df=pd.DataFrame()
        df.to_excel(r'{}\原始数据\原始数据.xlsx'.format(self.path))
        return df
    def get_buy_sell_data(self):
        '''
        获取买卖数据
        交易id检查
        '''
        df=pd.read_excel(r'{}\原始数据\原始数据.xlsx'.format(self.path))
        try:
            del df['Unnamed: 0']
        except:
            pass
        log=pd.read_excel(r'{}\成交记录\成交记录.xlsx'.format(self.path))
        try:
            del log['Unnamed: 0']
        except:
            pass
        if log.shape[0]>0:
            log['策略id']=log['策略id'].astype(str)
            id_list=log['策略id'].tolist()
        else:
            id_list=[]
        if df.shape[0]>0:
            df['策略id']=df['策略id'].astype(str)
            df['交易检查']=df['策略id'].apply(lambda x: '已经成交' if x in id_list else '未成交')
            df=df[df['交易检查']=='未成交']
            df.to_excel(r'{}\交易检查\交易检查.xlsx'.format(self.path))
        else:
            df=pd.DataFrame()
            df.to_excel(r'{}\交易检查\交易检查.xlsx'.format(self.path))
        return df
    def get_deal_trader_data(self):
        '''
        处理成交数据
        '''
        with open(r'{}\小果策略交易系统.json'.format(self.path),encoding='utf-8') as f:
            com=f.read()
        text=json.loads(com)
        trader_models=text['交易模式']
        fix_value=text['固定交易资金']
        sell_value=text['卖出资金']
        hold_value_limit=text['持有金额限制']
        fix_amount=text['固定交易数量']
        sell_amount=text['卖出数量']
        hold_amount_limit=text['持有数量限制']
        fix_ratio=text['交易百分比']
        sell_ratio=text['卖出百分比']
        hold_ratio=text['持有百分比']
        df=pd.read_excel(r'{}\交易检查\交易检查.xlsx'.format(self.path))
        try:
            del df['Unnamed: 0']
        except:
            pass
        log=pd.read_excel(r'{}\成交记录\成交记录.xlsx'.format(self.path))
        try:
            del log['Unnamed: 0']
        except:
            pass
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            amount_list=[]
            for date,stock,trader_type in zip(df['时间'].tolist(),df['证券代码'].tolist(),df['交易状态'].tolist()):
                price=self.data.get_spot_data(stock=stock)['最新价']
                if trader_type=='买':
                    trader_type='buy'
                elif trader_type=='卖':
                    trader_type=='sell'
                else:
                    trader_type=''
                if trader_type=='buy':
                    if trader_models=='数量':
                        trader_type,amount,price=self.trader.order_target_volume(stock=stock,amount=hold_amount_limit,price=price)
                        if trader_type=='buy' and amount>=10:
                            if self.trader.check_stock_is_av_buy(stock=stock,amount=fix_amount,price=price):
                                amount_list.append(fix_amount)
                            else:
                                amount_list.append(0)
                        else:
                            amount_list.append(0)
                    elif trader_models=='金额':
                        trader_type,amount,price=self.trader.order_target_value(stock=stock,value=hold_value_limit,price=price)
                        if trader_type=='buy' and amount>=10:
                            trader_type,amount,price=self.trader.order_value(stock=stock,value=fix_value,price=price,trader_type='buy')
                            if trader_type=='buy' and amount>=10:
                                amount_list.append(amount)
                            else:
                                amount_list.append(0)
                        else:
                            amount_list.append(0)
                    elif trader_models=='百分比':
                        trader_type,amount,price=self.trader.order_target_percent(stock=stock,target_percent=hold_ratio,price=price)
                        if trader_type=='buy' and amount>=10:
                            trader_type,amount,price=self.trader.order_percent(stock=stock,percent=fix_ratio,price=price,trader_type='buy')
                            if trader_type=='buy' and amount>=10:
                                amount_list.append(amount)
                            else:
                                amount_list.append(0)
                        else:
                            amount_list.append(0)
                    else:
                        amount_list.append(0)
                elif trader_type=='sell':
                    if trader_models=='数量':
                        if self.trader.check_stock_is_av_sell(stock=stock,amount=sell_amount):
                            amount_list.append(sell_amount)
                        else:
                            amount_list.append(0)
                    elif trader_models=='金额':
                        trader_type,amount,price=self.trader.order_value(stock=stock,value=sell_value,price=price,trader_type='sell')
                        if trader_type=='sell' and amount>=10:
                            amount_list.append(amount)
                        else:
                            amount_list.append(0)
                    elif trader_models=='百分比':
                        trader_type,amount,price=self.trader.order_percent(stock=stock,percent=sell_ratio,price=price,trader_type='sell')
                        if trader_type=='sell' and amount>=10:
                            amount_list.append(amount)
                        else:
                            amount_list.append(0)
                    else:
                        amount_list.append(0)
                else:
                    amount_list.append(0)
            df['交易数量']=amount_list
            buy_df=df[df['交易数量']>=10]
            log=pd.concat([log,buy_df],ignore_index=True)
            log.to_excel(r'{}\成交记录\成交记录.xlsx'.format(self.path))
            print('{}买入股票池*********************'.format(datetime.now()))
            print(buy_df)
            not_trader=df[df['交易数量']<=0]
            print('{}不能成交的标的等待下次成交**************************'.format(datetime.now()))
            print(not_trader)
        else:
            buy_df=pd.DataFrame()
            print('{}**************没有交易数据'.format(datetime.now()))
        buy_df.to_excel(r'{}\交易股票池\交易股票池.xlsx'.format(self.path))
        return buy_df
    def get_start_trader_on(self):
        '''
        开始下单
        '''
        df=pd.read_excel(r'{}\交易股票池\交易股票池.xlsx'.format(self.path))
        try:
            del df['Unnamed: 0']
        except:
            pass
        if df.shape[0]>0:
            df['证券代码']=df['证券代码'].apply(lambda x: '0'*(6-len(str(x)))+str(x))
            for date,stock,amount,name,trader_type in zip(df['时间'].tolist(),
                df['证券代码'].tolist(),df['交易数量'].tolist(),df['策略名称'].tolist(),df['交易状态'].tolist()):
                price=self.data.get_spot_data(stock=stock)['最新价']
                if trader_type=='买':
                    if self.trader_tool=='ths':
                        self.trader.buy(security=stock,price=price,amount=amount)
                    else:
                        self.trader.buy(security=stock,price=price,amount=amount,strategy_name=name,order_remark=name)
                elif trader_type=='卖':
                    if self.trader_tool=='ths':
                        self.trader.sell(security=stock,price=price,amount=amount)
                    else:
                        self.trader.sell(security=stock,price=price,amount=amount,strategy_name=name,order_remark=name)
                else:
                    print('未知的交易类型{}'.format(trader_type))
        else:
            print('{} 没有交易的股票池数据'.format(datetime.now()))
    def update_all_data(self):
        '''
        更新全部策略数据
        '''
        if self.base_func.check_is_trader_date_1()==True:
            with open(r'{}\小果策略交易系统.json'.format(self.path),encoding='utf-8') as f:
                com=f.read()
            text=json.loads(com)
            name_list=text['策略名称']
            id_list=text['策略id']
            stop_time=text['不同策略的间隔时间秒']
            for name,st_id in zip(name_list,id_list):
                self.get_trader_data(strategy_id=st_id,name=name)
                self.get_buy_sell_data()
                self.get_deal_trader_data()
                self.get_start_trader_on()
                print('{} {} 策略分析完成'.format(datetime.now(),name))
                time.sleep(stop_time)
        else:
            print('{} 目前不是交易时间'.format(datetime.now()))
if __name__=='__main__':
    '''
    运行程序
    '''
    with open('分析配置.json','r+',encoding='utf-8') as f:
        com=f.read()
    text=json.loads(com)
    trader_tool=text['交易系统']
    exe=text['同花顺下单路径']
    tesseract_cmd=text['识别软件安装位置']
    print(tesseract_cmd)
    qq=text['发送qq']
    test=text['测试']
    open_set=text['是否开启特殊证券公司交易设置']
    qmt_path=text['qmt路径']
    qmt_account=text['qmt账户']
    qmt_account_type=text['qmt账户类型']
    slippage=text['滑点']
    trader=small_fruit_strategy_trading_system(trader_tool=trader_tool,exe=exe,tesseract_cmd=tesseract_cmd,
            qmt_path=qmt_path,qmt_account=qmt_account,qmt_account_type=qmt_account_type)
    trader.save_position()
    trader.save_balance()
    schedule.every(0.03).minutes.do(trader.update_all_data)
    while True:
        schedule.run_pending()
        time.sleep(1)



    
    


                



        

    
        
            


                            

                        









                
    




        

        

    
            


                







        
    