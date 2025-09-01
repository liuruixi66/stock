import pandas as pd
class account:
    def __init__(self,
                start_date='20250101',
                total_cash=1000):
        '''
        账户数据
        '''
        self.start_date=start_date
        self.total_cash=total_cash
        self.account=pd.DataFrame()
        self.account['时间']=[self.start_date]
        self.account['总资产']=[self.total_cash]
        self.account['股票市值']=[0]
        self.account['可用金额']=[self.total_cash]
        self.account['当日盈亏']=[0]
        self.account['当日盈亏比']=[0]
        self.account['持仓盈亏']=[0]
        self.account['收益']=[0]
    def get_account_data(self):
        '''
        获取全部账户数据
        '''
        self.account=self.account.drop_duplicates(subset=['时间','总资产'],keep='last')
        return self.account
    def get_trader_daily_account_data(self,date='20250101'):
        '''
        获取特定日期的账户数据
        '''
        self.account=self.account.drop_duplicates(subset=['时间','总资产'],keep='last')
        df=self.account
        df=df[df['时间']==date]
        return df
    def get_last_account_data(self):
        '''
        获取最新的账户数据
        '''
        self.account=self.account.drop_duplicates(subset=['时间','总资产'],keep='last')
        df=self.account
        date=df['时间'].tolist()[-1]
        df=df[df['时间']==date]
        return df
    def re_account_data(self):
        '''
        重新建立数据
        '''
        self.account=pd.DataFrame()
        self.account['时间']=[self.start_date]
        self.account['总资产']=[self.total_cash]
        self.account['股票市值']=[0]
        self.account['可用金额']=[self.total_cash]
        self.account['当日盈亏']=[0]
        self.account['当日盈亏比']=[0]
        self.account['持仓盈亏']=[0]
        self.account['收益']=[0]
        
