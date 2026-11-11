import sys
from pathlib import Path
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import (
    QApplication,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from database.db import get_connection


class FinancialReportsModule(QMainWindow):
    """
    Financial Reports Module - View financial statements and reports.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("LISTEC College - Financial Reports")
        self.resize(1300, 900)
        self.setMinimumSize(1000, 700)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #F4F6FA;
            }
            QLabel {
                color: #243247;
                font-size: 13px;
            }
            QDateEdit {
                padding: 8px;
                background-color: white;
                border: 1px solid #CBD5E1;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #172B4D;
                color: white;
                padding: 10px 16px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #344D70;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #CBD5E1;
                gridline-color: #E2E8F0;
                font-size: 12px;
            }
            QTabWidget::pane {
                border: 1px solid #CBD5E1;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #E2E8F0;
                color: #243247;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #172B4D;
                color: white;
            }
        """)

        self._build_ui()
        self._load_dashboard()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        central = QWidget()
        scroll.setWidget(central)
        self.setCentralWidget(scroll)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Back button
        back_btn = QPushButton("← Back")
        back_btn.setMaximumWidth(100)
        back_btn.setStyleSheet("background-color: #64748B;")
        back_btn.clicked.connect(self.close)
        layout.addWidget(back_btn)

        # Title
        heading = QLabel("FINANCIAL REPORTS")
        heading.setStyleSheet(
            "font-size: 25px; font-weight: bold; color: #183153;"
        )
        subtitle = QLabel("View financial summaries, collections, and detailed reports.")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._build_dashboard_tab(), "Dashboard")
        tabs.addTab(self._build_revenue_tab(), "Revenue & Collections")
        tabs.addTab(self._build_debtors_tab(), "Debtors Report")
        tabs.addTab(self._build_course_summary_tab(), "Course Summary")
        layout.addWidget(tabs)

    def _build_dashboard_tab(self):
        """Main financial dashboard."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Summary cards
        summary_layout = QHBoxLayout()

        self.total_revenue_card = self._make_card("Total Revenue", "R 0.00", "#2563EB")
        self.collections_card = self._make_card("Collections Received", "R 0.00", "#16A34A")
        self.outstanding_card = self._make_card("Outstanding Balance", "R 0.00", "#DC2626")
        self.collection_rate_card = self._make_card("Collection Rate", "0%", "#2563EB")

        summary_layout.addWidget(self.total_revenue_card)
        summary_layout.addWidget(self.collections_card)
        summary_layout.addWidget(self.outstanding_card)
        summary_layout.addWidget(self.collection_rate_card)

        layout.addLayout(summary_layout)

        # Statistics table
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.setMaximumHeight(300)
        self.stats_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.stats_table)

        # Refresh and Print buttons
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_dashboard)
        print_btn = QPushButton("Print Dashboard")
        print_btn.clicked.connect(lambda: self._print_tab("Dashboard"))
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(print_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()
        return widget

    def _build_revenue_tab(self):
        """Revenue and collections report."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.revenue_table = QTableWidget()
        self.revenue_table.setColumnCount(4)
        self.revenue_table.setHorizontalHeaderLabels([
            "Invoice Number", "Student Name", "Amount", "Collected", "Outstanding"
        ])
        self.revenue_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.revenue_table)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_revenue)
        print_btn = QPushButton("Print Report")
        print_btn.clicked.connect(lambda: self._print_tab("Revenue"))
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(print_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def _build_debtors_tab(self):
        """Debtors/outstanding invoices report."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.debtors_table = QTableWidget()
        self.debtors_table.setColumnCount(6)
        self.debtors_table.setHorizontalHeaderLabels([
            "Student Number", "Student Name", "Total Owing",
            "Oldest Invoice", "Days Since", "Status"
        ])
        self.debtors_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.debtors_table)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_debtors)
        print_btn = QPushButton("Print Report")
        print_btn.clicked.connect(lambda: self._print_tab("Debtors"))
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(print_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def _build_course_summary_tab(self):
        """Course revenue summary."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.course_table = QTableWidget()
        self.course_table.setColumnCount(5)
        self.course_table.setHorizontalHeaderLabels([
            "Course Code", "Course Name", "Enrollments",
            "Total Invoiced", "Total Collected"
        ])
        self.course_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.course_table)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_courses)
        print_btn = QPushButton("Print Report")
        print_btn.clicked.connect(lambda: self._print_tab("Courses"))
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(print_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def _make_card(self, title, value, color):
        """Create a summary card."""
        frame = QWidget()
        frame.setStyleSheet(
            f"background-color: white; border: 2px solid {color}; "
            "border-radius: 10px; padding: 15px;"
        )
        layout = QVBoxLayout(frame)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 11px; color: #64748B; font-weight: bold;")

        value_lbl = QLabel(value)
        value_lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")
        value_lbl.setObjectName("value")

        layout.addWidget(title_lbl)
        layout.addWidget(value_lbl)
        layout.addStretch()

        frame.value_lbl = value_lbl
        return frame

    def _load_dashboard(self):
        """Load dashboard data."""
        connection = get_connection()
        try:
            # Get totals
            totals = connection.execute("""
                SELECT
                    COALESCE(SUM(i.total_amount), 0) AS total_invoiced,
                    COALESCE(SUM(p.amount), 0) AS total_collected
                FROM invoices i
                LEFT JOIN payments p ON p.invoice_id = i.id
            """).fetchone()

            total_invoiced = float(totals["total_invoiced"] or 0)
            total_collected = float(totals["total_collected"] or 0)
            outstanding = max(0.0, total_invoiced - total_collected)
            rate = (total_collected / total_invoiced * 100) if total_invoiced > 0 else 0

            # Update cards
            self.total_revenue_card.value_lbl.setText(f"R {total_invoiced:,.2f}")
            self.collections_card.value_lbl.setText(f"R {total_collected:,.2f}")
            self.outstanding_card.value_lbl.setText(f"R {outstanding:,.2f}")
            self.collection_rate_card.value_lbl.setText(f"{rate:.1f}%")

            # Load statistics
            stats = connection.execute("""
                SELECT
                    COUNT(DISTINCT i.id) AS total_invoices,
                    COUNT(DISTINCT i.student_id) AS total_students,
                    COUNT(DISTINCT p.id) AS total_payments,
                    COUNT(DISTINCT CASE WHEN i.status = 'Paid' THEN i.id END) AS paid_invoices,
                    COUNT(DISTINCT CASE WHEN i.status LIKE '%Unpaid%' THEN i.id END) AS unpaid_invoices
                FROM invoices i
                LEFT JOIN payments p ON p.invoice_id = i.id
            """).fetchone()

            self.stats_table.setRowCount(0)
            stats_data = [
                ("Total Invoices", str(stats["total_invoices"])),
                ("Total Students", str(stats["total_students"])),
                ("Total Payments", str(stats["total_payments"])),
                ("Paid Invoices", str(stats["paid_invoices"])),
                ("Unpaid/Partial", str(stats["unpaid_invoices"])),
            ]

            for i, (label, value) in enumerate(stats_data):
                self.stats_table.insertRow(i)
                self.stats_table.setItem(i, 0, QTableWidgetItem(label))
                self.stats_table.setItem(i, 1, QTableWidgetItem(value))

        finally:
            connection.close()

    def _load_revenue(self):
        """Load revenue and collections data."""
        connection = get_connection()
        try:
            invoices = connection.execute("""
                SELECT
                    i.invoice_number,
                    s.first_name || ' ' || s.last_name AS student_name,
                    i.total_amount,
                    COALESCE(SUM(p.amount), 0) AS collected
                FROM invoices i
                JOIN students s ON i.student_id = s.id
                LEFT JOIN payments p ON p.invoice_id = i.id
                GROUP BY i.id
                ORDER BY i.invoice_date DESC
            """).fetchall()

            self.revenue_table.setRowCount(0)
            for inv in invoices:
                total = float(inv["total_amount"] or 0)
                collected = float(inv["collected"] or 0)
                outstanding = max(0.0, total - collected)

                row = self.revenue_table.rowCount()
                self.revenue_table.insertRow(row)

                self.revenue_table.setItem(row, 0, QTableWidgetItem(inv["invoice_number"]))
                self.revenue_table.setItem(row, 1, QTableWidgetItem(inv["student_name"]))
                self.revenue_table.setItem(row, 2, QTableWidgetItem(f"R {total:,.2f}"))
                self.revenue_table.setItem(row, 3, QTableWidgetItem(f"R {collected:,.2f}"))
                self.revenue_table.setItem(row, 4, QTableWidgetItem(f"R {outstanding:,.2f}"))

        finally:
            connection.close()

    def _load_debtors(self):
        """Load debtors report."""
        connection = get_connection()
        try:
            debtors = connection.execute("""
                SELECT
                    s.student_number,
                    s.first_name || ' ' || s.last_name AS student_name,
                    SUM(i.total_amount) - COALESCE(SUM(p.amount), 0) AS total_owing,
                    MIN(i.invoice_date) AS oldest_invoice,
                    COUNT(DISTINCT i.id) AS num_invoices
                FROM students s
                JOIN invoices i ON i.student_id = s.id
                LEFT JOIN payments p ON p.invoice_id = i.id
                WHERE i.status != 'Paid'
                GROUP BY s.id
                HAVING total_owing > 0
                ORDER BY total_owing DESC
            """).fetchall()

            self.debtors_table.setRowCount(0)
            today = datetime.now().date()

            for debtor in debtors:
                oldest_date = datetime.strptime(debtor["oldest_invoice"], "%Y-%m-%d").date()
                days_since = (today - oldest_date).days

                status = "OVERDUE" if days_since > 0 else "DUE SOON"

                row = self.debtors_table.rowCount()
                self.debtors_table.insertRow(row)

                self.debtors_table.setItem(row, 0, QTableWidgetItem(debtor["student_number"]))
                self.debtors_table.setItem(row, 1, QTableWidgetItem(debtor["student_name"]))
                self.debtors_table.setItem(row, 2, QTableWidgetItem(f"R {debtor['total_owing']:,.2f}"))
                self.debtors_table.setItem(row, 3, QTableWidgetItem(debtor["oldest_invoice"]))
                self.debtors_table.setItem(row, 4, QTableWidgetItem(str(days_since)))
                self.debtors_table.setItem(row, 5, QTableWidgetItem(status))

        finally:
            connection.close()

    def _load_courses(self):
        """Load course summary data."""
        connection = get_connection()
        try:
            courses = connection.execute("""
                SELECT
                    c.course_code,
                    c.course_name,
                    COUNT(DISTINCT sc.id) AS enrollments,
                    COALESCE(SUM(i.total_amount), 0) AS total_invoiced,
                    COALESCE(SUM(p.amount), 0) AS total_collected
                FROM courses c
                LEFT JOIN student_courses sc ON c.id = sc.course_id
                LEFT JOIN invoices i ON sc.student_id = i.student_id
                LEFT JOIN payments p ON p.invoice_id = i.id
                GROUP BY c.id
                ORDER BY total_invoiced DESC
            """).fetchall()

            self.course_table.setRowCount(0)
            for course in courses:
                row = self.course_table.rowCount()
                self.course_table.insertRow(row)

                self.course_table.setItem(row, 0, QTableWidgetItem(course["course_code"]))
                self.course_table.setItem(row, 1, QTableWidgetItem(course["course_name"]))
                self.course_table.setItem(row, 2, QTableWidgetItem(str(course["enrollments"])))
                self.course_table.setItem(row, 3, QTableWidgetItem(f"R {course['total_invoiced']:,.2f}"))
                self.course_table.setItem(row, 4, QTableWidgetItem(f"R {course['total_collected']:,.2f}"))

        finally:
            connection.close()

    def _print_tab(self, tab_name):
        """Print the current tab."""
        QMessageBox.information(self, "Print", f"{tab_name} report will be printed.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FinancialReportsModule()
    window.show()
    sys.exit(app.exec())
