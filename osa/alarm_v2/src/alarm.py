# -*- coding:utf-8 -*-
import time
from concurrent.futures import ThreadPoolExecutor

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
from collections import OrderedDict

"""
版本号
"""

VERSION = "2.0.5"  # 系统版号


"""
报警程序配置
"""

RECORD_LOG_STATUS = "Y"  # 是否记录日志 Y 或者 N
LOG_FILE_PATH = ""  # 日志文件绝对路径，如果为空则默认存储到项目的 logs 目录下

DB_CONFIG = {       # 数据库配置
    'host': '172.17.146.238',
    'port': 3306,
    'user': 'root',
    'passwd': 'Sui@911120',
    'db': 'du_alarm_app',
    'charset': 'utf8',
}


"""
邮箱配置
"""

MAIL_HOST = "mail.shuzilm.cn"  # 邮箱接口地址
MAIL_SENDER = "it@shuzilm.cn"  # 邮件发送用户
MAIL_USERNAME = "it@shuzilm.cn"  # 登陆邮箱用户名
MAIL_PASSWORD = "Puyu7636"  # 登陆邮箱密码


"""
钉钉配置
"""

DING_CORP_ID = "ding536db086d3f7648e"  # 钉钉企业编号
DING_CORP_SECRET = "X17Dkb0ZwD6JjhJ92Z3WdsUBAX6HGCzVLeB-oku8SiQF1eAhJ8VDJHMXoW5Z3muh"  # 钉钉企业密钥


"""
微信配置（WeChat 在这里简称 WC）
"""

WC_CORP_ID = "wxee18c29ced9a8c63"  # 微信企业编号
WC_CORP_SECRET = "7BtRqm6U7s34sBUlqBAcNyIzQ2kmeMkc_AqJINVVzyfJSJ_K7pXPTvMKcLTd1BmX"  # 微信企业密钥


# 公共账号　和　ｉｔ　这两个账号的钉钉好都是运维部门ｉｔ的钉钉号, IT_ID　为其钉钉号用于创建所有钉钉告警群
IT_ID = '0167570929777239589'


executor = ThreadPoolExecutor(2)

def send_email_information(recipients, content, db_id, table, title="告警信息",):
    """
    发送邮件消息

    :param recipients: 收件人，数据类型为列表
    :param content: 邮件内容，数据类型为字符串
    :param title: 邮件标题，数据类型为字符串
    :param db_id：数据库日志编号
    :param q：发送队列
    :return: 成功返回 1 ，异常返回 -1
    """
    # q.get()  # 对列里每次放的是 1，q.get()取出来就是 1
    # 发送邮件并把成功的状态email_status='success'写入alarm_log
    try:
        server = smtplib.SMTP(MAIL_HOST, 25)
        # server.connect()
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)

        msg = MIMEText(content, _subtype='plain', _charset='utf-8')
        msg['Subject'] = title
        msg['From'] = MAIL_SENDER
        msg['To'] = ', '.join(recipients)
        server.sendmail(MAIL_SENDER, recipients, msg.as_string())
        server.close()
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn_email = pymysql.connect(**DB_CONFIG)
        cursor = conn_email.cursor()
        cursor.execute(
            "update %s set email_status='success',update_time='%s' where id='%s';"%(table, now_time, db_id))
        conn_email.commit()
        cursor.close()
        conn_email.close()
        print('send_email_information 1')
        return 1

    except Exception as error1:
        # 把邮件发送失败的状态email_status='false'写入alarm_log
        try:
            now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn_email = pymysql.connect(**DB_CONFIG)
            cursor = conn_email.cursor()
            cursor.execute(
                "update %s set email_status='false',update_time='%s' where id='%s';"%(table, now_time, db_id))
            conn_email.commit()
            cursor.close()
            conn_email.close()
        except Exception as error:
            write_logs("alarm.err", RECORD_LOG_STATUS, error, LOG_FILE_PATH)
            print('send_email_information -1')
            return -1
        write_logs("alarm.err", RECORD_LOG_STATUS, error1, LOG_FILE_PATH)
        return -1


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


def send_ding_information(token, chat_id, content, title, db_id, table):
    # print(content, title)
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
        # print(get_data)
        get_data_dic = eval(get_data)
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not get_data_dic["errcode"]:
            conn_ding = pymysql.connect(**DB_CONFIG)
            cursor = conn_ding.cursor()
            cursor.execute(
                "update %s set ding_status='success',update_time='%s' where id='%s';"%(table,now_time, db_id))
            conn_ding.commit()
            cursor.close()
            conn_ding.close()
            print('send_ding_information 1')
            return 1
        else:
            log_data = str(get_data_dic)
            write_logs("alarm.err", RECORD_LOG_STATUS, log_data, LOG_FILE_PATH)
            conn_ding = pymysql.connect(**DB_CONFIG)
            cursor = conn_ding.cursor()
            cursor.execute(
                "update %s set ding_status='false',update_time='%s' where id='%s';"%(table, now_time, db_id))
            conn_ding.commit()
            cursor.close()
            conn_ding.close()
            print('send_ding_information 0')
            return 0
    except Exception as error:
        write_logs("alarm.err", RECORD_LOG_STATUS, error, LOG_FILE_PATH)
        return -1


def get_wc_token():
    """
    获取微信的 TOKEN

    :return: 成功返回 TOKEN 值，失败返回 0 并记录日志，异常返回 -1
    """

    url = r"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s" % (
        WC_CORP_ID, WC_CORP_SECRET)

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


def send_wc_information(token, recipients, content, db_id, table):
    """
    发送微信消息

    :param token: 微信认证的动态口令，数据类型为字符串
    :param recipients:
    :param content: 消息内容，数据类型为字符串
    :param db_id：数据库日志编号
    :param q：发送队列
    :return: 成功返回 1 ，失败返回 0 并记录日志，异常返回 -1
    """
    # q.get()
    ding_url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s" % token
    put_data_dic = {
        "touser": '|'.join(recipients),
        "msgtype": "text",
        "agentid": 1,
        "text": {
            "content": content,
        },
        "safe": 0
    }

    try:
        put_data = json.dumps(put_data_dic).encode("utf-8")
        req = request.Request(ding_url, put_data)
        req.add_header('Content-Type', 'application/json')
        response = request.urlopen(req)
        get_data = response.read().decode('utf-8')
        get_data_dic = eval(get_data)

        if not get_data_dic["errcode"]:
            now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn_wechat = pymysql.connect(**DB_CONFIG)
            cursor = conn_wechat.cursor()
            cursor.execute(
                "update %s set wechat_status='success',update_time='%s' where id='%s';"%(table, now_time, db_id))
            conn_wechat.commit()
            cursor.close()
            conn_wechat.close()
            print('send_wc_information 1')
            return 1
        else:
            log_data = str(get_data_dic)
            write_logs("alarm.err", RECORD_LOG_STATUS, log_data, LOG_FILE_PATH)
            now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn_wechat = pymysql.connect(**DB_CONFIG)
            cursor = conn_wechat.cursor()
            cursor.execute(
                "update %s set wechat_status='false',update_time='%s' where id='%s';"%(table, now_time, db_id))
            conn_wechat.commit()
            cursor.close()
            conn_wechat.close()
            print('send_wc_information 0')
            return 0

    except Exception as error:
        write_logs("alarm.err", RECORD_LOG_STATUS, error, LOG_FILE_PATH)
        try:
            now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn_wechat = pymysql.connect(**DB_CONFIG)
            cursor = conn_wechat.cursor()
            cursor.execute(
                "update %s set wechat_status='false',update_time='%s' where id='%s';"%(table, now_time, db_id))
            conn_wechat.commit()
            cursor.close()
            conn_wechat.close()
        except Exception as error:
            write_logs("alarm.err", RECORD_LOG_STATUS, error, LOG_FILE_PATH)
            return -1
        return -1

# 调用：main(content_data, executor, id, level, table, new_id)
def main(content, id, level, table, new_id):
    # time.sleep(3)
    # return 0
    # 连库
    try:
        conn_db = pymysql.connect(**DB_CONFIG)
        cursor = conn_db.cursor(cursor=pymysql.cursors.DictCursor)
    except Exception as error:
        write_logs("alarm.err", RECORD_LOG_STATUS, error, LOG_FILE_PATH)
        return 3000
    else:
        # 连接正常，查询
        cursor.execute("select id,ding_user,email_user,wechat_user,chat_name,title,ding_chat_id from \
            alarm_info where owner=%s and level=%s;", (id, level))
        alarm_session = cursor.fetchall()
        # print('alarm_session=',alarm_session)
        if not alarm_session:
            conn_db.commit()
            cursor.close()
            conn_db.close()
            return 3001  # 数据库配置信息不存在
        num = alarm_session[0]["id"]
        email_user = alarm_session[0]["email_user"]
        ding_user = alarm_session[0]["ding_user"]
        wc_user = alarm_session[0]["wechat_user"]
        chat_name = alarm_session[0]["chat_name"]
        title = alarm_session[0]["title"]
        ding_chat_id = alarm_session[0]["ding_chat_id"]
        # 发送钉钉消息
        if ding_user:
            cursor.execute("update %s set ding_status='sending' where id='%s';"%(table, new_id))
            conn_db.commit()
            ding_token = get_ding_token()
            if ding_token == -1 or not ding_token:
                conn_db.commit()
                cursor.close()
                conn_db.close()
                return 4000  # 钉钉 TOKEN 获取失败
            else:
                ding_title = title
                if not ding_chat_id:
                    ding_chat_name = chat_name
                    ding_user_list = ding_user
                    ding_id_list = []
                    owner_id = IT_ID
                    for i in ding_user_list.split("；"):
                        if i:
                            cursor.execute("select dingding from user_info where name=%s;", (i,))
                            ding_id_data = cursor.fetchall()
                            user = ding_id_data[0]["dingding"]
                            ding_id_list.append(user)
                    create_chat = create_ding_group(ding_token, ding_chat_name, owner_id, ding_id_list)
                    # 创建失败，关闭数据库连接
                    if create_chat == 0 or create_chat == -1:
                        conn_db.commit()
                        cursor.close()
                        conn_db.close()
                        return 4001
                    # 创建成功，更新 alarm_info 表的 ding_chat_id
                    else:
                        cursor.execute("update alarm_info set ding_chat_id=%s where id=%s;", (create_chat, num))
                        conn_db.commit()
                        ding_chat_id = create_chat
                # unicode 码变成 中文
                # content = content.encode('utf-8').decode('unicode_escape')
                future = executor.submit(send_ding_information, ding_token, ding_chat_id, content, ding_title, new_id, table)
                print('send_ding_information,future.result()', future.result())


        # 发送微信消息
        if wc_user:
            cursor.execute("update %s set wechat_status='sending' where id='%s';"%(table, new_id))
            conn_db.commit()
            user_list = wc_user
            wc_list = []
            for i in user_list.split("；"):
                if i:
                    cursor.execute("select weixin from user_info where name=%s;", (i,))
                    wc_id_data = cursor.fetchall()
                    user = wc_id_data[0]["weixin"]
                    wc_list.append(user)
            wc_token = get_wc_token()
            if wc_token == -1 or not wc_token:
                conn_db.commit()
                cursor.close()
                conn_db.close()
                return 4003
            else:
                future = executor.submit(send_wc_information, wc_token, wc_list, content, new_id, table)
                print('send_wc_information,future.result()=,:', future.result())


        # 发送邮件消息
        if email_user:
            cursor.execute("update %s set email_status='sending' where id='%s';"%(table, new_id))
            conn_db.commit()
            email_title = title
            email_user_list = email_user
            email_list = []
            for i in email_user_list.split("；"):
                if i:
                    cursor.execute("select email from user_info where name=%s;", (i,))
                    email_id_data = cursor.fetchall()
                    user = email_id_data[0]["email"]
                    email_list.append(user)
            future = executor.submit(send_email_information, email_list, content, new_id, table, email_title)
            print('send_email_information,future.result()=', future.result())


        # 断开数据库链接
        conn_db.commit()
        conn_db.close()
        return 0







'''
存储 接收告警的组合
mysql> desc alarm_info;
+--------------+--------------+------+-----+---------+----------------+
| Field        | Type         | Null | Key | Default | Extra          |
+--------------+--------------+------+-----+---------+----------------+
| id           | int(11)      | NO   | PRI | NULL    | auto_increment |
| owner        | varchar(100) | NO   | MUL | NULL    |                |
| level        | int(11)      | NO   |     | NULL    |                |
| ding_user    | text         | YES  |     | NULL    |                |
| email_user   | text         | YES  |     | NULL    |                |
| wechat_user  | text         | YES  |     | NULL    |                |
| chat_name    | text         | NO   |     | NULL    |                |
| title        | text         | NO   |     | NULL    |                |
| ding_chat_id | text         | YES  |     | NULL    |                |
| notes        | text         | YES  |     | NULL    |                |
+--------------+--------------+------+-----+---------+----------------+
mysql> select * from alarm_info limit 10\G
*************************** 1. row ***************************
          id: 16
       owner: liujx
       level: 1
   ding_user: 刘家兴
  email_user: 
 wechat_user: 
   chat_name: liujx 告警测试 - 高
       title: 高级告警
ding_chat_id: chat90e36f16f01fac3b630fecbbbaa66bcd
       notes: 测试
-----------------------------------------------------------------------------

存储 告警记录
mysql> desc alarm_log;
+---------------+--------------+------+-----+---------+----------------+
| Field         | Type         | Null | Key | Default | Extra          |
+---------------+--------------+------+-----+---------+----------------+
| id            | int(11)      | NO   | PRI | NULL    | auto_increment |
| owner         | varchar(100) | NO   |     | NULL    |                |
| level         | int(11)      | NO   |     | NULL    |                |
| ding_status   | varchar(100) | YES  |     | NULL    |                |
| email_status  | varchar(100) | YES  |     | NULL    |                |
| wechat_status | varchar(100) | YES  |     | NULL    |                |
| content       | text         | YES  |     | NULL    |                |
| create_time   | datetime     | YES  |     | NULL    |                |
| update_time   | datetime     | YES  |     | NULL    |                |
+---------------+--------------+------+-----+---------+----------------+
9 rows in set (0.00 sec)
mysql> select * from alarm_log limit 10\G
*************************** 1. row ***************************
           id: 1
        owner: suiyang
        level: 1
  ding_status: success
 email_status: success
wechat_status: success
      content: 时间：2017-10-31 10:53:55 报警主机：du-dna-4:10.29.91.113 报警业务：du_dna_server2 程序：dna_business_p.py pid:1049 功能：dna 主业务 异常说明：第 132 分区，数据延时 335s
  create_time: 2018-02-01 11:55:43
  update_time: 2018-02-01 11:55:49
'''
