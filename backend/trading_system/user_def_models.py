from xgtrader.stock_data_ths import stock_data_ths
from xgtrader.bond_cov_data_ths import bond_cov_data_ths
from xgtrader.etf_fund_data_ths import etf_fund_data_ths
from xgtrader.xgtrader import xgtrader
from xgtrader.unification_data_ths import unification_data_ths
from trader_tool.ths_limitup_data import ths_limitup_data
from trader_tool.dfcf_rq import popularity
from trader_tool.ths_rq import ths_rq
from trader_tool import jsl_data
from trader_tool.dfcf_theme import dfcf_theme


from trader_tool.stock_upper_data import stock_upper_data
from trader_tool.analysis_models import analysis_models
from trader_tool.shape_analysis import shape_analysis
from trader_tool.trader_frame import trader_frame
from trader_tool.base_func import base_func
from  qmt_trader.xtquant import xtdata
import time
import json
import pywencai
import pandas as pd
from trader_tool.stock_em import stock_em
from trader_tool.unification_data import unification_data
#微盘股趋势轮动
from trader_models.micro_stock_cap_trend_trading.micro_stock_cap_trend_trading import micro_stock_cap_trend_trading

#可转债三低趋势增强策略
#from trader_models.bond_cov_three_low_trend_enhancement_strategy.bond_cov_three_low_trend_enhancement_strategy import bond_cov_three_low_trend_enhancement_strategy
#小果行业动量轮动交易策略

#小果全球动量模型实盘策略
from trader_models.small_fruit_global_momentum_model_solid_trading_strategy.small_fruit_global_momentum_model_solid_trading_strategy import small_fruit_global_momentum_model_solid_trading_strategy
#小果波段掘金趋势增强策略
from trader_models.small_fruit_band_trading_strategy.small_fruit_band_trading_strategy import small_fruit_band_trading_strategy

from trader_models.xueqiou_trading_strategy.xueqiou_trading_strategy import xueqiou_trading_strategy
#聚宽交易策略系统
from trader_models.joinquant_trading_strategy.joinquant_trading_strategy import joinquant_trading_strategy

from trader_models.small_fruit_bond_six_pulse_excalibur_trend_enhancement_strategy.small_fruit_bond_six_pulse_excalibur_trend_enhancement_strategy import small_fruit_bond_six_pulse_excalibur_trend_enhancement_strategy
from trader_models.small_kirin_trend_enhancement_strategy.small_kirin_trend_enhancement_strategy import small_kirin_trend_enhancement_strategy
from trader_models.global_broad_class_low_correlation_trend_rotation_strategy.global_broad_class_low_correlation_trend_rotation_strategy import global_broad_class_low_correlation_trend_rotation_strategy

from trader_models.global_outer_disc_six_pulse_excalibur_trend_strategy.global_outer_disc_six_pulse_excalibur_trend_strategy import global_outer_disc_six_pulse_excalibur_trend_strategy

from trader_models.convertible_bond_five_factor_rotation_strategy.convertible_bond_five_factor_rotation_strategy import convertible_bond_five_factor_rotation_strategy
#
from trader_models.global_major_asset_six_pulse_excalibur_rotation_strategy.global_major_asset_six_pulse_excalibur_rotation_strategy import global_major_asset_six_pulse_excalibur_rotation_strategy

#红利低波趋势轮动策略
from trader_models.dividend_low_wave_trend_rotation_strategy.dividend_low_wave_trend_rotation_strategy import dividend_low_wave_trend_rotation_strategy

from trader_models.xiaoguo_zhong_index_trend_enhancement_strategy.xiaoguo_zhong_index_trend_enhancement_strategy import xiaoguo_zhong_index_trend_enhancement_strategy

from trader_models.small_fruit_small_market_trend_enhancement_strategy.small_fruit_small_market_trend_enhancement_strategy import small_fruit_small_market_trend_enhancement_strategy
#
from trader_models.small_fruit_industry_six_pulse_excalibur_trend_enhancement_strategy.small_fruit_industry_six_pulse_excalibur_trend_enhancement_strategy import small_fruit_industry_six_pulse_excalibur_trend_enhancement_strategy

from trader_models.xg_bond_cov_3_low_strategy.xg_bond_cov_3_low_strategy import xg_bond_cov_3_low_strategy#

from trader_models.small_fruit_reit_fund_six_pulse_excalibur_trend_enhancement_strategy.small_fruit_reit_fund_six_pulse_excalibur_trend_enhancement_strategy import small_fruit_reit_fund_six_pulse_excalibur_trend_enhancement_strategy
from trader_models.global_broad_class_low_correlation_six_pulse_excalibur_trend_rotation_strategy.global_broad_class_low_correlation_six_pulse_excalibur_trend_rotation_strategy import global_broad_class_low_correlation_six_pulse_excalibur_trend_rotation_strategy
from trader_models.global_outboard_trend_strategy.global_outboard_trend_strategy import global_outboard_trend_strategy
class user_def_models:
    def __init__(self,trader_tool='ths',exe='C:/同花顺软件/同花顺/xiadan.exe',tesseract_cmd='C:/Program Files/Tesseract-OCR/tesseract',
                qq='1029762153@qq.com',open_set='否',qmt_path='D:/国金QMT交易端模拟/userdata_mini',
                qmt_account='55009640',qmt_account_type='STOCK',data_api='qmt'):
        '''
        自定义模型
        '''
        self.data_api=data_api
        self.exe=exe
        self.tesseract_cmd=tesseract_cmd
        self.qq=qq
        self.trader_tool=trader_tool
        self.open_set=open_set
        self.qmt_path=qmt_path
        self.qmt_account=qmt_account
        self.qmt_account_type=qmt_account_type

        order_frame=trader_frame(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                 open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                 qmt_account_type=self.qmt_account_type)
        self.trader=order_frame.get_trader_frame()
        data=unification_data(trader_tool=self.trader_tool,data_api=self.data_api)
        self.data=data.get_unification_data()
        self.stats=0
        self.base_func=base_func()
        self.connect()
    def connect(self):
        self.trader.connect()
    def run_global_outboard_trend_strategy(self):
        '''
        全球外盘波段趋势增强策略
        '''
        if  self.base_func.check_is_trader_date_1():
            models=global_outboard_trend_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                    open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                    qmt_account_type=self.qmt_account_type,name='run_global_outboard_trend_strategy',data_api=self.data_api)
            models.update_all_data()
        else:
            print('全球外盘波段趋势增强策略不是交易时间') 
    def run_global_broad_class_low_correlation_six_pulse_excalibur_trend_rotation_strategy(self):
        '''
        全球大类低相关性六脉神剑趋势轮动策略
        '''
        if  self.base_func.check_is_trader_date_1():
            models=global_broad_class_low_correlation_six_pulse_excalibur_trend_rotation_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                    open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                    qmt_account_type=self.qmt_account_type,name='run_global_broad_class_low_correlation_six_pulse_excalibur_trend_rotation_strategy',data_api=self.data_api)
            models.update_all_data()
        else:
            print('小果reits基金六脉神剑趋势增强策略不是交易时间') 
    def run_small_fruit_reit_fund_six_pulse_excalibur_trend_enhancement_strategy(self):
        '''
        小果reits基金六脉神剑趋势增强策略
        '''
        
        if  self.base_func.check_is_trader_date_1():
            models=small_fruit_reit_fund_six_pulse_excalibur_trend_enhancement_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                    open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                    qmt_account_type=self.qmt_account_type,name='run_small_fruit_reit_fund_six_pulse_excalibur_trend_enhancement_strategy',data_api=self.data_api)
            models.update_all_data()
        else:
            print('小果reits基金六脉神剑趋势增强策略不是交易时间') 
    

    def sell_all_stock_on_time(self,name='尾盘一键清仓'):
        '''
        尾盘一键清仓
        '''
        df=self.trader.position()
        if df.shape[0]>0:
            for  stock,hold_amount,amount in zip(df['证券代码'].tolist(),
                        df['股票余额'].tolist(),df['可用余额'].tolist()):
                price=self.data.get_spot_data(stock=stock)['最新价']
                if amount>=10:
                    print(name,stock,'持有{} 可以{} 卖出{}'.format(hold_amount,amount,amount))
                    if self.trader_tool=='ths':
                        self.trader.sell(security=stock,price=price,amount=amount)
                    else:
                        self.trader.sell(security=stock,price=price,amount=amount,strategy_name=name,order_remark=name)
                else:
                    print(name,stock,'持有{} 可以{} 卖出{}'.format(hold_amount,amount,amount))

    def run_xg_bond_cov_3_low_strategy(self):
        '''
        小果可转债3低轮动策略
        '''
        if  self.base_func.check_is_trader_date_1():
            models=xg_bond_cov_3_low_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                    open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                    qmt_account_type=self.qmt_account_type,name='run_run_xg_bond_cov_3_low_strategy',data_api=self.data_api)
            models.updata_all_data()
        else:
            print('小果主流外盘基金四趋势模型增强策略不是交易时间') 
    
        
    
        
    
    def run_small_fruit_industry_six_pulse_excalibur_trend_enhancement_strategy(self):
        '''
        小果行业六脉神剑趋势增强策略
        '''
        if  self.base_func.check_is_trader_date():
            models=small_fruit_industry_six_pulse_excalibur_trend_enhancement_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                    open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                    qmt_account_type=self.qmt_account_type,name='run_small_fruit_industry_six_pulse_excalibur_trend_enhancement_strategy',data_api=self.data_api)
            models.update_all_data()
        else:
            print('小果小市值趋势增强策略不是交易时间') 
    def run_small_fruit_small_market_trend_enhancement_strategy(self):
        '''
        小果小市值趋势增强策略
        '''
        if  self.base_func.check_is_trader_date():
            models=small_fruit_small_market_trend_enhancement_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                    open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                    qmt_account_type=self.qmt_account_type,name='run_small_fruit_small_market_trend_enhancement_strategy',data_api=self.data_api)
            models.update_all_data()
        else:
            print('小果小市值趋势增强策略不是交易时间') 
    def run_xiaoguo_zhong_index_trend_enhancement_strategy(self):
        '''
        小果指数趋势增强策略
        '''
        if  self.base_func.check_is_trader_date():
            models=xiaoguo_zhong_index_trend_enhancement_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                    open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                    qmt_account_type=self.qmt_account_type,name='run_xiaoguo_zhong_index_trend_enhancement_strategy',data_api=self.data_api)
            models.update_all_data()
        else:
            print('小果指数趋势增强策略不是交易时间') 
    
    
    def run_dividend_low_wave_trend_rotation_strategy(self):
        '''
        红利低波趋势轮动策略
        '''
        if  self.base_func.check_is_trader_date():
            models=dividend_low_wave_trend_rotation_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                    open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                    qmt_account_type=self.qmt_account_type,name='run_dividend_low_wave_trend_rotation_strategy',data_api=self.data_api)
            models.update_all_data()
        else:
            print('红利低波趋势轮动策略不是交易时间') 

    
    
    def run_global_major_asset_six_pulse_excalibur_rotation_strategy(self):
        '''
        全球大类资产六脉神剑轮动策略
        '''
        if  self.base_func.check_is_trader_date():
            models=global_major_asset_six_pulse_excalibur_rotation_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                    open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                    qmt_account_type=self.qmt_account_type,name='run_global_major_asset_six_pulse_excalibur_rotation_strategy',data_api=self.data_api)
            models.update_all_data()
        else:
            print('全球大类资产六脉神剑轮动策略不是交易时间') 
    def run_convertible_bond_five_factor_rotation_strategy(self):
        '''
        可转债五因子轮动策略
        '''
        models=convertible_bond_five_factor_rotation_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                qmt_account_type=self.qmt_account_type,name='run_convertible_bond_five_factor_rotation_strategy',data_api=self.data_api)
        models.updata_all_data()
    def run_global_broad_class_low_correlation_trend_rotation_strategy(self):
        '''
        全球大类低相关性波段趋势轮动策略
        '''
        
        models=global_broad_class_low_correlation_trend_rotation_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                qmt_account_type=self.qmt_account_type,name='run_global_broad_class_low_correlation_trend_rotation_strategy',data_api=self.data_api)
        models.update_all_data()
    def run_small_kirin_trend_enhancement_strategy(self):
        '''
        小果麒麟趋势增强策略
        '''
        models=small_kirin_trend_enhancement_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                qmt_account_type=self.qmt_account_type,name='run_small_kirin_trend_enhancement_strategy',data_api=self.data_api)
        models.update_all_data()
    def run_small_fruit_bond_six_pulse_excalibur_trend_enhancement_strategy(self):
        '''
        小果债券六脉神剑趋势增强策略
        '''
        models=small_fruit_bond_six_pulse_excalibur_trend_enhancement_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                qmt_account_type=self.qmt_account_type,name='run_small_fruit_bond_six_pulse_excalibur_trend_enhancement_strategy',data_api=self.data_api)
        models.update_all_data()
    def run_micro_stock_cap_trend_trading(self):
        '''
        微盘股趋势轮动策略
        '''
        models=micro_stock_cap_trend_trading(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                qmt_account_type=self.qmt_account_type,name='run_micro_stock_cap_trend_trading',data_api=self.data_api)
        models.update_all_data()
   
    
    def get_bidPrice1(self,stock='204001.SH'):
        '''
        获取价格
        '''
        xtdata.subscribe_whole_quote(code_list=[stock])
        tick=xtdata.get_full_tick(code_list=[stock])
        tick=tick[stock]
        return tick['lastPrice']
    def run_reverse_repurchase_of_treasury_bonds_1(self,buy_ratio=1):
        '''
        国债逆回购1,新的函数
        购买比例buy_ratio
        '''
        try:
            # 对交易回调进行订阅，订阅后可以收到交易主推，返回0表示订阅成功
            account=self.trader.balance()
            av_cash=account['可用金额'].tolist()[-1]
            av_cash=float(av_cash)
            av_cash=av_cash*buy_ratio
            stock_code_sh = '204001.SH'
            stock_code_sz = '131810.SZ'
            price_sh = self.get_bidPrice1(stock_code_sh)
            price_sz = self.get_bidPrice1(stock_code_sz)
            bidPrice1 = max(price_sh,price_sz)
            if price_sh > price_sz:
                stock_code = stock_code_sh
            else:
                stock_code = stock_code_sz
            print(stock_code,bidPrice1)
            price=bidPrice1
            stock=stock_code
            #下单的数量要是1000
            amount = int(av_cash/1000)*10
            #借出钱sell
            if amount>0:
                fix_result_order_id =self.trader.sell(security=stock,amount=amount,price=price)
                text='国债逆回购交易类型 代码{} 价格{} 数量{} 订单编号{}'.format(stock,price,amount,fix_result_order_id)
                print(text)
                return '交易成功',text
            else:
                text='国债逆回购卖出 标的{} 价格{} 委托数量{}小于0有问题'.format(stock,price,amount)
                print(text)
                return '交易失败',text
        except Exception as e:
            print(e)
            return '国债逆回购卖出交易失败'
    def run_reverse_repurchase_of_treasury_bonds_2(self):
        '''
        国债逆回购1,新的函数
        购买比例buy_ratio
        '''
        try:
            self.trader.reverse_repurchase_of_treasury_bonds()
            print('逆回购回购成功****************')
        except Exception as e:
            print(e)
            return '国债逆回购卖出交易失败'
    
    
    

    
    def run_small_fruit_global_momentum_model_solid_trading_strategy(self):
        '''
        小果全球动量模型实盘策略
        '''
        if  self.base_func.check_is_trader_date():
            models=small_fruit_global_momentum_model_solid_trading_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                    open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                    qmt_account_type=self.qmt_account_type,name='run_small_fruit_global_momentum_model_solid_trading_strategy',data_api=self.data_api)
            models.update_all_data()
        else:
            print('小果全球动量模型实盘策略不是交易时间')
    def run_small_fruit_band_trading_strategy(self):
        '''
        小果波段掘金趋势增强策略
        '''
        if  self.base_func.check_is_trader_date():
            models=small_fruit_band_trading_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                    open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                    qmt_account_type=self.qmt_account_type,name='run_small_fruit_band_trading_strategy',data_api=self.data_api)
            models.update_all_data()
        else:
            print('小果波段掘金趋势增强策略不是交易时间')
        
    def run_xueqiou_trading_strategy(self):
        '''
        雪球跟单模型
        '''
        if  self.base_func.check_is_trader_date():
            models=xueqiou_trading_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                    open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                    qmt_account_type=self.qmt_account_type,name='run_xueqiou_trading_strategy',data_api=self.data_api)
            models.update_all_data()
        else:
            print('雪球跟单模型不是交易时间') 
    def run_joinquant_trading_strategy(self):
        '''
        聚宽交易策略系统
        '''
        if  self.base_func.check_is_trader_date():
            models=joinquant_trading_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                    open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                    qmt_account_type=self.qmt_account_type,name='run_joinquant_trading_strategy',data_api=self.data_api)
            models.update_all_data()
        else:
            print('聚宽交易策略系统不是交易时间') 
    
    def run_global_outer_disc_six_pulse_excalibur_trend_strategy(self):
        '''
        全球外盘六脉神剑趋势策略
        '''
        models=global_outer_disc_six_pulse_excalibur_trend_strategy(trader_tool=self.trader_tool,exe=self.exe,tesseract_cmd=self.tesseract_cmd,
                                open_set=self.open_set,qmt_path=self.qmt_path,qmt_account=self.qmt_account,
                                qmt_account_type=self.qmt_account_type,name='run_global_outer_disc_six_pulse_excalibur_trend_strategy',data_api=self.data_api)
        models.update_all_data()
if __name__=='__main__':
    with open('分析配置.json','r+',encoding='utf-8') as f:
        com=f.read()
    text=json.loads(com)
    trader_tool=text['交易系统']
    exe=text['同花顺下单路径']
    tesseract_cmd=text['识别软件安装位置']
    qq=text['发送qq']
    test=text['测试']                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
    open_set=text['是否开启特殊证券公司交易设置']
    qmt_path=text['qmt路径']
    qmt_account=text['qmt账户']
    qmt_account_type=text['qmt账户类型']
    data_api=text['交易数据源']
    models=user_def_models(trader_tool=trader_tool,exe=exe,tesseract_cmd=tesseract_cmd,qq=qq,
                           open_set=open_set,qmt_path=qmt_path,qmt_account=qmt_account,
                           qmt_account_type=qmt_account_type,data_api=data_api)
    models.connect()
    func_list=text['自定义函数']
    for func in func_list:
        runc_func='models.{}()'.format(func)
        eval(runc_func)
