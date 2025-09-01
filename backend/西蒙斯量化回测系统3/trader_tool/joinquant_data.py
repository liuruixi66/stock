import requests
import pandas as pd
import json
from io import StringIO, BytesIO
import os
class joinquant_data:
    def __init__(self,account='',password='',n=0):
        self.account=account
        self.password=password
        self.path=os.path.dirname(os.path.abspath(__file__))
        self.n=n
    def login(self):
        '''
        登录
        :return:
        '''
        #建立网站链接
        base_url='https://www.joinquant.com'
        session=requests.session()
        #一般请求头
        session.headers={
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.8',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.100 Safari/537.36',
            'Referer':'https://www.joinquant.com/user/login/doLogin?ajax=1',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }
        #建立一般连接
        session.get(url=base_url)
        login_url='https://www.joinquant.com/user/login/doLogin?ajax=1'
        data={
            'CyLoginForm[username]': self.account,
            'CyLoginForm[pwd]': self.password,
        }
        response=session.post(url=login_url,data=data)
        text=response.json()
        if text['status']=='2':
            print('登录失败',text)
            return  False
        else:
            print('{} 登录成功'.format(self.account))
            session.headers.update({
                'cookie': response.headers['Set-Cookie']}
            )
            headers = str(session.headers)
            f = open(r'{}\headers.txt'.format(self.path), 'w+')
            f.write(headers)
            f.close()
            return  True
    def get_headers(self):
        '''
        获取请求头
        :return:
        '''
        f = open(r'{}\headers.txt'.format(self.path),'r+',encoding='utf-8')
        comm=f.readline()
        f.close()
        headers=eval(comm)
        return headers
    def check_availability_headers(self):
        '''
        简称请求头是不是可用
        :return:
        '''
        #获取全部的策略
        headers=self.get_headers()
        res =requests.get(url='https://www.joinquant.com/algorithm/index/statistics',headers=headers)
        text=res.json()
        mess=text['data']['done']
        if len(mess)>0:
            print('请求头可用')
            return True
        else:
            print('请求头过期，自动重新登录')
            self.login()
            return False
    def get_all_simulate_the_backtest_list(self):
        '''
        获取全部模拟回测列表，安顺序
        :return:
        '''
        try:
            headers=self.get_headers()
            url='https://www.joinquant.com/algorithm/trade/list?process=1'
            res=requests.post(url=url,headers=headers)
            text=res.json()
            df=pd.DataFrame(text['data']['liveArr'])
            return df
        except:
            print('重新登录')
            self.login()
            df=pd.DataFrame()
            return df
    def get_all_simulate_the_backtest_stats(self):
        '''
        获取全部回测的统计
        全部组合统计
        :return:
        '''
        try:
            headers=self.get_headers()
            df=self.get_all_simulate_the_backtest_list()
            backtest_list=','.join(df['backtestId'].tolist())
            url='https://www.joinquant.com/algorithm/live/stats?'
            params={
                'offset':'-1',
                'limit':'1',
                'backtestIds':backtest_list,
                'ajax':'1'
            }
            res=requests.post(url=url,headers=headers,params=params)
            text=res.json()
            data=pd.DataFrame(text['data'])
            return data
        except:
            print('重新登录')
            self.login()
            df=pd.DataFrame()
            return df
    def get_position(self,date='2023-03-24'):
        '''
        获取持股
        安默认策略选择策略,n=0代表第一个回测组合
        提供get_all_simulate_the_backtest_list()获取全部的组合
        '''
        try:
            headers=self.get_headers()
            df=self.get_all_simulate_the_backtest_list()
            backtest_list=df['backtestId'].tolist()
            backtestId=backtest_list[self.n]
            params={
                'limit':'50',
                'backtestId':backtestId,
                'date':date,
                'isForward':'1',
                'field':'' ,
                'order':'' ,
                'ajax':'1',
            }
            url='https://www.joinquant.com/algorithm/live/position?'
            res=requests.post(url=url,params=params,headers=headers)
            text=res.json()
            df=pd.DataFrame(text['data']['position'])
            if df.shape[0]>0:
                df['证券代码']=df['stock'].apply(lambda x: str(x).split('.')[0][-6:])
                df['amount']=df['amount'].apply(lambda x:int(str(x).split('股')[0]))
            else:
                print('账户没有持股')
                df=pd.DataFrame()
            return df
        except:
            print('重新登录')
            self.login()
            df=pd.DataFrame()
            return df
    def get_backtrader_result_stats(self):
        '''
        获取回测结果统计
        安默认策略选择策略,n=0代表第一个回测组合
        提供get_all_simulate_the_backtest_list()获取全部的组合
        '''
        try:
            headers=self.get_headers()
            df=self.get_all_simulate_the_backtest_list()
            backtest_list=df['backtestId'].tolist()
            backtestId=backtest_list[self.n]
            params={
                'backtestId':backtestId,
                'offset':'0',
                'userRecordOffset':'0',
                'ajax':'1',
            }
            url='https://www.joinquant.com/algorithm/backtest/result?'
            res=requests.post(url=url,params=params,headers=headers)
            text=res.json()
            #数据解析的例子。，根据需要来
            '''
            benchmark=text['result']['benchmark']
            df=pd.DataFrame(benchmark)
            '''
            return text
        except:
            print('重新登录')
            self.login()
            df=pd.DataFrame()
            return df
    def get_backtrader_main_indictres(self):
        '''
        获取模拟交易的重要指标分析
        单个组合统计
        安默认策略选择策略,n=0代表第一个回测组合
        提供get_all_simulate_the_backtest_list()获取全部的组合
        '''
        try:
            headers=self.get_headers()
            df=self.get_all_simulate_the_backtest_list()
            backtest_list=df['backtestId'].tolist()
            backtestId=backtest_list[self.n]
            params={
                'offset':'-1',
                'limit':'1',
                'backtestId': backtestId,
                'ajax':'1'
            }
            url='https://www.joinquant.com/algorithm/live/stat?'
            res=requests.post(url=url,params=params,headers=headers)
            text=res.json()
            '''
            根据需要解析数据
            alpha=text['data']['stat']['value']
            print(alpha)
            '''
            return text
        except:
            print('重新登录')
            self.login()
            df=pd.DataFrame()
            return df
    def get_backtrader_log(self,):
        '''
        获取模拟盘交易日志
        单个组合统计
        安默认策略选择策略,n=0代表第一个回测组合
        提供get_all_simulate_the_backtest_list()获取全部的组合
        '''
        try:
            headers=self.get_headers()
            df=self.get_all_simulate_the_backtest_list()
            backtest_list=df['backtestId'].tolist()
            backtestId=backtest_list[self.n]
            params={
                'backtestId':backtestId,
                'offset':'-1',
                'ajax':'1',
            }
            url='https://www.joinquant.com/algorithm/live/log?'
            res=requests.post(url=url,params=params,headers=headers)
            text=res.json()
            df=pd.DataFrame(text['data'])
            return df
        except:
            print('重新登录')
            self.login()
            df=pd.DataFrame()
            return df
    def get_backtrader_trader_log(self,date='2023-03-20'):
        '''
        获取下单详情
        单个组合统计
        安默认策略选择策略,n=0代表第一个回测组合
        提供get_all_simulate_the_backtest_list()获取全部的组合
        '''
        try:
            headers=self.get_headers()
            df=self.get_all_simulate_the_backtest_list()
            backtest_list=df['backtestId'].tolist()
            backtestId=backtest_list[self.n]
            params={
                'limit':'200',
                'backtestId':backtestId,
                'date':date,
                'field':'' ,
                'order':'',
                'ajax':'1',
            }
            url='https://www.joinquant.com/algorithm/live/transactionDetail?'
            res=requests.post(url=url,params=params,headers=headers)
            text=res.json()
            df=pd.DataFrame(text['data']['transaction'])
            try:
                df['证券代码']=df['stock'].apply(lambda x: str(x).split('.')[0][-6:])
                try:
                    df['amount']=df['amount'].apply(lambda x:int(str(x).split('股')[0].split('-')[-1]))
                except:
                    
                    df['amount']=df['amount'].apply(lambda x:int(str(x).split('股')[0].split('>')[-1]))
                return df
            except:
                df=pd.DataFrame()
                print('{}没有交易'.format(date))
                return df
        except:
            print('重新登录')
            self.login()
            df=pd.DataFrame()
            return df
    def get_backtarder_daily_statistics(self):
        '''
        当日统计
        '''
        pass
    def get_backtrader_daily_trader(self):
        '''
        当日交易
        '''
        pass
    def get_account_data(self,date='2023-03-24'):
        '''
        获取账户数据
        可用通过get_all_simulate_the_backtest_list()获取全部
        这个程序智能获取部分
        安默认策略选择策略,n=0代表第一个回测组合
        提供get_all_simulate_the_backtest_list()获取全部的组合
        '''
        try:
            headers=self.get_headers()
            df=self.get_all_simulate_the_backtest_list()
            backtest_list=df['backtestId'].tolist()
            backtestId=backtest_list[self.n]
            params={
                'limit':'50',
                'backtestId':backtestId,
                'date':date,
                'isForward':'1',
                'field':'' ,
                'order':'' ,
                'ajax':'1',
            }
            url='https://www.joinquant.com/algorithm/live/position?'
            res=requests.post(url=url,params=params,headers=headers)
            text=res.json()
            cash=text['data']['cash']
            totalValue=text['data']['totalValue']
            data_dict={'可用现金':cash,'总价值':totalValue}
            return data_dict
        except:
            print('程序登录')
            self.login()
    def get_all_hist_trader_data(self,):
        '''
        获取全部的历史交易数据
        可用通过get_all_simulate_the_backtest_list()获取全部
        这个程序智能获取部分
        安默认策略选择策略,n=0代表第一个回测组合
        :param n:
        :return:
        '''
        try:
            headers=self.get_headers()
            df=self.get_all_simulate_the_backtest_list()
            backtest_list=df['backtestId'].tolist()
            backtestId=backtest_list[self.n]
            url='https://www.joinquant.com/algorithm/live/exportPosition?backtestId={}'.format(backtestId)
            res=requests.get(url=url,headers=headers)
            res.encoding = "gbk"
            df=pd.read_csv(StringIO(res.text))
            return df
        except:
            print('程序登录')
            self.login()
    def get_all_hist_hold_stock(self):
        '''
        获取全部的历史持股数据
        :param n:
        :return:
        '''
        try:
            headers=self.get_headers()
            df=self.get_all_simulate_the_backtest_list()
            backtest_list=df['backtestId'].tolist()
            backtestId=backtest_list[self.n]
            url='https://www.joinquant.com/algorithm/live/exportPosition?backtestId={}'.format(backtestId)
            res=requests.get(url=url,headers=headers)
            res.encoding = "gbk"
            df=pd.read_csv(StringIO(res.text))
            return df
        except:
            print('程序登录')
            self.login()
if __name__=='__main__':
    '''
    聚宽实盘跟单
    '''
    #输入最近的账号，密码
    tarder=joinquant_data(account='15117320079',password='LiXG135790')
    #第一次运行必须启动登录函数，替代我的账户数据
    tarder.login()
    #获取全部的策略
    df=tarder.get_backtrader_trader_log(date='2023-11-02')
    print(df)
    #全部策略的回测统计
    df1=tarder.get_all_simulate_the_backtest_stats()
    print(df1)
    #获取最近持股
    df2=tarder.get_position(date='2023-03-24')
    print(df2)
    #获取单个回测统计
    df3=tarder.get_backtrader_result_stats()
    print(df3)
    #重要指标统计
    df4=tarder.get_backtrader_main_indictres()
    print(df4)
    #交易日志
    df5=tarder.get_backtrader_log()
    print(df5)
    #下单记录
    df6=tarder.get_backtrader_trader_log(date='2023-03-24')
    print(df6)
    #获取账户数据,最新
    df7=tarder.get_account_data(date='2023-02-24')
    print(df7)
    #历史全部下单数据
    df8=tarder.get_all_hist_trader_data()
    print(df8)
    #历史全部持股数据
    df9=tarder.get_all_hist_hold_stock()
    print(df9)




