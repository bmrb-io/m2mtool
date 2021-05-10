import os
from typing import List

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMessageBox

from bmrbdep import BMRBDepSession


class ProgressBar(QtWidgets.QWidget):
    def __init__(self, files, session):
        super().__init__()

        ui_path = os.path.join(os.path.dirname(__file__), 'bar.ui')
        uic.loadUi(ui_path, self)

        self.session: BMRBDepSession = session
        self.files: List[str] = files
        self.count: int = len(files)
        self.label.setText(f'0 of {self.count} files uploaded...')
        self.progressBar.setValue(0)

        self.uploader: Uploader = Uploader(self.files)
        self.uploader.start()
        self.uploader.file_uploaded.connect(self.update_progress_bar)
        self.uploader.finished.connect(self.finished)

    def update_progress_bar(self, uploaded_count: int) -> None:
        self.label.setText(f'{uploaded_count} of {self.count} files uploaded...')
        self.progressBar.setValue(uploaded_count / self.count * 100)

    def finished(self) -> None:
        self.close()
        self.show_success()

    @staticmethod
    def show_success() -> None:
        # show success message after upload complete
        msg = QMessageBox()
        msg.setWindowTitle("Upload complete")
        msg.setText("Your files have been uploaded successfully.")
        msg.exec_()


class Uploader(QtCore.QThread):
    file_uploaded = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, files):
        super().__init__()
        self.files = files
        self.count = len(files)

    def run(self):
        counter = 0
        for file in self.files:
            self.session.upload_file(file)
            counter += 1
            self.file_uploaded.emit(counter)
        self.finished.emit()


def run_progress_bar(files: List[str], session: BMRBDepSession):
    app = QtWidgets.QApplication([])
    widget = ProgressBar(files, session)
    widget.show()
    app.exec_()
