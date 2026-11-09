
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QGridLayout,
    QSizePolicy
)

from modules.students import StudentsModule
from modules.fees_invoices import FeesInvoicesModule
from PyQt6.QtCore import Qt


class ListecAccountingSystem(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "LISTEC College Accounting System"
        )

        self.resize(950, 700)
        self.setMinimumSize(800, 600)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #F4F6FA;
            }

            QLabel {
                color: #243247;
            }

            QPushButton {
                border: none;
                padding: 12px;
                text-align: left;
                color: #FFFFFF;
                font-size: 14px;
            }

            QPushButton:hover {
                background-color: #344D70;
            }
        """)

        self.create_interface()

    def create_interface(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # LEFT SIDEBAR

        sidebar = QFrame()
        sidebar.setFixedWidth(245)

        sidebar.setStyleSheet("""
            QFrame {
                background-color: #172B4D;
            }
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 25, 15, 20)
        sidebar_layout.setSpacing(8)

        logo = QLabel("LISTEC COLLEGE")
        logo.setStyleSheet("""
            color: white;
            font-size: 21px;
            font-weight: bold;
            padding: 10px;
        """)

        subtitle = QLabel("FINANCIAL MANAGEMENT")
        subtitle.setStyleSheet("""
            color: #B8C7DC;
            font-size: 10px;
            padding-left: 10px;
        """)

        sidebar_layout.addWidget(logo)
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(30)

        menu_items = [
            "Dashboard",
            "Student Management",
            "Fees & Invoices",
            "Payments & Receipts",
            "General Ledger",
            "Debtors & Creditors",
            "Payment Reminders",
            "Financial Reports",
            "Budgeting",
            "System Settings"
        ]

        for item in menu_items:

            button = QPushButton(item)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            if item == "Student Management":
                button.clicked.connect(self.open_students)
            if item == "Fees & Invoices":
             button.clicked.connect(self.open_fees_invoices)

            if item == "Dashboard":
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #344D70;
                        border-radius: 6px;
                        font-weight: bold;
                    }
                """)

            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()

        version = QLabel("LISTEC ACCOUNTING SYSTEM\nVersion 1.0")
        version.setStyleSheet("""
            color: #B8C7DC;
            font-size: 10px;
            padding: 10px;
        """)

        sidebar_layout.addWidget(version)

        # MAIN CONTENT

        content = QWidget()

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 25, 30, 25)
        content_layout.setSpacing(20)

        heading = QLabel("Financial Dashboard")
        heading.setStyleSheet("""
            font-size: 27px;
            font-weight: bold;
        """)

        welcome = QLabel(
            "Welcome to the LISTEC College Financial Management System"
        )

        welcome.setStyleSheet("""
            color: #718096;
            font-size: 13px;
        """)

        content_layout.addWidget(heading)
        content_layout.addWidget(welcome)

        # FINANCIAL SUMMARY CARDS

        cards_layout = QGridLayout()
        cards_layout.setSpacing(15)

        card_data = [
            ("TOTAL REVENUE", "R 0.00", "#2563EB"),
            ("PAYMENTS RECEIVED", "R 0.00", "#16A34A"),
            ("OUTSTANDING FEES", "R 0.00", "#D97706"),
            ("STUDENTS WITH DEBT", "0", "#DC2626")
        ]

        for index, (title, value, color) in enumerate(card_data):

            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 10px;
                }
            """)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 20, 20, 20)

            title_label = QLabel(title)
            title_label.setStyleSheet("""
                color: #718096;
                font-size: 11px;
                font-weight: bold;
            """)

            value_label = QLabel(value)
            value_label.setStyleSheet(f"""
                color: {color};
                font-size: 25px;
                font-weight: bold;
            """)

            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)

            cards_layout.addWidget(
                card,
                index // 2,
                index % 2
            )

        content_layout.addLayout(cards_layout)

        # LOWER DASHBOARD SECTIONS

        lower_layout = QHBoxLayout()
        lower_layout.setSpacing(15)

        transactions = QFrame()
        transactions.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
            }
        """)

        transaction_layout = QVBoxLayout(transactions)
        transaction_layout.setContentsMargins(20, 20, 20, 20)

        transaction_title = QLabel("Recent Transactions")
        transaction_title.setStyleSheet("""
            font-size: 17px;
            font-weight: bold;
        """)

        transaction_info = QLabel(
            "No transactions recorded yet."
        )

        transaction_info.setStyleSheet("""
            color: #718096;
            font-size: 13px;
            padding-top: 15px;
        """)

        transaction_layout.addWidget(transaction_title)
        transaction_layout.addWidget(transaction_info)
        transaction_layout.addStretch()

        overview = QFrame()
        overview.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
            }
        """)

        overview_layout = QVBoxLayout(overview)
        overview_layout.setContentsMargins(20, 20, 20, 20)

        overview_title = QLabel("Financial Overview")
        overview_title.setStyleSheet("""
            font-size: 17px;
            font-weight: bold;
        """)

        overview_info = QLabel(
            "Financial performance information\n"
            "will appear here once transactions\n"
            "are recorded."
        )

        overview_info.setStyleSheet("""
            color: #718096;
            font-size: 13px;
        """)

        overview_layout.addWidget(overview_title)
        overview_layout.addWidget(overview_info)
        overview_layout.addStretch()

        lower_layout.addWidget(transactions, 2)
        lower_layout.addWidget(overview, 1)

        content_layout.addLayout(lower_layout)
        content_layout.addStretch()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

    def open_students(self):

        self.students_window = StudentsModule()
        self.students_window.show()

    def open_fees_invoices(self):
        self.fees_window = FeesInvoicesModule()
        self.fees_window.show()

    def main(self):

        pass


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = ListecAccountingSystem()
    window.show()

    sys.exit(app.exec())
