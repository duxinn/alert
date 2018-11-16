# -*- coding:utf-8 -*-

import pymysql
import json
import datetime
import hashlib
import smtplib
from urllib import request
from threading import Thread
from email.mime.text import MIMEText
from email.header import Header
from tools.log_management import write_logs




DB_CONFIG = {       # 数据库配置
    'host': '172.17.146.238',
    'port': 3306,
    'user': 'root',
    'passwd': 'Sui@911120',
    'db': 'du_alarm_app',
    'charset': 'utf8',
}

RECORD_LOG_STATUS = "Y"  # 是否记录日志 Y 或者 N
LOG_FILE_PATH = ""  # 日志文件绝对路径，如果为空则默认存储到项目的 logs 目录下


"""
钉钉配置
"""

DING_CORP_ID = "ding536db086d3f7648e"  # 钉钉企业编号
DING_CORP_SECRET = "X17Dkb0ZwD6JjhJ92Z3WdsUBAX6HGCzVLeB-oku8SiQF1eAhJ8VDJHMXoW5Z3muh"  # 钉钉企业密钥




def get_ding_token():
    """
    获取钉钉的 TOKEN

    :return: 成功返回 TOKEN 值，失败返回 0 并记录日志，异常返回 -1
    """

    url = r"https://oapi.dingtalk.com/gettoken?corpid=%s&corpsecret=%s" % (
        DING_CORP_ID, DING_CORP_SECRET)
    try:
        response = request.urlopen(url)
        get_data = response.read().decode('utf-8')
        get_data_dic = eval(get_data)

        if not get_data_dic["errcode"]:
            access_token = get_data_dic["access_token"]
            return access_token
        else:
            log_data = str(get_data_dic)
            write_logs("alarm.err", RECORD_LOG_STATUS, log_data, LOG_FILE_PATH)
            return 0

    except Exception as error:
        write_logs("alarm.err", RECORD_LOG_STATUS, error, LOG_FILE_PATH)
        return -1


def create_ding_group(token, group_name, group_owner, recipients):
    """
    钉钉创建聊天群

    :param token: 钉钉认证的动态口令，数据类型为字符串
    :param group_name: 钉钉聊天群的名字，数据类型为字符串
    :param group_owner: 钉钉聊天群的群主，数据类型为字符串
    :param recipients: 钉钉聊天群的成员，数据类型为列表
    :return: 成功返回聊天群 ID 值，失败返回 0 并记录日志，异常返回 -1
    """

    ding_url = "https://oapi.dingtalk.com/chat/create?access_token=%s" % token
    put_data_dic = {
        "name": group_name,
        "owner": group_owner,
        "useridlist": recipients,
    }

    try:
        put_data = json.dumps(put_data_dic).encode("utf-8")
        req = request.Request(ding_url, put_data)
        req.add_header('Content-Type', 'application/json')
        data = request.urlopen(req)
        get_data = data.read().decode('utf-8')
        get_data_dic = eval(get_data)

        if not get_data_dic["errcode"]:
            chat_id = get_data_dic['chatid']
            return chat_id
        else:
            log_data = str(get_data_dic)
            write_logs("alarm.err", RECORD_LOG_STATUS, log_data, LOG_FILE_PATH)
            return 0

    except Exception as error:
        write_logs("alarm.err", RECORD_LOG_STATUS, error, LOG_FILE_PATH)
        return -1


def select_ding_group(token, chat_id):
    """
    查询钉钉群是否存在

    :param token: 钉钉认证的动态口令，数据类型为字符串
    :param chat_id: 钉钉群的编号，数据类型为字符串
    :return: 存在返回 1 ，不存在返回 0 ，异常返回 -1
    """

    url = r"https://oapi.dingtalk.com/chat/get?access_token=%s&chatid=%s" % (
        token, chat_id)
    try:
        response = request.urlopen(url)
        get_data = response.read().decode('utf-8')
        get_data_dic = eval(get_data)

        if not get_data_dic["errcode"]:
            return 1
        else:
            return 0

    except Exception as error:
        write_logs("alarm.err", RECORD_LOG_STATUS, error, LOG_FILE_PATH)
        return -1


def send_ding_information(token, chat_id, content, title, ):
    """
    发送钉钉消息

    :param token: 钉钉认证的动态口令，数据类型为字符串
    :param chat_id: 钉钉群的编号，数据类型为字符串
    :param content: 发送的内容，数据类型为字符串
    :param title: 发送消息的标题，数据类型为字符串
    :param db_id：数据库日志编号
    :param q：发送队列
    :return:  成功返回 1，失败返回 0 并记录日志，异常返回 -1
    """
    # q.get()
    ding_url = "https://oapi.dingtalk.com/chat/send?access_token=%s" % token
    put_data_dic = {
        "chatid": chat_id,
        "msgtype": "action_card",
        "action_card": {
            "title": title,
            "markdown": content,
        }
    }

    try:
        put_data = json.dumps(put_data_dic).encode("utf-8")
        # put_data = json.dumps(put_data_dic)

        req = request.Request(ding_url, put_data)
        req.add_header('Content-Type', 'application/json')
        req = request.urlopen(req)
        get_data = req.read().decode('utf-8')
        print(get_data)
        get_data_dic = eval(get_data)
        # now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # if not get_data_dic["errcode"]:
        #     conn_ding = pymysql.connect(**DB_CONFIG)
        #     cursor = conn_ding.cursor()
        #     cursor.execute(
        #         "update %s set ding_status='success',update_time='%s' where id='%s';"%(table,now_time, db_id))
        #     conn_ding.commit()
        #     cursor.close()
        #     conn_ding.close()
        #     print('send_ding_information',1)
        #     return 1
        # else:
        #     log_data = str(get_data_dic)
        #     write_logs("alarm.err", RECORD_LOG_STATUS, log_data, LOG_FILE_PATH)
        #     conn_ding = pymysql.connect(**DB_CONFIG)
        #     cursor = conn_ding.cursor()
        #     cursor.execute(
        #         "update %s set ding_status='false',update_time='%s' where id='%s';"%(table, now_time, db_id))
        #     conn_ding.commit()
        #     cursor.close()
        #     conn_ding.close()
        #     print('send_ding_information',0)
        #     return 0
    except Exception as error:
        # write_logs("alarm.err", RECORD_LOG_STATUS, error, LOG_FILE_PATH)
        # return -1
        print(error)

ding_token = get_ding_token()
print(ding_token)
# token, chat_id, content, title
send_ding_information(ding_token,'chat9da8e4ce2ec75a32b048d1f59c86bd4b','中文','title')
# chat9da8e4ce2ec75a32b048d1f59c86bd4b

string = ''
b_string = b''
string.encode()
b_string.decode()

