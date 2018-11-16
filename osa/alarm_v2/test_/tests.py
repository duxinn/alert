import pymysql
from django.test import TestCase

# Create your tests here.


DB_CONFIG = {       # 数据库配置
    'host': '172.17.146.238',
    'port': 3306,
    'user': 'root',
    'passwd': 'Sui@911120',
    'db': 'du_alarm_app',
    'charset': 'utf8',
}

id = 'chenmin'
level = '3'
conn_db = pymysql.connect(**DB_CONFIG)
cursor = conn_db.cursor(cursor=pymysql.cursors.DictCursor)
cursor.execute("select id,ding_user,email_user,wechat_user,chat_name,title,ding_chat_id from \
            alarm_info where owner=%s and level=%s;", (id, level))
alarm_session = cursor.fetchall()
print(alarm_session[0]['email_user'])
temp = '陈敏'
import threadpool
