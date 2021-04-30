import os

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QStyle, QApplication, QDesktopWidget
from PyQt5.QtGui import QIcon


class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        ui_path = os.path.join(os.path.dirname(__file__), 'form.ui')
        uic.loadUi(ui_path, self)

        # TODO: add code to assign self.directory
        test_directory = "/home/nmrbox/0015/jchin/Qt5.12.10/"

        self.directory = test_directory
        self.selected_files = []

        # center window on screen
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        # populate list with files and subfolders from directory
        self.populate_files()

        # connect push buttons to methods
        self.pushButton_submit.clicked.connect(self.submit)
        self.pushButton_cancel.clicked.connect(self.cancel)

    def populate_files(self):
        # search self.directory and create separate lists for subdirectories and files
        subdirectories = [s for s in os.listdir(self.directory) if os.path.isdir(os.path.join(self.directory, s))]
        files = [f for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]

        # add subdirectories to listWidget
        for subdirectory in subdirectories:
            item = QtWidgets.QListWidgetItem()
            item.setText(subdirectory)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked)
            item.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_DirIcon)))
            item.setData(QtCore.Qt.UserRole, "subdirectory")
            self.listWidget_files.addItem(item)

        # add files to listWidget
        for file in files:
            item = QtWidgets.QListWidgetItem()
            item.setText(file)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked)
            item.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_FileIcon)))
            item.setData(QtCore.Qt.UserRole, "file")
            self.listWidget_files.addItem(item)

        # files_and_subdirectories = [f for f in os.listdir(self.directory) if
        #                         os.path.isdir(os.path.join(self.directory, f)) or
        #                         os.path.isfile(os.path.join(self.directory, f))]
        #
        # for each in files_and_subdirectories:
        #     item = QtWidgets.QListWidgetItem()
        #     item.setText(each)
        #     item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        #     item.setCheckState(QtCore.Qt.Checked)
        #     if os.path.isfile(os.path.join(self.directory, each)):
        #         item.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_FileIcon)))
        #         item.setData(QtCore.Qt.UserRole, "file")
        #     elif os.path.isdir(os.path.join(self.directory, each)):
        #         item.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_DirIcon)))
        #         item.setData(QtCore.Qt.UserRole, "subdirectory")
        #     self.listWidget_files.addItem(item)

    def submit(self):
        selected_subdirectories = []

        # add selected files to selected_files list and make list of selected subdirectories
        for index in range(self.listWidget_files.count()):
            if self.listWidget_files.item(index).checkState() == QtCore.Qt.Checked:
                if self.listWidget_files.item(index).data(QtCore.Qt.UserRole) == "file":
                    self.selected_files.append(self.listWidget_files.item(index).text())
                elif self.listWidget_files.item(index).data(QtCore.Qt.UserRole) == "subdirectory":
                    selected_subdirectories.append(self.listWidget_files.item(index).text())

        # recursively add files from selected subdirectories to selected_files list
        for subdir in selected_subdirectories:
            self.add_subdirectory_files(subdir)

        # retrieve deposition nickname
        nickname = self.plainTextEdit_nickname.toPlainText()

        # TODO: pass self.selected_files, nickname to api

    def add_subdirectory_files(self, subdirectory):
        for each in os.listdir(os.path.join(os.path.dirname(self.directory), subdirectory)):
            if os.path.isfile(os.path.join(os.path.dirname(self.directory), subdirectory, each)):
                self.selected_files.append(f'{subdirectory}/{each}')
            elif os.path.isdir(os.path.join(os.path.dirname(self.directory), subdirectory, each)):
                self.add_subdirectory_files(f'{subdirectory}/{each}')

    def cancel(self):
        self.close()
