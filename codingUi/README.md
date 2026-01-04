# README

## 警告！

由于该文件使用代码自动生成，因此存在代码错误需要手动修改。

1.请在`__init__.py`文件中写入 UI Class 类代码。

```python
from .QMainWindow import Ui_QMainWindow
from .QDialog import Ui_Dialog
```

2.如果 UI 有使用外部资源，请手动修正资源文件的导入路径。

`import IconRc_rc` > `from codingQrc import IconRc`
