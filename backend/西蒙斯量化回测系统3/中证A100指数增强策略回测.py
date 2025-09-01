from xms_quant_backtrader import xms_quant_backtrader
from tdx_strategy_models.small_fruit_band_trading import small_fruit_band_trading
import pandas as pd
class xms_quant_backtrader_zz100:
    def __init__(self,
            trader_tool='qmt',
            data_api='qmt',
            data_type='D',
            stock_list=[],
            start_date='20200101',
            end_date='20500101',
            total_cash=100000,
            st_name='全球大类资产波段趋势增强策略'
            ):
        '''
        西蒙斯量化回测系统3.0
        作者:西蒙斯量化
        微信:xg_quant
        数据源data_api选择qmt，需要先打开miniqmt登录，选择dfcf就不需要，建议使用qmt
        '''
        self.trader_tool=trader_tool
        self.data_api=data_api
        self.data_type=data_type
        self.stock_list=stock_list
        self.start_date=start_date
        self.end_date=end_date
        self.total_cash=total_cash
        self.trader=xms_quant_backtrader(
                trader_tool=self.trader_tool,
                data_api=self.data_api,
                data_type=self.data_type,
                stock_list=self.stock_list,
                start_date=self.start_date,
                end_date=self.end_date,
                total_cash=self.total_cash,
                st_name=st_name)
        self.hold_limit=10
        self.buy_value=10000
        self.sell_value=20000
        self.sell_ratio=0
    def get_all_hist_data(self):
        '''
        获取全部历史数据
        '''
        #stock_list=self.trader.get_read_tdx_data(r'ZZA100.blk')['证券代码'].tolist()
        df=pd.read_excel(r'自定义交易股票池.xlsx')
        df['证券代码']=df['证券代码'].astype(str)
        stock_list=df['证券代码'].tolist()
        self.trader.re_trader_stock(stock_list=stock_list)
        self.trader.get_hist_data()
        hist=self.trader.data.get_hist_data()
        hist.to_csv(r'全部历史数据.csv')
        return hist
    def get_all_user_hist_data(self):
        '''
        加载本地历史数据
        '''
        stock_list=self.trader.get_read_tdx_data(r'ZZA100.blk')['证券代码'].tolist()
        self.trader.re_trader_stock(stock_list=stock_list)
        df=pd.read_csv(r'全部历史数据.csv')
        self.trader.get_user_hist_data(df)
        hist=self.trader.data.get_hist_data()
        return hist
    def cacal_all_stock_indicator(self):
        '''
        计算全部的指标
        '''
        data=pd.DataFrame()
        #hist=self.get_all_user_hist_data()
        hist=self.get_all_hist_data()
        print(hist)
        stock_list=self.trader.get_trader_stock()
        for stock in stock_list:
            df=hist[hist['stock']==stock]
            if df.shape[0]>0:
                models=small_fruit_band_trading(df=df)
                result=models.small_fruit_band_trading()
                stats=result['stats'].tolist()
                df['波段']=stats
                data=pd.concat([data,df],ignore_index=True)
        return data
    def get_buy_sell_data(self):
        '''
        获取买卖数据
        '''
        df=self.cacal_all_stock_indicator()
        buy_df=df[df['波段']=='买']
        sell_df=df[df['波段']=='卖']
        return buy_df,sell_df
    def run_backtrader(self):
        '''
        运行回测
        '''
        st_buy_df,st_sell_df=self.get_buy_sell_data()
        trader_date_list=self.trader.get_trader_date_list()
        for date in trader_date_list:
            if st_buy_df.shape[0]>0:
                buy_df=st_buy_df[st_buy_df['date']==date]
            else:
                buy_df=pd.DataFrame()
            
            if st_sell_df.shape[0]>0:
                sell_df=st_sell_df[st_sell_df['date']==date]
            else:
                sell_df=pd.DataFrame()
            
            position=self.trader.position.get_position_data()
            if position.shape[0]>0:
                position=position[position['股票余额']>=10]
                if position.shape[0]>0:
                    position=position
                    hold_amount=position.shape[0]
                    hold_stock_list=position['证券代码'].tolist()
                else:
                    position=pd.DataFrame()
                    hold_amount=0
                    hold_stock_list=[]
            else:
                position=pd.DataFrame()
                hold_amount=0
                hold_stock_list=[]
            if position.shape[0]>0:
                if sell_df.shape[0]>0:
                    sell_stock_list=sell_df['stock'].tolist()
                else:
                    sell_stock_list=[]
                position['卖出']=position['证券代码'].apply(lambda x: '是' if x in sell_stock_list else '不是')
                sell_df=position[position['卖出']=='是']
                sell_amount=sell_df.shape[0]

            else:
                sell_df=pd.DataFrame()
                sell_amount=0
            av_amount=(self.hold_limit-hold_amount)+sell_amount
            if av_amount<0:
                print(date,'达到持股限制不买入')
                av_amount=0
            else:
                av_amount=av_amount
            print('***************************')
            print('{} 持股限制{} 持有数量{} 卖出数量{} 可以买入数量{}'.format(date,self.hold_limit,hold_amount,sell_amount,av_amount))
            if buy_df.shape[0]>0:
                buy_df['持股']=buy_df['stock'].apply(lambda x: '是' if x in hold_stock_list else '不是')
                buy_df=buy_df[buy_df['持股']=='不是']
            else:
                buy_df=buy_df
            buy_df=buy_df[:av_amount]
            print('持有的股票*****************')
            print(position)
            print('卖出股票***********')
            print(sell_df)
            print('买入股票************')
            print(buy_df)
            #先卖出在买入
            if sell_df.shape[0]>0:
                for stock in position['证券代码'].tolist():
                    price=self.trader.get_price(date=date,stock=stock)
                    trader_type,amount,price=self.trader.order_value(
                        date=date,
                        stock=stock,
                        value=self.sell_value,
                        price=price,
                        trader_type='sell'
                    )
                    if trader_type=='sell' and amount>=10:
                        self.trader.sell(
                            date=date,
                            stock=stock,
                            amount=amount,
                            price=price,
                            maker='卖出成功')
                    else:
                        print(date,stock,'卖出失败')
            else:
                print(date,'卖出没有持股数据')
            #买入
            if buy_df.shape[0]>0:
                for stock in buy_df['stock'].tolist():
                    price=self.trader.get_price(date=date,stock=stock)
                    trader_type,amount,price=self.trader.order_value(
                        date=date,
                        stock=stock,
                        value=self.buy_value,
                        price=price,
                        trader_type='buy'
                    )
                    if trader_type=='buy' and amount>=10:
                        self.trader.buy(
                            date=date,
                            stock=stock,
                            amount=amount,
                            price=price,
                            maker='买入成功')
                    else:
                        print(date,stock,'卖出失败')
            else:
                print(date,'买入没有持股数据')
            #结算
            self.trader.settlement_data(date=date)
    def get_backtrader_result(self):
        '''
        获取回测结果
        '''
        self.trader.generate_strategy_report()
        self.trader.get_all_trader_data()
if __name__=='__main__':
    trader=xms_quant_backtrader_zz100()
    df=trader.run_backtrader()
    trader.get_backtrader_result()



