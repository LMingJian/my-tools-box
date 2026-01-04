import time
import traceback
from paho.mqtt import client as mqtt
from PySide6.QtCore import QObject, Signal, QRunnable, QMutex, Slot, QMutexLocker


class WorkerSignals(QObject):
    """信号"""
    finished = Signal()  # QtCore.Signal
    result = Signal(object)
    error = Signal(tuple)


class WorkerSingle(QRunnable):
    """单个工作处理"""
    def __init__(self, fn, *args, **kwargs):
        super(WorkerSingle, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.mutex = QMutex()

    def connect(self, fn_result, fn_finish, fn_error):
        """事件绑定"""
        self.signals.result.connect(fn_result)
        self.signals.finished.connect(fn_finish)
        self.signals.error.connect(fn_error)

    @Slot()
    def run(self):
        try:
            with QMutexLocker(self.mutex):
                result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit((type(e), str(e), traceback.format_exc()))
        finally:
            time.sleep(0.3)  # 显示等待，避免 result 信号和 finish 信号过快发送导致 finish 连接的事件处理过快出现
            self.signals.finished.emit()


class WorkerController(QObject):
    """全局工作控制器"""
    _instance = None
    stop_all_signal = Signal()  # 全局停止信号‌

    def __init__(self):
        super().__init__()
        self.workers = []  # 已注册的工作器实例
        self.mutex = QMutex()  # 保护 workers 列表的线程安全‌

    @classmethod
    def instance(cls):
        """单例模式获取控制器实例‌"""
        if not cls._instance:
            cls._instance = WorkerController()
        return cls._instance

    def register_worker(self, worker):
        """注册工作器并连接停止信号"""
        with QMutexLocker(self.mutex):
            self.workers.append(worker)
            self.stop_all_signal.connect(worker.stop)

    def unregister_worker(self, worker):
        """注销工作器"""
        with QMutexLocker(self.mutex):
            if worker in self.workers:
                self.workers.remove(worker)

    def stop_all_workers(self):
        """触发全部工作器停止"""
        self.stop_all_signal.emit()  # 发射全局停止信号‌


class WorkerMultiple(QRunnable):
    """多个工作处理"""
    def __init__(self, fn, iterators, *args, **kwargs):
        super(WorkerMultiple, self).__init__()
        self.fn = fn
        self.iterators = iterators
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.mutex = QMutex()
        self._stop_flag = False
        self.controller = WorkerController.instance()  # 获取控制器单例‌
        self.controller.register_worker(self)  # 自动注册

    def stop(self):
        """响应停止信号"""
        if not self._stop_flag:  # 快速检查
            with QMutexLocker(self.mutex):
                self._stop_flag = True

    def connect(self, fn_result, fn_finish, fn_error):
        """事件绑定"""
        self.signals.result.connect(fn_result)
        self.signals.finished.connect(fn_finish)
        self.signals.error.connect(fn_error)

    @Slot()
    def run(self):
        try:
            while not self._stop_flag:
                with QMutexLocker(self.mutex):
                    iterator = next(self.iterators)
                result = self.fn(iterator, *self.args, **self.kwargs)
                self.signals.result.emit(result)
        except StopIteration:
            pass
        except Exception as e:
            self.signals.error.emit((type(e), str(e), traceback.format_exc()))
        finally:
            time.sleep(0.3)  # 显示等待，避免数据串位
            self.signals.finished.emit()
            self.controller.unregister_worker(self)

class EMQXSignals(QObject):
    """定义线程信号"""
    connected = Signal()
    disconnected = Signal()
    message_received = Signal(str, str)  # topic, message
    message_publish = Signal(str, str)  # topic, message
    error_occurred = Signal(str)
    connect_fail = Signal(str)


class EMQXWorker(QRunnable):
    """EMQX 连接工作线程"""

    def __init__(self, broker_host="broker.emqx.io", broker_port=1883,
                 client_id="", username=None, password=None):
        super().__init__()
        self.signals = EMQXSignals()
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id or f"client_{int(time.time())}"
        self.username = username
        self.password = password
        self.client = None
        self.is_connected = False
        self.setAutoDelete(True)

    def run(self):
        """线程执行函数"""
        try:
            self.client = mqtt.Client(client_id=self.client_id)
            # 设置回调函数
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            # 连接服务器
            self.client.username_pw_set(self.username, self.password)
            self.client.connect(self.broker_host, self.broker_port, 60)
            # 启动网络循环
            self.client.loop_forever()
        except Exception as e:
            self.signals.connect_fail.emit(f"连接失败: {str(e)}")

    def _on_connect(self, client, userdata, flags, rc):  # noqa
        """连接回调"""
        if rc == 0:
            self.is_connected = True
            self.signals.connected.emit()
        else:
            error_msg = f"连接失败，返回码: {rc}"
            self.signals.connect_fail.emit(error_msg)

    def _on_disconnect(self, client, userdata, rc):  # noqa
        """断开连接回调"""
        self.is_connected = False
        self.signals.disconnected.emit()
        if rc != 0:
            self.signals.error_occurred.emit(f"连接意外断开")

    def _on_message(self, client, userdata, msg):  # noqa
        """消息接收回调"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            self.signals.message_received.emit(topic, payload)
        except Exception as e:
            self.signals.error_occurred.emit(f"消息处理错误: {str(e)}")

    def subscribe(self, topic, qos=0):  # noqa
        """订阅主题"""
        if self.is_connected and self.client:
            self.client.subscribe(topic, qos)
            self.signals.message_received.emit(topic, 'subscribe success')

    def publish(self, topic, message, qos=0):  # noqa
        """发布消息"""
        if self.is_connected and self.client:
            self.client.publish(topic, message, qos)
            self.signals.message_publish.emit(topic, message)

    def stop(self):
        """停止连接"""
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
