# -*- coding: utf-8 -*-
import requests
import json
import time
from cqhttp import CQHttp
from CQLog import INFO, WARN
# 引入时间调度器 apscheduler 的 BlockingScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

def getIni():  # 获取配置文件
    fb = open('ini.json', 'rb')
    data = json.load(fb)
    fb.close()
    return data

bot = CQHttp(api_root='http://127.0.0.1:5700/')
interval_delay = getIni()['interval_delay']
# 实例化 BlockingScheduler
sched = BlockingScheduler()
header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) Appl\
eWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'}


def bilibili(nowTime, idol, host_uid,at ):  # 动态提醒
    url = 'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history'
    form = {
        "visitor_uid": 0,
        "host_uid": host_uid,
        "offset_dynamic_id": 0
    }
    response = requests.get(url, form, headers=header).json()
    data = response["data"]["cards"]
    msgDict = []
    timeArray = []
    for i in data:
        timestamp = i["desc"]["timestamp"]
        if timestamp <= nowTime and timestamp > (nowTime - int(interval_delay)):
            # 在时间段内有新消息则加入数组
            timeArray.append(i)

    # 当消息数组不为空则开始获取消息
    if timeArray:
        for i in timeArray:
            # 判断数据类型是不是字典
            card = i["card"] if isinstance(i["card"], dict) else json.loads(i["card"])
            msgtype = i["desc"]["type"]

            if msgtype == 1:
                msg = [{'type': 'text', 'data': {'text': '【%s】转发了视频\n配字：%s' % (idol, card["item"]["content"])}}]
            elif msgtype == 2:
                msg = [{'type': 'text', 'data': {'text': '【%s】 发布了 %s 张图片\n配字：%s' % (
                    idol, str(card["item"]["pictures_count"]), card["item"]["description"])}}]
                for pic in card["item"]['pictures']:
                    item = [{'type': 'text', 'data': {'text': '\n'}}, {
                        'type': 'image', 'data': {'file': pic['img_src']}}]
                    msg += item
            elif msgtype == 4:
                msg = [{'type': 'text', 'data': {'text': '【%s】发布文字\n内容：%s' % (idol, card["item"]["content"])}}]
            elif msgtype == 8:
                msg = [{'type': 'text', 'data': {'text': '【%s】发布视频\n标题：%s\n封面：\n' % (
                    idol, card['title'])}}, {'type': 'image', 'data': {'file': card['pic']}},{'type': 'text', 'data': {'text': '\n地址：https://www.bilibili.com/video/av%s' % card['aid']}}]
            elif msgtype == 16:
                msg = [{'type': 'text', 'data': {'text': '【%s】发布小视频\n配字：%s\n封面：\n' % (idol, card["item"]["description"])}}, {
                    'type': 'image', 'data': {'file': card['item']['cover']['default']}}]
            msg += [{'type': 'text', 'data': {'text': '\n'}},{'type': 'at', 'data': {'qq': at}}] if at else []
            msgDict.append(msg)

    else:
        timeDate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(nowTime))
        print("未发现更新：" + timeDate)
    return msgDict

def getbilibili():
    try:
        ini = getIni()
        idols = ini['idols']
        QQgroup = ini['QQgroup']
        for item in idols:
            stampTime = int(time.time())
            msgDict = bilibili(stampTime, item['idol'], item['host_uid'], item["at"])
            if msgDict:
                QQgroup = item['QQgroup'] if item['QQgroup'] else QQgroup
                for msg in msgDict:
                    bot.send_group_msg_async(
                        group_id=QQgroup, message=msg, auto_escape=False)
                    time.sleep(.2)
                INFO(msgDict)
            time.sleep(1)
    except:
        WARN('error when bilibili')
    finally:
        INFO('bilibili check completed')


print('B站监听间隔：'+str(interval_delay))
sched.add_job(
    getbilibili, 'interval', seconds=interval_delay,
    misfire_grace_time=interval_delay, coalesce=True, max_instances=15)
# 开始调度任务
sched.start()