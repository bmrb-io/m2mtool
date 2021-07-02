import os
import sys
import json
import logging
import time
import webbrowser
from typing import List
from tempfile import NamedTemporaryFile

import pynmrstar
import requests
from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QDesktopWidget

from m2mtool.bmrbdep import BMRBDepSession
from m2mtool.configuration import configuration
from m2mtool.helpers import ApiSession

logging.basicConfig()


class ProgressBar(QtWidgets.QWidget):
    def __init__(self, directory: str, nickname: str, files: List[str], session_file: str):
        super().__init__()

        ui_path = os.path.join(os.path.dirname(__file__), 'bar.ui')
        uic.loadUi(ui_path, self)

        self.directory: str = directory
        self.nickname: str = nickname
        self.files: List[str] = files
        self.count: int = len(files)
        self.session_file: str = session_file
        self.upload_complete: bool = False

        # center window on screen
        qt_rectangle = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        qt_rectangle.moveCenter(center_point)
        self.move(qt_rectangle.topLeft())

        # initialize display
        self.stackedWidget.setCurrentWidget(self.page_init)
        self.progressBar_init.setValue(0)

        # set up file upload progress bar (to be displayed later)
        self.label_upload.setText(f'0 of {self.count} files uploaded...')
        self.progressBar_upload.setValue(0)

        # initialize Uploader and Timer objects, and connect signals from both to gui
        self.uploader: Uploader = Uploader(self.directory, self.nickname, self.files, self.session_file)
        self.uploader.start()
        self.timer: Timer = Timer()
        self.timer.start()
        self.timer.tick.connect(self.update_init_progress_bar)
        self.uploader.start_upload.connect(self.start_upload)
        self.uploader.file_uploaded.connect(self.update_upload_progress_bar)
        self.uploader.upload_finished.connect(self.upload_finished)
        self.uploader.error.connect(self.handle_error)

    def update_init_progress_bar(self, bar_value: int) -> None:
        # animates the initial bar that appears during processes executed before file upload
        self.progressBar_init.setValue(bar_value)

    def start_upload(self) -> None:
        # changes the display when preparatory processes finish and file upload itself starts
        self.timer.stop_thread()
        self.stackedWidget.setCurrentWidget(self.page_upload)

    def update_upload_progress_bar(self, uploaded_count: int) -> None:
        # updates display of progress bar text/image when each file uploads
        self.label_upload.setText(f'{uploaded_count} of {self.count} files uploaded...')
        self.progressBar_upload.setValue(int(uploaded_count / self.count * 100))

    def upload_finished(self, session_url: str) -> None:
        # this runs after file upload finished
        self.upload_complete = True
        self.show_success()
        self.close()

        # open the session
        webbrowser.open_new_tab(session_url)

    def closeEvent(self, event) -> None:
        # handles user closing window in middle of upload
        if not self.upload_complete:
            if self.timer.isRunning():
                self.timer.stop_thread()
            if self.uploader.isRunning():
                self.uploader.stop_thread()
            self.show_cancel()
            sys.exit()

    def handle_error(self, err: Exception, error_data: str = None) -> None:
        if error_data == "retrieve_metadata_error":
            logging.exception("Encountered error when retrieving BMRBdep session metadata: %s", err)
        elif error_data:
            logging.exception("Encountered error when uploading file: %s\n%s", error_data, err)
        else:
            logging.exception("Encountered error: %s", err)
        if self.timer.isRunning():
            self.timer.stop_thread()
        if self.uploader.isRunning():
            self.uploader.stop_thread()
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
        # show error message to user
        msg = QMessageBox()
        msg.setWindowTitle("Error")
        msg.setText("Error occurred during file upload.\n\nPlease contact support@nmrbox.org.")
        msg.exec_()


class Uploader(QtCore.QThread):
    """ This class runs the processes that prepare for and complete the actual file upload."""

    # Define class level variables (signals emitted to gui)
    start_upload = pyqtSignal()
    file_uploaded = pyqtSignal(int)
    upload_finished = pyqtSignal(str)
    error = pyqtSignal(Exception, str)

    def __init__(self, directory: str, nickname: str, files: List[str], session_file: str):
        super().__init__()
        self.directory: str = directory
        self.nickname: str = nickname
        self.files: List[str] = files
        self.session_file: str = session_file
        self.error_occurred: bool = False

    @staticmethod
    def get_vm_version() -> str:
        # returns the version of the VM that is running
        try:
            with open('/etc/nmrbox.d/motd-identifier', 'r') as motd:
                return motd.readline().split(":")[1].strip()
        except (IOError, ValueError):
            logging.error('Could not determine the version of NMRbox running on this machine.')
            return 'unknown'

    def run(self):
        # handles the processes that prepare the file upload, as well as actual file upload

        # fetch the software list
        with ApiSession() as api:
            try:
                url = f"{configuration['api_root_url']}/user/get-bmrbdep-metadata"
                r = api.get(url, json={'path': self.directory, 'vm_id': self.get_vm_version()})
                r.raise_for_status()
            except requests.exceptions.HTTPError as err:
                self.error_occurred: bool = True
                self.error.emit(err, "retrieve_metadata_error")

            if not self.error_occurred:
                try:
                    with NamedTemporaryFile() as star_file:
                        star_file.write(r.text.encode())
                        star_file.flush()
                        star_file.seek(0)

                        user_email = pynmrstar.Entry.from_string(r.text).get_tag('_Contact_person.Email_address')[0]
                        self.start_upload.emit()

                        # upload the files
                        with BMRBDepSession(nmrstar_file=star_file,
                                            user_email=user_email,
                                            nickname=self.nickname) as bmrbdep_session:
                            counter = 0
                            for file in self.files:
                                try:
                                    bmrbdep_session.upload_file(file, self.directory)
                                except Exception as err:
                                    self.error_occurred: bool = True
                                    self.error.emit(err, file)
                                    break
                                counter += 1
                                self.file_uploaded.emit(counter)

                            if not self.error_occurred:
                                bmrbdep_session.delete_file('m2mtool_generated.str')

                        if not self.error_occurred:
                            with open(self.session_file, "w") as session_log:
                                session_info = {"sid": bmrbdep_session.sid, "ctime": time.time()}
                                session_log.write(json.dumps(session_info))

                            self.upload_finished.emit(bmrbdep_session.session_url)

                except IOError as err:
                    self.error.emit(err)

    def stop_thread(self):
        self.terminate()


class Timer(QtCore.QThread):
    """ This class uses a timer to periodically animate the initial bar (which appears while the processes
     that prepare the file upload are running)"""

    # Define class level variable (signal emitted to gui)
    tick = pyqtSignal(int)

    def __init__(self):
        super().__init__()

    def run(self):
        # run timer to periodically animate initial bar
        bar_value = 0
        while True:
            bar_value += 25
            if bar_value > 100:
                bar_value = 0
            time.sleep(1)
            self.tick.emit(bar_value)

    def stop_thread(self):
        self.terminate()


def run_progress_bar(directory: str, nickname: str, files: List[str], session_file: str):
    app = QtWidgets.QApplication([])
    widget = ProgressBar(directory, nickname, files, session_file)
    widget.show()
    app.exec_()
