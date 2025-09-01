import pandas as pd
import requests
import json
from qmt_trader.qmt_data import qmt_data
#可转债数据
class bond_cov_data_qmt:
    def __init__(self):
        self.qmt_data=qmt_data()
        self.qmt_all_data=self.qmt_data.get_all_data()
    def get_cov_bond_hist_data(self,stock='113016',start='20100101',end='20500101',limit='10000',
                                data_type='D',fqt='1',count=8000):
        '''
        可转债历史数据
        stock 证券代码
        end结束时间
        limit数据长度
        data_type数据类型：
           1 1分钟
           5 5分钟
           15 15分钟
           30 30分钟
           60 60分钟
           D 日线数据
           W 周线数据
           M 月线数据
        fqt 复权
        fq=0股票除权
        fq=1前复权
        fq=2后复权
        '''
        stock=str(stock)[:6]
        stock_1=stock
        data_dict = {'1': '1', '5': '5', '15': '15', '30': '30', '60': '60', 'D': '101', 'W': '102', 'M': '103'}
        klt=data_dict[data_type]
        try:
            params={
                'secid':'1.{}'.format(stock),
                'klt':klt,
                'fqt':fqt,
                'lmt':limit,
                'start':start,
                'end':end,
                'iscca': '1',
                'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8',
                'fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64',
                'ut':'f057cbcbce2a86e2866ab8877db1d059',
                'forcect':'1'
            }
            url='https://push2his.eastmoney.com/api/qt/stock/kline/get?'
            res = requests.get(url=url, params=params)
            text = res.text
            json_text = json.loads(text)
            df = pd.DataFrame(json_text['data']['klines'])
            df.columns = ['数据']
            data_list = []
            for i in df['数据']:
                data_list.append(i.split(','))
            data = pd.DataFrame(data_list)
            columns = ['date', 'open', 'close', 'high', 'low', 'volume', 
                    '成交额', '振幅', '涨跌幅', '涨跌额', '换手率','_','_','_']
            data.columns = columns
            del data['_']
            for m in columns[1:-3]:
                data[m] = pd.to_numeric(data[m])
            data1=data.sort_index(ascending=True,ignore_index=True)
            #data1['累计涨跌幅']=data1['涨跌幅'].cumsum()
            return data1
        except Exception as e:
            try:
                params={
                    'secid':'0.{}'.format(stock),
                    'klt':klt,
                    'fqt':fqt,
                    'start':start,
                    'lmt':limit,
                    'end':end,
                    'iscca': '1',
                    'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8',
                    'fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64',
                    'ut':'f057cbcbce2a86e2866ab8877db1d059',
                    'forcect':'1'
                }
                url='https://push2his.eastmoney.com/api/qt/stock/kline/get?'
                res = requests.get(url=url, params=params)
                text = res.text
                json_text = json.loads(text)
                df = pd.DataFrame(json_text['data']['klines'])
                df.columns = ['数据']
                data_list = []
                for i in df['数据']:
                    data_list.append(i.split(','))
                data = pd.DataFrame(data_list)
                columns = ['date', 'open', 'close', 'high', 'low', 'volume', 
                        '成交额', '振幅', '涨跌幅', '涨跌额', '换手率','_','_','_']
                data.columns = columns
                del data['_']
                for m in columns[1:-3]:
                    data[m] = pd.to_numeric(data[m])
                data1=data.sort_index(ascending=True,ignore_index=True)
                return data1
            except Exception as e:
                print("运行错误:",e)
                stock=self.qmt_data.adjust_stock(stock)
                data1=self.qmt_all_data.get_market_data_ex(stock_list=[stock])
                data1=data1[stock]
                
    def get_cov_bond_spot(self,stock='113016'):
        '''
        获取可转债实时数据
        '''
        stock=str(stock)[:6]
        stock_1=stock
        try:
            stock=str(stock)[:6]
            params={
                        'cb':'jQuery35107788691587529397_1680967733868',
                        'secid':'1.{}'.format(stock),
                        'forcect':'1',
                        'invt': '2',
                        'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f59,f60,f108,f152,f154,f161,f168,f169,f170,f262,f264,f265,f266,f267,f424,f426,f427,f428,f429,f432',
                        'ut': 'f057cbcbce2a86e2866ab8877db1d059',
                        '_': '1680967733870',
                    }
            url='https://push2.eastmoney.com/api/qt/stock/get?'
            res=requests.get(url=url,params=params)
            text=res.text[41:len(res.text)-2]
            json_text=json.loads(text)['data']
            data_dict={}
            data_dict['最新价']=json_text['f43']/1000
            data_dict['最高价']=json_text['f44']/1000
            data_dict['最低价']=json_text['f45']/1000
            data_dict['今开']=json_text['f46']/1000 
            data_dict['总手']=json_text['f47']
            data_dict['金额']=json_text['f48']
            #data_dict['量比']=json_text['f50']/100
            data_dict['外盘']=json_text['f49']
            data_dict['涨停价']=json_text['f51']/1000
            data_dict['跌停价']=json_text['f52']/1000
            data_dict['昨收']=json_text['f60']/1000
            data_dict['涨跌幅']=json_text['f170']/100
            data_dict['证券代码']=json_text['f262']
            data_dict['名称']=json_text['f264']
            data_dict['溢价率']=json_text['f428']/100
            return data_dict
        except Exception as e:
            print("运行错误:",e)
            try:
                stock=str(stock)[:6]
                params={
                                'cb':'jQuery35107788691587529397_1680967733868',
                                'secid':'0.{}'.format(stock),
                                'forcect':'1',
                                'invt': '2',
                                'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f59,f60,f108,f152,f154,f161,f168,f169,f170,f262,f264,f265,f266,f267,f424,f426,f427,f428,f429,f432',
                                'ut': 'f057cbcbce2a86e2866ab8877db1d059',
                                '_': '1680967733870',
                            }
                url='https://push2.eastmoney.com/api/qt/stock/get?'
                res=requests.get(url=url,params=params)
                text=res.text[41:len(res.text)-2]
                json_text=json.loads(text)['data']
                data_dict={}
                data_dict['最新价']=json_text['f43']/1000
                data_dict['最高价']=json_text['f44']/1000
                data_dict['最低价']=json_text['f45']/1000
                data_dict['今开']=json_text['f46']/1000 
                data_dict['总手']=json_text['f47']
                data_dict['金额']=json_text['f48']
                #data_dict['量比']=json_text['f50']/100
                data_dict['外盘']=json_text['f49']
                data_dict['涨停价']=json_text['f51']/1000
                data_dict['跌停价']=json_text['f52']/1000
                data_dict['昨收']=json_text['f60']/1000
                data_dict['涨跌幅']=json_text['f170']/100
                data_dict['证券代码']=json_text['f262']
                data_dict['名称']=json_text['f264']
                data_dict['溢价率']=json_text['f428']/100
                return data_dict
            except Exception as e:
                try:
                    result={}
                    stock_1=stock
                    stock_1=str(stock)+'.SH'
                    self.qmt_data.subscribe_whole_quote(code_list=[stock_1])
                    text=self.qmt_data.get_full_tick(code_list=[stock_1])
                    text=text[stock_1]
                    if len(text)>0:
                        result['最新价']=text['lastPrice']
                        result['最高价']=text['high']
                        result['最低价']=text['low']
                        result['开盘价']=text['open']
                        result['金额']=text['amount']
                        result['涨跌幅']=((text['lastPrice']-text['open'])/text['open'])*100
                        return result
                    else:
                        result={}
                except:
                    result={}
                    stock_1=str(stock)+'.SZ'
                    self.qmt_data.subscribe_whole_quote(code_list=[stock_1])
                    text=self.qmt_data.get_full_tick(code_list=[stock_1])
                    text=text[stock_1]
                    result['最新价']=text['lastPrice']
                    result['最高价']=text['high']
                    result['最低价']=text['low']
                    result['开盘价']=text['open']
                    result['金额']=text['amount']
                    result['涨跌幅']=((text['lastPrice']-text['open'])/text['open'])*100
                    return result
    def get_cov_bond_spot_trader_data(self,stock='123018'):
        '''
        控制住实时数据
        '''
        stock=str(stock)[:6]
        stock_1=stock
        try:
            url='https://push2.eastmoney.com/api/qt/stock/details/get?'
            params={
                #'cb': 'jQuery3510784161408794853_1689866980183',
                'secid': '0.{}'.format(stock),
                'forcect': '1',
                'invt': '2',
                'pos': '-10000',
                'iscca': '1',
                'fields1': 'f1,f2,f3,f4,f5',
                'fields2': 'f51,f52,f53,f54,f55',
                'ut': 'f057cbcbce2a86e2866ab8877db1d059',
                '_': '1689866980185'
            }
            res=requests.get(url=url,params=params)
            text=res.json()
            df=pd.DataFrame(text['data']['details'])
            df.columns=['数据']
            all_df=[]
            for i in df['数据']:
                all_df.append(i.split(','))
            data=pd.DataFrame(all_df)
            data.columns=['时间','价格','成交量','单数','性质']
            def select_stock(x):
                if x=='2':
                    return '买盘'
                elif x=='1':
                    return '卖盘'
                else:
                    return x
            data['性质']=data['性质'].apply(select_stock)
            data['价格']=data['价格'].astype(float)
            data['时间']=data['时间'].apply(lambda x :int(str(x).replace(':','')))
            data1=data[data['时间']<=92600]
            open_price=data1['价格'].tolist()[-1]
            data['涨跌幅']=((data['价格']-open_price)/open_price)*100
            data['实时涨跌幅']=data['涨跌幅']-data['涨跌幅'].shift(1)
            return data
        except Exception as e:
            url='https://push2.eastmoney.com/api/qt/stock/details/get?'
            params={
                    #'cb': 'jQuery3510784161408794853_1689866980183',
                    'secid': '1.{}'.format(stock),
                    'forcect': '1',
                    'invt': '2',
                    'pos': '-10000',
                    'iscca': '1',
                    'fields1': 'f1,f2,f3,f4,f5',
                    'fields2': 'f51,f52,f53,f54,f55',
                    'ut': 'f057cbcbce2a86e2866ab8877db1d059',
                    '_': '1689866980185'
            }
            res=requests.get(url=url,params=params)
            text=res.json()
            df=pd.DataFrame(text['data']['details'])
            df.columns=['数据'] 
            all_df=[]
            for i in df['数据']:
                all_df.append(i.split(','))
            data=pd.DataFrame(all_df)
            data.columns=['时间','价格','成交量','单数','性质']
            def select_stock(x):
                if x=='2':
                    return '买盘'
                elif x=='1':
                    return '卖盘'
                else:
                    return x
            data['性质']=data['性质'].apply(select_stock)
            data['价格']=data['价格'].astype(float)
            data['时间']=data['时间'].apply(lambda x :int(str(x).replace(':','')))
            data1=data[data['时间']<=92600]
            open_price=data1['价格'].tolist()[-1]
            data['涨跌幅']=((data['价格']-open_price)/open_price)*100
            data['实时涨跌幅']=data['涨跌幅']-data['涨跌幅'].shift(1)
            return data
    def get_cov_bond_dish_data(self,stock='111007'):
        '''
        获取可转债盘口数据
        '''
        try:
            url='https://push2.eastmoney.com/api/qt/stock/get?'
            data={}
            params={
                'invt': '2',
                'fltt': '1',
                #'cb': 'jQuery35106054114396324737_1690471800729',
                'fields': 'f58,f734,f107,f57,f43,f59,f169,f170,f152,f46,f60,f44,f45,f171,f47,f86,f292,f19,f39,f20,f40,f17,f531,f18,f15,f16,f13,f14,f11,f12,f37,f38,f35,f36,f33,f34,f31,f32,f48,f50,f161,f49,f191,f192,f71,f264,f263,f262,f267,f265,f268,f706,f700,f701,f703,f154,f704,f702,f705,f721,f51,f52,f301',
                'secid': '1.'+stock,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'wbp2u': '|0|0|0|web',
            }
            res=requests.get(url=url,params=params)
            text=res.text
            text=res.json()['data']
            buy_5_price=text['f11']/1000
            data['buy_5_price']=buy_5_price
            buy_5_num=text['f12']
            data['buy_5_num']=buy_5_num
            buy_4_price=text['f13']/1000
            data['buy_4_price']=buy_4_price
            buy_4_num=text['f14']
            data['buy_4_num']=buy_4_num
            buy_3_price=text['f15']/1000
            data['buy_3_price']=buy_3_price
            buy_3_num=text['f16']
            data['buy_3_num']=buy_3_num
            buy_2_price=text['f17']/1000
            data['buy_2_price']=buy_2_price
            buy_2_num=text['f18']
            data['buy_2_num']=buy_2_num
            buy_1_price=text['f19']/1000
            data['buy_1_price']=buy_1_price
            buy_1_num=text['f20']
            data['buy_1_num']=buy_1_num
            sell_5_price=text['f31']/1000
            data['sell_5_price']=sell_5_price
            sell_5_num=text['f32']
            data['sell_5_num']=sell_5_num
            sell_4_price=text['f33']/1000
            data['sell_4_price']=sell_4_price
            sell_4_num=text['f34']
            data['sell_4_num']=sell_4_num
            sell_3_price=text['f35']/1000
            data['sell_3_price']=sell_3_price
            sell_3_num=text['f36']
            data['sell_3_num']=sell_3_num
            sell_2_price=text['f37']/100
            data['sell_2_price']=sell_2_price
            sell_2_num=text['f38']
            data['sell_2_num']=sell_2_num
            sell_1_price=text['f39']/1000
            data['sell_1_price']=sell_1_price
            sell_1_num=text['f40']
            data['sell_1_num']=sell_1_num
            data['最新价']=text['f43']/1000
            data['今开']=text['f46']/1000
            data['最高']=text['f44']/1000
            data['最低']=text['f45']/1000
            data['代码']=text['f57']
            data['名称']=text['f58']
            data['涨跌幅']=text['f169']/1000
            data['证券代码']=text['f262']
            data['股票名称']=text['f264']
            data['股票价格']=text['f267']/100
            data['股票涨跌幅']=text['f267']/100
            return data
        except Exception as e:
            print("运行错误:",e)
            url='https://push2.eastmoney.com/api/qt/stock/get?'
            data={}
            params={
                'invt': '2',
                'fltt': '1',
                #'cb': 'jQuery35106054114396324737_1690471800729',
                'fields': 'f58,f734,f107,f57,f43,f59,f169,f170,f152,f46,f60,f44,f45,f171,f47,f86,f292,f19,f39,f20,f40,f17,f531,f18,f15,f16,f13,f14,f11,f12,f37,f38,f35,f36,f33,f34,f31,f32,f48,f50,f161,f49,f191,f192,f71,f264,f263,f262,f267,f265,f268,f706,f700,f701,f703,f154,f704,f702,f705,f721,f51,f52,f301',
                'secid': '0.'+stock,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'wbp2u': '|0|0|0|web',
            }
            res=requests.get(url=url,params=params)
            text=res.text
            text=res.json()['data']
            buy_5_price=text['f11']/1000
            data['buy_5_price']=buy_5_price
            buy_5_num=text['f12']
            data['buy_5_num']=buy_5_num
            buy_4_price=text['f13']/1000
            data['buy_4_price']=buy_4_price
            buy_4_num=text['f14']
            data['buy_4_num']=buy_4_num
            buy_3_price=text['f15']/1000
            data['buy_3_price']=buy_3_price
            buy_3_num=text['f16']
            data['buy_3_num']=buy_3_num
            buy_2_price=text['f17']/1000
            data['buy_2_price']=buy_2_price
            buy_2_num=text['f18']
            data['buy_2_num']=buy_2_num
            buy_1_price=text['f19']/1000
            data['buy_1_price']=buy_1_price
            buy_1_num=text['f20']
            data['buy_1_num']=buy_1_num
            sell_5_price=text['f31']/1000
            data['sell_5_price']=sell_5_price
            sell_5_num=text['f32']
            data['sell_5_num']=sell_5_num
            sell_4_price=text['f33']/1000
            data['sell_4_price']=sell_4_price
            sell_4_num=text['f34']
            data['sell_4_num']=sell_4_num
            sell_3_price=text['f35']/1000
            data['sell_3_price']=sell_3_price
            sell_3_num=text['f36']
            data['sell_3_num']=sell_3_num
            sell_2_price=text['f37']/100
            data['sell_2_price']=sell_2_price
            sell_2_num=text['f38']
            data['sell_2_num']=sell_2_num
            sell_1_price=text['f39']/1000
            data['sell_1_price']=sell_1_price
            sell_1_num=text['f40']
            data['sell_1_num']=sell_1_num
            data['最新价']=text['f43']/1000
            data['今开']=text['f46']/1000
            data['最高']=text['f44']/1000
            data['最低']=text['f45']/1000
            data['代码']=text['f57']
            data['名称']=text['f58']
            data['涨跌幅']=text['f169']/1000
            data['证券代码']=text['f262']
            data['股票名称']=text['f264']
            data['股票价格']=text['f267']/100
            data['股票涨跌幅']=text['f267']/100
            return data
    
