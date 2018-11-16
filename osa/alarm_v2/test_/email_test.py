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


def send_email_information(recipients, content, db_id,  table, title="告警信息",):
    content = str(content)
    print('send_email_information:', recipients, content, db_id, table)
    # ['chenmin@shuzilm.cn']
    # {"部门": "运维", "环境": "生产环境", "告警业务": "陈敏测试alert_business", "告警功能": "陈敏测试alert_function", "告警主机": "du-da-test-1", "主机 IP": "192.168.1.2", "告警等级": "高", "告警时间": "2018-06-28 10:09:09", "异常说明": "陈敏测试之异常说明", "chenmin": "chenmin", "level": "3"}
    # 17 < multiprocessing.queues.Queue object at 0x7f73cf088cc0 >
    # alarm_log_prod
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
    server = smtplib.SMTP()
    server.connect(MAIL_HOST)
    # server.ehlo()
    # server.starttls()
    # server.ehlo()
    server.login(MAIL_USERNAME, MAIL_PASSWORD)

    # if content[0:4] == "HTML":
    #     content = content[4:]
    #     msg = MIMEText(content, _subtype='html', _charset='utf-8')
    # else:
    #     msg = MIMEText(content, _subtype='plain', _charset='utf-8')
    msg = MIMEText(content, _subtype='html', _charset='utf-8')

    msg['Subject'] = title
    msg['From'] = MAIL_SENDER
    msg['To'] = Header(title, 'utf-8')
    for email in recipients:
        server.sendmail(MAIL_SENDER, email, msg.as_string())
    server.close()
    # now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # conn_email = pymysql.connect(**DB_CONFIG)
    # cursor = conn_email.cursor()
    # cursor.execute(
    #     "update %s set email_status='success',update_time='%s' where id='%s';"%(table, now_time, db_id))
    # conn_email.commit()
    # cursor.close()
    # conn_email.close()
    print('send_email_information 1')
    return 1

    # except Exception as error1:
    #     # 把邮件发送失败的状态email_status='false'写入alarm_log
    #     try:
    #         now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #         conn_email = pymysql.connect(**DB_CONFIG)
    #         cursor = conn_email.cursor()
    #         cursor.execute(
    #             "update %s set email_status='false',update_time='%s' where id='%s';"%(table, now_time, db_id))
    #         conn_email.commit()
    #         cursor.close()
    #         conn_email.close()
    #     except Exception as error:
    #         # write_logs("alarm.err", RECORD_LOG_STATUS, error, LOG_FILE_PATH)
    #         print('send_email_information -1')
    #         return -1
    #     # write_logs("alarm.err", RECORD_LOG_STATUS, error1, LOG_FILE_PATH)
    #     return -1

# result = send_email_information(['chenmin@shuzilm.cn'],'{"部门": "运维", "环境": "生产环境", "告警业务": "陈敏测试alert_business", "告警功能": "陈敏测试alert_function", "告警主机": "du-da-test-1", "主机 IP": "192.168.1.2", "告警等级": "高", "告警时间": "2018-06-28 10:09:09", "异常说明": "陈敏测试之异常说明", "chenmin": "chenmin", "level": "3"}', 17, 'alarm_log_prod')
result = send_email_information(['chenmin@shuzilm.cn'],'test', 17, 'alarm_log_prod')
print(result)