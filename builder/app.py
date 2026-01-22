import sys
from PySide6.QtWidgets import QApplication
from builder.ui.main_window import MainWindow


def run_app() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Studio Folder Builder")
    app.setOrganizationName("Portfolio")

    win = MainWindow()
    win.show()

    return app.exec()
