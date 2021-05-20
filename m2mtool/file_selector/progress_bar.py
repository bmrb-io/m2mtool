import os
import sys
import logging
from typing import List

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QDesktopWidget

from m2mtool.bmrbdep import BMRBDepSession

logging.basicConfig()


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
        self.uploader.error.connect(self.handle_error)

    def update_progress_bar(self, uploaded_count: int) -> None:
        # updates display of progress bar text/image
        self.label.setText(f'{uploaded_count} of {self.count} files uploaded...')
        self.progressBar.setValue(int(uploaded_count / self.count * 100))

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

    def handle_error(self, err: Exception, file: str) -> None:
        logging.exception("Encountered error when uploading file: %s\n%s", file, err)
        self.show_error()
        sys.exit(1)

    @staticmethod
    def show_success() -> None:
        # show success message after upload complete
        msg = QMessageBox()
        msg.setWindowTitle("Upload complete")
        msg.setText("Your files have been uploaded successfully.")
        msg.exec_()

    @staticmethod
    def show_cancel() -> None:
        # show cancellation message if window closed before upload done
        msg = QMessageBox()
        msg.setWindowTitle("Upload cancelled")
        msg.setText("Your deposition upload was cancelled.")
        msg.exec_()

    @staticmethod
    def show_error() -> None:
        # show cancellation message if window closed before upload done
        msg = QMessageBox()
        msg.setWindowTitle("Error")
        msg.setText("Error occurred during file upload.\n\nPlease contact support@nmrbox.org.")
        msg.exec_()


class Uploader(QtCore.QThread):
    # this class handles the actual file upload
    file_uploaded = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(Exception, str)

    def __init__(self, session, files, directory):
        super().__init__()
        self.session: BMRBDepSession = session
        self.files: List[str] = files
        self.directory: str = directory
        self.error_occurred: bool = False

    def run(self):
        counter = 0
        for file in self.files:
            try:
                self.session.upload_file(file, self.directory)
            except Exception as err:
                self.error_occurred: bool = True
                self.error.emit(err, file)
                break
            counter += 1
            self.file_uploaded.emit(counter)
        if not self.error_occurred:
            self.finished.emit()

    def stop_thread(self):
        self.terminate()


def run_progress_bar(session: BMRBDepSession, files: List[str], directory: str):
    app = QtWidgets.QApplication([])
    widget = ProgressBar(session, files, directory)
    widget.show()
    app.exec_()
