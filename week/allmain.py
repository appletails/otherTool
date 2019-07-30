# -*- coding: utf-8 -*-
import json
import time
import requests
import urllib3
import codecs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
idoluserid =610042
idolid =67293973
def writeJson(data, path):
    # 保存
    fb = codecs.open('dataview/'+path+'.json', 'w', 'utf-8')
    fb.write(json.dumps(data, indent=4, ensure_ascii=False))
    fb.close()

def openjson(path):
	fb = open(path+'.json','rb')
	data = json.load(fb)  
	fb.close()
	return data

def getKoudai(nextTime=0):
    # idolid = 67313912
    url = "https://pocketapi.48.cn/im/api/v1/chatroom/msg/list/all"
    form = {
        'ownerId': idolid,
        'roomId': idolid,
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
        timeout=10).json()

# 将日期转换为时间戳


def timeStamp(dt):
    timeStamp = time.mktime(time.strptime(dt, "%Y-%m-%d %H:%M:%S"))
    return timeStamp

# 将时间轴转换时间格式(2016-05-05 20:28:54)


def timeDate(dt):
    timeDate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(dt/1000))
    return timeDate

# 判断特定键的dict是否存在于list


def hasKey(lists, key, value):
    for i, item in enumerate(lists):
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
        item["ttt"] = item["msgTime"] % 86400000
        if item["ttt"] >= 25200000 and item["ttt"] < 75600000:
            negative.append(item)
        else:
            if item["ttt"] >= 75600000:
                item["ttt"] -= 75600000
            else:
                item["ttt"] += 10800000

            positive.append(item)
    zao = sorted(positive, key=lambda item: abs(item["ttt"]))[
        0] if len(positive) else {"msgTime": 0}
    wan = sorted(negative, key=lambda item: item["ttt"], reverse=True)[0]
    # for item in zao:
    #     print(timeDate(item["msgTime"]),item["ttt"])
    # print("--------------------")
    # for item in wan:
    #     print(timeDate(item["msgTime"]))
    # return
    return [{
        "time": zao["msgTime"],
        "dataTime":timeDate(zao["msgTime"]).split(" ")
    }, {
        "time": wan["msgTime"],
        "dataTime":timeDate(wan["msgTime"]).split(" ")
    }]
# monAndNin(0)
# main


def week(needData=["2019-06-01", "2019-07-14"]):
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
    writeJson(datas,'msginfo')
    # datas = openjson('lh/msginfo')
    # 请求结束，开始配置数据结构
    weekData = {
        "msg": [
            {
                "name": "文字消息",
                "type": "TEXT",
                "value": 0
            },
            {
                "name": "直播/电台",
                "type": "LIVEPUSH",
                "value": 0
            },
            {
                "name": "偶像/匿名 翻牌",
                "type": "FLIPCARD",
                "value": 0
            },
            {
                "name": "图片",
                "type": "IMAGE",
                "value": 0
            },
            {
                "name": "语音",
                "type": "AUDIO",
                "value": 0
            },
            {
                "name": "视频",
                "type": "VIDEO",
                "value": 0
            },
            {
                "name": "普通翻牌",
                "type": "REPLY",
                "value": 0
            },
            {
                "name": "其他消息",
                "type": "OTHER",
                "value": 0
            }
        ],
        "allNumber": 0,
        "man": []
    }
    # 每天留数量的list
    allInfo = []
    # 所有翻牌
    reply = []
    # 所有图片
    images = []
    # 投票
    gift = []
    # 所有的人的id
    idlist = []
    # 分类计算
    for data in datas:
        # idoluserid = 608997
            # 文字消息
        extInfo = json.loads(data['extInfo'])
        if extInfo['user']['userId'] != idoluserid:
            # 计算翻牌最多的一天
            idInd = hasKey(idlist, "user_id", extInfo['user']['userId'])
            if idInd >= 0:
                idlist[idInd]["value"] += 1
            else:
                idlist.append({
                    "user_id": extInfo['user']['userId'],
                    "name":extInfo['user']['nickName'],
                    "value": 1
                })

        if extInfo['user']['userId'] == idoluserid:
            if data['msgType'] == 'TEXT':
                if extInfo['messageType'] == 'TEXT':
                    text = list(filter(lambda item: item["type"] == "TEXT", weekData['msg']))
                    text[0]['value'] += 1

                elif extInfo['messageType'] == 'REPLY':
                    replys = list(filter(lambda item: item["type"] == "REPLY", weekData['msg']))
                    replys[0]['value'] += 1
                    # 计算翻牌最多的一天
                    ind = hasKey(reply, "name", extInfo['replyName'])
                    if ind >= 0:
                        reply[ind]["value"] += 1
                    else:
                        reply.append({
                            "name": extInfo['replyName'],
                            "value": 1
                        })

                elif extInfo['messageType'] == 'LIVEPUSH':
                    live = list(filter(lambda item: item["type"] == "LIVEPUSH", weekData['msg']))
                    live[0]['value'] += 1

                elif extInfo['messageType'] == 'FLIPCARD':
                    flip = list(filter(lambda item: item["type"] == "FLIPCARD", weekData['msg']))
                    flip[0]['value'] += 1

                else:
                    other1 = list(filter(lambda item: item["type"] == "OTHER", weekData['msg']))
                    other1[0]['value'] += 1
            # image
            elif data['msgType'] == 'IMAGE':
                img = list(filter(lambda item: item["type"] == "IMAGE", weekData['msg']))
                img[0]['value'] += 1
                bodys = json.loads(data['bodys'])
                msg = {
                    "url": bodys['url']
                }
                images.append(msg)

            # voice
            elif data['msgType'] == 'AUDIO':
                audio = list(filter(lambda item: item["type"] == "AUDIO", weekData['msg']))
                audio[0]['value'] += 1

            elif data['msgType'] == 'VIDEO':
                video = list(filter(lambda item: item["type"] == "VIDEO", weekData['msg']))
                video[0]['value'] += 1

            else:
                other2 = list(filter(lambda item: item["type"] == "OTHER", weekData['msg']))
                other2[0]['value'] += 1
            # 计算发消息最多的一天
            day = timeDate(data['msgTime']).split(" ")[0]
            Key = hasKey(allInfo, "name", str(day))
            if Key >= 0:
                allInfo[Key]["value"] += 1
            else:
                allInfo.append({
                    "name": str(day),
                    "msgTime": data['msgTime'],
                    "value": 1
                })

        # 投票信息
        elif 'giftInfo' in extInfo and 'isVote' in extInfo['giftInfo'] and extInfo['giftInfo']['isVote']:
            gitUser = list(
                filter(lambda item: item["name"] == extInfo['user']['nickName'], gift))
            if len(gitUser):
                gitUser[0]['value'] += extInfo['giftInfo']['giftNum']
            else:
                gift.append({
                    "name": extInfo['user']['nickName'],
                    "value": extInfo['giftInfo']['giftNum']
                })

    # 图片合集
    writeJson(images, 'image')
    # 排序投票排行
    gift = sorted(gift, key=lambda item: item["value"], reverse=True)
    writeJson(gift, 'gift')
    # 取发言最多的一天
    allInfo = sorted(allInfo, key=lambda item: item["msgTime"])
    writeJson(allInfo, 'day')
    # 取翻牌最多的一位聚聚
    reply = sorted(reply, key=lambda item: item["value"], reverse=True)
    writeJson(reply, 'reply')
    # 消息排序
    weekData["msg"] = sorted(weekData["msg"], key=lambda item: item["value"], reverse=True)
    # 计算发消息最早和最晚的一天
    weekData["man"] = monAndNin(datas)
    # 所有的留言数
    weekData["allNumber"] = len(datas)
    # 所有留言的人数
    weekData["idlist"] = len(idlist)
    # 排序留言
    idlist = sorted(idlist, key=lambda item: item["value"], reverse=True)[0:16]
    writeJson(idlist, 'idlist')
    
    writeJson(weekData,'weekData')

week()


