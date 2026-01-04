# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'QDialog.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)
from codingQrc import IconRc

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(400, 117)
        Dialog.setMinimumSize(QSize(400, 117))
        Dialog.setMaximumSize(QSize(400, 117))
        icon = QIcon()
        icon.addFile(u":/logo/resources/toolboxs.ico", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        Dialog.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_1 = QHBoxLayout()
        self.horizontalLayout_1.setObjectName(u"horizontalLayout_1")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        self.label.setFont(font)

        self.horizontalLayout_1.addWidget(self.label)


        self.verticalLayout.addLayout(self.horizontalLayout_1)

        self.lineEdit = QLineEdit(Dialog)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setMinimumSize(QSize(0, 35))
        font1 = QFont()
        font1.setPointSize(15)
        self.lineEdit.setFont(font1)
        self.lineEdit.setEchoMode(QLineEdit.EchoMode.Password)

        self.verticalLayout.addWidget(self.lineEdit)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.Btn02 = QPushButton(Dialog)
        self.Btn02.setObjectName(u"Btn02")

        self.horizontalLayout_2.addWidget(self.Btn02)

        self.Btn01 = QPushButton(Dialog)
        self.Btn01.setObjectName(u"Btn01")

        self.horizontalLayout_2.addWidget(self.Btn01)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"\u7a0b\u5e8f\u6ce8\u518c", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"\u6ce8\u518c\u7801", None))
        self.lineEdit.setText("")
        self.Btn02.setText(QCoreApplication.translate("Dialog", u"\u786e\u8ba4", None))
        self.Btn01.setText(QCoreApplication.translate("Dialog", u"\u53d6\u6d88", None))
    # retranslateUi

