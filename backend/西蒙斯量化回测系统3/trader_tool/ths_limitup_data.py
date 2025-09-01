import requests
import json
import pandas as pd
class ths_limitup_data:
    def __init__(self):
        '''
        涨停数据
        '''
    def get_var(self):
        '''
        获取js
        '''
        with open('ths.js') as f:
            comm=f.read()
        comms=execjs.compile(comm)
        result=comms.call('v')
        return result
    def get_headers(self):
        '''
        请求头
        '''
        headers={
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        }
        return headers
    def get_limit_up_pool(self,date='20230926'):
        '''
        涨停股票池
        '''
        url='https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool?'
        params={
            'page': '1',
            'limit': '200',
            'field': '199112,10,9001,330323,330324,330325,9002,330329,133971,133970,1968584,3475914,9003,9004',
            'filter': 'HS,GEM2STAR',
            'order_field': '330324',
            'order_type': '0',
            'date':f"{date}",
            '_': '1695632712332',
        }
        headers=self.get_headers()
        res=requests.get(url=url,params=params,headers=headers)
        text=res.text
        if len(str(text))<70:
            return False,''
        else:
            try:
                text=res.json()
                df=pd.DataFrame(text['data']['info'])
                
                df.columns=['开板次数','首次涨停时间','最后涨停时间','证券代码','涨停形态','封单量',
                            '_','最近一年封板率','流通市值','_','_','涨跌幅','换手率','涨停原因',
                            '封单额','几天几板','股票名称','_','_','_','最新价','time_preview']
                del df['_']
                df['封单额比流通市值']=(df['封单额']/df['流通市值'])*100
                def select_daily(x):
                    try:
                        if x=='首板':
                            return 1
                        else:
                            x=str(x).split('天')[0][-1]
                            return int(x)
                    except:
                        return 0
                def select_num(x):
                    try:
                        if x=='首板':
                            return 1
                        else:
                            x=str(x).split('板')[0][-1]
                            return int(x)
                    except:
                        return 0
                df['几天']=df['几天几板'].apply(select_daily)
                df['几板']=df['几天几板'].apply(select_num)
                return True,df
            except:
                return False,''
    def get_limit_up(self,date='20230925'):
        '''
        冲刺涨停
        '''
        url='https://data.10jqka.com.cn/dataapi/limit_up/limit_up?'
        params={
            'page': '1',
            'limit': '200',
            'field': '199112,10,48,1968584,19,3475914,9003,9004',
            'filter': 'HS,GEM2STAR',
            'order_field': '199112',
            'order_type': '0',
            'date':f"{date}" ,
            '_': '1695635862890',
        }
        
        res=requests.get(url=url,params=params)
        text=res.text
        if len(str(text))<70:
            return False,''
        else:
            try:
                text=res.json()
                df=pd.DataFrame(text['data']['info'])
                columns=['开板次数','首次涨停时间','最后涨停时间','证券代码','涨停形态','封单量',
                            '_','最近一年封板率','流通市值','_','_','涨跌幅','换手率','涨停原因',
                            '封单额','几天几板','股票名称','_','_','_','最新价','time_preview']
                #del df['_']
                return True,df
            except:
                return False,''
#continuous_limit_pool
    def get_continuous_limit_pool(self,date='20230925'):
        '''
        连扳池
        '''
        url='https://data.10jqka.com.cn/dataapi/limit_up/continuous_limit_pool?'
        params={
            'page': '1',
            'limit': '200',
            'field': '199112,10,330329,330325,133971,133970,1968584,3475914,3541450,9004',
            'filter': 'HS,GEM2STAR',
            'order_field': '330329',
            'order_type': '0',
            'date': f'{date}',
            '_': '1695696080744',
        }
        res=requests.get(url=url,params=params)
        text=res.text
        if len(str(text))<70:
            return False,''
        else:
            try:
                text=res.json()
                df=pd.DataFrame(text['data']['info'])
                columns=['开板次数','首次涨停时间','最后涨停时间','证券代码','涨停形态','封单量',
                            '_','最近一年封板率','流通市值','_','_','涨跌幅','换手率','涨停原因',
                            '封单额','几天几板','股票名称','_','_','_','最新价','time_preview']
                #del df['_']
                return True,df
            except:
                return False,''
#open_limit_pool?
    def get_open_limit_pool(self,date='20230925'):
            '''
            炸板池
            '''
            url='https://data.10jqka.com.cn/dataapi/limit_up/open_limit_pool?'
            params={
                'page': '1',
                'limit': '15',
                'field': '199112,9002,48,1968584,19,3475914,9003,10,9004',
                'filter': 'HS,GEM2STAR',
                'order_field': '199112',
                'order_type': '0',
                'date':f'{date}',
                '_': '1695696646721',
            }
            res=requests.get(url=url,params=params)
            text=res.text
            if len(str(text))<70:
                return False,''
            else:
                try:
                    text=res.json()
                    df=pd.DataFrame(text['data']['info'])
                    columns=['开板次数','首次涨停时间','最后涨停时间','证券代码','涨停形态','封单量',
                                '_','最近一年封板率','流通市值','_','_','涨跌幅','换手率','涨停原因',
                                '封单额','几天几板','股票名称','_','_','_','最新价','time_preview']
                    #del df['_']
                    return True,df
                except:
                    return False,''
#lower_limit_pool
    def get_lower_limit_pool(self,date='20230925'):
            '''
            跌停
            '''
            url='https://data.10jqka.com.cn/dataapi/limit_up/lower_limit_pool?'
            params={
                'page': '1',
                'limit': '15',
                'field': '199112,10,330333,330334,1968584,3475914,9004',
                'filter': 'HS,GEM2STAR',
                'order_field': '330334',
                'order_type': '0',
                'date': f'{date}',
                '_': '1695697116683',
            }
            res=requests.get(url=url,params=params)
            text=res.text
            if len(str(text))<70:
                return False,''
            else:
                try:
                    text=res.json()
                    df=pd.DataFrame(text['data']['info'])
                    columns=['开板次数','首次涨停时间','最后涨停时间','证券代码','涨停形态','封单量',
                                '_','最近一年封板率','流通市值','_','_','涨跌幅','换手率','涨停原因',
                                '封单额','几天几板','股票名称','_','_','_','最新价','time_preview']
                    #del df['_']
                    return True,df
                except:
                    return False,''
#block_top
    def get_block_top_pool(self,date='20230925'):
            '''
            最强口
            '''
            url='https://data.10jqka.com.cn/dataapi/limit_up/block_top?'
            params={
                'filter': 'HS,GEM2STAR',
                'date':f'{date}'
            }
            res=requests.get(url=url,params=params)
            text=res.text
            print(text)
            if len(str(text))<70:
                return False,''
            else:
                try:
                    text=res.json()
                    df=pd.DataFrame(text['data'])
                    columns=['开板次数','首次涨停时间','最后涨停时间','证券代码','涨停形态','封单量',
                                '_','最近一年封板率','流通市值','_','_','涨跌幅','换手率','涨停原因',
                                '封单额','几天几板','股票名称','_','_','_','最新价','time_preview']
                    #del df['_']
                    return True,df
                except:
                    return False,''
    def read_func_data(self,func="self.get_block_top_pool(date='20230925')"):
        '''
        读取函数数据
        '''
        text=func
        while True:
            stats,df=eval(text)
            if stats==True:
                df=df
                break
            else:
                print('获取不成功{}'.format(func))
        return df
    def get_analysis_block_top_pool(self,date='20230925'):
        '''
        解析最强口
        '''
        func="self.get_block_top_pool(date='{}')".format(date)
        df=self.read_func_data(func=func)
        data=pd.DataFrame()
        for code,name,change,limit_up_num ,continuous_plate_num ,high ,high_num ,\
        days,stock_list in zip(df['code'],df['name'],df['change'] ,df['limit_up_num'], df['continuous_plate_num'],
                                df['high'] ,df['high_num'],df['days'],df['stock_list']):
            df1=pd.DataFrame(stock_list)
            df1['行业代码']=code
            df1['name']=name
            df1['change']=change
            df1['limit_up_num']=limit_up_num
            df1['continuous_plate_num']=continuous_plate_num
            df1['high']=high
            df1['high_num']=high_num
            df1['days']=days
            data=pd.concat([data,df1],ignore_index=True)
        data.to_excel(r'数据.xlsx')
        return data
    def get_stock_continuous_limit_up(self,date='20231124'):
        '''
        获取连扳天梯
        '''
        params={
            'filter': 'HS,GEM2STAR',
            'date':date,
        }
        url='https://data.10jqka.com.cn/dataapi/limit_up/continuous_limit_up?'
        res=requests.get(url=url,params=params)
        text=res.text
        data=pd.DataFrame()        
        if len(str(text))<70:
            return False,''
        else:
            try:
                text=res.json()
                df=pd.DataFrame(text['data'])
                for height,code_list in zip(df['height'],df['code_list']):
                    df1=pd.DataFrame(code_list)
                    data=pd.concat([data,df1],ignore_index=True)
                data['continue_num']=data['continue_num'].apply(lambda x:str(x)+'板')
                data['日期']=date
                data.columns=['证券代码','股票简称','market_id','连扳','日期']
                try:
                    del data['market_id']
                except:
                    pass
                return True,data
            except:
                return False,''
if __name__=='__main__':
    models=ths_limitup_data()
    df=models.read_func_data(func="models.get_limit_up_pool(date='20240117')")
    print(df)

        