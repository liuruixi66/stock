import pandas as pd
class position_log:
    def __init__(self):
        '''
        获取每天持股记录
        '''
        self.position_log=pd.DataFrame()
    def get_position_log_data(self):
        '''
        获取持股记录数据
        '''
        self.position_log=self.position_log.drop_duplicates(subset=['时间','证券代码'],keep='last')
        return self.position_log
    def add_position_log_data(self,log):
        '''
        添加持股记录
        '''
        self.position_log=pd.concat([self.position_log,log])
        self.position_log=self.position_log.drop_duplicates(subset=['时间','证券代码'],keep='last')
        return self.position_log
    
