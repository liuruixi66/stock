from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
# 已删除 xms_quants_data_client，改用其他数据源
import pandas as pd
import json

# 模拟数据客户端类
class MockDataClient:
    def __init__(self, url=None, port=None, password=None):
        self.url = url
        self.port = port
        
    def stock_zh_a_spot_em(self):
        # 返回模拟股票数据
        return pd.DataFrame({
            '代码': ['000001', '000002', '600031', '600036', '000063'],
            '名称': ['平安银行', '万科A', '三一重工', '招商银行', '中兴通讯'],
            '最新价': [10.5, 15.2, 20.8, 45.6, 28.3],
            '涨跌幅': [2.5, -1.2, 3.1, -0.8, 1.9],
            '成交量': [1000000, 800000, 1200000, 600000, 900000],
            '成交额': [10500000, 12160000, 24960000, 27360000, 25470000]
        })
        
    def data_to_pandas(self, data):
        # 直接返回DataFrame，因为已经是pandas格式
        return data

# 初始化模拟数据客户端
client = MockDataClient(
    url='http://124.220.32.224',
    port='8080',
    password='test'
)

@require_http_methods(["GET"])
def get_stock_data(request):
    try:
        # 获取股票数据
        data = client.stock_zh_a_spot_em()
        
        if data is None:
            return JsonResponse({
                'status': 'error',
                'message': '获取数据失败'
            })
            
        # 转换为pandas DataFrame
        df = client.data_to_pandas(data)
        
        if df.empty:
            return JsonResponse({
                'status': 'error',
                'message': '数据为空'
            })
            
        # 选择需要的列
        required_columns = ['代码', '名称', '最新价', '涨跌幅', '成交量', '成交额']
        df = df[required_columns]
        
        # 重命名列以匹配前端
        column_mapping = {
            '代码': 'code',
            '名称': 'name',
            '最新价': 'price',
            '涨跌幅': 'change_percent',
            '成交量': 'volume',
            '成交额': 'amount'
        }
        df = df.rename(columns=column_mapping)
            
        # 转换为字典列表
        stock_list = df.to_dict('records')
        
        return JsonResponse({
            'status': 'success',
            'data': stock_list
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }) 