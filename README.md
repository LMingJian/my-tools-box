# My Tools Box — 工具箱

@LiangMingJian 2026-01-05

## 1.概述

该项目的本体是工作中编写的一个工具箱软件，在这里移除敏感信息后做存档作用使用。

该项目本体设计之初的功能是为了搜索公司生产的一系列物联设备，并支持进行批量控制。

在编写之初，搜索与控制的实现通过 HTTP API 接口完成。 在后续，随着技术发展，引入了 MQTT 批量发送功能，协同 HTTP API 完成物联设备的批量控制。


## 2.实现功能

- 软件注册（123456）
- 设备搜索（支持搜索后保存到软件列表，支持导出）
- 设备批量控制（支持使用软件保存的列表进行批量控制，支持导入设备IP列表）
- 直播带宽计算器
- 设备接口批量控制（支持使用软件保存的列表进行批量HTTP请求发送）
- 设备 MQTT 批量控制（支持使用软件保存的列表进行批量主题订阅（主题/UUID），向批量主题发送，支持向单个主题发送）

## 3.图例

![img_0.png](images/img_0.png)

![img_1.png](images/img_1.png)

![img_2.png](images/img_2.png)

![img_3.png](images/img_3.png)

![img_4.png](images/img_4.png)

![img_5.png](images/img_5.png)

## 4.项目配置

Python 版本建议 3.10，建议通过 Pycharm 创建 venv 虚拟环境进行开发。

### 文件结构

- main.py：主程序文件
- resources：资源文件
- function：功能程序文件
- designerUi, designerQrc：QtDesigner 设计文件
- codingUi, codingQrc：界面代码文件

### QtDesigner

程序路径

```
.venv\Lib\site-packages\PySide6\designer.exe
```

工作目录

```
$FileDir$
```

### pyside6-uic

程序路径

```
.venv\Scripts\pyside6-uic.exe
```

实参

```
$FileName$ -o $FileNameWithoutExtension$.py
```

工作目录

```
$FileDir$
```

### pyside6-rcc

程序路径

```
.venv\Scripts\pyside6-uic.exe
```

实参

```
$FileName$ -o $FileNameWithoutExtension$_rc.py
```

工作目录

```
$FileDir$
```

## 5.项目打包

本项目通过 nuitka 进行打包，参考文档：[ Nuitka User Manual ](https://nuitka.net/user-documentation/user-manual.html#nuitka-requirements)

```
python -m nuitka --onefile --standalone `
--windows-icon-from-ico=resources/toolboxs.ico `
--copyright=LL@LMingJian --product-name=MyToolsBox `
--file-version=1.0 --file-description=MyToolsBox `
--enable-plugin=pyside6 --windows-console-mode=disable `
--output-filename=MyToolsBox.exe `
--onefile-windows-splash-screen-image=resources/toolboxs.png main.py
```

正常情况下，在执行上述命令时，程序会自动下载所需的依赖包，但某些时候，受限于网络环境，可能下载失败，此时可以手动下载然后再把包导入。

下载：[ winlibs-x86_64-posix-seh-gcc-13.2.0 ](https://github.com/brechtsanders/winlibs_mingw/releases/download/13.2.0-16.0.6-11.0.1-msvcrt-r1/winlibs-x86_64-posix-seh-gcc-13.2.0-llvm-16.0.6-mingw-w64msvcrt-11.0.1-r1.zip)

目标路径：

```
%USERPROFILE%\AppData\Local\Nuitka\Nuitka\Cache\DOWNLO~1\gcc\x86_64\13.2.0-16.0.6-11.0.1-msvcrt-r1\
```

下载：[ depends22_x64 ](https://dependencywalker.com/depends22_x64.zip)

目标路径：

```
%USERPROFILE%\AppData\Local\Nuitka\Nuitka\Cache\DOWNLO~1\depends\x86_64
```
