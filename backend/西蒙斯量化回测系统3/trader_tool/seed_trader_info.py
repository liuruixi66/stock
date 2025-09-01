import time
import pyautogui as pa
import pywinauto as pw
import schedule
import yagmail
import requests
import json
import random
from datetime import datetime
class seed_trader_info:
    '''
    qmt自动登录
    '''
    def __init__(self,
                seed_type='qq',
                seed_qq='1752515969@qq.com',
                qq_paasword='jgyhavzupyglecaf',
                re_qq='1029762153@qq.com',
                dd_token_list=[''],
                wx_token_list=['22222']):
        '''
       
        password密码
        seed_type发送方式 wx微信,qq qq,dd钉钉
        seed_qq发送qq
        qq_paasword QQ掩码
        re_qq接受qq
        dd_token_list钉钉机器人token
        wx_token_list 企业微信token

        '''
        self.seed_type=seed_type
        self.seed_qq=seed_qq
        self.qq_paasword=qq_paasword
        self.re_qq=re_qq
        self.dd_token_list=dd_token_list
        self.wx_token_list=wx_token_list
    def seed_dingding(self,msg='买卖交易成功,'):
        '''
        发送钉钉
        '''
        access_token=random.choice(self.dd_token_list)
        url='https://oapi.dingtalk.com/robot/send?access_token={}'.format(access_token)
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        data = {
            "msgtype": "text",  # 发送消息类型为文本
            "at": {
                #"atMobiles": reminders,
                "isAtAll": False,  # 不@所有人
            },
            "text": {
                "content": msg,  # 消息正文
            }
        }
        r = requests.post(url, data=json.dumps(data), headers=headers)
        text=r.json()
        errmsg=text['errmsg']
        if errmsg=='ok':
                print('钉钉发生成功')
                return text
        else:
            print(text)
            return text
    def get_seed_qq_test(self,msg='交易完成',):
        '''
        发送qq，可以自己给自己发
        text发送内容，支持表格文字
        see_qq发送QQ
        qq_pasword发送qq的掩码
        re_qq接收信息QQ
        '''
        try:
            yag = yagmail.SMTP(user=self.seed_qq, password=self.qq_paasword, host='smtp.qq.com')
            text = msg
            yag.send(to=self.re_qq, contents=text, subject='邮件')
            print('qq发送完成')
        except Exception as e:
            print(e,'qq发送失败')
    def seed_wechat(self, msg='买卖交易成功,'):
        '''
        发送企业微信
        '''
        access_token=random.choice(self.wx_token_list)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=' + access_token
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        data = {
            "msgtype": "text",  # 发送消息类型为文本
            "at": {
                # "atMobiles": reminders,
                "isAtAll": False,  # 不@所有人
            },
            "text": {
                "content": msg,  # 消息正文
            }
        }
        r = requests.post(url, data=json.dumps(data), headers=headers)
        text = r.json()
        errmsg = text['errmsg']
        if errmsg == 'ok':
            print('wechat发生成功')
            return text
        else:
            print(text)
            return text
    def seed_trader_info(self,msg=''):
        '''
        发送信息
        '''
        if self.seed_type=='qq':
            self.get_seed_qq_test(msg=msg)
        elif self.seed_type=='wx':
            self.seed_wechat(msg=msg)
        elif self.seed_type=='dd':
            self.seed_dingding(msg=msg)
        else:
            self.get_seed_qq_test(msg=msg)
if __name__=='__main__':
    '''
    "发送qq":"10297621536@qq.com",
    "qq掩码":"zhtndabqkzlubegb",
    "接收qq":"10297621536@qq.com",
    '''

    models=seed_trader_info(seed_type='qq',
                seed_qq='10297621536@qq.com',
                qq_paasword='zrhpygftnohbbfch',
                re_qq='10297621536@qq.com',
                dd_token_list=[''],
                wx_token_list=['22222'])
    models.seed_trader_info()