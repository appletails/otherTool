# -*- coding: utf-8 -*-
import json
import time
import requests
import urllib3
import codecs
import os
import datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def writeJson(data, path):
    # 保存
    fb = codecs.open(path+'.json', 'w', 'utf-8')
    fb.write(json.dumps(data, indent=4, ensure_ascii=False))
    fb.close()


def openJson(path):
    fb = open(path+'.json', 'rb')
    data = json.load(fb)
    fb.close()
    return data


def getKoudai(nextTime, roomId):
    # idolid = 67313912
    url = "https://pocketapi.48.cn/im/api/v1/chatroom/msg/list/all"
    form = {
        'ownerId': roomId,
        'roomId': roomId,
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
        'token': "BmuSzTmYX252UDv+agR0oPLqo/I8Yo5ep7waZT8WJsdswee72doI52IuI37XLDJl0svPKRGjkto="
    }
    return requests.post(
        url,
        data=json.dumps(form),
        headers=header,
        verify=False,
        timeout=10).json()
# 直播转换
def getLiveTime(livedata):
    extInfo = json.loads(livedata['extInfo'])
    liveId = extInfo['liveId']
    live = {
        "sumTime": 0,
        "langTime": '',
        "startTime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(livedata['msgTime']/1000)),
        "endTime": '',
        "title": extInfo['liveTitle'],
        "liveId": liveId
    }
    # 获取path
    data = requests.post(
        'https://pocketapi.48.cn/live/api/v1/live/getLiveOne',
        data=json.dumps({"liveId":liveId}),
        headers={'Content-Type': 'application/json;charset=utf-8'}
    ).json()
    if data['status'] == 200:
        path = data['content']['playStreamPath']
        all_content = requests.get(path).text  # 获取第一层M3U8文件内容
        times = []
        if "#EXTM3U" in all_content:
            file_line = all_content.split("\n")
            for line in file_line:
                if '#EXTINF:' in line:
                    stime = float(line.replace('#EXTINF:','').replace(',',''))
                    times.append(stime)
        sumTime = sum(times)
    else:
        sumTime = 0
    langTimeStr = datetime.timedelta(seconds = sumTime)
    live['sumTime'] = sumTime
    live['endTime'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(livedata['msgTime']/1000 + sumTime))
    live['langTime'] = str(langTimeStr)
    return live

# 将日期转换为时间戳
def timeStamp(dt):
    timeStamp = time.mktime(time.strptime(dt, "%Y/%m/%d %H:%M:%S"))
    return timeStamp

# 将时间轴转换时间格式(2016/05/05 20:28:54)
def timeDate(dt):
    timeDate = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(dt/1000))
    return timeDate

# 判断特定键的dict是否存在于list
def hasKey(lists, key, value):
    for i, item in enumerate(lists):
        if item[key] == value:
            return i
    return -1

# 计算距离凌晨5点的时间
def monAndNin(times):
    dateTime = [timeDate(item['msgTime']) for item in times]
    zao = list(filter(lambda item: int(''.join(item.split(' ')[1].split(':'))) >= 50000, dateTime))
    wan = list(filter(lambda item: int(''.join(item.split(' ')[1].split(':'))) < 50000, dateTime))
    timeSort = sorted(zao, key=lambda item: int(''.join(item.split(' ')[1].split(':')))) + sorted(wan, key=lambda item: int(''.join(item.split(' ')[1].split(':'))))
    return [{
        "time": timeStamp(timeSort[0]),
        "dataTime": timeSort[0].split(" ")
    },{
        "time": timeStamp(timeSort[-1]),
        "dataTime": timeSort[-1].split(" ")
    }]

def week(needData=["2019-08-01", "2019-08-31"], idol="唐霖"):
    rooms = list(filter(lambda item: item['name'] == idol, openJson('rooms')))
    roomId = rooms[0]['roomId']
    idolId = rooms[0]['id']
    start = int(timeStamp("%s 23:59:59" % needData[1])*1000)
    end = int(timeStamp("%s 00:00:00" % needData[0])*1000)
    datas = []
    while True:
        response = getKoudai(start, roomId)["content"]
        if response["nextTime"] > end:
            datas += response["message"]
            start = response["nextTime"]
        else:
            for item in response["message"]:
                if item["msgTime"] > end:
                    datas.append(item)
            break
        time.sleep(1)
    # 请求结束，开始配置数据结构
    weekData = {
        "idol": [
            { "name": "文字消息", "type": "TEXT", "value": 0 },
            { "name": "直播/电台", "type": "LIVEPUSH", "value": 0 },
            { "name": "图片消息", "type": "IMAGE", "value": 0 },
            { "name": "语音/视频", "type": "AUDIO", "value": 0 },
            { "name": "翻牌消息", "type": "REPLY", "value": 0 },
            { "name": "营业天数", "type": "DAY", "value": 0 }
        ],
        "fans": [
            { "name": "粉丝留言", "type": "FANSSAY", "value": 0 },
            { "name": "粉丝数", "type": "FANSNUM", "value": 0 }
        ],
        "imgs": [],
        'reply': {'max': 0, 'value': 0},
        'day': {},
        'MAN': [],
        "NEEDDATA": [],
        "liveSumTime": '',
        "previous": {}
    }
    # 传入日期
    weekData["NEEDDATA"] = needData
    idList = []
    # 成员留言日期
    allDate = []
    # 暂存的所有偶像留言list
    allInfo = []
    # 成员的留言时间
    allTimes = []
    # 直播列表
    liveList = []
    # 翻牌
    replyList = {}
    # 分类计算
    for data in datas:
        # idoluserid = 608997
            # 文字消息
        extInfo = json.loads(data['extInfo'])
        # if '小尾巴' in data['extInfo']:
        #     print(extInfo)
        if extInfo['user']['userId'] == idolId:
            if data['msgType'] == 'TEXT':
                if extInfo['messageType'] == 'TEXT':
                    text = list(
                        filter(lambda item: item["type"] == "TEXT", weekData["idol"]))
                    text[0]['value'] += 1

                elif extInfo['messageType'] == 'REPLY':
                    replys = list(
                        filter(lambda item: item["type"] == "REPLY", weekData["idol"]))
                    replys[0]['value'] += 1
                    if extInfo['replyName'] in replyList:
                        replyList[extInfo['replyName']] += 1
                    else:
                        replyList[extInfo['replyName']] = 1
                elif extInfo['messageType'] == 'LIVEPUSH':
                    live = list(
                        filter(lambda item: item["type"] == "LIVEPUSH", weekData["idol"]))
                    live[0]['value'] += 1
                    liveList.append(getLiveTime(data))

                else:
                    # print(extInfo)
                    pass
                    # other1 = list(
                    #     filter(lambda item: item["type"] == "OTHER", weekData["idol"]))
                    # other1[0]['value'] += 1
            # image
            elif data['msgType'] == 'IMAGE':
                img = list(
                    filter(lambda item: item["type"] == "IMAGE", weekData["idol"]))
                img[0]['value'] += 1
                bodys = json.loads(data['bodys'])
                msg = {
                    "url":bodys['url']
                }
                weekData["imgs"].append(msg)

            # voice
            elif data['msgType'] == 'AUDIO' or data['msgType'] == 'VIDEO':
                audio = list(
                    filter(lambda item: item["type"] == "AUDIO", weekData["idol"]))
                audio[0]['value'] += 1
            # 计算消息最多的一天 
            day = timeDate(data['msgTime']).split(" ")[0]
            Key = hasKey(allInfo,"day",str(day))
            if Key>=0:
                allInfo[Key]["num"] += 1
            else:
                allInfo.append({
                    "day":str(day),
                    "num":1
                })
            allTimes.append({"msgTime": data['msgTime']})
        else:
            if extInfo['user']['userId'] not in idList:
                idList.append(extInfo['user']['userId'])
            fanssay = list(
                filter(lambda item: item["type"] == "FANSSAY", weekData["fans"]))
            fanssay[0]['value'] += 1

        date = timeDate(data['msgTime']).split(" ")[0]
        if date not in allDate:
            allDate.append(date)
    fansnum = list(
        filter(lambda item: item["type"] == "FANSNUM", weekData["fans"]))
    fansnum[0]['value'] = len(idList)
    weekData['idol'][-1]['value'] = len(allDate)
    # 默认图片
    images = [{"url":"http://www.crean.top/img/occupy.png"},{"url":"http://www.crean.top/img/occupy.png"},{"url":"http://www.crean.top/img/occupy.png"},{"url":"http://www.crean.top/img/occupy.png"},{"url":"http://www.crean.top/img/occupy.png"},{"url":"http://www.crean.top/img/occupy.png"}]
    weekData["imgs"] = (weekData["imgs"]+images)[0:6]
    # 序列化reply
    allReply = [(item, replyList[item]) for item in replyList]
    weekData['reply']['max'] = sorted(allReply, key=lambda item: item[1], reverse= True)[0] if len(allReply) > 0 else None
    weekData['reply']['value'] = sum([item[1] for item in allReply])
    weekData['reply']['user'] = len(allReply)
    # 取发言最多的一天
    weekData["day"] = sorted(allInfo, key=lambda item: item["num"], reverse=True)[0] if len(allInfo) > 0 else None
    # 计算发消息最早和最晚的一天
    weekData["MAN"] = monAndNin(allTimes)
    # 计算总直播时长
    longLive = sum([item['sumTime'] for item in liveList])
    hour, a = divmod(longLive, 3600)
    mins, sec = divmod(a, 60)
    weekData["liveSumTime"] = '%d小时%d分%d秒'%(int(hour),int(mins),int(sec))
    previous = openJson('dataView')
    weekData['previous'] = previous['idol'] if 'idol' in previous else {}
    writeJson(weekData, 'dataView')


week(["2020/03/02","2020/03/08"],'唐霖')