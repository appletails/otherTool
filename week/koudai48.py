# -*- coding: utf-8 -*-
# from cqhttp import CQHttp
import json
import time
import setting
import requests
import urllib3
from CQLog import WARN, INFO
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Koudai:
    """docstring for Koudai"""
    response = {}
    # 系统时间
    sysTime13 = 0
    # 配置文件记录时间
    cfgTime13 = 0
    # 口袋房间消息时间
    kdmsgTime13 = 0

    # 初始化
    def __init__(self, i):
        super(Koudai, self).__init__()
        # 获取系统时间和配置文件时间
        self.sysTime13 = self.getSysTime13()
        self.cfgTime13 = self.getCfgTime13(i)
        # 请求一次口袋房间
        res = self.getMainpage(i)
        # 请求成功
        if res['status'] == 200:
            # 获取response
            self.response = res
            # 获取最新口袋消息时间
            self.kdmsgTime13 = self.getKdmsgTime13()
        elif res['status'] >= 401000:
            WARN('koudai48.py授权验证失败', res)
            if not setting.token_verify():
                WARN('token失效，尝试获取新token')
                setting.getNewToken()
        else:
            WARN('获取口袋房间信息出错', res['message'])

    def stamp_to_str(self, timestamp):
        x = time.localtime(timestamp / 1000)
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', x)
        return time_str

    # 请求口袋房间
    def getMainpage(self, i):
        roomId, ownerId = setting.roomId(i)
        url = "https://pocketapi.48.cn/im/api/v1/chatroom/msg/list/homeowner"
        form = {
            'ownerId': int(ownerId),
            'roomId': int(roomId)
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
            'token': setting.token()
        }
        try:
            response = requests.post(
                url,
                data=json.dumps(form),
                headers=header,
                verify=False,
                timeout=5).json()
            return response
        except Exception as e:
            raise e

    def getSysTime13(self):
        t = int(time.time() * 1000)
        return t

    def getCfgTime13(self, i):
        t = setting.read_kdmsg_time13(i)
        return t

    # 写配置文件时间
    def writeCfgTime13(self, t, i):
        setting.write_kdmsg_time13(t, i)

    def getKdmsgTime13(self):
        t = self.response['content']['message'][0]['msgTime']
        return t

    # 检查新消息
    def checkNew(self, i):
        # 判断response非空
        if self.response:
            # 忽略超过60秒的消息
            if self.sysTime13 > self.cfgTime13 + 60000:
                # 将配置文件时间设置为 系统时间 - 60s
                self.writeCfgTime13(self.sysTime13 - 60000, i)
                # 更新cfgTime13
                self.cfgTime13 = self.sysTime13 - 60000
            elif self.cfgTime13 == self.kdmsgTime13:
                pass
            elif self.cfgTime13 > self.kdmsgTime13:
                # 说明有撤回消息
                pass
            if self.cfgTime13 < self.kdmsgTime13:
                # 有新消息
                # 将配置文件时间设置为 最新一条消息的时间
                self.writeCfgTime13(self.kdmsgTime13, i)
                return True

    # 酷Qair消息
    def msgArray(self, cqType, idol, at):
        msg_array = []
        datas = self.response['content']['message']
        for data in datas:
            # 判断重复
            if data['msgTime'] <= self.cfgTime13:
                continue
            #
            # 文字消息
            extInfo = json.loads(data['extInfo'])
            if data['msgType'] == 'TEXT':
                if extInfo['messageType'] == 'TEXT':
                    msg = ('%s：%s\n来源：%s房间 %s' % (
                        extInfo['user']['nickName'],
                        extInfo['text'],
                        idol, self.stamp_to_str(data['msgTime'])))
                elif extInfo['messageType'] == 'REPLY':
                    msg = ('%s：%s\n%s：%s\n来源：%s房间 %s' % (
                        extInfo['replyName'], extInfo['replyText'],
                        extInfo['user']['nickName'], extInfo['text'],
                        idol, self.stamp_to_str(data['msgTime'])))
                elif extInfo['messageType'] == 'LIVEPUSH':
                    if cqType == "pro":
                        msg = [{'type': 'text', 'data': {
                            'text': '%s开直播/电台啦\n标题：%s\n封面：' % (idol, extInfo['liveTitle'])}},
                            {'type': 'image', 'data': {
                                'file': 'https://source.48.cn%s' % extInfo['liveCover']}},
                            {'type': 'text', 'data': {
                                'text': '\n来源：%s房间 时间：%s\n' % (idol, self.stamp_to_str(data['msgTime']))}}
                        ]
                        if at:
                            msg.append({'type': 'at', 'data': {
                                'qq': str(at)}})
                    else:
                        msg = ('%s开直播/电台啦\n标题：%s\n封面：https://source.48.cn%s\n来源：%s房间 时间：%s' % (
                            idol, extInfo['liveTitle'],
                            extInfo['liveCover'], idol,
                            self.stamp_to_str(
                                data['msgTime']),
                        ))
                        if at:
                            msg += '\n[CQ:at,qq=all]'

                elif extInfo['messageType'] == 'FLIPCARD':
                    answerData = self.getIdolFanPai(
                        extInfo['questionId'], extInfo['answerId'])
                    # INFO('idol翻牌')
                    msg = ('%s：%s\n%s：%s\n来源：%s的偶像翻牌 %s' % (
                        answerData['content']['userName'], extInfo['question'],
                        extInfo['user']['nickName'], extInfo['answer'],
                        idol, self.stamp_to_str(data['msgTime'])))
                else:
                    msg = '有未知格式的文字消息'
                    INFO('有未知格式的文字消息')
                    INFO(data)
            # image
            elif data['msgType'] == 'IMAGE':
                bodys = json.loads(data['bodys'])
                if cqType == "pro":
                    msg = [{'type': 'text', 'data': {
                        'text': '%s：\n' % extInfo['user']['nickName']}},
                        {'type': 'image', 'data': {
                            'file': '%s' % bodys['url']}},
                        {'type': 'text', 'data': {
                            'text': '\n来源：%s房间 %s' % (idol, self.stamp_to_str(data['msgTime']))}}
                    ]
                else:
                    msg = ('%s：图片消息：%s\n来源：%s房间 %s' % (
                        extInfo['user']['nickName'], bodys['url'], idol, self.stamp_to_str(data['msgTime'])))
            # voice
            elif data['msgType'] == 'AUDIO':
                bodys = json.loads(data['bodys'])
                if cqType == "pro":
                    msg = [{'type': 'text', 'data': {
                        'text': '%s：语音消息' % extInfo['user']['nickName']}},
                        {'type': 'record', 'data': {
                            'file': '%s' % bodys['url']}},
                        {'type': 'text', 'data': {
                            'text': '\n来源：%s房间 %s' % (idol, self.stamp_to_str(data['msgTime']))}}
                    ]
                else:
                    msg = ('%s：语音消息：%s\n来源：%s房间 %s' % (
                        extInfo['user']['nickName'], bodys['url'], idol, self.stamp_to_str(data['msgTime'])))

            elif data['msgType'] == 'VIDEO':
                bodys = json.loads(data['bodys'])
                msg = ("%s: 视频消息：%s\n来源：%s房间 %s" % (
                    extInfo['user']['nickName'], bodys['url'], idol,  self.stamp_to_str(data['msgTime'])))

            elif data['msgType'] == 'EXPRESS':
                msg = ("%s: [发送了表情]\n来源：%s房间 %s" % (
                    extInfo['user']['nickName'], idol,  self.stamp_to_str(data['msgTime'])))
            else:
                msg = '有未知类型的消息'
                INFO('有未知类型的消息')
                INFO(data)
            msg_array.append(msg)
        return msg_array

    def getIdolFanPai(self, qid, aid):
        url = "https://pocketapi.48.cn/idolanswer/api/idolanswer/v1/question_answer/detail"
        form = {
            "answerId": aid,
            "questionId": qid
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
            'token': setting.token()
        }
        try:
            response = requests.post(
                url,
                data=json.dumps(form),
                headers=header,
                verify=False,
                timeout=5).json()
            return response
        except Exception as e:
            raise e
