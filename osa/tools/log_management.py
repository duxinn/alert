import datetime
import os


def write_logs(file_name, status, content, file_path=""):

    """
    记录日志

    :param file_name: 文件名，数据类型为字符串
    :param status: 是否记录日志，Y 为记录，N 为不记录
    :param content: 日志内容，数据类型为字符串
    :param file_path: 日志存储绝对路径，默认为空，空值会保存在项目目录下的 logs 里
    """

    if status == "Y":
        if file_path:
            write_file = os.path.normpath(os.path.join(file_path, file_name))
        else:
            file_path = "logs"
            write_file = os.path.normpath(
                os.path.join(os.path.abspath(__file__), os.pardir, os.pardir, file_path, file_name))
        now_time = datetime.datetime.now().strftime("[ %Y-%m-%d %H:%M:%S ] ")
        log_data = str(now_time) + str(content) + "\n"
        with open(write_file, "a", encoding="utf-8") as H:
            H.write(log_data)
