import sys
from PyQt5 import QtWidgets

from file_selector.window import Window


def run_file_selector():
    app = QtWidgets.QApplication([])
    widget = Window()
    widget.show()
    sys.exit(app.exec_())
