import os
import logging

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QStyle, QApplication, QDesktopWidget
from PyQt5.QtGui import QIcon

logging.basicConfig(filename="debug.log", format='%(asctime)s %(name)s %(levelname)s %(message)s')
logging.getLogger().setLevel(logging.DEBUG)


class Window(QtWidgets.QWidget):
    def __init__(self, directory):
        super().__init__()

        ui_path = os.path.join(os.path.dirname(__file__), 'form.ui')
        uic.loadUi(ui_path, self)

        self.nickname = ''
        self.directory = directory
        self.selected_files = []

        # center window on screen
        qt_rectangle = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        qt_rectangle.moveCenter(center_point)
        self.move(qt_rectangle.topLeft())

        # populate list with files and subdirectories from directory
        self.populate_files()

        # connect push buttons to methods
        self.pushButton_submit.clicked.connect(self.submit)
        self.pushButton_cancel.clicked.connect(self.cancel)

    def populate_files(self):

        def alpha_and_folder(item):
            return os.path.isfile(os.path.join(self.directory, item)), item.lower()

        # sort the files/subdirectories alphabetically and by item type (file v. folder)
        sorted_directory = sorted(os.listdir(self.directory), key=alpha_and_folder)

        # add each file and subdirectory to the list widget
        for each in sorted_directory:
            list_item = QtWidgets.QListWidgetItem()
            if os.path.isfile(os.path.join(self.directory, each)):
                list_item.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_FileIcon)))
                list_item.setData(QtCore.Qt.UserRole, "file")
            elif os.path.isdir(os.path.join(self.directory, each)):
                list_item.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_DirIcon)))
                list_item.setData(QtCore.Qt.UserRole, "subdirectory")
            else:
                continue
            list_item.setText(each)
            list_item.setFlags(list_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            list_item.setCheckState(QtCore.Qt.Checked)
            self.listWidget_files.addItem(list_item)

    def submit(self):
        selected_subdirectories = []

        # add selected files to self.selected_files and create list of selected subdirectories
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
        self.nickname = self.plainTextEdit_nickname.toPlainText()

        # close window
        self.close()

    def add_subdirectory_files(self, subdirectory):
        # adds files from subdirectory to self.selected_files
        for each in os.listdir(os.path.join(os.path.dirname(self.directory), subdirectory)):
            if os.path.isfile(os.path.join(os.path.dirname(self.directory), subdirectory, each)):
                self.selected_files.append(f'{subdirectory}/{each}')
            elif os.path.isdir(os.path.join(os.path.dirname(self.directory), subdirectory, each)):
                self.add_subdirectory_files(f'{subdirectory}/{each}')

    def cancel(self):
        self.close()


def run_file_selector(directory):
    app = QtWidgets.QApplication([])
    widget = Window(directory)
    widget.show()
    app.exec_()
    return widget.nickname, widget.selected_files
