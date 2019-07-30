# -*- coding: utf-8 -*-
import random
import configparser
import os
import requests
import json
import codecs
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def GetSetting():
    fb = open('setting.json','rb')
    data = json.load(fb)
    fb.close()
    return data

# ----------------------口袋48设置----------------------
# 获取监听列表
def IdolList():
    data = GetSetting()
    return data['room']

# 口袋48:roomId
def roomId(i):
    data = GetSetting()
    roomId = data['room'][i]['roomId']
    ownerId = data['room'][i]['ownerId']
    return int(roomId), int(ownerId)


# 获取配置中存储的口袋房间消息时间
def read_kdmsg_time13(i):
    data = GetSetting()
    return int(data['room'][i]['msgTime'])


# 写入配置中存储的口袋房间消息时间
def write_kdmsg_time13(msgtime13,i):
    data = GetSetting()
    data['room'][i]['msgTime'] = msgtime13
    fb = codecs.open('setting.json','w', 'utf-8')  
    fb.write(json.dumps(data,indent=4,ensure_ascii=False))  
    fb.close()

# 获取配置中存储的token
def token():
    data = GetSetting()
    return str(data['token'])


# 验证token
def token_verify():
    url = 'https://pocketapi.48.cn/im/api/v1/chatroom/msg/list/homeowner'
    form = {
        'ownerId': 63558,
        'roomId': 67313743
    }
    header = {
        'Host': 'pocketapi.48.cn',
        'accept': '*/*',
        'Accept-Language': 'zh-Hans-CN;q=1',
        'User-Agent': 'PocketFans201807/6.0.0 (iPhone; iOS 12.2; Scale/2.00)',
        'Accept-Encoding': 'gzip, deflate',
        'appInfo': '{"vendor":"apple","deviceId":"0","appVersion":"6.0.0","appBuild":"190409","osVersion":"12.2.0","osType":"ios","deviceName":"iphone","os":"ios"}',
        'Content-Type': 'application/json;charset=utf-8',
        'Connection': 'keep-alive',
        'token': token()
    }
    response = requests.post(
            url,
            data=json.dumps(form),
            headers=header,
            verify=False,
            timeout=15).json()
    if response['status'] == 200:
        return True
    else:
        return False


# 获取新token
def getNewToken():
    ajax_url = "https://pocketapi.48.cn/user/api/v1/login/app/mobile"
    header = {
        'Host': 'pocketapi.48.cn',
        'accept': '*/*',
        'Accept-Language': 'zh-Hans-CN;q=1',
        'User-Agent': 'PocketFans201807/6.0.0 (iPhone; iOS 12.2; Scale/2.00)',
        'Accept-Encoding': 'gzip, deflate',
        'appInfo': '{"vendor":"apple","deviceId":"0","appVersion":"6.0.0","appBuild":"190409","osVersion":"12.2.0","osType":"ios","deviceName":"iphone","os":"ios"}',
        'Content-Type': 'application/json;charset=utf-8',
        'Connection': 'keep-alive'
    }
    data = GetSetting()
    form = {
        "mobile": data['user'],
        "pwd": data['password']
    }
    response = requests.post(
        ajax_url,
        data=json.dumps(form),
        headers=header,
        verify=False
    ).json()
    if response['status'] == 200:
        data['token'] = response['content']['token']
        fb = codecs.open('setting.json','w', 'utf-8')  
        fb.write(json.dumps(data,indent=4,ensure_ascii=False))  
        fb.close()
        return 'success'
    else:
        return response['message']


# 口袋48房间查询时间间隔读取
def kd_interval():
    data = GetSetting()
    return int(data['interval'])

# --------------------------------------------------------

# ----------------------qq群设置----------------------

# qq群id
def groupid(i):
    data = GetSetting()
    group = data['room'][i]['group']
    if group:
        return group
    else:
        return data['group']

