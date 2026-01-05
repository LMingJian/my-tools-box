import hashlib
import os
from ipaddress import IPv4Address
from re import search
from typing import Union

import requests


class ClientFunc:


    @staticmethod
    def search(ip, mode, model):
        if mode == 0:  # Api
            if model == 0:  # ALike
                try:
                    api = f'http://{ip}'
                    response = requests.get(api, timeout=0.5)
                    if response.status_code == 200:
                        return ip
                except BaseException:  # noqa
                    return 0
            elif model == 1:  # BLike
                try:
                    api = f'http://{ip}'
                    response = requests.get(api, timeout=0.5)
                    if response.status_code == 200:
                        return ip
                except BaseException:  # noqa
                    return 0
        else:  # Header
            if model == 0:
                try:
                    api = f'http://{ip}'
                    response = requests.head(api, timeout=0.5)
                    if response.status_code == 200:
                        return ip
                except BaseException:  # noqa
                    return 0
            elif model == 1:
                try:
                    api = f'http://{ip}'
                    response = requests.head(api, timeout=0.5)
                    if response.status_code == 200:
                        return ip
                except BaseException:  # noqa
                    return 0
        return 0

    @staticmethod
    def export(client_list: list[IPv4Address], model, filetype):
        file_name = 'Client'
        if model == 0:
            file_name += 'ALike'
        elif model == 1:
            file_name += 'BLike'
        if filetype == 0:
            with open(file_name + '.txt', 'w', encoding='UTF-8') as file:
                for each in client_list:
                    file.write(each.exploded + '\n')
        elif filetype == 1:
            with open(file_name + '.csv', 'w', encoding='UTF-8') as file:
                count = 1
                file.write(f'编号, 设备IP' + '\n')
                for each in client_list:
                    file.write(f'{count}, {each.exploded}' + '\n')
                    count += 1
        return f'请到当前文件夹中查看文件：{file_name}。'

    @staticmethod
    def register(password):
        if password != '123456':
            return False
        sha256_hash = hashlib.sha256()
        sha256_hash.update(password.encode('UTF-8'))
        hash_value = sha256_hash.hexdigest()
        path = os.environ['APPDATA']
        with open(os.path.join(path, 'toolsbox'), 'w', encoding='UTF-8') as file:
            file.write(hash_value)
        return True

    @staticmethod
    def logout():
        path = os.environ['APPDATA']
        file = os.path.join(path, 'toolsbox')
        if os.path.exists(file):
            os.remove(file)
        return True

    @staticmethod
    def check():
        password = '123456'
        sha256_hash = hashlib.sha256()
        sha256_hash.update(password.encode('UTF-8'))
        hash_value = sha256_hash.hexdigest()
        path = os.environ['APPDATA']
        keypath = os.path.join(path, 'toolsbox')
        if not os.path.exists(keypath):
            return False
        with open(keypath, 'r') as file:
            data = file.read()
        return data == hash_value

    def control(self, data: list, model):
        """
        设备控制，通过字典管理多个不同方法
        :param data: ('set', 1, ip, [data])  (work, flag, ip)
        :param model: 0, 1
        """
        action = {
            'set': self.handle_set,
            'work': self.handle_work,
            'http': self.handle_http
        }
        if data[0] not in action:
            return 0
        return action[data[0]](data[1:], model)  # noqa

    @staticmethod
    def handle_http(data: list, model):
        if model == 0:
            return f'执行 A 相关请求, {data}'
        elif model == 1:
            return f'执行 B 相关请求, {data}'
        else:
            return 0

    @staticmethod
    def handle_set(data: list, model):
        """这里的字典是功能函数字典，值是对应函数的方法名"""
        action_a = {
            0: 'A 功能 1',
            1: 'A 功能 2',
            2: 'A 功能 3'
        }
        action_d = {
            0: 'B 功能 1',
            1: 'B 功能 2',
            2: 'B 功能 3'
        }
        if model == 0:
            return action_a[data[0]]  # noqa
        elif model == 1:
            return action_d[data[0]]  # noqa
        else:
            return 0

    @staticmethod
    def handle_work(data: list, model):
        """这里的字典是功能函数字典，值是对应函数的方法名"""
        action_a = {
            0: 'a1',
            1: 'a2',
            2: 'a3',
            3: 'a4',
            4: 'a5',
        }
        action_d = {
            0: 'b1',
            1: 'b2',
            2: 'b3',
            3: 'b4',
            4: 'b5'
        }
        if model == 0:  # ALike
            return action_a[data[0]]  # noqa
        elif model == 1:  # BLike
            return action_d[data[0]]  # noqa
        else:
            return 0

    @staticmethod
    def live_compute(live_bitrate, live_duration, live_member, live_cost):
        flow = (float(live_bitrate) * float(live_duration) * 60 * float(live_member)) / (1024 * 8 * 1000)
        cost = float(flow) * float(live_cost)
        return f"耗费流量：{round(flow, 2)} GB，费用：{round(cost, 2)}"

    @staticmethod
    def conversion_MB2(flag, data):
        if flag == 0:
            mbps = float(data) * 8
            return f"结果为：{round(mbps, 2)} Mbps"
        else:
            kbps = float(data) * 8 * 1000
            return f"结果为：{round(kbps, 2)} Kbps"

    @staticmethod
    def conversion_Mbps2(flag, data):
        if flag == 0:
            mbps = float(data) / 8
            return f"结果为：{round(mbps, 2)} MB/s"
        else:
            kbps = float(data) * 1000
            return f"结果为：{round(kbps, 2)} Kbps"

class Xml:

    _statement_text = '<?xml version="1.0" encoding="utf-8"?>'

    def create(self, node_name: str, node_data: Union[str, list]):
        if isinstance(node_data, list):
            temp = ''
            for each in node_data:
                temp = temp + each
            node = '<{}>{}</{}>'.format(node_name, temp, node_name)
        else:
            node = '<{}>{}</{}>'.format(node_name, node_data, node_name)
            return node
        return self._statement_text + node

    @staticmethod
    def read(text: str, point):
        text = text.strip().replace('\n', '')
        try:
            res = search('<{}>(.*)</{}>'.format(point, point), text).group()
            return res.replace('<{}>'.format(point), '').replace('</{}>'.format(point), '')
        except BaseException as e:
            return e

    @staticmethod
    def readline(text: str):
        textline = text.split('\n')
        return textline


if __name__ == '__main__':
    client = ClientFunc()
