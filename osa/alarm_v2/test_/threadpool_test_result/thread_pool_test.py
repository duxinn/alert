import hashlib
import time
from collections import OrderedDict
import requests
import json
from multiprocessing import Process


data = {
        'id' : 'chenmin',
        'level' : '3',
        'dep' : 'du-op',
        'env' : 'prod',
        'alert_level' : '高',
        'alert_time' : '2018-01-1 11:11:11',
        'alert_business' : '陈敏测试alert_business',
        'alert_function' : '陈敏测试alert_function',
        'exception_spec' : '陈敏测试之异常说明',
    }
data2 = {
        'id' : 'chenmin',
        'level' : '3',
        'dep' : 'du-op',
        'env' : 'prod',
        'alert_level' : '高',
        'alert_time' : '2018-01-1 11:11:11',
        'alert_business' : '陈敏测试2',
        'alert_function' : '陈敏测试alert_function',
        'exception_spec' : '陈敏测试之异常说明',
    }
data3 = {
        'id' : 'chenmin',
        'level' : '3',
        'dep' : 'du-op',
        'env' : 'prod',
        'alert_level' : '高',
        'alert_time' : '2018-01-1 11:11:11',
        'alert_business' : '陈敏测试3',
        'alert_function' : '陈敏测试alert_function',
        'exception_spec' : '陈敏测试之异常说明',
    }
data4 = {
        'id' : 'chenmin',
        'level' : '3',
        'dep' : 'du-op',
        'env' : 'prod',
        'alert_level' : '高',
        'alert_time' : '2018-01-1 11:11:11',
        'alert_business' : '陈敏测试4',
        'alert_function' : '陈敏测试alert_function',
        'exception_spec' : '陈敏测试之异常说明',
    }
def send_v2(data):

    data_od = OrderedDict(sorted(data.items(), key=lambda x: x[0]))
    sign_string_a = ''.join(data_od.values())
    h = hashlib.md5(sign_string_a.encode('utf-8'))
    h.update('YYLmfY6IRdjZMQ1'.encode('utf-8'))
    data.setdefault("sign", h.hexdigest())
    data = json.dumps(data)
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap Chromium/69.0.3497.100 Chrome/69.0.3497.100 Safari/537.36'}
    # resp = requests.post('http://172.17.146.238:9015/alarm', data=data)
    resp = requests.post('http://localhost:9015/alarm_v2', data=data, headers=headers)
    print(time.time() - begin)
    print(resp,resp.text)


p1 = Process(target=send_v2, args=(data,))
p2 = Process(target=send_v2, args=(data2,))
p3 = Process(target=send_v2, args=(data3,))
p4 = Process(target=send_v2, args=(data4,))

begin = time.time()
print(time.ctime())
p1.start()
p2.start()
p3.start()
p4.start()
p1.join()
p2.join()
p3.join()
p4.join()
