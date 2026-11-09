import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QWidget,
    QVBoxLayout
)
from PyQt6.QtCore import Qt


class ListecAccountingSystem(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "LISTEC College Accounting System"
        )

        self.setMinimumSize(1100, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        title = QLabel(
            "LISTEC COLLEGE ACCOUNTING SYSTEM"
        )

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #17365D;
            padding: 30px;
        """)

        subtitle = QLabel(
            "Financial Management System"
        )

        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle.setStyleSheet("""
            font-size: 18px;
            color: #555555;
        """)

        layout.addWidget(title)
        layout.addWidget(subtitle)


def main():

    app = QApplication(sys.argv)

    window = ListecAccountingSystem()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
