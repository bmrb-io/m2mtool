import os
import sys
import logging
from typing import List, Tuple

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QStyle, QApplication, QDesktopWidget, QMessageBox
from PyQt5.QtGui import QIcon, QColor

logging.basicConfig()


class FileSelector(QtWidgets.QWidget):
    def __init__(self, directory: str):
        super().__init__()

        ui_path = os.path.join(os.path.dirname(__file__), 'selector.ui')
        uic.loadUi(ui_path, self)

        self.nickname: str = ''
        self.directory: str = directory
        self.selected_files: List[str] = []
        self.select_submitted: bool = False
        self.flag: bool = False
        self.warning: bool = False

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

        # show warning if there are any files/folders which user does not have permission to upload
        if self.warning:
            self.show_warning_msg()

    def populate_files(self) -> None:

        def alpha_and_folder(item) -> Tuple[bool, str]:
            # sort by item type (folder vs file) and alphabetically
            return os.path.isfile(os.path.join(self.directory, item)), item.lower()

        def set_prohibited_item(prohibited_item: QtWidgets.QListWidgetItem, item_type: str) -> None:
            # add list item that user does not have permission to upload
            prohibited_item.setText(f'{each} ⚠️')
            prohibited_item.setForeground(QColor(255, 0, 0))
            prohibited_item.setToolTip(f'You do not have permission to upload this {item_type}')
            prohibited_item.setFlags(list_item.flags() & ~QtCore.Qt.ItemIsUserCheckable)
            prohibited_item.setCheckState(QtCore.Qt.Unchecked)

        def set_permitted_item(permitted_item: QtWidgets.QListWidgetItem, item_type: str) -> None:
            # add list item that user does have permission to upload
            permitted_item.setText(each)
            permitted_item.setData(QtCore.Qt.UserRole, item_type)
            permitted_item.setFlags(list_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            permitted_item.setCheckState(QtCore.Qt.Checked)

        def set_restricted_item(restricted_item: QtWidgets.QListWidgetItem) -> None:
            # add list item (only applies to subdirectories, not files) that user does have full access to
            restricted_item.setText(f'{each} ⚠️')
            restricted_item.setForeground(QColor(255, 130, 0))
            restricted_item.setToolTip(f'At least some files/folders in this subdirectory cannot be uploaded (you do '
                                       f'not have permission)')
            restricted_item.setData(QtCore.Qt.UserRole, "subdirectory")
            restricted_item.setFlags(list_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            restricted_item.setCheckState(QtCore.Qt.Checked)

        # sort the files/subdirectories by item type (folder vs file) and alphabetically
        sorted_directory = sorted(os.listdir(self.directory), key=alpha_and_folder)

        # add each file and subdirectory to the list widget based on user permission
        for each in sorted_directory:
            list_item = QtWidgets.QListWidgetItem()
            if os.path.isfile(os.path.join(self.directory, each)):
                list_item.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_FileIcon)))
                if not os.access(os.path.join(self.directory, each), os.R_OK):
                    set_prohibited_item(list_item, "file")
                    self.warning = True
                else:
                    set_permitted_item(list_item, "file")
            elif os.path.isdir(os.path.join(self.directory, each)):
                list_item.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_DirIcon)))
                self.flag = False
                if not os.access(os.path.join(self.directory, each), os.X_OK | os.R_OK):
                    set_prohibited_item(list_item, "subdirectory")
                    self.warning = True
                elif self.subdirectory_contains_prohibited(os.path.join(self.directory, each)):
                    set_restricted_item(list_item)
                    self.warning = True
                else:
                    set_permitted_item(list_item, "subdirectory")
            else:
                continue
            self.listWidget_files.addItem(list_item)

    def submit(self) -> None:
        # retrieve deposition nickname
        self.nickname = self.plainTextEdit_nickname.toPlainText().strip()
        if not self.nickname:
            self.show_nickname_msg()
            return

        # add selected files to self.selected_files and create list of selected subdirectories
        selected_subdirectories = []

        for index in range(self.listWidget_files.count()):
            if self.listWidget_files.item(index).checkState() == QtCore.Qt.Checked:
                if self.listWidget_files.item(index).data(QtCore.Qt.UserRole) == "file":
                    self.selected_files.append(self.listWidget_files.item(index).text())
                elif self.listWidget_files.item(index).data(QtCore.Qt.UserRole) == "subdirectory":
                    selected_subdirectories.append(self.listWidget_files.item(index).text().
                                                   strip(f' ⚠️'))

        # recursively add files from selected subdirectories to selected_files list
        for subdir in selected_subdirectories:
            self.add_subdirectory_files(subdir)

        # set to true to ensure code in closeEvent method does not run
        self.select_submitted = True

        # close window
        self.close()

    def subdirectory_contains_prohibited(self, subdirectory: str) -> bool:
        # check if folder contains any prohibited item, if so return True
        if self.flag:
            return self.flag
        for item in os.listdir(subdirectory):
            if os.path.isfile(os.path.join(subdirectory, item)) and not os.access((os.path.join(
                    subdirectory, item)), os.R_OK):
                self.flag = True
            elif os.path.isdir(os.path.join(subdirectory, item)) and not os.access((os.path.join(
                    subdirectory, item)), os.X_OK | os.R_OK):
                self.flag = True
            elif os.path.isdir(os.path.join(subdirectory, item)) and os.access((os.path.join(
                    subdirectory, item)), os.X_OK | os.R_OK):
                self.subdirectory_contains_prohibited(f'{subdirectory}/{item}')
        return self.flag

    def add_subdirectory_files(self, subdirectory: str) -> None:
        # adds files from subdirectory to self.selected_files
        for each in os.listdir(os.path.join(self.directory, subdirectory)):
            if os.path.isfile(os.path.join(self.directory, subdirectory, each)) and os.access((os.path.join(
                    self.directory, subdirectory, each)), os.R_OK):
                self.selected_files.append(f'{subdirectory}/{each}')
            elif os.path.isdir(os.path.join(self.directory, subdirectory, each)) and os.access((os.path.join(
                    self.directory, subdirectory, each)), os.X_OK | os.R_OK):
                self.add_subdirectory_files(f'{subdirectory}/{each}')

    @staticmethod
    def show_warning_msg() -> None:
        # show message if no nickname provided
        msg = QMessageBox()
        msg.setWindowTitle("Warning")
        msg.setText("There are some files/folders in this directory which you do not have permission to upload.\n\n"
                    f"(Please hover over list items with a warning ⚠️ symbol next to them for details.)")
        msg.exec_()

    @staticmethod
    def show_nickname_msg() -> None:
        # show message if no nickname provided
        msg = QMessageBox()
        msg.setWindowTitle("Nickname needed")
        msg.setText("Deposition nickname is required.")
        msg.exec_()

    def cancel(self) -> None:
        self.close()

    def closeEvent(self, event) -> None:
        if not self.select_submitted:
            sys.exit()


def run_file_selector(directory: str) -> Tuple[str, List[str]]:
    app = QtWidgets.QApplication([])
    widget = FileSelector(directory)
    widget.show()
    app.exec_()
    return widget.nickname, widget.selected_files
