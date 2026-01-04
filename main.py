import csv
import ipaddress
import json
import os
import tempfile
from datetime import datetime
import sys
from itertools import islice
from codingQrc import *  # noqa
from PySide6.QtCore import QObject, Signal, QThreadPool, QRegularExpression, QTimer, QFile, QIODevice
from PySide6.QtGui import QTextCursor, QRegularExpressionValidator
from PySide6.QtWidgets import QApplication, QMainWindow, QLineEdit, QComboBox, QFileDialog, QDialog
from codingUi import Ui_QMainWindow, Ui_Dialog
from function import *
from function.Worker import WorkerSingle, WorkerMultiple, WorkerController, EMQXWorker


class OutputStream(QObject):
    """重定向控制台输出到 GUI"""
    newText = Signal(str)

    def write(self, text):
        if text != '':
            self.newText.emit(str(text))
        return None

    def flush(self): pass  # 该方法必须写上，否则无法打印


class ListMonitor(QObject):
    """数据列表监听器"""
    data_modified = Signal(list)

    def __init__(self, target_list, interval=500):
        super().__init__()
        self._original_list = target_list
        self._last_state = list(target_list)
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_update)
        self.timer.start(interval)

    def _check_update(self):
        if self._last_state != self._original_list:
            self._last_state = list(self._original_list)
            self.data_modified.emit(self._last_state)


class RegisterDialog(QDialog):
    """注册弹窗"""
    dataSend = Signal(str)

    def __init__(self):
        super(RegisterDialog, self).__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.Btn01.clicked.connect(self.cancel)
        self.ui.Btn02.clicked.connect(self.confirm)

    def cancel(self):
        self.reject()

    def confirm(self):
        data = self.ui.lineEdit.text()
        self.dataSend.emit(data)
        self.accept()


class MainWindow(QMainWindow):
    """主界面窗口"""
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_QMainWindow()
        self.ui.setupUi(self)

        # 自定义 UI 设置补充
        self.ui.ProgressBar.setVisible(False)
        ip_regex = r'^[\d|.]+$'
        validator = QRegularExpressionValidator(QRegularExpression(ip_regex))
        line_edit = [
            self.ui.LineEditIP01, self.ui.LineEditIP02,
            self.ui.LineEditMark01, self.ui.LineEditMark02,
            self.ui.LineEditIP0201, self.ui.LineEditIP0202,
            self.ui.LineEditSET301, self.ui.LineEditSET306,
            self.ui.LineEditLive01, self.ui.LineEditLive02,
            self.ui.LineEditLive03, self.ui.LineEditLive04,
            self.ui.LineEditBit01, self.ui.LineEditBit02,
        ]
        # 限制输入内容
        for each in line_edit:
            each.setValidator(validator)

        # 输出重定向
        sys.stdout = OutputStream(newText=self.onNewText)  # noqa

        # 多线程处理
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(10)
        self.task_count = 0
        self.completed_tasks = 0
        self.progress_value = 0

        # 功能
        self.client = ClientFunc()
        self.client_list = []
        self.client_temp = []
        self.monitor = ListMonitor(self.client_list)
        self.emqx_worker = None
        self.client_uuid = {}

        # 事件绑定
        self.init_events()

        # 验权
        self.check()

    def closeEvent(self, event):
        # 重写关闭事件，以避免窗口关闭后没关闭子线程
        if self.emqx_worker:
            self.emqx_worker.stop()
        event.accept()

    def resizeEvent(self, event):
        """重写缩放事件，实现窗口只能在垂直方向上缩放"""
        super().resizeEvent(event)
        fixed_width = 760
        current_height = self.height()
        self.setFixedWidth(fixed_width)
        self.resize(fixed_width, current_height)

    def onNewText(self, text):  # noqa
        """Print 文本覆盖写入"""
        cursor = self.ui.MessageBrowser.textCursor()
        cursor.movePosition(QTextCursor.End) # noqa
        self.ui.MessageBrowser.append(text)
        self.ui.MessageBrowser.setTextCursor(cursor)
        self.ui.MessageBrowser.ensureCursorVisible()

    def init_events(self):
        """事件注册"""
        # StartButton
        self.ui.StartButton.clicked.connect(self.startButtonEvent)
        # ExitButton
        self.ui.ExitButton.clicked.connect(self.exitButtonEvent)
        # Lock01
        self.ui.LockCheckBox03.clicked.connect(lambda: self.lockEvent(message='参数', state=self.ui.LockCheckBox03.isChecked(), ui=[self.ui.LineEditIP01, self.ui.LineEditMark01]))
        # Lock02
        self.ui.LockCheckBox04.clicked.connect(lambda: self.lockEvent(message='参数', state=self.ui.LockCheckBox04.isChecked(), ui=[self.ui.LineEditIP02, self.ui.LineEditMark02]))
        # Lock03
        self.ui.LockCheckBox01.clicked.connect(lambda: self.lockEvent(message='参数', state=self.ui.LockCheckBox01.isChecked(), ui=[self.ui.ComboBox01]))
        # Lock04
        self.ui.LockCheckBox02.clicked.connect(lambda: self.lockEvent(message='参数', state=self.ui.LockCheckBox02.isChecked(), ui=[self.ui.ComboBox02]))
        # LockAll
        self.ui.LockAllCheckBox.clicked.connect(self.lockAllEvent)
        # ExportButton
        self.ui.ExportButton01.clicked.connect(lambda: self.exportButtonEvent(0))
        self.ui.ExportButton02.clicked.connect(lambda: self.exportButtonEvent(1))
        # Tag02 Lock
        self.ui.LockCheckBox0201.clicked.connect(lambda: self.lockEvent(message='参数', state=self.ui.LockCheckBox0201.isChecked(), ui=[self.ui.ComboBox0201]))
        self.ui.LockCheckBox0202.clicked.connect(lambda: self.lockEvent(message='参数', state=self.ui.LockCheckBox0202.isChecked(), ui=[self.ui.ComboBox0202]))
        self.ui.LockCheckBox0203.clicked.connect(lambda: self.lockEvent(message='参数', state=self.ui.LockCheckBox0203.isChecked(), ui=[self.ui.LineEditIP0201]))
        self.ui.LockCheckBox0204.clicked.connect(lambda: self.lockEvent(message='参数', state=self.ui.LockCheckBox0204.isChecked(), ui=[self.ui.LineEditIP0202]))
        self.ui.LockCheckBox0205.clicked.connect(lambda:
                                        self.lockEvent(
                                            message='参数',
                                            state=self.ui.LockCheckBox0205.isChecked(),
                                            ui=[
                                                self.ui.LineEditSET301, self.ui.LineEditSET302,
                                                self.ui.LineEditSET303, self.ui.LineEditSET304,
                                                self.ui.LineEditSET305, self.ui.LineEditSET306
                                            ]
                                        ))
        self.ui.OpenButton.clicked.connect(self.fileOpenButtonEvent)
        self.ui.CleanButton.clicked.connect(self.fileCloseButtonEvent)
        # self.ui.ShowButton.clicked.connect(self.showClientButtonEvent)
        self.ui.ShowButton.clicked.connect(self.saveClientEvent)
        self.ui.RegisterButton.clicked.connect(self.registerDialogEvent)
        self.ui.LogoutButton.clicked.connect(self.registerDelete)
        self.ui.LiveButton01.clicked.connect(self.liveComputing)
        self.ui.CBitButton01.clicked.connect(self.cMB2Mbps)
        self.ui.CBitButton02.clicked.connect(self.cMB2Kbps)
        self.ui.CBitButton03.clicked.connect(self.cMbps2MB)
        self.ui.CBitButton04.clicked.connect(self.cMbps2Kbps)
        self.ui.ExportButton03.clicked.connect(self.copyClientEvent)
        self.monitor.data_modified.connect(lambda: self.ui.ListBrowser.setPlainText("\n".join(str(x) for x in self.client_list)))
        self.ui.pushButton0601.clicked.connect(self.mqtt_connect)
        self.ui.pushButton0602.clicked.connect(self.mqtt_subscribe)
        self.ui.pushButton0603.clicked.connect(lambda: self.download_file('uuid.csv'))

    def startButtonEvent(self, checked):  # noqa
        if checked:
            # 获取 Tab
            tab_index = self.ui.TabWidget.currentIndex()
            # 检查工作列表是否空闲
            if self.task_count != 0:
                warning('还有任务未结束，请等待结束后启动。')
                self.ui.StartButton.setChecked(False)
                return 0
            if tab_index == 0:
                self.search_client()
                return 0
            elif tab_index == 1:
                if not self.client_list:
                    warning('设备列表为空，禁止启动。')
                    self.ui.StartButton.setChecked(False)
                    return 0
                self.set_client()
                return 0
            elif tab_index == 2:
                # 使用功能：计算器，功能按钮请见 liveComputing
                info('当前使用功能：计算器')
                info('请使用"开始计算"按钮进行计算')
                self.ui.StartButton.setChecked(False)
                return 0
            elif tab_index == 3:
                if not self.client_list:
                    warning('设备列表为空，禁止启动。')
                    self.ui.StartButton.setChecked(False)
                    return 0
                self.http_send()
                return 0
            elif tab_index == 4:
                self.mqtt_tools()
                return 0
            elif tab_index == 5:
                pass
                return 0
            else:
                self.ui.StartButton.setChecked(False)
                return 0
        else:
            WorkerController.instance().stop_all_workers()
            self.ui.StartButton.setText("Start")
            warning('任务被终止，请等待任务结束。')
            return 0

    def http_send(self):
        info('当前使用功能：请求发送')
        method = self.ui.comboBox0401.currentIndex()
        model = self.ui.comboBox0402.currentIndex()
        api = self.ui.textEdit0402.toPlainText()
        data = self.ui.textEdit0401.toPlainText()
        workers = []
        for ip in self.client_list:
            workers.append(['http', ip, method, api, data])
            self.task_count += 1
        # 计算工作量
        length = len(workers)
        quotient, remainder = divmod(length, 10)
        if quotient == 0:
            tasks = [workers[i:i + 1] for i in range(0, length)]
        elif remainder == 0:
            tasks = [workers[i:i + quotient] for i in range(0, length - remainder, quotient)]
        else:
            x = workers[:-remainder]
            y = workers[:-remainder - 1:-1]
            y.reverse()
            tasks = [x[i:i + quotient] for i in range(0, length - remainder, quotient)]
            f = 0
            while y:
                tasks[f].append(y.pop())
                f += 1
        self.task_count = len(tasks)
        # 分配工作
        for t in tasks:
            worker = WorkerMultiple(self.client.control, iter(t), model)
            worker.connect(self.workerMultipleResultEven, self.workerMultipleFinishEven, self.workerErrorEven)
            self.threadpool.start(worker)
        # 显示进度条
        self.progress_value = 0
        self.ui.ProgressBar.setRange(0, length)
        self.ui.ProgressBar.setValue(0)
        self.ui.ProgressBar.setVisible(True)
        # 切换按钮状态，避免多次点击
        self.ui.StartButton.setText("Abort")
        info(f'任务已启动，请等待运行。')
        return 0

    def search_client(self):
        info('当前使用功能：搜索')
        self.client_temp.clear()
        # 获取数据
        mode = self.ui.ComboBox01.currentIndex()
        mode_name = self.ui.ComboBox01.currentText()
        model = self.ui.ComboBox02.currentIndex()
        model_name = self.ui.ComboBox02.currentText()
        ip01 = self.ui.LineEditIP01.text()
        mark01 = self.ui.LineEditMark01.text()
        ip02 = self.ui.LineEditIP02.text()
        mark02 = self.ui.LineEditMark02.text()
        # 确认参数
        if not (self.ui.LockCheckBox01.isChecked() and self.ui.LockCheckBox02.isChecked()):
            warning('请锁定搜索模式和设备型号。')
            self.ui.StartButton.setChecked(False)
            return 0
        if not (self.ui.LockCheckBox03.isChecked() or self.ui.LockCheckBox04.isChecked()):
            warning('请锁定任一搜索参数。')
            self.ui.StartButton.setChecked(False)
            return 0
        # 执行
        info(f'当前模式：{mode_name}，当前型号：{model_name}')
        progress_range = 0
        # 使用参数 1
        if self.ui.LockCheckBox03.isChecked():
            info(f'使用参数：{ip01}/{mark01}')
            # 计算工作量
            host_islice, host_number = self.workerCount(ip01, mark01)
            progress_range += host_number
            # 分配工作
            for host01 in host_islice:
                worker01 = WorkerMultiple(self.client.search, host01, mode, model)
                worker01.connect(self.workerMultipleResultEven, self.workerMultipleFinishEven, self.workerErrorEven)
                self.threadpool.start(worker01)
                self.task_count += 1
        # 使用参数 2
        if self.ui.LockCheckBox04.isChecked():
            info(f'使用参数：{ip02}/{mark02}')
            # 计算工作量
            host_islice, host_number = self.workerCount(ip02, mark02)
            progress_range += host_number
            # 分配工作
            for host02 in host_islice:
                worker02 = WorkerMultiple(self.client.search, host02, mode, model)
                worker02.connect(self.workerMultipleResultEven, self.workerMultipleFinishEven, self.workerErrorEven)
                self.threadpool.start(worker02)
                self.task_count += 1
        # 显示进度条
        self.progress_value = 0
        self.ui.ProgressBar.setRange(0, progress_range)
        self.ui.ProgressBar.setValue(0)
        self.ui.ProgressBar.setVisible(True)
        # 切换按钮状态，避免多次点击
        self.ui.StartButton.setText("Abort")
        info(f'任务已启动，请等待运行。')
        # info(f'当前可用线程数量：{self.threadpool.maxThreadCount() - self.threadpool.activeThreadCount()}')
        return 0

    def set_client(self):
        info('当前使用功能：批量设置')
        # 参数获取
        model = self.ui.ComboBox0201.currentIndex()
        model_name = self.ui.ComboBox0201.currentText()
        # 参数检查
        if not self.ui.LockCheckBox0201.isChecked():
            warning('请锁定设备型号。')
            self.ui.StartButton.setChecked(False)
            return 0
        if not self.client_list:
            warning('设备列表为空，请导入设备。')
            self.ui.StartButton.setChecked(False)
            return 0
        info(f'当前型号：{model_name}')
        workers = []
        # 功能确认
        if self.ui.LockCheckBox0203.isChecked():
            data = self.ui.LineEditIP0201.text()
            for ip in self.client_list:
                workers.append(['set', 0, ip, [data]])
                self.task_count += 1
        if self.ui.LockCheckBox0204.isChecked():
            data = self.ui.LineEditIP0202.text()
            for ip in self.client_list:
                workers.append(['set', 1, ip, [data]])
                self.task_count += 1
        if self.ui.LockCheckBox0205.isChecked():
            data = [self.ui.LineEditSET304.text(), self.ui.LineEditSET305.text(),
                    self.ui.LineEditSET306.text(), self.ui.LineEditSET301.text(),
                    self.ui.LineEditSET302.text(), self.ui.LineEditSET303.text(),
                    self.ui.LockCheckBox0205x2.isChecked()]
            for ip in self.client_list:
                workers.append(['set', 2, ip, data])  # 此处的 data 是列表
                self.task_count += 1
        if self.ui.LockCheckBox0202.isChecked():
            flag = self.ui.ComboBox0202.currentIndex()
            for ip in self.client_list:
                workers.append(['work', flag, ip])
                self.task_count += 1
        if self.task_count == 0:
            info('请选择功能。')
            self.ui.StartButton.setChecked(False)
            return 0
        # 计算工作量
        length = len(workers)
        quotient, remainder = divmod(length, 10)
        if quotient == 0:
            tasks = [workers[i:i + 1] for i in range(0, length)]
        elif remainder == 0:
            tasks = [workers[i:i + quotient] for i in range(0, length - remainder, quotient)]
        else:
            x = workers[:-remainder]
            y = workers[:-remainder - 1:-1]
            y.reverse()
            tasks = [x[i:i + quotient] for i in range(0, length - remainder, quotient)]
            f = 0
            while y:
                tasks[f].append(y.pop())
                f += 1
        self.task_count = len(tasks)
        # 分配工作
        for t in tasks:
            worker = WorkerMultiple(self.client.control, iter(t), model)
            worker.connect(self.workerMultipleResultEven, self.workerMultipleFinishEven, self.workerErrorEven)
            self.threadpool.start(worker)
        # 显示进度条
        self.progress_value = 0
        self.ui.ProgressBar.setRange(0, length)
        self.ui.ProgressBar.setValue(0)
        self.ui.ProgressBar.setVisible(True)
        # 切换按钮状态，避免多次点击
        self.ui.StartButton.setText("Abort")
        info(f'任务已启动，请等待运行。')
        # info(f'当前可用线程数量：{self.threadpool.maxThreadCount() - self.threadpool.activeThreadCount()}')
        return 0

    @staticmethod
    def workerCount(ip, mark):
        """工作量计算"""
        cidr = f'{ip}/{mark}'
        network = ipaddress.IPv4Network(cidr, strict=False)
        # network_address = network.network_address
        # broadcast_address = network.broadcast_address
        host_address = network.hosts()
        host_number = network.num_addresses - 2
        host_gen = iter(host_address)
        host_islice = [islice(host_gen, i, i + host_number // 5 + (1 if i < host_number % 5 else 0)) for i in range(5)]
        return host_islice, host_number

    @staticmethod
    def workerErrorEven(s):
        """worker错误事件处理"""
        error(s)

    def workerMultipleResultEven(self, s):
        """worker批量事件结果处理"""
        if s == 0:
            self.progress_value += 1
            self.ui.ProgressBar.setValue(self.progress_value)
            return 0
        try:
            # 尝试将字符串解析为 IPv4 或 IPv6 地址
            ip = ipaddress.ip_address(s)
            self.client_temp.append(ip)
            success(f'<span>IP：</span><a style="color: #0066cc" href="http://{ip}">{ip}</a>')
        except ValueError:
            success(s)
        finally:
            self.progress_value += 1
            self.ui.ProgressBar.setValue(self.progress_value)
        return None

    def workerMultipleFinishEven(self):
        """worker批量事件完成处理"""
        self.completed_tasks += 1
        if self.completed_tasks == self.task_count:
            self.completed_tasks = 0
            self.task_count = 0
            self.ui.StartButton.setText("Start")
            self.ui.StartButton.setChecked(False)
            self.ui.ProgressBar.setVisible(False)
            info(f'任务已全部结束。')
            # info(f'当前设备列表数量：{len(self.client_list)}')

    @staticmethod
    def workerSingleResultEven(s):
        success(s) if s != 0 else 0

    def workerSingleFinishEven(self):
        self.completed_tasks += 1
        if self.completed_tasks == self.task_count:
            self.completed_tasks = 0
            self.task_count = 0
            info(f'任务已完成。')

    def exitButtonEvent(self):  # noqa 此处必须带 self
        if self.emqx_worker:
            self.emqx_worker.stop()
        sys.exit()

    @staticmethod
    def lockEvent(message: str, state: bool, ui: list[QLineEdit | QComboBox]):
        if state:
            for each in ui:
                each.setEnabled(False)
            info(f'{message}，已被锁定。')
        else:
            for each in ui:
                each.setEnabled(True)
            info(f'{message}，已被解锁。')

    def lockAllEvent(self):
        state = self.ui.LockAllCheckBox.isChecked()
        locks = [self.ui.LockCheckBox01, self.ui.LockCheckBox02, self.ui.LockCheckBox03, self.ui.LockCheckBox04]
        objs = [self.ui.LineEditIP01, self.ui.LineEditIP02,
                self.ui.LineEditMark01, self.ui.LineEditMark02,
                self.ui.ComboBox01, self.ui.ComboBox02]
        if state:
            for lock in locks:
                lock.setChecked(True)
            for obj in objs:
                obj.setEnabled(False)
            info('所有设置已被锁定。')
        else:
            for lock in locks:
                lock.setChecked(False)
            for obj in objs:
                obj.setEnabled(True)
            info('所有设置已被解锁。')

    def exportButtonEvent(self, flag):
        # 获取参数
        self.task_count += 1
        model = self.ui.ComboBox02.currentIndex()
        # 分配工作
        if flag == 0:
            info('当前使用功能：导出 TXT')
            worker = WorkerSingle(self.client.export, self.client_temp, model, 0)
        else:
            info('当前使用功能：导出 CSV')
            worker = WorkerSingle(self.client.export, self.client_temp, model, 1)
        worker.connect(self.workerSingleResultEven, self.workerSingleFinishEven, self.workerErrorEven)
        self.threadpool.start(worker)

    def fileOpenButtonEvent(self):
        file_path = QFileDialog.getOpenFileName(self.ui.QMainWidget, '请选择文件', '.', '文件类型 (*.txt *.csv)')
        if file_path[0]:
            info(file_path[0])
            file_type = file_path[0].split('.')[-1]
            if file_type == 'txt':
                with open(file_path[0], mode='r', encoding='utf-8') as file:
                    temp = file.readlines()
                # 检查 IP 格式
                for ip in temp:
                    try:
                        ip = ip.replace('\n', '').strip()
                        ipaddress.ip_address(ip)
                        if ip not in self.client_list:
                            self.client_list.append(ip)
                    except ValueError:
                        warning('文件格式错误，请检查文件。')
                        break
                success('导入成功')
            elif file_type == 'csv':
                with open(file_path[0], mode='r', encoding='utf-8') as file:
                    temp = csv.DictReader(file)
                    for row in temp:
                        try:
                            ip = row['ip']
                            ip = ip.replace('\n', '').strip()
                            ipaddress.ip_address(ip)
                            if ip not in self.client_list:
                                self.client_list.append(ip)
                            self.client_uuid[ip] = row['uuid']
                        except ValueError:
                            warning('文件格式错误，请检查文件。')
                            break
                success('导入成功')
            else:
                warning('文件类型错误，请检查文件。')
            success(f'当前设备列表数量为：{len(self.client_list)}')
        else:
            warning('没有文件可以打开。')

    def fileCloseButtonEvent(self):
        self.client_list.clear()
        success('设备列表已清空。')

    def showClientButtonEvent(self):
        info('开始打印设备列表。')
        for ip in self.client_list:
            info(f'<a style="color: #0066cc" href="http://{ip}">{ip}</a>')
        success('设备列表已打印完成。')

    def copyClientEvent(self):
        for each in self.client_temp:
            if each not in self.client_list:
                self.client_list.append(each)
        success('结果已复制到列表。')

    def saveClientEvent(self):
        data = self.ui.ListBrowser.toPlainText()
        lines = [line.strip() for line in data.split('\n') if line.strip()]
        result = []
        for each in lines:
            if each in self.client_list:
                continue
            try:
                ipaddress.ip_address(each)
                result.append(each)
            except ValueError:
                continue
        self.client_list += list(set(result))
        self.ui.ListBrowser.setPlainText("\n".join(str(x) for x in self.client_list))
        success('输入内容已保存到列表。')
        success(f'当前列表数量：{len(self.client_list)}')

    def check(self):
        if not self.client.check():
            error('未找到注册文件，请进行注册。')
            self.ui.TabWidget.setEnabled(False)
            buttons = [self.ui.StartButton, self.ui.ExitButton,
                       self.ui.OpenButton, self.ui.CleanButton,
                       self.ui.ShowButton]
            for each in buttons:
                each.setEnabled(False)
        else:
            success(f'当前日期：{datetime.now().strftime("%Y-%m-%d")}')
            success('欢迎使用 My Tools Box 工具。')

    def registerDialogEvent(self):
        dialog = RegisterDialog()
        dialog.dataSend.connect(self.register)
        dialog.exec()

    def register(self, s):
        if self.client.register(s):
            success('注册成功，请重启程序。')
        else:
            error('注册失败')

    def registerDelete(self):
        if self.client.logout():
            success('注册信息已清除，请重启程序。')
        else:
            error('清除失败。')

    def liveComputing(self):
        live_bitrate = self.ui.LineEditLive01.text()
        live_duration = self.ui.LineEditLive02.text()
        live_member = self.ui.LineEditLive03.text()
        live_cost = self.ui.LineEditLive04.text()
        self.task_count += 1
        worker = WorkerSingle(self.client.live_compute, live_bitrate, live_duration, live_member, live_cost)
        worker.connect(self.workerSingleResultEven, self.workerSingleFinishEven, self.workerErrorEven)
        self.threadpool.start(worker)

    def cMB2Mbps(self):
        data = self.ui.LineEditBit01.text()
        self.task_count += 1
        worker = WorkerSingle(self.client.conversion_MB2, 0, data)
        worker.connect(self.workerSingleResultEven, self.workerSingleFinishEven, self.workerErrorEven)
        self.threadpool.start(worker)

    def cMB2Kbps(self):
        data = self.ui.LineEditBit01.text()
        self.task_count += 1
        worker = WorkerSingle(self.client.conversion_MB2, 1, data)
        worker.connect(self.workerSingleResultEven, self.workerSingleFinishEven, self.workerErrorEven)
        self.threadpool.start(worker)

    def cMbps2MB(self):
        data = self.ui.LineEditBit02.text()
        self.task_count += 1
        worker = WorkerSingle(self.client.conversion_Mbps2, 0, data)
        worker.connect(self.workerSingleResultEven, self.workerSingleFinishEven, self.workerErrorEven)
        self.threadpool.start(worker)

    def cMbps2Kbps(self):
        data = self.ui.LineEditBit02.text()
        self.task_count += 1
        worker = WorkerSingle(self.client.conversion_Mbps2, 1, data)
        worker.connect(self.workerSingleResultEven, self.workerSingleFinishEven, self.workerErrorEven)
        self.threadpool.start(worker)

    def mqtt_tools(self):
        if not self.emqx_worker:
            error('请先连接 MQTT 服务器！')
            self.ui.StartButton.setChecked(False)
            return 0
        if self.ui.checkBox0601.isChecked():
            # 切换按钮状态，避免多次点击
            self.ui.StartButton.setText("Abort")
            info(f'任务已启动，请等待运行。')
            # 单台测试
            topic = self.ui.lineEdit0601.text()
            message = self.ui.textEdit0601.toPlainText()
            message = json.loads(message)
            message = json.dumps(message)
            self.task_count += 1
            self.emqx_worker.publish(topic, message)
            return 0
        else:
            # 切换按钮状态，避免多次点击
            self.ui.StartButton.setText("Abort")
            info(f'任务已启动，请等待运行。')
            # 批量发送
            for key, value in self.client_uuid.items():
                self.task_count += 1
                topic = self.ui.lineEdit0601.text() + value
                message = self.ui.textEdit0601.toPlainText()
                message = json.loads(message)
                message = json.dumps(message)
                self.emqx_worker.publish(topic, message)
            return 0

    def mqtt_subscribe(self):
        if not self.emqx_worker:
            error('请先连接 MQTT 服务器！')
            return 0
        topic = self.ui.lineEdit0601.text()
        self.emqx_worker.subscribe(topic)
        return 0

    def mqtt_connect(self, checked):
        if checked:
            info('连接中...')
            broker_host = self.ui.lineEdit0602.text()
            broker_port = int(self.ui.lineEdit0605.text())
            broker_username = self.ui.lineEdit0603.text() or "Client"
            broker_password = self.ui.lineEdit0604.text() or None
            # 执行 mqtt 连接
            self.emqx_worker = EMQXWorker(
                broker_host=broker_host,
                broker_port=broker_port,
                username=broker_username,
                password=broker_password
            )
            # 连接信号
            self.emqx_worker.signals.connected.connect(self.on_connected)
            self.emqx_worker.signals.disconnected.connect(self.on_disconnected)
            self.emqx_worker.signals.message_received.connect(self.on_message_received)
            self.emqx_worker.signals.message_publish.connect(self.on_message_publish)
            self.emqx_worker.signals.error_occurred.connect(self.on_error)
            self.emqx_worker.signals.connect_fail.connect(self.on_connect_fail)
            # 启动线程
            self.threadpool.start(self.emqx_worker)
            info("正在连接 EMQX Broker...")
            return 0
        else:
            info('关闭中...')
            # 断开连接
            if self.emqx_worker:
                self.emqx_worker.stop()
                self.emqx_worker = None
            success('关闭成功')
            self.ui.pushButton0601.setText("连接")
            return 0

    def on_connected(self):
        """连接成功回调"""
        self.ui.pushButton0601.setText("关闭连接")
        success("成功连接到 EMQX Broker")

    @staticmethod
    def on_disconnected():
        """断开连接回调"""
        warning("与 EMQX Broker 断开连接")

    @staticmethod
    def on_message_received(topic, message):
        """消息接收回调"""
        success(f"收到消息 [{topic}]: {message}")

    def on_message_publish(self, topic, message):
        """消息发送回调"""
        self.task_count -= 1
        if self.task_count == 0:
            self.ui.StartButton.setText("Start")
            self.ui.StartButton.setChecked(False)
        success(f"发送消息 [{topic}]: {message}")

    @staticmethod
    def on_error(error_msg):
        """错误回调"""
        error(error_msg)

    def on_connect_fail(self, error_msg):
        """错误回调"""
        self.ui.pushButton0601.setChecked(False)
        error(error_msg)
        self.emqx_worker = None

    def download_file(self, filename):
        """处理下载按钮点击事件，将嵌入的文件保存到用户指定位置"""
        # 弹出文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存文件",
            filename,  # 默认文件名
            "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'wb') as f:
                    qfile = QFile(u":/file/resources/uuid.csv")
                    if not qfile.open(QIODevice.ReadOnly):  # noqa
                        error(f"无法打开资源文件: {qfile.errorString()}")
                    buffer_size = 1024 * 1024  # 1MB缓冲区
                    while not qfile.atEnd():
                        chunk = qfile.read(buffer_size)
                        # 处理数据块
                        f.write(chunk.data())
                    qfile.close()
                success("文件已成功保存")
            except Exception as e:
                error(f"保存文件时出错：{str(e)}")

if __name__ == "__main__":

    if "NUITKA_ONEFILE_PARENT" in os.environ:
        splash_filename = os.path.join(
            tempfile.gettempdir(),
            "onefile_%d_splash_feedback.tmp" % int(os.environ["NUITKA_ONEFILE_PARENT"]),
        )
        if os.path.exists(splash_filename):
            os.unlink(splash_filename)

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
