# -*- coding: utf-8 -*-
import json
import time
import requests
import urllib3
import codecs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def writeJson(data,path):
    # 保存
    fb = codecs.open(path+'.json', 'w', 'utf-8')
    fb.write(json.dumps(data, indent=4, ensure_ascii=False))
    fb.close()

def getKoudai(nextTime=0):
    url = "https://pocketapi.48.cn/im/api/v1/chatroom/msg/list/homeowner"
    form = {
        'ownerId': 67293973,
        'roomId': 67293973,
        "nextTime": nextTime
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
        'token': "y0gXSNbw3cCJe21iIloJVtZtovUrhoNjDIzg3hWIXnd8WEhEsuhmGDAM8p2piwSYnEi7NDmdX+0="
    }
    return requests.post(
        url,
        data=json.dumps(form),
        headers=header,
        verify=False,
        timeout=5).json()

# 将日期转换为时间戳
def timeStamp(dt):
    timeStamp = time.mktime(time.strptime(dt, "%Y-%m-%d %H:%M:%S"))
    return timeStamp

# 将时间轴转换时间格式(2016-05-05 20:28:54)
def timeDate(dt):
    timeDate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(dt/1000))
    return timeDate

# 判断特定键的dict是否存在于list
def hasKey(lists,key,value):
    for i,item in enumerate(lists):
        if item[key] == value:
            return i
    return -1

# 计算距离凌晨5点的时间 times 2019-02-02 05:59:12,2019-02-04 05:12:12,2019-02-05 06:00:00,2019-02-03 06:12:12
def monAndNin(times):
    # times=[
    #     {"msgTime":1559789575345},
    #     {"msgTime":104400000},
    #     {"msgTime":1559857854499},
    #     {"msgTime":1559857864134},
    #     {"msgTime":1559857866293},
    #     {"msgTime":79200000},
    #     {"msgTime":86555555},
    #     {"msgTime":1559685054000}
    # ]
    positive = []
    negative = []
    for item in times:
        item["ttt"] = item["msgTime"]%86400000
        if item["ttt"]>=25200000  and item["ttt"]<75600000:
            negative.append(item)
        else:
            if item["ttt"] >= 75600000:
                item["ttt"] -= 75600000
            else:
                item["ttt"] += 10800000

            positive.append(item)
    zao = sorted(positive, key=lambda item: abs(item["ttt"]))[0] if len(positive) else {"msgTime":0}
    wan = sorted(negative, key=lambda item: item["ttt"],reverse=True)[0]
    # for item in zao:
    #     print(timeDate(item["msgTime"]),item["ttt"])
    # print("--------------------")
    # for item in wan:
    #     print(timeDate(item["msgTime"]))
    # return
    return [{
        "time":zao["msgTime"],
        "dataTime":timeDate(zao["msgTime"]).split(" ")
    },{
        "time":wan["msgTime"],
        "dataTime":timeDate(wan["msgTime"]).split(" ")
    }]
# monAndNin(0)
# main
def week(needData = ["2019-07-22","2019-07-28"]):
    start = int(timeStamp("%s 23:59:59" % needData[1])*1000)
    end = int(timeStamp("%s 00:00:00" % needData[0])*1000)
    datas = []
    while True:
        response = getKoudai(start)["content"]
        if response["nextTime"] > end:
            datas += response["message"]
            start = response["nextTime"]
        else:
            for item in response["message"]:
                if item["msgTime"] > end:
                    datas.append(item)
            break
        time.sleep(1)

    # 保存
    
    # for data in datas:
    #         # 文字消息
    #     data['extInfo'] = json.loads(data['extInfo'])
    # writeJson(datas,'alldata')
    # 请求结束，开始配置数据结构   
    weekData = {
        "ALL":{
            "TEXT": 0,
            "LIVEPUSH": 0,
            "FLIPCARD": 0,
            "IMAGE":0,
            "AUDIO": 0,
            "VIDEO": 0,
            "EXPRESS": 0,
            "OTHER": 0,
            "REPLY": 0,
            "ALLNUMBER":0
        },
        "REPLY": {},
        "IMAGE": [],
        "DAY":{},
        "MAN":[],
        "NEEDDATA":[]
    }
    # 传入日期
    weekData["NEEDDATA"] = needData
    # 所有的留言数
    weekData["ALL"]["ALLNUMBER"] = len(datas)
    # 暂存的所有留言list
    allInfo = []
    # 暂存的所有翻牌
    reply = []
    # 分类计算
    for data in datas:
            # 文字消息
        extInfo = json.loads(data['extInfo'])
        if data['msgType'] == 'TEXT':
            if extInfo['messageType'] == 'TEXT':
                weekData["ALL"]["TEXT"] += 1
                
            elif extInfo['messageType'] == 'REPLY':
                weekData["ALL"]["REPLY"] += 1
                # 计算翻牌最多的一天
                ind = hasKey(reply,"replyName",extInfo['replyName'])
                if ind>=0:
                    reply[ind]["num"] += 1
                else:
                    reply.append({
                        "replyName":extInfo['replyName'],
                        "num":1
                    })

            elif extInfo['messageType'] == 'LIVEPUSH':
                weekData["ALL"]["LIVEPUSH"] += 1

            elif extInfo['messageType'] == 'FLIPCARD':
                weekData["ALL"]["FLIPCARD"] += 1
            else:
                weekData["ALL"]["OTHER"] += 1
        # image
        elif data['msgType'] == 'IMAGE':
            weekData["ALL"]["IMAGE"] += 1
            bodys = json.loads(data['bodys'])
            msg = {
                "url":bodys['url']
            }
            weekData["IMAGE"].append(msg)

        # voice
        elif data['msgType'] == 'AUDIO':
            weekData["ALL"]["AUDIO"] += 1

        elif data['msgType'] == 'VIDEO':
            weekData["ALL"]["VIDEO"] += 1

        elif data['msgType'] == 'EXPRESS':
            weekData["ALL"]["EXPRESS"] += 1
        else:
            weekData["ALL"]["OTHER"] += 1
        # 计算发消息最多的一天
        day = timeDate(data['msgTime']).split(" ")[0]
        Key = hasKey(allInfo,"day",str(day))
        if Key>=0:
            allInfo[Key]["num"] += 1
        else:
            allInfo.append({
                "day":str(day),
                "num":1
            })

    # 计算发消息最早和最晚的一天
    weekData["MAN"] = monAndNin(datas)
    # 取发言最多的一天
    weekData["DAY"] = sorted(allInfo, key=lambda item: item["num"], reverse=True)[0]
    # 取翻牌最多的一位聚聚
    if len(reply):
        weekData["REPLY"] = sorted(reply, key=lambda item: item["num"], reverse=True)[0]
    else:
        weekData["REPLY"] = {
            "replyName":False,
            "num":0
        }
    weekData["REPLY"]["user"] = len(reply)
    # 默认图片
    images = [{"url":"http://www.crean.top/img/occupy.png"},{"url":"http://www.crean.top/img/occupy.png"},{"url":"http://www.crean.top/img/occupy.png"},{"url":"http://www.crean.top/img/occupy.png"},{"url":"http://www.crean.top/img/occupy.png"},{"url":"http://www.crean.top/img/occupy.png"}]
    weekData["IMAGE"] = (weekData["IMAGE"]+images)[0:6]
    # 保存
    writeJson(weekData,'data')

week()


