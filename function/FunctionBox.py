import hashlib
import os
from ipaddress import IPv4Address
from re import search
from typing import Union


class ClientFunc:


    @staticmethod
    def search(ip, mode, model):
        pass

    @staticmethod
    def export(client_list: list[IPv4Address], model, filetype):
        pass

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
        pass

    def handle_http(self, data: list, model):
        pass

    def handle_set(self, data: list, model):
        pass

    def handle_work(self, data: list, model):
        pass

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
