import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox


class Window(QtWidgets.QWidget):
    def __init__(self, err: IOError):
        super().__init__()
        self.error_text: str = str(err)
        self.show_error_to_user(self.error_text)

    @staticmethod
    def show_error_to_user(err: str) -> None:
        # show error message to user if a request fails
        msg = QMessageBox()
        msg.setWindowTitle("Error")
        error_message = err
        msg.setText(f"{error_message}\n\nPlease contact support@nmrbox.org.")

        msg.exec_()
        sys.exit()


def show_error(err: IOError):
    app = QtWidgets.QApplication([])
    widget = Window(err)  # we do not actually show this; we are using it as a foundation for QMessageBox
    app.exec_()
