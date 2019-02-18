import gevent 
import time 

#协程函数
def foo(a,b):
    print("Running in foo",a,b)
    gevent.sleep(3)  #模拟遇到ＩＯ阻塞的情况
    print('switch to foo again')
    return 1

def bar():
    print("Running in bar")
    gevent.sleep(2)
    print("switch to bar again")
    return 1

x = []

#注册为协程事件
f = gevent.spawn(foo,1,2)
b = gevent.spawn(bar)
t = [f,b]


# gevnet.join(f)
# gevnet.join(b)
# print('iwait',gevent.iwait([f,b]))
# print('wait',gevent.wait([f,b]))
x = gevent.joinall(t)
# print(x)
# [<Greenlet "Greenlet-0" at 0x7f6c55089e48: _run>, <Greenlet "Greenlet-1" at 0x7f6c55089b48: _run>]
for i in t:
    print(i.get())


