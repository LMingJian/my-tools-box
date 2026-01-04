from datetime import datetime


def info(*args, **kwargs):
    """Info"""
    # 获取当前时间
    current_time = datetime.now().strftime("%H:%M:%S.%f")[: -3]
    # 格式化输出字符串，前面加上时间戳
    output = (f"<p style='margin: 0 0 3px 0; font-size: 8.5pt'>"
              f"<b style='color: #00aeef;'>INFO [{current_time}]：</b>" +
              " ".join(map(str, args)) +
              "</p>")
    # 使用内置的 print 函数打印格式化后的字符串
    print(output, **kwargs, end='')


def warning(*args, **kwargs):
    """Warning"""
    # 获取当前时间
    current_time = datetime.now().strftime("%H:%M:%S.%f")[: -3]
    # 格式化输出字符串，前面加上时间戳
    output = (f"<p style='margin: 0 0 3px 0; font-size: 8.5pt'>"
              f"<b style='color: #ffc20e;'>WARNING [{current_time}]：</b>" +
              " ".join(map(str, args)) +
              "</p>")
    # 使用内置的 print 函数打印格式化后的字符串
    print(output, **kwargs, end='')


def error(*args, **kwargs):
    """Error"""
    # 获取当前时间
    current_time = datetime.now().strftime("%H:%M:%S.%f")[: -3]
    # 格式化输出字符串，前面加上时间戳
    output = (f"<p style='margin: 0 0 3px 0; font-size: 8.5pt'>"
              f"<b style='color: #f26522;'>ERROR [{current_time}]：</b>" +
              " ".join(map(str, args)) +
              "</p>")
    # 使用内置的 print 函数打印格式化后的字符串
    print(output, **kwargs, end='')


def success(*args, **kwargs):
    """Success"""
    # 获取当前时间
    current_time = datetime.now().strftime("%H:%M:%S.%f")[: -3]
    # 格式化输出字符串，前面加上时间戳
    output = (f"<p style='margin: 0 0 3px 0; font-size: 8.5pt'>"
              f"<b style='color: #8dc63f;'>SUCCESS [{current_time}]：</b>" +
              " ".join(map(str, args)) +
              "</p>")
    # 使用内置的 print 函数打印格式化后的字符串
    print(output, **kwargs, end='')
