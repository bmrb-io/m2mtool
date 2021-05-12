import os
import sys
from typing import List

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QDesktopWidget

from bmrbdep import BMRBDepSession


class ProgressBar(QtWidgets.QWidget):
    def __init__(self, session, files):
        super().__init__()

        ui_path = os.path.join(os.path.dirname(__file__), 'bar.ui')
        uic.loadUi(ui_path, self)

        self.session: BMRBDepSession = session
        self.files: List[str] = files
        self.count: int = len(files)

        # center window on screen
        qt_rectangle = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        qt_rectangle.moveCenter(center_point)
        self.move(qt_rectangle.topLeft())

        # initialize display of progress bar text/image
        self.label.setText(f'0 of {self.count} files uploaded...')
        self.progressBar.setValue(0)

        # initialize file uploader, connect uploader to gui
        self.uploader: Uploader = Uploader(self.session, self.files)
        self.uploader.start()
        self.uploader.file_uploaded.connect(self.update_progress_bar)
        self.uploader.finished.connect(self.finished)

    def update_progress_bar(self, uploaded_count: int) -> None:
        # updates display of progress bar text/image
        self.label.setText(f'{uploaded_count} of {self.count} files uploaded...')
        self.progressBar.setValue(uploaded_count / self.count * 100)

    def finished(self) -> None:
        # runs after file upload finished
        self.close()
        self.show_success()

    def closeEvent(self, event) -> None:
        # runs if user closes window in middle of upload
        self.close()
        self.show_cancel()
        sys.exit()

    @staticmethod
    def show_success() -> None:
        # show success message after upload complete
        msg = QMessageBox()
        msg.setWindowTitle("Upload complete")
        msg.setText("Your files have been uploaded successfully.")
        msg.exec_()

    @staticmethod
    def show_cancel() -> None:
        # show cancellation message if user closes window
        msg = QMessageBox()
        msg.setWindowTitle("Upload cancelled")
        msg.setText("Your deposition upload was cancelled.")
        msg.exec_()


class Uploader(QtCore.QThread):
    # this class handles the actual file upload
    file_uploaded = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, session, files):
        super().__init__()
        self.session: BMRBDepSession = session
        self.files: List[str] = files

    def run(self):
        counter = 0
        for file in self.files:
            self.session.upload_file(file)
            counter += 1
            self.file_uploaded.emit(counter)
        self.finished.emit()


def run_progress_bar(session: BMRBDepSession, files: List[str]):
    app = QtWidgets.QApplication([])
    widget = ProgressBar(session, files)
    widget.show()
    app.exec_()
