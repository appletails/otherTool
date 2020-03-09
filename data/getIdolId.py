# -*- coding: utf-8 -*-
import json
import requests
import urllib3
import codecs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
def openJson(path):
    fb = open(path+'.json', 'rb')
    data = json.load(fb)
    fb.close()
    return data

token = openJson('init')['token'] # 自行获取token
def getKoudai(roomId):
    url = "https://pocketapi.48.cn/im/api/v1/chatroom/msg/list/homeowner"
    form = {
        'ownerId': roomId,
        'roomId': roomId
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
        'token': token
    }
    data = requests.post(
        url,
        data=json.dumps(form),
        headers=header,
        verify=False,
        timeout=5).json()
    return json.loads(data['content']['message'][0]['extInfo'])['user']

rooms = openJson('rooms')
for item in rooms:
    if item['id'] == 0:
        user = getKoudai(item['roomId'])
        item['id'] = user['userId']
        item['name'] = item['name'] if item['name'] else user['nickName']

# 保存
fb = codecs.open('rooms.json', 'w', 'utf-8')
fb.write(json.dumps(rooms, indent=4, ensure_ascii=False))
fb.close()
