# -*- coding: utf-8 -*-

import os
import requests
import json
import time
import codecs
from cqhttp import CQHttp
from CQLog import INFO, WARN
# 引入时间调度器 apscheduler 的 BlockingScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

bot = CQHttp(api_root='http://127.0.0.1:5700/')

# 创建调度器实例
sched = BlockingScheduler()

header = {
	"Host": "api.amemv.com",
	"Connection": "keep-alive",
	"Accept-Encoding": "gzip",
	"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"
}

def openData():
	fb = open('init.json','rb')
	data = json.load(fb)
	fb.close()
	return data

def writeData(data):
	fb = codecs.open('init.json','w', 'utf-8')  
	fb.write(json.dumps(data,indent=4,ensure_ascii=False))
	fb.close()

ini = openData()
QQqun = ini["QQqun"]
interval_delay = ini["delay"]

def dydata(user_id,dytk):
	p = os.popen('node fuck-byted-acrawler.js %s' % user_id)
	signature = p.readlines()[0]
	video_url = 'https://www.amemv.com/web/api/v2/aweme/post/?{0}'
	video_form = {
		"user_id":str(user_id),
		"count":"21",
		"max_cursor":"0",
		"aid":"1128",
		"_signature":signature,
		"dytk":dytk
	}
	url = video_url.format(
        '&'.join([key + '=' + video_form[key] for key in video_form]))
	response = requests.get(url, headers=header).json()
	print('查到数据：%d条' % len(response["aweme_list"]))
	data = response["aweme_list"]
	return data

def douying(nowTime,secondsDelay):
	timeDate = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
	print("开始查询：" + timeDate)
	timeArray = []
	# 获取用户数据
	data = dydata(ini["user_id"],ini["dytk"])
	# 判断之前是否记录
	if not(ini["aweme_id"]):
		ini["aweme_id"] = data[0]["aweme_id"]
		writeData(ini)

	# 最后一次获取的抖音的id
	aweme_idS = ini["aweme_id"]
	if data == []:
		INFO(str(ini["name"]) + "未获取到数据，请检查用户是否发过抖音")
		print(str(ini["name"]) + "未获取到数据，请检查用户是否发过抖音")
	else:
		test = str(ini["name"]) + "：共有"+str(len(data))+"条抖音"
		INFO(test)
		print(test)
	msg = ""
	for i in data:
		# aweme_id = 当前抖音的id
		aweme_id=i["aweme_id"]
		if int(aweme_id)>int(aweme_idS):
			# 讲这条数据加入待发送数组
			timeArray.append(i)

	if timeArray:
		print("发现" + str(len(timeArray)) + "条新抖音\n")

		ini["aweme_id"] = timeArray[0]["aweme_id"]
		writeData(ini)
		for i in timeArray:
			share_desc = i["desc"]
			cover_img = "https://p9-dy.byteimg.com/img/" + i["video"]["cover"]["uri"] + "~c5_300x400.jpg"
			play_addr = "https://aweme.snssdk.com/aweme/v1/play/?video_id=" + i["video"]["play_addr"]["uri"] + "&line=0"
			# msg = ini["name"] + "更新抖音啦！\n" + \
			# 	"标题：" + share_desc + "\n" +\
			# 	"封面：" + cover_img + "\n" +\
			# 	"链接：" + play_addr + "\n"
			msg = [{'type': 'at', 'data': {'qq': '476297692'}},
					{'type': 'text', 'data': {'text': '\n%s更新抖音啦！\n标题：%s\n封面：\n' % (ini["name"],share_desc)}},
					{'type': 'image','data': {'file': cover_img}},
					{'type': 'text', 'data': {'text': '\n链接：%s\n' % play_addr}}]

	else:
		INFO("未发现更新\n")
		print("未发现更新\n")
	return msg

def getdouying():
	try:
		INFO('check douying')
		stampTime = int(time.time())
		msgDict = douying(stampTime, int(interval_delay))
		if msgDict:
			bot.send_group_msg_async(group_id=QQqun, message=msgDict, auto_escape=False)
			time.sleep(0.1)
	except:
		WARN('error when douying')
	finally:
		pass

try:
	sched.add_job(
	    getdouying, 'interval', seconds=interval_delay,
	    misfire_grace_time=interval_delay, coalesce=True, max_instances=15)
except Exception as e:
	WARN('error when start thread')
# 开始调度任务
sched.start()