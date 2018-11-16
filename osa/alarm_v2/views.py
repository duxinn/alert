import json
from django.shortcuts import render, HttpResponse
from .src import alarm
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from multiprocessing import Queue
from threading import Thread
import time
import requests
from collections import OrderedDict
import hashlib
import pymysql
import datetime
import copy
from tools.log_management import write_logs
from concurrent.futures import ThreadPoolExecutor


# Create your views here.


# 云端 1分钟超过2个
THRESHOLD_VALUE_SRV = 2  # 云端告警阈值
TIME_VALUE_SRV = 60  # 云端告警时间范围

# 运维组 4分钟超过4个
THRESHOLD_VALUE_OP = 3  # 运维组告警阈值
TIME_VALUE_OP = 60  # 运维组告警时间范围

SALT_DU_OP = 'YYLmfY6IRdjZMQ1'
SALT_DU_SRV = 'YYLmfY6IRdjZMQ1'
SALT_DU_FE = 'YYLmfY6IRdjZMQ1'
SALT_DU_DA = 'YYLmfY6IRdjZMQ1'

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

# 测试用本机数据库测试
# DB_CONFIG = {       # 数据库配置
#     'host': '127.0.0.1',
#     'port': 3306,
#     'user': 'duxin',
#     'passwd': 'duxin',
#     'db': 'du_alarm_app',
#     'charset': 'utf8',
# }

# 未启用
# executor = ThreadPoolExecutor(8)


def sign_verif(sign, content_sign, salt):
    '''
    此函数用于签名验证，成功返回1，失败返回0,返回值类型为 int
    sign:获取的签名
    content_sign:要验证的字符串
    '''
    sign_md5 = hashlib.md5(content_sign.encode('utf-8'))
    sign_md5.update(salt.encode('utf-8'))
    sign_local = sign_md5.hexdigest()
    if sign != sign_local:
        return 0
    else:
        return 1


def key_gen(string):
    '''此函数用于对 字符串进行 md5 加密'''
    h = hashlib.md5()
    h.update(string.encode('utf-8'))
    return h.hexdigest()


def write_db(id, level, dep, env, alert_level, alert_host, alert_ip, alert_time, alert_business, alert_function, exception_spec, status, notes, others):
    '''测试结果：插入空 和 不插入这个 字段是，在库中都是NULL，查出来都是 None'''
    '''此函数用于僵收到的报警信息写库'''
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    except Exception as error:
        write_logs("alarm.err", RECORD_LOG_STATUS, error, LOG_FILE_PATH)
        return HttpResponse(json.dumps({"code": 3000}))
    else:
        # 记录数据库日志
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if env == 'prod':
            table = 'alarm_log_prod'
        elif env == 'pre':
            table = 'alarm_log_pre'
        elif env == 'dev':
            table = 'alarm_log_dev'
        sql = "insert into %s\
                    (owner,level,dep,env,alert_level,alert_host,alert_ip,alert_time,alert_business,\
                    alert_function,exception_spec,status,notes,others,create_time,update_time)\
                    VALUES('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" \
              %(table, id, level, dep, env, alert_level, alert_host, alert_ip, alert_time, alert_business, alert_function, \
                exception_spec, status, notes, others, now_time, now_time)
        # print(sql)
        cursor.execute(sql)
        conn.commit()
        # 获取最后一行的id
        new_id = cursor.lastrowid

        cursor.close()
        conn.close()
        return new_id



# url:''
@csrf_exempt
def alarm_main(req):

    if req.method != "POST":
        # 如果不是 POST 方法
        return HttpResponse(json.dumps({"code": 1004}))
    else:
        # print('req.body=',req.body)
        # req.body = b'{"id": "chenmin", "level": "3", "dep": "du-op", "env": "prod", "alert_level": "\\u9ad8", "alert_host": "du-da-test-1", "alert_ip": "192.168.1.2", "alert_time": "2018-06-28 10:09:09", "alert_business": "\\u9648\\u654f\\u6d4b\\u8bd5alert_business", "alert_function": "\\u9648\\u654f\\u6d4b\\u8bd5alert_function", "exception_spec": "\\u9648\\u654f\\u6d4b\\u8bd5\\u4e4b\\u5f02\\u5e38\\u8bf4\\u660e", "sign": "0c27e9b673f8185e666b3f51b8f2ae89"}'
        req_data = req.body.decode("utf-8")
        # print(req_data)
        try:
            req_data = json.loads(req_data)
        except Exception:
            # json 格式解析失败 返回 1002
            return HttpResponse(json.dumps({"code": 1002}))
        else:
            # json 解析成功
            if not isinstance(req_data, dict):
                # 内容格式不是字典 返回 1000
                return HttpResponse(json.dumps({'code': 1000}))
            else:
                # 内容格式是字典
                if not (req_data.get('id') and req_data.get('level') and req_data.get('dep') and req_data.get('env') and req_data.get('sign')):
                    # 如果没有id、level、dep、env、sign，则返回 1001 参数错误
                    return HttpResponse(json.dumps({'code': 1001}))
                else:
                    # print('如果必须参数正确')
                    # 如果必须参数正确
                    # content_data 用来发送内容的字典,此字典的目的是为了调整消息发送顺序
                    req_data = OrderedDict(sorted(req_data.items(), key=lambda x: x[0]))

                    # 如果参数的值不是 字符串 返回 2009
                    for i in req_data:
                        if not isinstance(req_data[i], str):
                            return HttpResponse(json.dumps({'code': 2009}))

                    sign = req_data.pop('sign', None)
                    # 如果没有签名，返回 2000
                    if not sign:
                        return HttpResponse(json.dumps({'code': 2000}))

                    # content_sign 是拼接的要验证的字符串
                    content_sign = ''.join(req_data.values())
                    if not isinstance(content_sign, str):
                        # 如果拼接的值里面不是字符串
                        return HttpResponse(json.dumps({'code': 2009}))

                    # 实例化要发送的内容
                    content_data = OrderedDict()
                    # 部门
                    dep = req_data.get('dep')
                    if dep == 'du-op':
                        salt = SALT_DU_OP
                        content_data['部门'] = '运维'
                    elif dep == 'du-srv':
                        salt = SALT_DU_SRV
                        content_data['部门'] = '云端'
                    elif dep == 'du-fe':
                        salt = SALT_DU_FE
                        content_data['部门'] = '前端'
                    elif dep == 'du-da':
                        salt = SALT_DU_DA
                        content_data['部门'] = '大数据'
                    else:
                        return HttpResponse(json.dumps({'code': 2002}))
                    # 如果签名验证失败，返回 2000
                    if not sign_verif(sign, content_sign, salt):
                        return HttpResponse(json.dumps({'code': 2000}))

                    # 取值
                    id = req_data.get('id')
                    level = req_data.get('level')
                    if not (id and level):
                        return HttpResponse(json.dumps({'code': 1001}))

                    # 环境
                    env = req_data.get('env')
                    if env == 'prod':
                        content_data['环境'] = '生产环境'
                        table = 'alarm_log_prod'
                    elif env == 'pre':
                        content_data['环境'] = '预发布'
                        table = 'alarm_log_pre'
                    elif env == 'dev':
                        content_data['环境'] = '测试环境'
                        table = 'alarm_log_dev'
                    else:
                        return HttpResponse(json.dumps({'code': 2003}))

                    # 需要写库的数据
                    alert_level = req_data.get('alert_level')
                    alert_time = req_data.get('alert_time')
                    alert_business = req_data.get('alert_business')
                    alert_host = req_data.get('alert_host')
                    alert_function = req_data.get('alert_function')
                    alert_ip = req_data.get('alert_ip')
                    exception_spec = req_data.get('exception_spec')
                    status = req_data.get('status')
                    notes = req_data.get('notes')
                    others = req_data.get('others')

                    # 将发送的内容里的英文 换成中文
                    for i in req_data:
                        if i not in ['id', 'level', 'dep', 'env', 'sign']:
                            if i == 'alert_level':
                                content_data['告警等级'] = req_data.get(i)
                            elif i == 'alert_time':
                                content_data['告警时间'] = req_data.get(i)
                            elif i == 'alert_business':
                                content_data['告警业务'] = req_data.get(i)
                            elif i == 'alert_host':
                                content_data['告警主机'] = req_data.get(i)
                            elif i == 'alert_ip':
                                content_data['主机 IP'] = req_data.get(i)
                            elif i == 'alert_function':
                                content_data['告警功能'] = req_data.get(i)

                            elif i == 'exception_spec':
                                content_data['异常说明'] = req_data.get(i)
                            elif i == 'status':
                                content_data['目前状态'] = req_data.get(i)
                            elif i == 'notes':
                                content_data['备注'] = req_data.get(i)
                            elif i == 'others':
                                content_data['其他'] = req_data.get(i)
                            else:
                                content_data[i] = req_data.get(i)

                    # 写入用于发送内容的字典
                    # content_data['id'] = id
                    # content_data['level'] = level
                    # 写库
                    print('正在写库')
                    new_id = write_db(id, level, dep, env, alert_level, alert_host, alert_ip, alert_time,
                                      alert_business, alert_function, exception_spec, status, notes, others)

                    # 根据部门需求，统计频率，选择发送
                    print('根据部门需求，统计频率，选择发送')
                    content_str = ''
                    # 回车前面的两个空格是为了兼容钉钉
                    for i in content_data:
                        content_str += str(i) + ':' + str(content_data[i]) + '  \n'
                    content_data = str(content_str)
                    # print('content_data=',content_data)
                    key = key_gen(content_data)
                    if dep == 'du-srv':
                        print('进入 du-srv 部门')
                        if key not in cache:
                            # 不在缓存里, 存缓存, 并发送
                            cache.set(key, 1, TIME_VALUE_SRV)
                            resp_code = alarm.main(content_data, id, level, table, new_id)
                            print('resp_code=', resp_code)
                            return HttpResponse(json.dumps({'code': resp_code}))
                        else:
                            # 在缓存里，取值
                            count = cache.get(key)
                            if count > THRESHOLD_VALUE_SRV:
                                # 大于阈值不发送
                                cache.set(key, count + 1,
                                          TIME_VALUE_SRV)
                            elif count <= THRESHOLD_VALUE_SRV:
                                # 小于阈值,发送
                                cache.set(key, count + 1,
                                          TIME_VALUE_SRV)

                                resp_code = alarm.main(content_data, id, level, table, new_id)
                                print('resp_code=',resp_code)
                                return HttpResponse(json.dumps({'code': resp_code}))
                    elif dep == 'du-fe':
                        print('进入了du-fe部门')
                        resp_code = alarm.main(content_data, id, level, table, new_id)
                        return HttpResponse(json.dumps({'code': resp_code}))

                    elif dep == 'du-da':
                        print('进入了du-da部门')
                        resp_code = alarm.main(content_data, id, level, table, new_id)
                        return HttpResponse(json.dumps({'code': resp_code}))

                    elif dep == 'du-op':
                        print('进入了du-op部门')
                        if key not in cache:
                            # 不在缓存里, 存缓存, 并发送
                            print('不在缓存里')
                            cache.set(key, 1, TIME_VALUE_OP)
                            resp_code = alarm.main(content_data, id, level, table, new_id)
                            print('resp_code=', resp_code)
                            return HttpResponse(json.dumps({'code': resp_code}))
                        else:
                            # 在缓存里，取值
                            print('在缓存里')
                            count = cache.get(key)
                            if count > THRESHOLD_VALUE_OP:
                                # 大于阈值不发送
                                print('大于阈值')
                                cache.set(key, count + 1,
                                          TIME_VALUE_OP)
                                return HttpResponse(json.dumps({'code': 1010}))
                            elif count <= THRESHOLD_VALUE_OP:
                                # 小于阈值,发送
                                print('小于阈值')
                                cache.set(key, count + 1,
                                          TIME_VALUE_OP)
                                resp_code = alarm.main(content_data, id, level, table, new_id)
                                print('resp_code=',resp_code)
                                return HttpResponse(json.dumps({'code': resp_code}))








