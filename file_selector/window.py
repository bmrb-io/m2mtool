import os

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QStyle, QApplication, QDesktopWidget
from PyQt5.QtGui import QIcon


class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        ui_path = os.path.join(os.path.dirname(__file__), 'form.ui')
        uic.loadUi(ui_path, self)

        # center window on screen
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        # populate list with files and subfolders from directory
        test_directory = "/home/nmrbox/0015/jchin/Qt5.12.10/"
        self.populate_files(test_directory)

        # connect push buttons to methods
        self.pushButton_submit.clicked.connect(self.submit)
        self.pushButton_cancel.clicked.connect(self.cancel)

    def populate_files(self, directory):
        subfolders = [s for s in os.listdir(directory) if os.path.isdir(os.path.join(directory, s))]
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

        for subfolder in subfolders:
            item = QtWidgets.QListWidgetItem()
            item.setText(subfolder)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked)
            icon = QIcon(QApplication.style().standardIcon(QStyle.SP_DirIcon))
            item.setIcon(icon)
            self.listWidget_files.addItem(item)

        for file in files:
            item = QtWidgets.QListWidgetItem()
            item.setText(file)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked)
            icon = QIcon(QApplication.style().standardIcon(QStyle.SP_FileIcon))
            item.setIcon(icon)
            self.listWidget_files.addItem(item)

        # files = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f)) or
        # os.path.isfile(os.path.join(directory, f))]
        #
        # for file in files:
        #     item = QtWidgets.QListWidgetItem()
        #     item.setText(file)
        #     item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        #     item.setCheckState(QtCore.Qt.Checked)
        #     if os.path.isfile(os.path.join(directory, file)):
        #         icon = QIcon(QApplication.style().standardIcon(QStyle.SP_FileIcon))
        #     elif os.path.isdir(os.path.join(directory, file)):
        #         icon = QIcon(QApplication.style().standardIcon(QStyle.SP_DirIcon))
        #     item.setIcon(icon)
        #     self.listWidget_files.addItem(item)

    def submit(self):
        pass

    def cancel(self):
        self.close()