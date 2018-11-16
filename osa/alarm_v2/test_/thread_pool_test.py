import time
from concurrent.futures import ThreadPoolExecutor

# 方便测试创建三个线程
executor = ThreadPoolExecutor(3)

def test_function(num1, num2):
    print(num1, num2)
    # 方法休眠十秒
    time.sleep(4)
    return num1 + num2

# 由于我们的结果是十秒后返回，所以这里也会被阻塞，十秒后才会收到结果
result_iterators = executor.map(test_function, [1, 2, 3], [5, 6, 7])

for result in result_iterators:
    print(result)

# 到这里很显然前面三个线程都在使用中，10秒后才能得到执行
future = executor.submit(test_function, 4, 8)
print(future.result())
