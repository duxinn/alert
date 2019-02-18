## 支持渠道
- 钉钉
- 邮箱
- 微信
- 说明：三个渠道发送的过程是异步同时进行的，单个渠道发送失败不影响其他渠道发送，前提是告警群成员都是公司员工、钉钉告警群创建成功。
## 支持消息内容格式
- 文本（钉钉、邮箱、微信）
- markdown（钉钉）

## 链接地址
- URL : http://xxxx

## 服务配置:
- 使用前需要在页面配置相应的接收人等信息
- 配置地址：http://xxx
- 说明：配置好后，owner 的姓名就是 发送告警时的 id，level 是用来区别同一 owner 所拥有的不同告警组

## 请求方式
#### 使用 HTTP 协议 POST 请求，新接口目前只支持 POST 请求
- 在请求体中添加参数
- 使用 json 格式

## 请求参数:
- 必须参数

|参数名|是否必须|类型|说明|
|:----    |:---|:----- |-----   |
|id |是  |string |告警服务使用者（服务配置页面告警组使用人的邮箱前缀）|
|level |是  |string | 服务配置页面告警组配置编号 |
|dep |是 |string |部门 云端：du-srv，初步指定为：运维：du-op， 前端：du-fe， 大数据：du-da，暂缺终端部门和产品部门 |
|env|是 | string |环境，生产环境为'prod'，预发布环境'pre'，测试环境'dev' |
|sign |是  |string | 消息签名    |

- 以下参数为生产环境建议参数，
- 必选参数仅为为  alert_level, alert_time, alert_business。


|参数名|是否必须|类型|在发送的消息中翻译为 |说明|
|:----    |:---|:----- |-----   |
|alert_level |是 |string |告警等级 |告警等级，选值为 '高'、'中'、'低' |
|alert_host |否 |string |告警主机 |告警主机，比如 'du-ftp-qd-2' |
|alert_ip |否 |string |告警 IP |告警 IP，比如 '10.27.23.65' |
|alert_time |是 |string |告警时间 |告警时间，比如 '2018-09-11 19:24:45' |
|alert_business |是 |string |告警业务 |告警业务，比如 'du_dna_servers' |
|alert_function |否 |string |告警功能 |告警功能，比如 'dna 主业务'|
|exception_spec |否 |string |异常说明 |异常说明，比如 '第 33 分区，数据延时 231s' |


- 以下参数为预留参数，可选


|参数名|是否必须|类型|在发送的消息中翻译为 |说明|
|:----    |:---|:----- |-----   |
|status |否 |string |状态 |现在的状态 |
|notes |否 |string |备注 |备注 |
|others |否 |string |其他 |其他 |


- 所有参数的值的类型为字符串

## 签名方法:
- 将 json.dumps 之前的字典（不包含 sign 键值对）按照键的 ASCII 升序排列， 将其中的值按顺序顺序组合成字符串得到 sign_string_a
- 将 sign_string_a 最后添加 YYLmfY6IRdjZMQ1（各部门可自定义） 字符串得到 signStrB
- 将 sign_string_a 进行 MD5 加密得到 sign 签名

## 示例代码 ：
请求
```
data = {
        'id' : 'xxx',
        'level' : 'x',
        'dep' : 'xxx',
        'env' : 'xxx',
        'alert_level' : '高',
        'alert_time' : '2018-01-1 01:01:01',
        'alert_business' : '陈敏测试alert_business',
        'alert_function' : '陈敏测试alert_function',
        'exception_spec' : '陈敏测试之异常说明',
    }
def send_v2(data):
		data_sign = OrderedDict(sorted(data.items(), key=lambda x: x[0]))
		sign_string_a = ''.join(data_sign.values())
		sign_string_b = hashlib.md5(sign_string_a.encode('utf-8'))
		sign_string_b.update('YYLmfY6IRdjZMQ1'.encode('utf-8'))
		data.setdefault("sign", sign_string_b.hexdigest())
		data = json.dumps(data)
		resp = requests.post('http://osa.shuzilm.cn/alarm_v2', data=data)
		return resp
resp = send_v2(data)
print(resp)  # <Response [200]>
print(resp.text)  # {"code": 0}
```
- 注意 post('http://osa.shuzilm.cn/alarm_v2', data=data),此处　alarm_v2　后面不能加 /
 将会发送给所有者为 chenmin，level 为 3 的告警接群，收到的信息将会如下展示：
```
部门:xx
环境:xx
告警业务:陈敏测试alert_business
告警功能:陈敏测试alert_function
告警等级:高
告警时间:2018-01-1 11:11:11
异常说明:陈敏测试之异常说明
```

## 返回示例:

- ##### 正常时返回:
```
# response.text =
{"code": 0}
# 表示发送成功
{"code": 1010}
# 表示告警信息在缓存期内，不发送 1010
```

- ##### 异常时返回:
```
{"code": 错误码}
```
>内容格式不是字典返回 1000
内容参数不正确返回  1001　（即必须参数少了或多了未识别的参数）
json 格式解析失败  1002
请求方法不正确 1003 （旧版）
请求方法不是 POST 1004
签名校验失败返回    2000
部门参数 dep 参数错误 2002
环境参数 env 参数错误 2003
参数的值不是字符串，必须是字符串 2009
链接数据库失败  3000
数据库配置信息不存在 3001　（即根据你在配置页面的 使用人(id) 和 配置编号(level) 去查找时不存在，即你的 id 和 level 值错误）
钉钉 TOKEN 获取失败 4000
钉钉创建聊天群失败  4001
钉钉发送消息失败  4002
微信 TOKEN 获取失败 4003
微信发送消息失败  4004
邮件发送消息失败  4005

## 日常维护：
当告警接收人员中有员工离职时，需要在配置地址：http://osa.du.com/alert_info　及时把离职员工从群接收者中删除。否则当系统重启或聊天群id过期后，重新建立聊天群时，会返回 4001 钉钉创建聊天群失败。
## 备注:
- 暂无
