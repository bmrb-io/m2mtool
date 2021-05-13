import os
import sys
import logging
from typing import List

import requests
from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QDesktopWidget

from bmrbdep import BMRBDepSession

logging.basicConfig(filename="debug.log", format='%(asctime)s %(name)s %(levelname)s %(message)s')
logging.getLogger().setLevel(logging.DEBUG)


class ProgressBar(QtWidgets.QWidget):
    def __init__(self, session: BMRBDepSession, files: List[str], directory: str):
        super().__init__()

        ui_path = os.path.join(os.path.dirname(__file__), 'bar.ui')
        uic.loadUi(ui_path, self)

        self.session: BMRBDepSession = session
        self.files: List[str] = files
        self.directory: str = directory
        self.count: int = len(files)
        self.upload_complete: bool = False

        # center window on screen
        qt_rectangle = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        qt_rectangle.moveCenter(center_point)
        self.move(qt_rectangle.topLeft())

        # initialize display of progress bar text/image
        self.label.setText(f'0 of {self.count} files uploaded...')
        self.progressBar.setValue(0)

        # initialize file uploader, connect uploader to gui
        self.uploader: Uploader = Uploader(self.session, self.files, self.directory)
        self.uploader.start()
        self.uploader.file_uploaded.connect(self.update_progress_bar)
        self.uploader.finished.connect(self.finished)

    def update_progress_bar(self, uploaded_count: int) -> None:
        # updates display of progress bar text/image
        self.label.setText(f'{uploaded_count} of {self.count} files uploaded...')
        self.progressBar.setValue(uploaded_count / self.count * 100)

    def finished(self) -> None:
        # runs after file upload finished
        self.upload_complete = True
        self.show_success()
        self.close()

    def closeEvent(self, event) -> None:
        # handles user closing window in middle of upload
        if not self.upload_complete:
            self.uploader.stop_thread()
            self.show_cancel()
            sys.exit()

    def show_success(self) -> None:
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

    def __init__(self, session, files, directory):
        super().__init__()
        self.session: BMRBDepSession = session
        self.files: List[str] = files
        self.directory: str = directory

    def run(self):
        counter = 0
        for file in self.files:
            try:
                print(f'On file {file}')
                self.session.upload_file(file, self.directory)
            except requests.exceptions.HTTPError as err:
                logging.exception("Encountered error when uploading file: %s\n%s", file, err)
                raise IOError('Error occurred during attempt to upload file.')
                # TODO: error above doesn't get raised to m2mtool, need to implement handling here
            counter += 1
            self.file_uploaded.emit(counter)
        self.finished.emit()

    def stop_thread(self):
        self.terminate()


def run_progress_bar(session: BMRBDepSession, files: List[str], directory: str):
    app = QtWidgets.QApplication([])
    widget = ProgressBar(session, files, directory)
    widget.show()
    app.exec_()
